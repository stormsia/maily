from __future__ import annotations

import httpx
import pytest

from mailtmapi.exceptions import MailValidationError
from mailtmapi.http import HttpClient
from mailtmapi.providers.base import MailboxInfo, MailboxSpec
from mailtmapi.providers.tempmail_plus import TempMailPlus

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
