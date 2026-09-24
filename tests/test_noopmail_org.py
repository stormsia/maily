"""Тесты провайдера noopmail.org.

noopmail.org защищён Cloudflare; при живых запросах нужны куки cf_clearance
(см. docstring класса NoopMail) — в тестах они не нужны, т.к. сеть замокана.
"""

from __future__ import annotations

import json

import httpx
import pytest

from mailtmapi.exceptions import MailNotFoundError
from mailtmapi.http import HttpClient
from mailtmapi.providers.base import MailboxInfo, MailboxSpec
from mailtmapi.providers.noopmail_org import NoopMail

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0"


def _http(handler) -> HttpClient:
    http = HttpClient.__new__(HttpClient)
    http._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    return http


def _mailbox() -> MailboxInfo:
    return MailboxInfo(
        provider="noopmail.org",
        address="al234tf05o@yzcalo.com",
        token="",
        provider_account_id="al234tf05o@yzcalo.com",
    )


@pytest.mark.asyncio
async def test_list_targets_collects_all_domains_and_caches():
    calls = 0
    queue = ["a.com", "b.com", "c.com"]  # уникальные, потом только повторы

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        assert request.url.path == "/api/rd"
        dm = queue.pop(0) if queue else "c.com"
        return httpx.Response(200, json={"dm": dm, "exp": "2027-04-22T01:41:10.000Z", "kept": False})

    http = _http(handler)
    provider = NoopMail(http)
    try:
        targets = await provider.list_targets()
        # 3 уникальных + 15 подряд повторов для остановки, но не больше 100
        assert calls == 18
        assert {t.id for t in targets} == {"a.com", "b.com", "c.com"}
        assert len(targets) == 3  # без дубликатов
        assert all(t.kind == "domain" and t.provider == "noopmail.org" for t in targets)
        assert targets[0].label == "a.com"

        # TTL-кэш: второй вызов не бьёт по сети
        calls_before = calls
        again = await provider.list_targets()
        assert calls == calls_before
        assert {t.id for t in again} == {"a.com", "b.com", "c.com"}

        # fresh=True must keep sampling past domains already cached, or a
        # refresh that draws a known domain first would replace the DB with one row.
        queue.extend(["a.com", "d.com"])
        calls_before = calls
        refreshed = await provider.list_targets(fresh=True)
        assert calls > calls_before
        assert {t.id for t in refreshed} == {"a.com", "b.com", "c.com", "d.com"}
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_with_address():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no network expected for create_mailbox with address")

    http = _http(handler)
    provider = NoopMail(http)
    try:
        box = await provider.create_mailbox(MailboxSpec(address="al234tf05o@yzcalo.com"))
        assert box.provider == "noopmail.org"
        assert box.address == "al234tf05o@yzcalo.com"
        assert box.token == ""  # у noopmail нет api-token
        assert box.provider_account_id == "al234tf05o@yzcalo.com"
        assert box.password is None
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_without_address_uses_target_domain():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/rd"
        return httpx.Response(200, json={"dm": "b.com", "exp": "2027-01-01T00:00:00.000Z", "kept": False})

    http = _http(handler)
    provider = NoopMail(http)
    try:
        box = await provider.create_mailbox(MailboxSpec())
        local, sep, domain = box.address.partition("@")
        assert sep and domain == "b.com"
        assert len(local) == 10
        assert box.token == ""
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_address_used_verbatim():
    http = _http(lambda request: None)
    provider = NoopMail(http)
    try:
        box = await provider.create_mailbox(MailboxSpec(address="some-user@yzcalo.com"))
        assert box.address == "some-user@yzcalo.com"
        assert box.provider_account_id == "some-user@yzcalo.com"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_with_domain_in_spec():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no network expected when domain given in spec")

    http = _http(handler)
    provider = NoopMail(http)
    try:
        box = await provider.create_mailbox(MailboxSpec(domain="yzcalo.com"))
        local, sep, domain = box.address.partition("@")
        assert sep and domain == "yzcalo.com"
        assert len(local) == 10
        assert box.token == ""
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_list_messages_posts_local_and_domain():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/api/c"
        assert request.headers["user-agent"] == _UA
        assert json.loads(request.content) == {"e": "al234tf05o", "d": "yzcalo.com"}
        return httpx.Response(
            200,
            json=[
                {
                    "id": "HcTsW_BHeZm9dWhe",
                    "m_id": "CDNKAWl4687wKMey",
                    "to": "al234tf05o@yzcalo.com",
                    "from": "sf_root@outlook.com",
                    "subject": "thene",
                    "text": "first line\nsecond\n",
                    "hasAttm": 0,
                    "date": "2026-09-15T20:30:05.000Z",
                }
            ],
        )

    http = _http(handler)
    provider = NoopMail(http)
    try:
        msgs = await provider.list_messages(_mailbox())
        assert len(msgs) == 1
        msg = msgs[0]
        assert msg.id == "HcTsW_BHeZm9dWhe"
        assert msg.subject == "thene"
        assert msg.from_.name is None
        assert msg.from_.address == "sf_root@outlook.com"
        assert msg.to[0].address == "al234tf05o@yzcalo.com"
        assert msg.intro == "first line"
        assert msg.seen is False
        assert msg.has_attachments is False
        assert msg.received_at is not None
        assert msg.received_at.tzinfo is not None
        assert msg.received_at.isoformat() == "2026-09-15T20:30:05+00:00"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_list_messages_parses_named_from():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=[
                {
                    "id": "x",
                    "from": '"Some Bot" <bot@ex.com>',
                    "to": "al234tf05o@yzcalo.com",
                    "subject": "s",
                    "text": "t\n",
                    "hasAttm": 1,
                    "date": "2026-09-15T20:30:05Z",
                }
            ],
        )

    http = _http(handler)
    provider = NoopMail(http)
    try:
        msgs = await provider.list_messages(_mailbox())
        assert msgs[0].from_.name == "Some Bot"
        assert msgs[0].from_.address == "bot@ex.com"
        assert msgs[0].has_attachments is True
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_message_maps_detail():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "GET"
        assert request.url.path == "/api/i/HcTsW_BHeZm9dWhe"
        assert request.headers["user-agent"] == _UA
        return httpx.Response(
            200,
            json={
                "id": "HcTsW_BHeZm9dWhe",
                "m_id": "CDNKAWl4687wKMey",
                "from": "sf_root@outlook.com",
                "to": "al234tf05o@yzcalo.com",
                "cc": None,
                "subject": "thene",
                "hasAttm": 0,
                "html": "<html><body>hi</body></html>",
                "text": "hello world\n",
                "atts": None,
                "date": "2026-09-15T20:30:05Z",
            },
        )

    http = _http(handler)
    provider = NoopMail(http)
    try:
        detail = await provider.get_message(_mailbox(), "HcTsW_BHeZm9dWhe")
        assert detail.id == "HcTsW_BHeZm9dWhe"
        assert detail.subject == "thene"
        assert detail.from_.address == "sf_root@outlook.com"
        assert detail.to[0].address == "al234tf05o@yzcalo.com"
        assert detail.seen is False
        assert detail.text == "hello world\n"
        assert detail.html == ["<html><body>hi</body></html>"]
        assert detail.attachments == []
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_message_missing_raises_not_found():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "message not found"})

    http = _http(handler)
    provider = NoopMail(http)
    try:
        with pytest.raises(MailNotFoundError):
            await provider.get_message(_mailbox(), "missing")
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_source_fetches_raw_and_decodes_base64():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/api/i/HcTsW_BHeZm9dWhe":
            return httpx.Response(
                200,
                json={
                    "id": "HcTsW_BHeZm9dWhe",
                    "m_id": "CDNKAWl4687wKMey",
                    "from": "a@b.c",
                    "to": "al234tf05o@yzcalo.com",
                    "subject": "s",
                    "html": "",
                    "text": "t\n",
                    "date": "2026-09-15T20:30:05Z",
                },
            )
        assert request.url.path == "/raw/CDNKAWl4687wKMey"
        return httpx.Response(200, json={"data": "RnJvbTogYQo="})  # base64("From: a\n")

    http = _http(handler)
    provider = NoopMail(http)
    try:
        src = await provider.get_source(_mailbox(), "HcTsW_BHeZm9dWhe")
        assert src.id == "HcTsW_BHeZm9dWhe"
        assert src.data == "From: a\n"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_source_raises_when_message_missing():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={})

    http = _http(handler)
    provider = NoopMail(http)
    try:
        with pytest.raises(MailNotFoundError):
            await provider.get_source(_mailbox(), "missing")
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_delete_message_is_idempotent_on_404():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            assert request.url.path == "/api/i/HcTsW_BHeZm9dWhe"
            return httpx.Response(
                200,
                json={
                    "id": "HcTsW_BHeZm9dWhe",
                    "m_id": "CDNKAWl4687wKMey",
                    "from": "a@b.c",
                    "to": "al234tf05o@yzcalo.com",
                    "subject": "s",
                    "html": "",
                    "text": "t\n",
                    "date": "2026-09-15T20:30:05Z",
                },
            )
        assert request.method == "DELETE"
        assert request.url.path == "/api/i/HcTsW_BHeZm9dWhe/CDNKAWl4687wKMey"
        return httpx.Response(404, json={"detail": "message not found"})

    http = _http(handler)
    provider = NoopMail(http)
    try:
        assert await provider.delete_message(_mailbox(), "HcTsW_BHeZm9dWhe") is True
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_delete_message_success():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            assert request.url.path == "/api/i/HcTsW_BHeZm9dWhe"
            return httpx.Response(
                200,
                json={
                    "id": "HcTsW_BHeZm9dWhe",
                    "m_id": "CDNKAWl4687wKMey",
                    "from": "a@b.c",
                    "to": "al234tf05o@yzcalo.com",
                    "subject": "s",
                    "html": "",
                    "text": "t\n",
                    "date": "2026-09-15T20:30:05Z",
                },
            )
        assert request.method == "DELETE"
        assert request.url.path == "/api/i/HcTsW_BHeZm9dWhe/CDNKAWl4687wKMey"
        return httpx.Response(200, json={"ok": True})

    http = _http(handler)
    provider = NoopMail(http)
    try:
        assert await provider.delete_message(_mailbox(), "HcTsW_BHeZm9dWhe") is True
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_delete_mailbox_returns_true_but_does_not_call_network():
    called = False

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal called
        called = True
        return httpx.Response(500)

    http = _http(handler)
    provider = NoopMail(http)
    try:
        assert await provider.delete_mailbox(_mailbox()) is True
        assert called is False
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_mark_read_is_noop():
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no network expected for mark_read")

    http = _http(handler)
    provider = NoopMail(http)
    try:
        assert await provider.mark_read(_mailbox(), "HcTsW_BHeZm9dWhe") is True
    finally:
        await http.close()
