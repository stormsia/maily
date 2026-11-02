from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from maily.app.main import create_app
from maily.exceptions import MailAuthError
from maily.http import HttpClient
from maily.providers.base import MailboxInfo, MailboxSpec
from maily.providers.dispoemail_org import DispoEmailOrg
from maily.providers.registry import ProviderRegistry
from maily.settings import Settings

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
                            "from": {
                                "name": "Ivan Taran",
                                "address": "mister.ivan.boss@gmail.com",
                            },
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
                        "from": {
                            "name": "Ivan Taran",
                            "address": "mister.ivan.boss@gmail.com",
                        },
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
        assert messages[0].from_.name == "Ivan Taran"
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
                    "tokens": {"m690v3w4h715c@vibe-hub.ccwu.cc": "token-xyz"},
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
            json={
                "provider": "dispoemail.org",
                "address": "m690v3w4h715c@vibe-hub.ccwu.cc",
            },
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


@pytest.mark.asyncio
async def test_dispoemail_create_multiple_mailboxes_no_cookie_leak():
    recorded_cookies: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/session/mailboxes":
            cookie_header = request.headers.get("cookie", "")
            recorded_cookies.append(cookie_header)
            mb_num = len(recorded_cookies)
            email = f"user{mb_num}@vibe-hub.ccwu.cc"
            sess = f"session_{mb_num}"
            tok = f"token_{mb_num}"
            return httpx.Response(
                200,
                headers=[("Set-Cookie", f"astro-session={sess}; Path=/")],
                json={"ok": True, "tokens": {email: tok}},
            )
        return httpx.Response(404)

    http = _http(handler)
    provider = DispoEmailOrg(http)
    try:
        box1 = await provider.create_mailbox(MailboxSpec(address="user1@vibe-hub.ccwu.cc"))
        box2 = await provider.create_mailbox(MailboxSpec(address="user2@vibe-hub.ccwu.cc"))

        assert box1.token == "token_1:session_1"
        assert box2.token == "token_2:session_2"

        # Neither create_mailbox call leaked previous cookies into the request
        assert len(recorded_cookies) == 2
        assert recorded_cookies[0] == ""
        assert recorded_cookies[1] == ""
        assert "session_1" not in recorded_cookies[1]
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_dispoemail_astro_session_multi_cookie_parsing():
    cases = [
        # Multi-header list (standard separate Set-Cookie headers)
        (
            [
                (
                    "Set-Cookie",
                    "__cf_bm=token_cf_123; path=/; expires=Sat, 31-Oct-2026 12:00:00 GMT; HttpOnly",
                ),
                (
                    "Set-Cookie",
                    "astro-session=cf_session_abcdef123456; path=/; HttpOnly; Secure",
                ),
                ("Set-Cookie", "_cfuvid=uvid_789; path=/"),
            ],
            "cf_session_abcdef123456",
        ),
        # Comma-folded header starting with astro-session
        (
            [
                (
                    "Set-Cookie",
                    "astro-session=cf_sess_first, __cf_bm=token_123; path=/",
                ),
            ],
            "cf_sess_first",
        ),
        # Comma-folded header with astro-session in middle (following GMT date with comma)
        (
            [
                (
                    "Set-Cookie",
                    "__cf_bm=token_cf_123; path=/; expires=Sat, 31-Oct-2026 12:00:00 GMT, astro-session=cf_sess_middle; path=/",
                ),
            ],
            "cf_sess_middle",
        ),
        # Quoted cookie value
        (
            [
                (
                    "Set-Cookie",
                    'astro-session="cf_sess_quoted"; path=/; HttpOnly',
                ),
            ],
            "cf_sess_quoted",
        ),
    ]

    for idx, (headers_list, expected_sess) in enumerate(cases):

        def _make_handler(h_list: list[tuple[str, str]], i: int):
            def handler(request: httpx.Request) -> httpx.Response:
                if request.url.path == "/api/session/mailboxes":
                    return httpx.Response(
                        200,
                        headers=h_list,
                        json={
                            "ok": True,
                            "tokens": {f"user{i}@vibe-hub.ccwu.cc": f"mb_tok_{i}"},
                        },
                    )
                return httpx.Response(404)

            return handler

        http = _http(_make_handler(headers_list, idx))
        provider = DispoEmailOrg(http)
        try:
            box = await provider.create_mailbox(MailboxSpec(address=f"user{idx}@vibe-hub.ccwu.cc"))
            assert box.token == f"mb_tok_{idx}:{expected_sess}"
        finally:
            await http.close()


@pytest.mark.asyncio
async def test_dispoemail_list_and_get_messages_forbidden_raises_auth_error():
    for err_code in (401, 403):

        def _make_err_handler(code: int):
            def handler(request: httpx.Request) -> httpx.Response:
                if request.url.path.startswith("/api/inboxes/"):
                    return httpx.Response(code, json={"error": "unauthorized/forbidden"})
                if request.url.path.startswith("/api/messages/"):
                    return httpx.Response(code, json={"error": "unauthorized/forbidden"})
                return httpx.Response(404)

            return handler

        http = _http(_make_err_handler(err_code))
        provider = DispoEmailOrg(http)
        box = _mailbox()
        try:
            with pytest.raises(MailAuthError) as exc_info:
                await provider.list_messages(box)
            assert exc_info.value.status_code == err_code

            with pytest.raises(MailAuthError) as exc_info:
                await provider.get_message(box, "any-msg")
            assert exc_info.value.status_code == err_code
        finally:
            await http.close()


@pytest.mark.asyncio
async def test_dispoemail_auth_headers_clears_cookie_when_no_session():
    """Verify that mailboxes without astro-session explicitly clear the Cookie header."""
    http = _http(lambda req: httpx.Response(200))
    provider = DispoEmailOrg(http)
    try:
        # Mailbox with session sets Cookie
        h1 = provider._auth_headers("tok123:sess456")
        assert h1.get("Cookie") == "astro-session=sess456"
        assert h1.get("X-Mailbox-Token") == "tok123"

        # Mailbox without session explicitly clears Cookie to empty string
        h2 = provider._auth_headers("tok123")
        assert h2.get("Cookie") == ""
        assert h2.get("X-Mailbox-Token") == "tok123"

        # None/empty token explicitly clears Cookie
        h3 = provider._auth_headers(None)
        assert h3.get("Cookie") == ""
    finally:
        await http.close()
