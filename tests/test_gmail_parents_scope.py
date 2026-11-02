from __future__ import annotations

import asyncio
import json
import time
from collections.abc import Awaitable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TypeVar

import httpx
import pytest
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from maily.app.authz import Principal
from maily.app.routers import gmail as gmail_router
from maily.crypto import encrypt
from maily.db.models import ApiKey, Base, GmailAccount
from maily.exceptions import MailValidationError
from maily.http import HttpClient
from maily.providers.base import MailboxSpec
from maily.providers.gmail import (
    GmailOAuth,
    GmailParent,
    GmailProvider,
    MemoryGmailStore,
)
from maily.providers.gmail.db_store import DbGmailStore
from maily.settings import Settings

_T = TypeVar("_T")
_ROOT_EMAIL = "root@corp.io"
_OWN_EMAIL = "mine@corp.io"
_OTHER_EMAIL = "other@corp.io"
_KEPT_REFRESH = "refresh-kept"


def _run(coro: Awaitable[_T]) -> _T:
    return asyncio.run(coro)


def _scope(actions: list[str], parent_ids: list[int]) -> str:
    return json.dumps(
        {"providers": ["gmail"], "parent_ids": parent_ids, "actions": actions}
    )


def _principal(*, key_id: int, actions: list[str], parent_ids: list[int]) -> Principal:
    key = ApiKey(
        id=key_id,
        name="issued",
        prefix="mk_test",
        secret_enc="ciphertext-not-used",
        secret_sha256="abc",
        scope_json=_scope(actions, parent_ids),
        expires_at=None,
    )
    return Principal(is_root=False, key=key)


def _root() -> Principal:
    return Principal(is_root=True, key=None)


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'parents.db'}",
        secret_key="test-secret",
        _env_file=None,
    )


async def _profile_http(email: str) -> HttpClient:
    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/profile"):
            return httpx.Response(200, json={"emailAddress": email})
        if path.endswith("/settings/sendAs"):
            return httpx.Response(200, json={"sendAs": [{"sendAsEmail": email}]})
        if path.endswith("/token"):
            return httpx.Response(
                200,
                json={
                    "access_token": "refreshed",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                },
            )
        return httpx.Response(200, json={})

    http = HttpClient()
    await http._client.aclose()
    http._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return http


async def _direct_store(
    tmp_path: Path, secret: str
) -> tuple[DbGmailStore, async_sessionmaker[AsyncSession], AsyncEngine]:
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'direct.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return DbGmailStore(factory, secret), factory, engine


async def _seed_account(
    factory: async_sessionmaker[AsyncSession],
    secret: str,
    *,
    email: str,
    owner_key_id: int | None,
    refresh_token: str,
) -> GmailAccount:
    row = GmailAccount(
        email=email,
        refresh_token_enc=encrypt(secret, refresh_token),
        access_token_enc=encrypt(secret, "live-access"),
        access_expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
        + timedelta(hours=1),
        send_as_json=json.dumps([email]),
        status="active",
        owner_key_id=owner_key_id,
    )
    async with factory() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


async def _stored_refresh(store: DbGmailStore, email: str) -> str:
    parent = await store.get_by_email(email)
    assert parent is not None
    return parent.refresh_token


def _request(provider: GmailProvider) -> Request:
    app = FastAPI()
    app.state.gmail = provider
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/v1/gmail/accounts/import",
        "raw_path": b"/v1/gmail/accounts/import",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
        "app": app,
    }
    return Request(scope)


def test_import_of_root_owned_email_is_403_and_token_unchanged(tmp_path: Path) -> None:
    """Given a root-owned parent, a key import returns 403 and leaves the refresh token."""

    async def scenario() -> None:
        settings = _settings(tmp_path)
        secret = settings.resolved_secret_key()
        store, factory, engine = await _direct_store(tmp_path, secret)
        provider = None
        try:
            await _seed_account(
                factory,
                secret,
                email=_ROOT_EMAIL,
                owner_key_id=None,
                refresh_token=_KEPT_REFRESH,
            )
            http = await _profile_http(_ROOT_EMAIL)
            provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
            request = _request(provider)
            with pytest.raises(HTTPException) as caught:
                await gmail_router._upsert_parent(
                    request,
                    {"refresh_token": "stolen", "access_token": "at"},
                    7,
                )
            assert caught.value.status_code == 403
            assert await _stored_refresh(store, _ROOT_EMAIL) == _KEPT_REFRESH
        finally:
            if provider is not None:
                await provider.close()
            await engine.dispose()

    _run(scenario())


def test_new_import_records_caller_key_id(tmp_path: Path) -> None:
    """Given no existing parent, import stores the caller key id and the refresh token."""

    async def scenario() -> None:
        settings = _settings(tmp_path)
        secret = settings.resolved_secret_key()
        store, _factory, engine = await _direct_store(tmp_path, secret)
        provider = None
        try:
            http = await _profile_http(_OWN_EMAIL)
            provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
            request = _request(provider)
            parent = await gmail_router._upsert_parent(
                request,
                {"refresh_token": "fresh", "access_token": "at"},
                7,
            )
            stored = await store.get_by_email(_OWN_EMAIL)
            assert stored is not None
            assert stored.owner_key_id == 7
            assert stored.refresh_token == "fresh"
            assert parent.owner_key_id == 7
        finally:
            if provider is not None:
                await provider.close()
            await engine.dispose()

    _run(scenario())


def test_key_deletes_only_its_parent() -> None:
    """Given own and other parents, delete is allowed only when owner_key_id equals the caller."""
    own = GmailParent(id=1, email=_OWN_EMAIL, refresh_token="r", owner_key_id=7)
    other = GmailParent(id=2, email=_OTHER_EMAIL, refresh_token="r", owner_key_id=9)
    root_owned = GmailParent(
        id=3, email=_ROOT_EMAIL, refresh_token="r", owner_key_id=None
    )
    caller = _principal(key_id=7, actions=["parents:delete"], parent_ids=[])
    assert gmail_router._may_mutate_parent(caller, own) is True
    with pytest.raises(HTTPException) as other_caught:
        gmail_router._may_mutate_parent(caller, other)
    with pytest.raises(HTTPException) as root_caught:
        gmail_router._may_mutate_parent(caller, root_owned)
    assert other_caught.value.status_code == 403
    assert root_caught.value.status_code == 403
    assert gmail_router._may_mutate_parent(_root(), other) is True


def test_list_accounts_hides_other_keys_and_shows_granted_root_parents() -> None:
    """Given mixed owners, a key sees its parents plus root parents listed in parent_ids."""
    parents = [
        GmailParent(id=1, email=_OWN_EMAIL, refresh_token="r", owner_key_id=7),
        GmailParent(id=2, email=_OTHER_EMAIL, refresh_token="r", owner_key_id=9),
        GmailParent(id=3, email=_ROOT_EMAIL, refresh_token="r", owner_key_id=None),
        GmailParent(
            id=4, email="ungranted@corp.io", refresh_token="r", owner_key_id=None
        ),
    ]
    caller = _principal(key_id=7, actions=["parents:read"], parent_ids=[3])
    visible = gmail_router._visible_parents(caller, parents)
    assert [parent.id for parent in visible] == [1, 3]


def test_stale_oauth_state_expires_after_ttl() -> None:
    """Given a state older than 600 seconds, purge drops it using entry ts."""
    now = time.time()
    states = {
        "fresh": {"ts": now - 10, "owner_key_id": 7},
        "stale": {"ts": now - gmail_router._OAUTH_STATE_TTL - 1, "owner_key_id": None},
    }
    gmail_router._purge_stale_oauth_states(states, now)
    assert "stale" not in states
    assert states["fresh"]["owner_key_id"] == 7
    assert now - float(states["fresh"]["ts"]) <= gmail_router._OAUTH_STATE_TTL


@pytest.mark.asyncio
async def test_pick_parent_allow_list_skips_parents_outside_it() -> None:
    """Given an allow-list, auto-pick never returns a parent whose id is absent."""
    store = MemoryGmailStore()
    outside = await store.add(
        GmailParent(
            id=0,
            email="outside@corp.io",
            refresh_token="r",
            send_as=["outside@corp.io"],
        )
    )
    allowed = await store.add(
        GmailParent(
            id=0,
            email="allowed@corp.io",
            refresh_token="r",
            send_as=["allowed@corp.io"],
        )
    )
    http = await _profile_http("allowed@corp.io")
    provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
    spec = MailboxSpec(allowed_parent_ids=(allowed.id,))
    picked = await provider._pick_parent(spec)
    await provider.close()
    assert picked.id == allowed.id
    assert picked.id != outside.id


@pytest.mark.asyncio
async def test_pick_parent_empty_allow_list_raises_no_grant() -> None:
    """Given an empty allow-list, auto-pick raises the grant error and ignores active parents."""
    store = MemoryGmailStore()
    await store.add(GmailParent(id=0, email="active@corp.io", refresh_token="r"))
    http = await _profile_http("active@corp.io")
    provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
    with pytest.raises(MailValidationError, match="no gmail parent granted"):
        await provider._pick_parent(MailboxSpec(allowed_parent_ids=()))
    await provider.close()


def test_memory_store_persists_owner_key_id() -> None:
    """Given owner_key_id on add, memory get returns the same owner."""

    async def scenario() -> None:
        store = MemoryGmailStore()
        added = await store.add(
            GmailParent(id=0, email=_OWN_EMAIL, refresh_token="r", owner_key_id=7)
        )
        loaded = await store.get(added.id)
        assert loaded.owner_key_id == 7

    _run(scenario())


def test_db_store_round_trips_owner_key_id(tmp_path: Path) -> None:
    """Given owner_key_id on add, the DB row mapping returns it after update."""

    async def scenario() -> None:
        settings = _settings(tmp_path)
        secret = settings.resolved_secret_key()
        store, _factory, engine = await _direct_store(tmp_path, secret)
        try:
            added = await store.add(
                GmailParent(id=0, email=_OWN_EMAIL, refresh_token="r", owner_key_id=7)
            )
            added.status = "expired"
            await store.update(added)
            loaded = await store.get(added.id)
            assert loaded.owner_key_id == 7
            assert loaded.status == "expired"
            root_owned = await store.add(
                GmailParent(
                    id=0, email=_ROOT_EMAIL, refresh_token="r", owner_key_id=None
                )
            )
            assert (await store.get(root_owned.id)).owner_key_id is None
        finally:
            await engine.dispose()

    _run(scenario())
