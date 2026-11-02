from __future__ import annotations

import asyncio
import time

import httpx
import pytest

from maily.exceptions import MailAPIError, MailAuthError, MailValidationError
from maily.http import HttpClient
from maily.providers.base import MailboxInfo, MailboxSpec
from maily.providers.gmail import (
    GmailOAuth,
    GmailParent,
    GmailProvider,
    MemoryGmailStore,
)


class _CopyingStore(MemoryGmailStore):
    """get() returns a detached copy, matching DbGmailStore's per-call objects."""

    async def get(self, parent_id: int) -> GmailParent:
        stored = await super().get(parent_id)
        return GmailParent(
            id=stored.id,
            email=stored.email,
            refresh_token=stored.refresh_token,
            access_token=stored.access_token,
            access_expires_at=stored.access_expires_at,
            send_as=list(stored.send_as),
            scopes=stored.scopes,
            status=stored.status,
            owner_key_id=stored.owner_key_id,
        )


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
                200,
                json={
                    "messages": [{"id": "m1", "threadId": "t1"}],
                    "resultSizeEstimate": 1,
                },
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
            200,
            json={"access_token": "new-at", "expires_in": 3600, "token_type": "Bearer"},
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


@pytest.mark.asyncio
async def test_concurrent_ensure_access_refreshes_once():
    store = _CopyingStore()
    parent = await store.add(
        GmailParent(
            id=0,
            email="alice@corp.io",
            refresh_token="rt-old",
            access_token="stale",
            access_expires_at=time.time() - 10,
        )
    )
    started = asyncio.Event()
    release = asyncio.Event()
    calls = 0

    async def _refresh(refresh_token: str) -> dict:
        nonlocal calls
        calls += 1
        started.set()
        await release.wait()
        return {
            "access_token": "new-at",
            "refresh_token": "rt-rotated",
            "expires_at": time.time() + 3600,
            "scopes": "",
        }

    http = await _http(_unused)
    oauth = GmailOAuth("cid", "sec", http)
    oauth.refresh = _refresh  # type: ignore[method-assign]
    provider = GmailProvider(store, oauth, http)
    stale = GmailParent(
        id=parent.id,
        email=parent.email,
        refresh_token="rt-old",
        access_token="stale",
        access_expires_at=time.time() - 10,
    )
    other = GmailParent(
        id=parent.id,
        email=parent.email,
        refresh_token="rt-old",
        access_token="stale",
        access_expires_at=time.time() - 10,
    )
    first = asyncio.create_task(provider._ensure_access(stale))
    await started.wait()
    second = asyncio.create_task(provider._ensure_access(other))
    await asyncio.sleep(0)
    release.set()
    tokens = await asyncio.gather(first, second)
    await provider.close()
    stored = await store.get(parent.id)
    assert calls == 1
    assert tokens == ["new-at", "new-at"]
    assert stale.access_token == "new-at"
    assert other.access_token == "new-at"
    assert other.refresh_token == "rt-rotated"
    assert stored.access_token == "new-at"
    assert stored.refresh_token == "rt-rotated"


@pytest.mark.asyncio
async def test_refresh_invalid_grant_raises_mail_auth_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"error": "invalid_grant", "error_description": "revoked"})

    http = await _http(handler)
    oauth = GmailOAuth("cid", "csec", http)
    with pytest.raises(MailAuthError, match="revoked"):
        await oauth.refresh("rt-revoked")
    await http.close()


@pytest.mark.asyncio
async def test_ensure_access_marks_expired_on_mail_auth_error():
    store = MemoryGmailStore()
    parent = await store.add(
        GmailParent(
            id=0,
            email="alice@corp.io",
            refresh_token="rt-old",
            access_token="stale",
            access_expires_at=time.time() - 10,
        )
    )

    async def _refresh(refresh_token: str) -> dict:
        raise MailAuthError("revoked")

    http = await _http(_unused)
    oauth = GmailOAuth("cid", "sec", http)
    oauth.refresh = _refresh  # type: ignore[method-assign]
    provider = GmailProvider(store, oauth, http)
    with pytest.raises(MailAuthError):
        await provider._ensure_access(parent)
    await provider.close()
    stored = await store.get(parent.id)
    assert parent.status == "expired"
    assert stored.status == "expired"


def _mailbox(parent: GmailParent, alias: str) -> MailboxInfo:
    return MailboxInfo(
        provider="gmail",
        address=alias,
        token=alias,
        provider_account_id=alias,
        parent_id=parent.id,
    )


def _full_message(msg_id: str) -> dict:
    return {
        "id": msg_id,
        "labelIds": ["INBOX"],
        "snippet": msg_id,
        "sizeEstimate": 1,
        "internalDate": "1700000000000",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "From", "value": "s@x.com"},
                {"name": "Subject", "value": msg_id},
            ],
            "body": {"data": "aGk"},
        },
    }


@pytest.mark.asyncio
async def test_list_messages_page_token_is_per_page():
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
    page_tokens_sent: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/messages") and request.method == "GET":
            sent = request.url.params.get("pageToken")
            page_tokens_sent.append(sent)
            if sent is None:
                return httpx.Response(
                    200,
                    json={"messages": [{"id": "m1"}], "nextPageToken": "tok-page-2"},
                )
            if sent == "tok-page-2":
                return httpx.Response(
                    200,
                    json={"messages": [{"id": "m2"}], "nextPageToken": "tok-page-3"},
                )
            return httpx.Response(200, json={"messages": [{"id": "unexpected"}]})
        msg_id = path.rsplit("/", 1)[-1]
        return httpx.Response(200, json=_full_message(msg_id))

    http = await _http(handler)
    provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
    mailbox = _mailbox(parent, alias)
    page1 = await provider.list_messages(mailbox, page=1)
    page2 = await provider.list_messages(mailbox, page=2)
    page3 = await provider.list_messages(mailbox, page=3)
    skipped = await provider.list_messages(mailbox, page=4)
    await provider.close()
    assert [m.id for m in page1] == ["m1"]
    assert [m.id for m in page2] == ["m2"]
    assert [m.id for m in page3] == ["unexpected"]
    assert skipped == []
    assert page_tokens_sent == [None, "tok-page-2", "tok-page-3"]
    assert provider._page_tokens[(alias, 2)] == "tok-page-2"
    assert provider._page_tokens[(alias, 3)] == "tok-page-3"
    assert (alias, 4) not in provider._page_tokens


@pytest.mark.asyncio
async def test_list_messages_page_without_cursor_returns_empty():
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
    hits = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal hits
        hits += 1
        return httpx.Response(200, json={"messages": []})

    http = await _http(handler)
    provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
    provider._page_tokens[(alias, 2)] = "only-page-2"
    msgs = await provider.list_messages(_mailbox(parent, alias), page=3)
    await provider.close()
    assert msgs == []
    assert hits == 0


@pytest.mark.asyncio
async def test_list_messages_raises_when_a_detail_fetch_fails():
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

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path.endswith("/messages") and request.method == "GET":
            return httpx.Response(200, json={"messages": [{"id": "ok"}, {"id": "bad"}]})
        if path.endswith("/messages/ok"):
            return httpx.Response(200, json=_full_message("ok"))
        return httpx.Response(500, json={"detail": "boom"})

    http = await _http(handler)
    provider = GmailProvider(store, GmailOAuth("cid", "sec", http), http)
    with pytest.raises(MailAPIError):
        await provider.list_messages(_mailbox(parent, "alice+abc@corp.io"), page=1)
    await provider.close()
