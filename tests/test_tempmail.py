from __future__ import annotations

import httpx
import pytest

from maily.exceptions import MailValidationError
from maily.http import HttpClient
from maily.providers.base import MailboxInfo, MailboxSpec
from maily.providers.tempmail_plus import TempMailPlus

_HTML = """
<html>
  <div class="dropdown-menu">
    <button class="dropdown-item">@mailto.plus</button>
  </div>
</html>
"""


def _http(handler) -> HttpClient:
    http = HttpClient.__new__(HttpClient)
    http._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    return http


@pytest.mark.asyncio
async def test_list_targets_parses_dropdown_item():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/en/"
        return httpx.Response(200, text=_HTML)

    http = _http(handler)
    provider = TempMailPlus(http)
    try:
        targets = await provider.list_targets()
        assert len(targets) == 1
        assert targets[0].id == "mailto.plus"
        assert targets[0].kind == "domain"
        assert targets[0].provider == "tempmail.plus"
        assert targets[0].label == "mailto.plus"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_validates_inbox():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/mails"
        assert request.url.params["email"] == "user@mailto.plus"
        assert request.url.params["limit"] == "1"
        return httpx.Response(200, json={"mail_list": [], "count": 0, "first_id": 0})

    http = _http(handler)
    provider = TempMailPlus(http)
    try:
        box = await provider.create_mailbox(MailboxSpec(address="user@mailto.plus"))
        assert box.provider == "tempmail.plus"
        assert box.address == "user@mailto.plus"
        assert box.token == "user@mailto.plus"
        assert box.provider_account_id == "user@mailto.plus"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_with_domain_in_spec():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/mails"
        email = request.url.params["email"]
        assert email.endswith("@mailto.plus")
        assert request.url.params["limit"] == "1"
        return httpx.Response(200, json={"mail_list": [], "count": 0, "first_id": 0})

    http = _http(handler)
    provider = TempMailPlus(http)
    try:
        box = await provider.create_mailbox(MailboxSpec(domain="mailto.plus"))
        assert box.address.endswith("@mailto.plus")
        assert box.token == box.address
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_rejects_err():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"err": {"msg": "invalid domain"}})

    http = _http(handler)
    provider = TempMailPlus(http)
    try:
        with pytest.raises(MailValidationError):
            await provider.create_mailbox(MailboxSpec(address="bad@nope.tld"))
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_list_messages_maps_mail_list():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/mails"
        assert request.url.params["email"] == "user@mailto.plus"
        return httpx.Response(
            200,
            json={
                "first_id": 9,
                "count": 1,
                "mail_list": [
                    {
                        "mail_id": 9,
                        "subject": "Code",
                        "from_mail": "bot@ex.com",
                        "from_name": "Bot",
                        "date": "2024-01-15 12:30:45",
                        "is_new": True,
                        "mail_size": 42,
                    }
                ],
            },
        )

    http = _http(handler)
    provider = TempMailPlus(http)
    mailbox = MailboxInfo(
        provider="tempmail.plus",
        address="user@mailto.plus",
        token="user@mailto.plus",
        provider_account_id="user@mailto.plus",
    )
    try:
        msgs = await provider.list_messages(mailbox)
        assert len(msgs) == 1
        msg = msgs[0]
        assert msg.id == "9"
        assert msg.subject == "Code"
        assert msg.from_.name == "Bot"
        assert msg.from_.address == "bot@ex.com"
        assert msg.to[0].address == "user@mailto.plus"
        assert msg.seen is False
        assert msg.size == 42
        assert msg.received_at is not None
        assert msg.received_at.strftime("%Y-%m-%d %H:%M:%S") == "2024-01-15 12:30:45"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_source_download_url_is_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/mails/9"
        return httpx.Response(
            200,
            json={
                "mail_id": 9,
                "subject": "Code",
                "from_mail": "bot@ex.com",
                "html": "<p>hello</p>",
                "text": "hello",
            },
        )

    http = _http(handler)
    provider = TempMailPlus(http, epin="secret-pin")
    mailbox = MailboxInfo(
        provider="tempmail.plus",
        address="user@mailto.plus",
        token="user@mailto.plus",
        provider_account_id="user@mailto.plus",
    )
    try:
        src = await provider.get_source(mailbox, "9")
        assert src.id == "9"
        assert src.data == "<p>hello</p>"
        assert src.download_url == ""
        assert "epin" not in src.download_url
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_tempmail_plus_delete_operations_and_attachments():
    deleted = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/api/mails":
            # return 1 message then empty
            if "offset" in request.url.params and request.url.params["offset"] != "0":
                return httpx.Response(200, json={"mail_list": []})
            if deleted:
                return httpx.Response(200, json={"mail_list": []})
            return httpx.Response(
                200,
                json={
                    "mail_list": [
                        {
                            "mail_id": "m100",
                            "subject": "subj",
                            "from_name": "sender",
                            "from_mail": "sender@ex.com",
                            "is_new": False,
                            "date": "2024-01-01 10:00:00",
                        }
                    ]
                },
            )
        if request.method == "DELETE" and request.url.path == "/api/mails/m100":
            deleted.append("m100")
            return httpx.Response(200, json={"result": True})
        if request.method == "GET" and request.url.path == "/api/mails/att_msg":
            return httpx.Response(
                200,
                json={
                    "mail_id": "att_msg",
                    "subject": "Attachments",
                    "from_mail": "a@b.c",
                    "text": "sample text",
                    "html": "",
                    "attachments": [
                        {
                            "id": "att1",
                            "name": "photo.jpg",
                            "content_type": "image/jpeg",
                            "size": 2048,
                            "url": "https://tempmail.plus/dl/att1",
                        }
                    ],
                },
            )
        return httpx.Response(404)

    http = _http(handler)
    provider = TempMailPlus(http)
    mailbox = MailboxInfo(
        provider="tempmail.plus",
        address="user@mailto.plus",
        token="user@mailto.plus",
        provider_account_id="user@mailto.plus",
    )
    try:
        # Delete message
        res_del = await provider.delete_message(mailbox, "m100")
        assert res_del is True

        # Mark read
        assert await provider.mark_read(mailbox, "m100") is True

        # Delete mailbox clears inbox
        assert await provider.delete_mailbox(mailbox) is True

        # Get message with attachments
        detail = await provider.get_message(mailbox, "att_msg")
        assert detail.has_attachments is True
        assert len(detail.attachments) == 1
        assert detail.attachments[0].filename == "photo.jpg"
        assert detail.attachments[0].download_url == "https://tempmail.plus/dl/att1"
    finally:
        await http.close()
