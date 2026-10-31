"""Shared TestClient and Gmail HTTP stub for the API-key scope suite.

Given: Settings(api_key="root", _env_file=None) and create_app
When: a test needs a root key, an issued key, or a Gmail parent
Then: helpers return that client without calling the live Gmail API
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import parse_qs

import httpx
from fastapi.testclient import TestClient
from typing_extensions import TypedDict

from mailtmapi.app.main import create_app
from mailtmapi.crypto import encrypt
from mailtmapi.db.models import GmailAccount
from mailtmapi.http import HttpClient
from mailtmapi.settings import Settings

ROOT = "root"
FERNET = "x" * 32
PLUS_DETAIL = "gmail address must be a plus-alias"
_LIVE_ACCESS = time.time() + 3600


def client_for(tmp_path: Path, *, api_key: str = ROOT) -> TestClient:
    db = tmp_path / "api-keys.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            api_key=api_key,
            secret_key=FERNET,
            _env_file=None,
        )
    )
    return TestClient(app)


def auth(secret: str) -> dict[str, str]:
    return {"X-API-Key": secret}


class KeySpec(TypedDict, total=False):
    name: str
    providers: list[str]
    parent_ids: list[int]
    actions: list[str]
    expires_at: str | None


def key_body(spec: KeySpec | None = None) -> dict[str, object]:
    given = spec or {}
    return {
        "name": given.get("name", "ops"),
        "expires_at": given.get("expires_at"),
        "scope": {
            "providers": given.get("providers", ["stub"]),
            "parent_ids": given.get("parent_ids", []),
            "actions": given.get("actions", ["mailboxes:read", "mailboxes:write"]),
        },
        "retention": [],
    }


def issue(client: TestClient, spec: KeySpec | None = None) -> tuple[int, str]:
    created = client.post("/v1/admin/keys", json=key_body(spec), headers=auth(ROOT))
    assert created.status_code == 200, created.text
    body = created.json()
    return body["id"], body["secret"]


def forbid(response: httpx.Response) -> None:
    assert response.status_code == 403
    assert response.headers.get("x-mailtm-error") is None


def seed_parent(
    client: TestClient,
    *,
    email: str,
    refresh_token: str,
    owner_key_id: int | None,
) -> int:
    session_factory = client.app.state.session_factory

    async def _insert() -> int:
        async with session_factory() as session:
            row = GmailAccount(
                email=email,
                refresh_token_enc=encrypt(FERNET, refresh_token),
                access_token_enc=encrypt(FERNET, "live-access"),
                access_expires_at=datetime.now(timezone.utc).replace(tzinfo=None)
                + timedelta(hours=1),
                send_as_json=json.dumps([email]),
                status="active",
                owner_key_id=owner_key_id,
            )
            session.add(row)
            await session.commit()
            await session.refresh(row)
            return row.id

    parent_id = client.portal.call(_insert)
    assert isinstance(parent_id, int)
    return parent_id


def stored_refresh(client: TestClient, email: str) -> str:
    async def _load() -> str:
        parent = await client.app.state.gmail._store.get_by_email(email)
        assert parent is not None
        return parent.refresh_token

    token = client.portal.call(_load)
    assert isinstance(token, str)
    return token


def mailbox_parent(client: TestClient, mailbox_id: int) -> int | None:
    async def _load() -> int | None:
        from mailtmapi.db.models import Mailbox

        async with client.app.state.session_factory() as session:
            row = await session.get(Mailbox, mailbox_id)
            assert row is not None
            return row.parent_id

    parent_id = client.portal.call(_load)
    assert parent_id is None or isinstance(parent_id, int)
    return parent_id


class RecordingGmail:
    """MockTransport that answers profile and message reads and records trash."""

    def __init__(self, *, profile_email: str, message: dict | None = None) -> None:
        self.profile_email = profile_email
        self.message = message
        self.calls: list[tuple[str, str]] = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append((request.method, request.url.path))
        path = request.url.path
        query = parse_qs(request.url.query.decode())
        fmt = query.get("format", [None])[0]
        if path.endswith("/token"):
            return httpx.Response(
                200,
                json={"access_token": "refreshed", "expires_in": 3600, "token_type": "Bearer"},
            )
        if path.endswith("/profile"):
            return httpx.Response(200, json={"emailAddress": self.profile_email})
        if path.endswith("/settings/sendAs"):
            return httpx.Response(200, json={"sendAs": [{"sendAsEmail": self.profile_email}]})
        if request.method == "GET" and path.endswith("/messages/m1") and fmt == "full":
            return httpx.Response(200, json=self.message or {})
        if request.method == "POST" and path.endswith("/trash"):
            return httpx.Response(200, json={"id": "m1", "threadId": "t1"})
        return httpx.Response(404, json={"detail": path})

    def trash_calls(self) -> list[tuple[str, str]]:
        return [call for call in self.calls if call[1].endswith("/trash")]


def stub_gmail(client: TestClient, recorder: RecordingGmail) -> None:
    """Swap the app HTTP client so Gmail never leaves the process."""

    async def _swap() -> None:
        http: HttpClient = client.app.state.http
        await http._client.aclose()
        http._client = httpx.AsyncClient(transport=httpx.MockTransport(recorder.handler))

    client.portal.call(_swap)
