from __future__ import annotations

import json

import httpx
import pytest

from mailtmapi.exceptions import MailNotFoundError, MailValidationError
from mailtmapi.http import HttpClient
from mailtmapi.providers.base import MailboxInfo, MailboxSpec
from mailtmapi.providers.tempmail_io import TempMailIO


def _http(handler) -> HttpClient:
    http = HttpClient.__new__(HttpClient)
    http._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    return http


def _mailbox() -> MailboxInfo:
    return MailboxInfo(
        provider="temp-mail.io",
        address="al234tf05o@yzcalo.com",
        token="r0M69rpdW2k1Th5RRxna",
        provider_account_id="al234tf05o@yzcalo.com",
    )


@pytest.mark.asyncio
async def test_list_targets_maps_domains():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v4/domains"
        return httpx.Response(
            200,
            json={
                "domains": [
                    {
                        "name": "ozsaip.com",
                        "type": "public",
                        "forward_available": True,
                        "forward_max_seconds": 7772400,
                    }
                ]
            },
        )

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        targets = await provider.list_targets()
        assert len(targets) == 1
        assert targets[0].id == "ozsaip.com"
        assert targets[0].kind == "domain"
        assert targets[0].provider == "temp-mail.io"
        assert targets[0].label == "ozsaip.com"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_posts_name_and_domain():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/email/new"
        assert request.method == "POST"
        body = json.loads(request.content)
        assert body == {"name": "al234tf05o", "domain": "yzcalo.com"}
        return httpx.Response(
            200,
            json={"email": "al234tf05o@yzcalo.com", "token": "r0M69rpdW2k1Th5RRxna"},
        )

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        box = await provider.create_mailbox(MailboxSpec(address="al234tf05o@yzcalo.com"))
        assert box.provider == "temp-mail.io"
        assert box.address == "al234tf05o@yzcalo.com"
        assert box.token == "r0M69rpdW2k1Th5RRxna"
        assert box.provider_account_id == "al234tf05o@yzcalo.com"
        assert box.password is None
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_without_token_raises_validation_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"email": "al234tf05o@yzcalo.com"})

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        with pytest.raises(MailValidationError):
            await provider.create_mailbox(MailboxSpec(address="al234tf05o@yzcalo.com"))
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_list_messages_maps_and_encodes_email_in_path():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.raw_path == b"/api/v3/email/al234tf05o@yzcalo.com/messages"
        return httpx.Response(
            200,
            json=[
                {
                    "id": "09253cfc-abc",
                    "from": '"sf_root@outlook.com" <sf_root@outlook.com>',
                    "to": "al234tf05o@yzcalo.com",
                    "cc": None,
                    "subject": "Hello",
                    "body_text": "first line\nsecond line",
                    "body_html": "",
                    "created_at": "2026-09-15T18:56:45.308303Z",
                    "attachments": [],
                }
            ],
        )

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        msgs = await provider.list_messages(_mailbox())
        assert len(msgs) == 1
        msg = msgs[0]
        assert msg.id == "09253cfc-abc"
        assert msg.subject == "Hello"
        assert msg.from_.name == "sf_root@outlook.com"
        assert msg.from_.address == "sf_root@outlook.com"
        assert msg.to[0].address == "al234tf05o@yzcalo.com"
        assert msg.intro == "first line"
        assert msg.seen is False
        assert msg.has_attachments is False
        assert msg.received_at is not None
        assert msg.received_at.tzinfo is not None
        assert msg.received_at.isoformat() == "2026-09-15T18:56:45.308303+00:00"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_message_maps_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v3/message/09253cfc-abc"
        return httpx.Response(
            200,
            json={
                "id": "09253cfc-abc",
                "from": "bot@ex.com",
                "to": "al234tf05o@yzcalo.com",
                "subject": "Code",
                "body_text": "hello world",
                "body_html": "<p>hello</p>",
                "created_at": "2026-09-15T18:56:45Z",
                "attachments": [
                    {"id": "1", "filename": "a.txt", "content_type": "text/plain", "size": 12}
                ],
            },
        )

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        detail = await provider.get_message(_mailbox(), "09253cfc-abc")
        assert detail.id == "09253cfc-abc"
        assert detail.text == "hello world"
        assert detail.html == ["<p>hello</p>"]
        assert detail.from_.name is None
        assert detail.from_.address == "bot@ex.com"
        assert detail.to[0].address == "al234tf05o@yzcalo.com"
        assert len(detail.attachments) == 1
        assert detail.attachments[0].id == "1"
        assert detail.attachments[0].filename == "a.txt"
        assert detail.attachments[0].content_type == "text/plain"
        assert detail.attachments[0].size == 12
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_message_http_404_raises_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "message not found"})

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        with pytest.raises(MailNotFoundError):
            await provider.get_message(_mailbox(), "missing")
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_message_empty_body_raises_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        with pytest.raises(MailNotFoundError):
            await provider.get_message(_mailbox(), "missing")
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_delete_message_is_idempotent_on_404():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/api/v3/message/abc"
        assert json.loads(request.content) == {"token": "r0M69rpdW2k1Th5RRxna"}
        return httpx.Response(404, json={"detail": "message not found"})

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        assert await provider.delete_message(_mailbox(), "abc") is True
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_delete_message_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.path == "/api/v3/message/abc"
        assert json.loads(request.content) == {"token": "r0M69rpdW2k1Th5RRxna"}
        return httpx.Response(200, json={"success": True})

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        assert await provider.delete_message(_mailbox(), "abc") is True
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_delete_mailbox_is_idempotent_on_404():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "DELETE"
        assert request.url.raw_path == b"/api/v3/email/al234tf05o@yzcalo.com"
        assert json.loads(request.content) == {"token": "r0M69rpdW2k1Th5RRxna"}
        return httpx.Response(404, json={"detail": "email not found"})

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        assert await provider.delete_mailbox(_mailbox()) is True
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_source_uses_source_code_endpoint():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/v3/message/abc/source_code"
        return httpx.Response(200, json={"data": "From: a@b.c\nSubject: hi\n"})

    http = _http(handler)
    provider = TempMailIO(http)
    try:
        src = await provider.get_source(_mailbox(), "abc")
        assert src.id == "abc"
        assert src.data == "From: a@b.c\nSubject: hi\n"
        assert src.download_url is None
    finally:
        await http.close()