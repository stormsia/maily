from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Awaitable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import TypeVar

import pytest
from fastapi import FastAPI, HTTPException, Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from mailtmapi.app.authz import (
    Principal,
    owns_mailbox,
    parent_allowed,
    provider_allowed,
    require_action,
    require_principal,
    require_root,
)
from mailtmapi.db.models import ApiKey, Base, Mailbox
from mailtmapi.settings import Settings

_T = TypeVar("_T")


def _run(coro: Awaitable[_T]) -> _T:
    return asyncio.run(coro)


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _sha256(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def _settings(tmp_path: Path, **kwargs: str) -> Settings:
    db = tmp_path / "authz.db"
    return Settings(
        database_url=f"sqlite+aiosqlite:///{db}",
        secret_key="test-secret",
        _env_file=None,
        **kwargs,
    )


def _request(settings: Settings) -> Request:
    app = FastAPI()
    app.state.settings = settings
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/probe",
        "raw_path": b"/probe",
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 123),
        "server": ("test", 80),
        "app": app,
    }
    return Request(scope)


@dataclass(frozen=True, slots=True)
class _Db:
    factory: async_sessionmaker[AsyncSession]
    engine: AsyncEngine


async def _direct_db(tmp_path: Path) -> _Db:
    """Schema from models, not Alembic. Migration 009 cannot add SQLite FKs yet."""
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'direct.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return _Db(factory=async_sessionmaker(engine, expire_on_commit=False), engine=engine)


async def _call_principal(
    settings: Settings,
    factory: async_sessionmaker[AsyncSession],
    *,
    x_api_key: str | None = None,
    authorization: str | None = None,
) -> Principal:
    async with factory() as session:
        return await require_principal(
            _request(settings),
            session,
            authorization,
            x_api_key,
        )


def _status(exc: HTTPException) -> tuple[int, str, str | None]:
    headers = exc.headers or {}
    detail = exc.detail if isinstance(exc.detail, str) else ""
    return exc.status_code, detail, headers.get("X-MailTM-Error")


async def _insert_key(
    factory: async_sessionmaker[AsyncSession],
    *,
    secret: str,
    scope_json: str,
    expires_at: datetime | None,
) -> ApiKey:
    row = ApiKey(
        name="issued",
        prefix=secret[:8],
        secret_enc="ciphertext-not-used",
        secret_sha256=_sha256(secret),
        scope_json=scope_json,
        expires_at=expires_at,
    )
    async with factory() as session:
        session.add(row)
        await session.commit()
        await session.refresh(row)
    return row


def _scope(providers: list[str], parent_ids: list[int], actions: list[str]) -> str:
    return json.dumps({"providers": providers, "parent_ids": parent_ids, "actions": actions})


def _principal(*, scope_json: str, key_id: int = 3) -> Principal:
    key = ApiKey(
        id=key_id,
        name="issued",
        prefix="mk_test",
        secret_enc="ciphertext-not-used",
        secret_sha256="abc",
        scope_json=scope_json,
        expires_at=None,
    )
    return Principal(is_root=False, key=key)


def test_empty_api_key_yields_root_without_header(tmp_path: Path) -> None:
    # Given MAILTM_API_KEY is empty (open mode)
    # When require_principal runs with no credential
    # Then the principal is root and no header is required

    async def _body() -> Principal:
        db = await _direct_db(tmp_path)
        try:
            return await _call_principal(_settings(tmp_path, api_key=""), db.factory)
        finally:
            await db.engine.dispose()

    principal = _run(_body())
    assert principal.is_root is True
    assert principal.key is None


def test_presented_env_key_yields_root(tmp_path: Path) -> None:
    # Given MAILTM_API_KEY is set
    # When that exact secret is presented to require_principal
    # Then the principal is root

    async def _body() -> Principal:
        db = await _direct_db(tmp_path)
        try:
            return await _call_principal(
                _settings(tmp_path, api_key="root-secret"),
                db.factory,
                x_api_key="root-secret",
            )
        finally:
            await db.engine.dispose()

    principal = _run(_body())
    assert principal.is_root is True
    assert principal.key is None


def test_unknown_secret_is_401_with_api_key_header(tmp_path: Path) -> None:
    # Given MAILTM_API_KEY is set and the presented secret is not stored
    # When require_principal runs
    # Then the error is 401 invalid api key with X-MailTM-Error: api_key

    async def _body() -> HTTPException:
        db = await _direct_db(tmp_path)
        try:
            await _call_principal(
                _settings(tmp_path, api_key="root-secret"),
                db.factory,
                x_api_key="not-a-key",
            )
        except HTTPException as exc:
            return exc
        else:
            raise AssertionError("expected 401")
        finally:
            await db.engine.dispose()

    status, detail, header = _status(_run(_body()))
    assert status == 401
    assert detail == "invalid api key"
    assert header == "api_key"


def test_expired_key_is_401_with_api_key_header(tmp_path: Path) -> None:
    # Given a stored key whose expires_at is before utc now
    # When that secret is presented to require_principal
    # Then the error is 401 invalid api key with X-MailTM-Error: api_key

    async def _body() -> HTTPException:
        db = await _direct_db(tmp_path)
        secret = "mk_expired"
        try:
            await _insert_key(
                db.factory,
                secret=secret,
                scope_json=_scope([], [], ["mailboxes:read"]),
                expires_at=_utcnow_naive() - timedelta(seconds=1),
            )
            await _call_principal(
                _settings(tmp_path, api_key="root-secret"),
                db.factory,
                x_api_key=secret,
            )
        except HTTPException as exc:
            return exc
        else:
            raise AssertionError("expected 401")
        finally:
            await db.engine.dispose()

    status, detail, header = _status(_run(_body()))
    assert status == 401
    assert detail == "invalid api key"
    assert header == "api_key"


def test_known_unexpired_key_is_not_root(tmp_path: Path) -> None:
    # Given a stored unexpired key
    # When that secret is presented to require_principal
    # Then is_root is False and the principal carries that key

    async def _body() -> tuple[Principal, int]:
        db = await _direct_db(tmp_path)
        secret = "mk_live"
        try:
            key = await _insert_key(
                db.factory,
                secret=secret,
                scope_json=_scope(["mail.tm"], [7], ["mailboxes:read"]),
                expires_at=None,
            )
            principal = await _call_principal(
                _settings(tmp_path, api_key="root-secret"),
                db.factory,
                x_api_key=secret,
            )
            return principal, key.id
        finally:
            await db.engine.dispose()

    principal, key_id = _run(_body())
    assert principal.is_root is False
    assert principal.key is not None
    assert principal.key.id == key_id


def test_require_action_missing_is_403_without_api_key_header(tmp_path: Path) -> None:
    # Given an unexpired key whose actions omit mailboxes:write
    # When require_action("mailboxes:write") runs
    # Then the response is 403 forbidden and does not set X-MailTM-Error

    async def _body() -> HTTPException:
        db = await _direct_db(tmp_path)
        try:
            key = await _insert_key(
                db.factory,
                secret="mk_readonly",
                scope_json=_scope([], [], ["mailboxes:read"]),
                expires_at=None,
            )
            await require_action("mailboxes:write")(Principal(is_root=False, key=key))
        except HTTPException as exc:
            return exc
        else:
            raise AssertionError("expected 403")
        finally:
            await db.engine.dispose()

    status, detail, header = _status(_run(_body()))
    assert status == 403
    assert detail == "forbidden"
    assert header is None


def test_require_root_is_403_for_issued_key(tmp_path: Path) -> None:
    # Given an unexpired issued key
    # When require_root runs
    # Then the response is 403 forbidden with no X-MailTM-Error header

    async def _body() -> HTTPException:
        db = await _direct_db(tmp_path)
        try:
            key = await _insert_key(
                db.factory,
                secret="mk_issued",
                scope_json=_scope([], [], ["mailboxes:read", "mailboxes:write"]),
                expires_at=None,
            )
            await require_root(Principal(is_root=False, key=key))
        except HTTPException as exc:
            return exc
        else:
            raise AssertionError("expected 403")
        finally:
            await db.engine.dispose()

    status, detail, header = _status(_run(_body()))
    assert status == 403
    assert detail == "forbidden"
    assert header is None


def test_provider_allowed_empty_or_listed() -> None:
    # Given scopes with an empty providers list and a list that contains the slug
    # When provider_allowed is called
    # Then empty allows every slug, a listed slug is allowed, and a missing slug is not
    empty = _principal(scope_json=_scope([], [], []))
    listed = _principal(scope_json=_scope(["mail.tm"], [], []))
    assert provider_allowed(empty, "gmail") is True
    assert provider_allowed(listed, "mail.tm") is True
    assert provider_allowed(listed, "gmail") is False


def test_parent_allowed_empty_denies_and_listed_allows() -> None:
    # Given parent_ids empty, and a list that contains one id
    # When parent_allowed is called
    # Then empty denies every id, and only the listed id is allowed
    empty = _principal(scope_json=_scope([], [], []))
    listed = _principal(scope_json=_scope([], [4], []))
    assert parent_allowed(empty, 4) is False
    assert parent_allowed(listed, 4) is True
    assert parent_allowed(listed, 9) is False


def test_owns_mailbox_root_always_and_issued_only_when_owner_matches() -> None:
    # Given a root principal and an issued key
    # When owns_mailbox is called
    # Then root owns every mailbox, and the issued key owns only its own
    root = Principal(is_root=True, key=None)
    issued = _principal(scope_json=_scope([], [], []), key_id=3)
    own = Mailbox(owner_key_id=3)
    other = Mailbox(owner_key_id=999)
    assert owns_mailbox(root, own) is True
    assert owns_mailbox(root, other) is True
    assert owns_mailbox(issued, own) is True
    assert owns_mailbox(issued, other) is False


def test_bearer_extracts_like_require_api_key(tmp_path: Path) -> None:
    # Given MAILTM_API_KEY is set
    # When the secret is sent as Authorization: Bearer to require_principal
    # Then the principal is root

    async def _body() -> Principal:
        db = await _direct_db(tmp_path)
        try:
            return await _call_principal(
                _settings(tmp_path, api_key="root-secret"),
                db.factory,
                authorization="Bearer root-secret",
            )
        finally:
            await db.engine.dispose()

    principal = _run(_body())
    assert principal.is_root is True
    assert principal.key is None


def test_invalid_scope_json_denies_action_and_allow_helpers(tmp_path: Path) -> None:
    # Given a stored key whose scope_json is not valid JSON
    # When require_action runs and the allow helpers read the scope
    # Then the action is 403 and both allow helpers are False

    async def _body() -> tuple[HTTPException, Principal]:
        db = await _direct_db(tmp_path)
        principal = Principal(is_root=False, key=None)
        try:
            key = await _insert_key(
                db.factory,
                secret="mk_badjson",
                scope_json="{not-json",
                expires_at=None,
            )
            principal = Principal(is_root=False, key=key)
            await require_action("mailboxes:write")(principal)
        except HTTPException as exc:
            return exc, principal
        else:
            raise AssertionError("expected 403")
        finally:
            await db.engine.dispose()

    exc, principal = _run(_body())
    status, detail, header = _status(exc)
    assert status == 403
    assert detail == "forbidden"
    assert header is None
    assert provider_allowed(principal, "mail.tm") is False
    assert parent_allowed(principal, 1) is False


def test_null_expires_at_never_expires(tmp_path: Path) -> None:
    # Given a stored key with expires_at null
    # When that secret is presented to require_principal
    # Then the principal is that issued key

    async def _body() -> tuple[Principal, int]:
        db = await _direct_db(tmp_path)
        secret = "mk_forever"
        try:
            key = await _insert_key(
                db.factory,
                secret=secret,
                scope_json=_scope([], [], []),
                expires_at=None,
            )
            principal = await _call_principal(
                _settings(tmp_path, api_key="root-secret"),
                db.factory,
                x_api_key=secret,
            )
            return principal, key.id
        finally:
            await db.engine.dispose()

    principal, key_id = _run(_body())
    assert principal.is_root is False
    assert principal.key is not None
    assert principal.key.id == key_id


def test_require_action_needs_every_named_action(tmp_path: Path) -> None:
    # Given a key that has only one of two required actions
    # When require_action demands both
    # Then the response is 403

    async def _body() -> HTTPException:
        db = await _direct_db(tmp_path)
        try:
            key = await _insert_key(
                db.factory,
                secret="mk_partial",
                scope_json=_scope([], [], ["mailboxes:read"]),
                expires_at=None,
            )
            await require_action("mailboxes:read", "mailboxes:write")(Principal(is_root=False, key=key))
        except HTTPException as exc:
            return exc
        else:
            raise AssertionError("expected 403")
        finally:
            await db.engine.dispose()

    status, detail, _header = _status(_run(_body()))
    assert status == 403
    assert detail == "forbidden"


def test_root_bypasses_require_action() -> None:
    # Given a root principal
    # When require_action runs
    # Then the same principal is returned

    async def _body() -> Principal:
        return await require_action("mailboxes:write")(Principal(is_root=True, key=None))

    resolved = _run(_body())
    assert resolved.is_root is True
    assert resolved.key is None


def test_env_key_wins_over_colliding_row(tmp_path: Path) -> None:
    # Given a stored key whose secret equals settings.api_key and is already expired
    # When that secret is presented to require_principal
    # Then the principal is root, not the expired row

    async def _body() -> Principal:
        db = await _direct_db(tmp_path)
        try:
            await _insert_key(
                db.factory,
                secret="root-secret",
                scope_json=_scope(["mail.tm"], [], []),
                expires_at=_utcnow_naive() - timedelta(days=1),
            )
            return await _call_principal(
                _settings(tmp_path, api_key="root-secret"),
                db.factory,
                x_api_key="root-secret",
            )
        finally:
            await db.engine.dispose()

    principal = _run(_body())
    assert principal.is_root is True
    assert principal.key is None


def test_expiry_equal_to_now_is_401(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Given expires_at equal to the clock authz uses
    # When that secret is presented to require_principal
    # Then the key is rejected as expired
    frozen = datetime(2020, 1, 1, 0, 0, 0)

    async def _body() -> HTTPException:
        db = await _direct_db(tmp_path)
        secret = "mk_exact"
        try:
            await _insert_key(
                db.factory,
                secret=secret,
                scope_json=_scope([], [], []),
                expires_at=frozen,
            )
            await _call_principal(
                _settings(tmp_path, api_key="root-secret"),
                db.factory,
                x_api_key=secret,
            )
        except HTTPException as exc:
            return exc
        else:
            raise AssertionError("expected 401")
        finally:
            await db.engine.dispose()

    monkeypatch.setattr("mailtmapi.app.authz.utcnow_naive", lambda: frozen)
    status, detail, header = _status(_run(_body()))
    assert status == 401
    assert detail == "invalid api key"
    assert header == "api_key"
