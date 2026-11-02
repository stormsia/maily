from __future__ import annotations

import time
from urllib.parse import parse_qs

import httpx
import pytest

from maily.app.services import mailboxes as mailbox_svc
from maily.exceptions import MailNotFoundError, MailValidationError
from maily.http import HttpClient
from maily.providers.base import MailboxInfo, MailboxSpec
from maily.providers.gmail import (
    GmailOAuth,
    GmailParent,
    GmailProvider,
    MemoryGmailStore,
)
from maily.providers.registry import ProviderRegistry
from maily.settings import Settings
from tests.helpers import StubProvider
from tests.test_mailboxes_service import FakeSession

ALIAS = "user+tag@gmail.com"
BARE = "user@gmail.com"
PLUS_DETAIL = "gmail address must be a plus-alias"


def _full_payload(message_id: str, headers: list[tuple[str, str]]) -> dict:
    return {
        "id": message_id,
        "threadId": "t1",
        "labelIds": ["INBOX"],
        "snippet": "hello",
        "sizeEstimate": 12,
        "internalDate": "1700000000000",
        "payload": {
            "mimeType": "text/plain",
            "headers": [{"name": name, "value": value} for name, value in headers],
            "body": {"data": "aGVsbG8"},
        },
    }


class _RecordingHttp:
    """Gmail HTTP fake that records every request, including forbidden mutations."""

    def __init__(self, payload: dict) -> None:
        self.calls: list[tuple[str, str, str | None]] = []
        self._payload = payload

    def handler(self, request: httpx.Request) -> httpx.Response:
        query = parse_qs(request.url.query.decode())
        fmt = query.get("format", [None])[0]
        self.calls.append((request.method, request.url.path, fmt))
        path = request.url.path
        if (
            request.method == "GET"
            and path.endswith("/messages/m1")
            and fmt in {"full", "metadata"}
        ):
            return httpx.Response(200, json=self._payload)
        if request.method == "GET" and fmt == "raw":
            return httpx.Response(200, json={"id": "m1", "raw": "RnJvbTogYQo="})
        if request.method == "POST":
            return httpx.Response(200, json={"id": "m1", "threadId": "t1"})
        return httpx.Response(404, json={"detail": path})


async def _http(handler) -> HttpClient:
    http = HttpClient()
    await http._client.aclose()
    http._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return http


async def _provider(
    payload: dict | None = None,
) -> tuple[GmailProvider, _RecordingHttp]:
    store = MemoryGmailStore()
    await store.add(
        GmailParent(
            id=0,
            email=BARE,
            refresh_token="r1",
            access_token="tok",
            access_expires_at=time.time() + 3600,
            send_as=[BARE],
        )
    )
    recorder = _RecordingHttp(payload or _full_payload("m1", [("To", BARE)]))
    http = await _http(recorder.handler)
    return GmailProvider(store, GmailOAuth("cid", "sec", http), http), recorder


def _mailbox(address: str = ALIAS) -> MailboxInfo:
    return MailboxInfo(
        provider="gmail",
        address=address,
        token=address,
        provider_account_id=address,
        parent_id=1,
    )


def _mutating(
    calls: list[tuple[str, str, str | None]],
) -> list[tuple[str, str, str | None]]:
    return [
        call
        for call in calls
        if call[2] == "raw" or call[1].endswith("/trash") or call[1].endswith("/modify")
    ]


@pytest.mark.asyncio
async def test_create_mailbox_rejects_bare_address_when_explicit():
    """Given a parent base user@gmail.com, an explicit bare address is rejected."""
    provider, recorder = await _provider()
    try:
        with pytest.raises(MailValidationError, match=PLUS_DETAIL):
            await provider.create_mailbox(MailboxSpec(parent_id=1, address=BARE))
    finally:
        await provider.close()
    assert recorder.calls == []


@pytest.mark.asyncio
async def test_create_mailbox_accepts_plus_alias_when_it_matches_parent():
    """Given a parent base user@gmail.com, user+tag@gmail.com is a plus-alias."""
    provider, _recorder = await _provider()
    try:
        info = await provider.create_mailbox(MailboxSpec(parent_id=1, address=ALIAS))
    finally:
        await provider.close()
    assert info.address == ALIAS


@pytest.mark.asyncio
async def test_create_mailbox_rejects_unrelated_plus_alias_when_not_a_base():
    """A plus sign is not enough: the address must still be an alias of the parent."""
    provider, _recorder = await _provider()
    try:
        with pytest.raises(MailValidationError) as exc:
            await provider.create_mailbox(
                MailboxSpec(parent_id=1, address="other+tag@gmail.com")
            )
    finally:
        await provider.close()
    assert PLUS_DETAIL not in str(exc.value)


@pytest.mark.asyncio
async def test_create_mailbox_auto_alias_contains_plus_when_address_omitted():
    """Given no explicit address, the generated alias already contains + and is stored."""
    provider, _recorder = await _provider()
    try:
        info = await provider.create_mailbox(MailboxSpec(parent_id=1))
    finally:
        await provider.close()
    local, domain = info.address.split("@")
    assert domain == "gmail.com"
    assert "+" in local


@pytest.mark.asyncio
async def test_service_create_rejects_bare_gmail_address_before_insert():
    """Given a provider that returns a bare gmail address, the row is not added."""
    session = FakeSession()
    stub = StubProvider(slug="gmail", address=BARE)
    registry = ProviderRegistry([stub])
    settings = Settings(
        secret_key="test-secret",
        database_url="sqlite+aiosqlite:///:memory:",
        _env_file=None,
    )
    with pytest.raises(MailValidationError, match=PLUS_DETAIL):
        await mailbox_svc.create_mailbox(
            session,
            registry,
            settings,
            provider="gmail",
            domain=None,
            parent_id=None,
            address=BARE,
            password=None,
        )
    assert session.added == []


@pytest.mark.asyncio
async def test_service_create_keeps_plus_gmail_address_when_alias_is_valid():
    """Given a provider that returns user+tag@gmail.com, the plus rule is not the failure."""
    session = FakeSession()
    stub = StubProvider(slug="gmail", address=ALIAS)
    registry = ProviderRegistry([stub])
    settings = Settings(
        secret_key="test-secret",
        database_url="sqlite+aiosqlite:///:memory:",
        _env_file=None,
    )
    row = await mailbox_svc.create_mailbox(
        session,
        registry,
        settings,
        provider="gmail",
        domain=None,
        parent_id=None,
        address=ALIAS,
        password=None,
    )
    assert row.address == ALIAS
    assert session.added


@pytest.mark.asyncio
async def test_get_message_is_not_found_when_only_bare_address_is_recipient():
    """A message addressed only to the stripped base is not this mailbox's mail."""
    provider, recorder = await _provider(
        _full_payload("m1", [("To", BARE), ("Cc", "")])
    )
    try:
        with pytest.raises(MailNotFoundError):
            await provider.get_message(_mailbox(), "m1")
    finally:
        await provider.close()
    assert _mutating(recorder.calls) == []


@pytest.mark.asyncio
async def test_delete_message_does_not_trash_when_only_bare_address_is_recipient():
    """A miss is not-found and must not call trash or modify."""
    provider, recorder = await _provider(
        _full_payload("m1", [("To", "someone@gmail.com"), ("Delivered-To", BARE)])
    )
    try:
        with pytest.raises(MailNotFoundError):
            await provider.delete_message(_mailbox(), "m1")
    finally:
        await provider.close()
    assert _mutating(recorder.calls) == []


@pytest.mark.asyncio
async def test_mark_read_does_not_modify_when_alias_is_absent():
    """BCC-only mail has none of To, Cc, or Delivered-To and must not modify labels."""
    provider, recorder = await _provider(
        _full_payload("m1", [("To", "other@gmail.com")])
    )
    try:
        with pytest.raises(MailNotFoundError):
            await provider.mark_read(_mailbox(), "m1")
    finally:
        await provider.close()
    assert _mutating(recorder.calls) == []


@pytest.mark.asyncio
async def test_get_source_skips_raw_when_alias_is_absent():
    """format=raw is fetched only after the recipient check matches."""
    provider, recorder = await _provider(_full_payload("m1", [("To", BARE)]))
    try:
        with pytest.raises(MailNotFoundError):
            await provider.get_source(_mailbox(), "m1")
    finally:
        await provider.close()
    assert _mutating(recorder.calls) == []
    assert any(fmt in {"full", "metadata"} for _method, _path, fmt in recorder.calls)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers",
    [
        [("To", "User+Tag <USER+TAG@gmail.com>")],
        [("Cc", "USER+TAG@gmail.com")],
        [("Delivered-To", "User+Tag@Gmail.com")],
    ],
)
async def test_get_message_allows_alias_when_header_contains_full_address(headers):
    """The full mailbox address matches To, Cc, or Delivered-To case-insensitively."""
    provider, recorder = await _provider(_full_payload("m1", headers))
    try:
        detail = await provider.get_message(_mailbox(), "m1")
    finally:
        await provider.close()
    assert detail.id == "m1"
    assert _mutating(recorder.calls) == []


@pytest.mark.asyncio
async def test_get_source_fetches_raw_when_delivered_to_matches():
    """A matching metadata/full load is followed by exactly one format=raw fetch."""
    provider, recorder = await _provider(
        _full_payload("m1", [("Delivered-To", "user+tag@gmail.com")])
    )
    try:
        source = await provider.get_source(_mailbox(), "m1")
    finally:
        await provider.close()
    assert source.id == "m1"
    raw_calls = [call for call in recorder.calls if call[2] == "raw"]
    assert raw_calls == [("GET", "/gmail/v1/users/me/messages/m1", "raw")]


@pytest.mark.asyncio
async def test_delete_message_trashes_when_cc_matches():
    """A matching recipient check is what allows the trash call."""
    provider, recorder = await _provider(
        _full_payload("m1", [("Cc", "user+tag@gmail.com")])
    )
    try:
        deleted = await provider.delete_message(_mailbox(), "m1")
    finally:
        await provider.close()
    assert deleted is True
    assert ("POST", "/gmail/v1/users/me/messages/m1/trash", None) in recorder.calls
