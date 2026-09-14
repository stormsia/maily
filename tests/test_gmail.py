from __future__ import annotations

import time

import httpx
import pytest

from mailtmapi.exceptions import MailValidationError
from mailtmapi.http import HttpClient
from mailtmapi.providers.base import MailboxInfo, MailboxSpec
from mailtmapi.providers.gmail import GmailOAuth, GmailParent, GmailProvider, MemoryGmailStore


async def _http(handler) -> HttpClient:
    http = HttpClient()
    await http._client.aclose()
    http._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return http


def _unused(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={})


@pytest.mark.asyncio
async def test_list_targets_two_parents_no_plus():
    store = MemoryGmailStore()
    await store.add(GmailParent(id=0, email="alice@corp.io", refresh_token="r1"))
    await store.add(GmailParent(id=0, email="bob+tag@other.net", refresh_token="r2"))
    http = await _http(_unused)
    provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
    targets = await provider.list_targets()
    await provider.close()
    assert len(targets) == 2
    assert {t.label for t in targets} == {"alice@corp.io", "bob@other.net"}
    assert all("+" not in t.label for t in targets)
    assert all(t.kind == "parent" and t.provider == "gmail" for t in targets)


@pytest.mark.asyncio
async def test_create_mailbox_plus_alias_for_parent():
    store = MemoryGmailStore()
    parent = await store.add(
        GmailParent(
            id=0,
            email="alice@corp.io",
            refresh_token="r1",
            send_as=["alice@corp.io"],
        )
    )
    http = await _http(_unused)
    provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
    info = await provider.create_mailbox(MailboxSpec(parent_id=parent.id))
    await provider.close()
    local, domain = info.address.split("@")
    assert domain == "corp.io"
    assert local.startswith("alice+")
    assert info.token == info.address
    assert info.provider == "gmail"
    assert info.parent_id == parent.id


def test_parse_import_requires_refresh_token():
    with pytest.raises(MailValidationError):
        GmailOAuth.parse_import({"access_token": "x", "expires_at": 1})
    with pytest.raises(MailValidationError):
        GmailOAuth.parse_import({"installed": {"client_id": "c", "client_secret": "s"}})
    parsed = GmailOAuth.parse_import({"refresh_token": "rt", "access_token": "at"})
    assert parsed["refresh_token"] == "rt"


@pytest.mark.asyncio
async def test_list_messages_maps_summary():
    store = MemoryGmailStore()
    parent = await store.add(
        GmailParent(
            id=0,
            email="alice@corp.io",
            refresh_token="r1",
            access_token="tok",
            access_expires_at=time.time() + 3600,
            send_as=["alice@corp.io"],
        )
    )
    alias = "alice+abc123@corp.io"

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/messages") and request.method == "GET":
            return httpx.Response(
                200, json={"messages": [{"id": "m1", "threadId": "t1"}], "resultSizeEstimate": 1}
            )
        if path.endswith("/messages/m1"):
            return httpx.Response(
                200,
                json={
                    "id": "m1",
                    "labelIds": ["INBOX", "UNREAD"],
                    "snippet": "hello there",
                    "sizeEstimate": 42,
                    "internalDate": "1700000000000",
                    "payload": {
                        "mimeType": "text/plain",
                        "headers": [
                            {"name": "From", "value": "Sender <s@x.com>"},
                            {"name": "To", "value": alias},
                            {"name": "Subject", "value": "Hi"},
                        ],
                        "body": {"data": "aGVsbG8gdGhlcmU"},
                    },
                },
            )
        return httpx.Response(404, json={"detail": path})

    http = await _http(handler)
    provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
    mailbox = MailboxInfo(
        provider="gmail",
        address=alias,
        token=alias,
        provider_account_id=alias,
        parent_id=parent.id,
    )
    msgs = await provider.list_messages(mailbox, page=1)
    await provider.close()
    assert len(msgs) == 1
    assert msgs[0].id == "m1"
    assert msgs[0].subject == "Hi"
    assert msgs[0].from_.address == "s@x.com"
    assert msgs[0].intro == "hello there"
    assert msgs[0].seen is False
    assert msgs[0].size == 42


@pytest.mark.asyncio
async def test_refresh_posts_urlencoded():
    seen: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["content_type"] = request.headers.get("content-type", "")
        seen["body"] = request.content.decode()
        return httpx.Response(
            200, json={"access_token": "new-at", "expires_in": 3600, "token_type": "Bearer"}
        )

    http = await _http(handler)
    oauth = GmailOAuth("cid", "csec", http)
    result = await oauth.refresh("rt-old")
    await http.close()
    assert "application/x-www-form-urlencoded" in seen["content_type"]
    assert "grant_type=refresh_token" in seen["body"]
    assert "refresh_token=rt-old" in seen["body"]
    assert result["access_token"] == "new-at"
    assert result["refresh_token"] == "rt-old"
