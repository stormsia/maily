from __future__ import annotations

from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.http import HttpClient
from mailtmapi.providers.anonymmail_net import AnonymMailNet
from mailtmapi.providers.base import MailboxInfo, MailboxSpec, MessageDetail
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
        provider="anonymmail.net",
        address="user123@anonymmail.net",
        token="user123@anonymmail.net",
        provider_account_id="user123@anonymmail.net",
    )


@pytest.mark.asyncio
async def test_anonymmail_fetch_targets():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(
                200,
                text='<input name="csrf_test_name" value="csrf123">',
                headers={"Set-Cookie": "csrf_cookie_name=csrf123"},
            )
        if request.url.path == "/api/getDomains":
            assert request.headers["x-csrf-token"] == "csrf123"
            return httpx.Response(200, json=[{"domain": "anon1.net"}, {"domain": "anon2.net"}])
        return httpx.Response(404)

    http = _http(handler)
    provider = AnonymMailNet(http)
    try:
        targets = await provider.list_targets()
        assert len(targets) == 2
        assert targets[0].id == "anon1.net"
        assert targets[1].id == "anon2.net"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_anonymmail_create_and_delete_mailbox():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, text='<input name="csrf_test_name" value="csrf123">')
        if request.url.path == "/api/getDomains":
            return httpx.Response(200, json=[{"domain": "anonymmail.net"}])
        if request.url.path == "/api/create":
            return httpx.Response(200, json={"success": True, "email": "mytest@anonymmail.net"})
        if request.url.path == "/api/delete":
            return httpx.Response(200, json={"success": True})
        return httpx.Response(404)

    http = _http(handler)
    provider = AnonymMailNet(http)
    try:
        box = await provider.create_mailbox(MailboxSpec(address="mytest@anonymmail.net"))
        assert box.address == "mytest@anonymmail.net"
        assert box.provider == "anonymmail.net"

        deleted = await provider.delete_mailbox(box)
        assert deleted is True
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_anonymmail_unique_identity_per_mailbox():
    """Verify that each mailbox creation sends a unique am_uid, stores session in token,
    and forwards that mailbox's session cookies in subsequent requests."""
    captured_uids: list[str] = []
    received_cookies: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        cookie_header = request.headers.get("cookie", "")
        if request.url.path == "/":
            return httpx.Response(
                200,
                text='<input name="csrf_test_name" value="csrf123">',
                headers={"Set-Cookie": "csrf_cookie_name=csrf123; path=/"},
            )
        if request.url.path == "/api/getDomains":
            return httpx.Response(200, json=[{"domain": "anonymmail.net"}])
        if request.url.path == "/api/create":
            for part in cookie_header.split(";"):
                part = part.strip()
                if part.startswith("am_uid="):
                    captured_uids.append(part.split("=", 1)[1])
            sess_id = f"sess_{len(captured_uids)}"
            return httpx.Response(
                200,
                json={"success": True, "email": request.read().decode("utf-8").split("email=")[1]},
                headers={"Set-Cookie": f"ci_session={sess_id}; path=/"},
            )
        if request.url.path == "/api/get":
            received_cookies["get"] = cookie_header
            return httpx.Response(200, json={})
        if request.url.path == "/api/delete":
            received_cookies["delete"] = cookie_header
            return httpx.Response(200, json={"success": True})
        if request.url.path == "/email" and request.method == "POST":
            received_cookies["delete_msg"] = cookie_header
            return httpx.Response(200, text="Deleted")
        return httpx.Response(404)

    http = _http(handler)
    provider = AnonymMailNet(http)
    try:
        # Create 3 mailboxes
        b1 = await provider.create_mailbox(MailboxSpec(address="box1@anonymmail.net"))
        b2 = await provider.create_mailbox(MailboxSpec(address="box2@anonymmail.net"))
        b3 = await provider.create_mailbox(MailboxSpec(address="box3@anonymmail.net"))

        # 1. Verify each has a unique am_uid
        assert len(captured_uids) == 3
        assert len(set(captured_uids)) == 3

        # 2. Verify token format is ci_session:am_uid
        assert b1.token == f"sess_1:{captured_uids[0]}"
        assert b2.token == f"sess_2:{captured_uids[1]}"
        assert b3.token == f"sess_3:{captured_uids[2]}"

        # 3. Verify list_messages sends box2's specific session and am_uid
        await provider.list_messages(b2)
        assert "ci_session=sess_2" in received_cookies["get"]
        assert f"am_uid={captured_uids[1]}" in received_cookies["get"]

        # 4. Verify delete_mailbox sends box3's specific session and am_uid
        await provider.delete_mailbox(b3)
        assert "ci_session=sess_3" in received_cookies["delete"]
        assert f"am_uid={captured_uids[2]}" in received_cookies["delete"]

        # 5. Verify delete_message sends box1's specific session and am_uid
        await provider.delete_message(b1, "msg_test")
        assert "ci_session=sess_1" in received_cookies["delete_msg"]
        assert f"am_uid={captured_uids[0]}" in received_cookies["delete_msg"]
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_anonymmail_feed_disappears_on_second_request_provider_level():
    """Test provider adapter behavior when /api/get returns message only once."""
    calls_get = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls_get
        if request.url.path == "/":
            return httpx.Response(200, text='<input name="csrf_test_name" value="csrf123">')
        if request.url.path == "/api/get":
            calls_get += 1
            if calls_get == 1:
                # First time: message is present
                return httpx.Response(
                    200,
                    json={
                        "user123@anonymmail.net": {
                            "created_at": "2026-10-28 01:00:00",
                            "emails": [
                                {
                                    "id": "1001",
                                    "token": "tok_abc",
                                    "from": "Sender <sender@xyz.com>",
                                    "subject": "Activation Code",
                                    "read": 0,
                                    "images": 0,
                                    "date": "2026-10-28T01:23:45Z",
                                }
                            ],
                        }
                    },
                )
            # Second time: provider removes it from feed!
            return httpx.Response(200, json={"user123@anonymmail.net": {"emails": []}})
        if request.url.path == "/email":
            assert request.url.params["id"] == "tok_abc"
            return httpx.Response(200, text="<div>Your code is <b>987654</b></div>")
        return httpx.Response(404)

    http = _http(handler)
    provider = AnonymMailNet(http)
    mb = _mailbox()
    try:
        # First call: seen and prefetched
        messages = await provider.list_messages(mb)
        assert len(messages) == 1
        msg = messages[0]
        assert msg.id == "tok_abc"
        assert msg.subject == "Activation Code"
        assert isinstance(msg, MessageDetail)
        assert "987654" in msg.text
        assert "<div>Your code is <b>987654</b></div>" in msg.html[0]

        # Second call to list_messages: provider returns empty
        messages_2nd = await provider.list_messages(mb)
        assert messages_2nd == []

        # But get_message for tok_abc STILL resolves from cached memory
        detail = await provider.get_message(mb, "tok_abc")
        assert detail.id == "tok_abc"
        assert "987654" in detail.text
    finally:
        await http.close()


def test_anonymmail_full_api_flow(tmp_path: Path):
    """End-to-end API test verifying DB persistence and subsequent reads when feed disappears."""
    calls_get = 0
    delete_called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls_get, delete_called
        if request.url.path == "/":
            return httpx.Response(200, text='<input name="csrf_test_name" value="csrf123">')
        if request.url.path == "/api/getDomains":
            return httpx.Response(200, json=[{"domain": "anonymmail.net"}])
        if request.url.path == "/api/create":
            return httpx.Response(200, json={"success": True, "email": "test@anonymmail.net"})
        if request.url.path == "/api/get":
            calls_get += 1
            if calls_get == 1:
                return httpx.Response(
                    200,
                    json={
                        "test@anonymmail.net": {
                            "emails": [
                                {
                                    "id": "msg_99",
                                    "token": "tok_99",
                                    "from": "Service <noreply@service.com>",
                                    "subject": "Welcome!",
                                    "read": 0,
                                    "images": 0,
                                    "date": "2026-10-28T01:30:00Z",
                                }
                            ]
                        }
                    },
                )
            # Subsequent calls: feed is empty
            return httpx.Response(200, json={"test@anonymmail.net": {"emails": []}})
        if request.url.path == "/email":
            assert request.url.params["id"] == "tok_99"
            if request.method == "POST":
                delete_called = True
                return httpx.Response(200, text="Deleted")
            return httpx.Response(200, text="<p>Welcome to our platform!</p>")
        return httpx.Response(404)

    http = _http(handler)
    provider = AnonymMailNet(http)

    db = tmp_path / "test.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            secret_key=SECRET,
            _env_file=None,
        )
    )
    app.state.registry = ProviderRegistry([provider])

    with TestClient(app) as client:
        client.app.state.registry = ProviderRegistry([provider])
        # 1. Create mailbox
        r = client.post("/v1/mailboxes", json={"provider": "anonymmail.net", "address": "test@anonymmail.net"})
        assert r.status_code == 200, r.json()
        mb_id = r.json()["id"]

        # 2. First list_messages: message is seen from provider and stored into DB
        r = client.get(f"/v1/mailboxes/{mb_id}/messages")
        assert r.status_code == 200, r.json()
        msgs = r.json()
        assert len(msgs) == 1
        assert msgs[0]["message_api_id"] == "tok_99"
        assert msgs[0]["subject"] == "Welcome!"
        assert msgs[0]["seen"] is False

        # 3. Second list_messages: provider returns empty feed, but we STILL return the message from DB!
        r2 = client.get(f"/v1/mailboxes/{mb_id}/messages")
        assert r2.status_code == 200
        msgs2 = r2.json()
        assert len(msgs2) == 1
        assert msgs2[0]["message_api_id"] == "tok_99"

        # 4. Fetch message details: served directly from DB with full text & HTML body
        r_detail = client.get(f"/v1/mailboxes/{mb_id}/messages/tok_99")
        assert r_detail.status_code == 200
        detail = r_detail.json()
        assert detail["message_api_id"] == "tok_99"
        assert detail["subject"] == "Welcome!"
        assert "Welcome to our platform!" in detail["text"]
        assert "<p>Welcome to our platform!</p>" in detail["html"][0]

        # 5. Mark read
        r_read = client.post(f"/v1/mailboxes/{mb_id}/messages/tok_99/read")
        assert r_read.status_code == 200
        assert r_read.json()["seen"] is True

        # Check detail again: seen is True
        r_detail_seen = client.get(f"/v1/mailboxes/{mb_id}/messages/tok_99")
        assert r_detail_seen.json()["seen"] is True

        # 6. Source
        r_src = client.get(f"/v1/mailboxes/{mb_id}/messages/tok_99/source")
        assert r_src.status_code == 200
        assert "<p>Welcome to our platform!</p>" in r_src.json()["data"]

        # 7. Delete message
        r_del = client.delete(f"/v1/mailboxes/{mb_id}/messages/tok_99")
        assert r_del.status_code == 204
        assert delete_called is True

        # 8. List again: should be empty now that it's deleted
        r_after_del = client.get(f"/v1/mailboxes/{mb_id}/messages")
        assert r_after_del.status_code == 200
        assert r_after_del.json() == []

        # 9. Get detail after delete should 404
        r_get_del = client.get(f"/v1/mailboxes/{mb_id}/messages/tok_99")
        assert r_get_del.status_code == 404
