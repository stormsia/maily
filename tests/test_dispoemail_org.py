from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.http import HttpClient
from mailtmapi.providers.base import MailboxInfo, MailboxSpec
from mailtmapi.providers.dispoemail_org import DispoEmailOrg
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.settings import Settings

SECRET = "test-secret"


def _http(handler) -> HttpClient:
    http = HttpClient.__new__(HttpClient)
    http._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    return http


def _mailbox() -> MailboxInfo:
    return MailboxInfo(
        provider="dispoemail.org",
        address="m472e0b2w5@vibe-hub.ccwu.cc",
        token="0dde64f0955412c055d5e2acc9a430eb42005856787e8ee894b8af8ae09c1573",
        provider_account_id="m472e0b2w5@vibe-hub.ccwu.cc",
    )


@pytest.mark.asyncio
async def test_dispoemail_fetch_targets():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/active-domains":
            return httpx.Response(
                200,
                json={
                    "domains": [
                        "pmmaster.kdns.fr",
                        "toolaster.kdns.fr",
                        "vibe-hub.ccwu.cc",
                        "vibe-hub.de5.net",
                    ]
                },
            )
        return httpx.Response(404)

    http = _http(handler)
    provider = DispoEmailOrg(http)
    try:
        targets = await provider.list_targets()
        assert len(targets) == 4
        assert targets[0].id == "pmmaster.kdns.fr"
        assert targets[0].provider == "dispoemail.org"
        assert targets[2].id == "vibe-hub.ccwu.cc"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_dispoemail_create_and_delete_mailbox():
    deleted_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal deleted_called
        if request.url.path == "/api/active-domains":
            return httpx.Response(200, json={"domains": ["vibe-hub.ccwu.cc"]})
        if request.url.path == "/api/session/mailboxes":
            assert request.method == "POST"
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "tokens": {
                        "m472e0b2w5@vibe-hub.ccwu.cc": "0dde64f0955412c055d5e2acc9a430eb42005856787e8ee894b8af8ae09c1573"
                    },
                    "denied": [],
                },
            )
        if request.url.path == "/api/inboxes/m472e0b2w5":
            assert request.method == "DELETE"
            assert request.url.query.decode() == "domain=vibe-hub.ccwu.cc"
            assert (
                request.headers.get("x-mailbox-token")
                == "0dde64f0955412c055d5e2acc9a430eb42005856787e8ee894b8af8ae09c1573"
            )
            deleted_called = True
            return httpx.Response(200, json={"ok": True, "deleted": 1})
        return httpx.Response(404)

    http = _http(handler)
    provider = DispoEmailOrg(http)
    try:
        box = await provider.create_mailbox(MailboxSpec(address="m472e0b2w5@vibe-hub.ccwu.cc"))
        assert box.address == "m472e0b2w5@vibe-hub.ccwu.cc"
        assert box.provider == "dispoemail.org"
        assert box.token == "0dde64f0955412c055d5e2acc9a430eb42005856787e8ee894b8af8ae09c1573"

        ok = await provider.delete_mailbox(box)
        assert ok is True
        assert deleted_called is True
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_dispoemail_list_and_get_messages():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/inboxes/m690v3w4h715c":
            assert (
                request.headers.get("x-mailbox-token")
                == "292ffd79fb59f8133b43da30a5e276fe8c11a8950f90b9622866b661fa8df7df"
            )
            assert request.url.query.decode() == "domain=vibe-hub.ccwu.cc"
            return httpx.Response(
                200,
                json={
                    "mailbox": "m690v3w4h715c",
                    "domain": "vibe-hub.ccwu.cc",
                    "ttlMs": 86400000,
                    "messages": [
                        {
                            "id": "f6c38518-3a9b-484c-bff1-c74eba89beef",
                            "mailbox": "m690v3w4h715c",
                            "from": {"name": "иван таран", "address": "mister.ivan.boss@gmail.com"},
                            "subject": "test theme",
                            "receivedAt": "2026-10-28T20:49:10.745Z",
                            "expiresAt": "2026-10-29T20:49:10.745Z",
                            "preview": "test text",
                            "hasHtml": True,
                            "attachments": 0,
                            "threatStatus": "clean",
                        }
                    ],
                },
            )
        if request.url.path == "/api/messages/f6c38518-3a9b-484c-bff1-c74eba89beef":
            assert (
                request.headers.get("x-mailbox-token")
                == "292ffd79fb59f8133b43da30a5e276fe8c11a8950f90b9622866b661fa8df7df"
            )
            return httpx.Response(
                200,
                json={
                    "message": {
                        "id": "f6c38518-3a9b-484c-bff1-c74eba89beef",
                        "mailbox": "m690v3w4h715c",
                        "address": "m690v3w4h715c@vibe-hub.ccwu.cc",
                        "subject": "test theme",
                        "from": {"name": "иван таран", "address": "mister.ivan.boss@gmail.com"},
                        "to": [{"name": "", "address": "m690v3w4h715c@vibe-hub.ccwu.cc"}],
                        "cc": [],
                        "receivedAt": "2026-10-28T20:49:10.745Z",
                        "expiresAt": "2026-10-29T20:49:10.745Z",
                        "text": "test text\n\n",
                        "html": "<div>test text</div>\n\n",
                        "preview": "test text",
                        "attachments": [],
                        "threatStatus": "clean",
                    }
                },
            )
        return httpx.Response(404)

    http = _http(handler)
    provider = DispoEmailOrg(http)
    box = MailboxInfo(
        provider="dispoemail.org",
        address="m690v3w4h715c@vibe-hub.ccwu.cc",
        token="292ffd79fb59f8133b43da30a5e276fe8c11a8950f90b9622866b661fa8df7df",
    )
    try:
        messages = await provider.list_messages(box)
        assert len(messages) == 1
        assert messages[0].id == "f6c38518-3a9b-484c-bff1-c74eba89beef"
        assert messages[0].subject == "test theme"
        assert messages[0].from_.name == "иван таран"
        assert messages[0].from_.address == "mister.ivan.boss@gmail.com"

        detail = await provider.get_message(box, "f6c38518-3a9b-484c-bff1-c74eba89beef")
        assert detail.id == "f6c38518-3a9b-484c-bff1-c74eba89beef"
        assert detail.subject == "test theme"
        assert "test text" in detail.text
        assert "<div>test text</div>" in detail.html[0]

        src = await provider.get_source(box, "f6c38518-3a9b-484c-bff1-c74eba89beef")
        assert "<div>test text</div>" in src.data
    finally:
        await http.close()


def test_dispoemail_full_api_flow(tmp_path: Path):
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/active-domains":
            return httpx.Response(200, json={"domains": ["vibe-hub.ccwu.cc"]})
        if request.url.path == "/api/session/mailboxes":
            return httpx.Response(
                200,
                json={
                    "ok": True,
                    "tokens": {
                        "m690v3w4h715c@vibe-hub.ccwu.cc": "token-xyz"
                    },
                    "denied": [],
                },
            )
        if request.url.path == "/api/inboxes/m690v3w4h715c":
            if request.method == "DELETE":
                return httpx.Response(200, json={"ok": True, "deleted": 1})
            return httpx.Response(
                200,
                json={
                    "mailbox": "m690v3w4h715c",
                    "domain": "vibe-hub.ccwu.cc",
                    "ttlMs": 86400000,
                    "messages": [
                        {
                            "id": "msg-123",
                            "mailbox": "m690v3w4h715c",
                            "from": {"name": "Sender", "address": "sender@test.com"},
                            "subject": "Welcome",
                            "receivedAt": "2026-10-28T20:49:10.745Z",
                            "preview": "Hello there",
                            "hasHtml": True,
                        }
                    ],
                },
            )
        if request.url.path == "/api/messages/msg-123":
            return httpx.Response(
                200,
                json={
                    "message": {
                        "id": "msg-123",
                        "mailbox": "m690v3w4h715c",
                        "address": "m690v3w4h715c@vibe-hub.ccwu.cc",
                        "subject": "Welcome",
                        "from": {"name": "Sender", "address": "sender@test.com"},
                        "receivedAt": "2026-10-28T20:49:10.745Z",
                        "text": "Hello there\n",
                        "html": "<p>Hello there</p>",
                    }
                },
            )
        return httpx.Response(404)

    http = _http(handler)
    provider = DispoEmailOrg(http)
    registry = ProviderRegistry([provider])

    db_path = tmp_path / "test.db"
    settings = Settings(
        api_key="",
        database_url=f"sqlite+aiosqlite:///{db_path}",
        secret_key="0" * 32,
        domain_cache_enabled=False,
    )
    app = create_app(settings)

    with TestClient(app) as client:
        app.state.registry = registry

        # 1. Targets
        resp = client.get("/v1/targets")
        assert resp.status_code == 200
        domains = resp.json()
        assert any(d["label"] == "vibe-hub.ccwu.cc" for d in domains)

        # 2. Create Mailbox
        r = client.post(
            "/v1/mailboxes",
            json={"provider": "dispoemail.org", "address": "m690v3w4h715c@vibe-hub.ccwu.cc"},
        )
        assert r.status_code == 200, r.text
        box_data = r.json()
        box_id = box_data["id"]
        assert box_data["address"] == "m690v3w4h715c@vibe-hub.ccwu.cc"
        assert box_data["provider"] == "dispoemail.org"

        # 3. List messages
        r = client.get(f"/v1/mailboxes/{box_id}/messages")
        assert r.status_code == 200
        msgs = r.json()
        assert len(msgs) == 1
        assert msgs[0]["message_api_id"] == "msg-123"
        assert msgs[0]["subject"] == "Welcome"

        # 4. Get message
        r = client.get(f"/v1/mailboxes/{box_id}/messages/msg-123")
        assert r.status_code == 200
        detail = r.json()
        assert detail["subject"] == "Welcome"
        assert "Hello there" in detail["text"]

        # 5. Delete mailbox
        r = client.delete(f"/v1/mailboxes/{box_id}")
        assert r.status_code == 204
