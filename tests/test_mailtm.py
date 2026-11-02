from __future__ import annotations

import json

import httpx
import pytest

from maily.http import HttpClient
from maily.providers.base import MailboxInfo, MailboxSpec
from maily.providers.mailtm import MailTM


def _http(handler) -> HttpClient:
    http = HttpClient.__new__(HttpClient)
    http._client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
    )
    return http


@pytest.mark.asyncio
async def test_list_targets_maps_hydra_member():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/domains"
        return httpx.Response(
            200,
            json={"hydra:member": [{"id": "1", "domain": "mail.tm", "isActive": True}]},
        )

    http = _http(handler)
    provider = MailTM(http)
    try:
        targets = await provider.list_targets()
        assert len(targets) == 1
        assert targets[0].id == "mail.tm"
        assert targets[0].kind == "domain"
        assert targets[0].provider == "mail.tm"
        assert targets[0].label == "mail.tm"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_posts_account_and_token():
    posts: list[tuple[str, dict]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "POST" and request.url.path == "/accounts":
            body = json.loads(request.content)
            posts.append(("accounts", body))
            return httpx.Response(201, json={"id": "acc1", "address": body["address"]})
        if request.method == "POST" and request.url.path == "/token":
            body = json.loads(request.content)
            posts.append(("token", body))
            return httpx.Response(200, json={"id": "acc1", "token": "jwt-token"})
        return httpx.Response(404, json={"detail": "not found"})

    http = _http(handler)
    provider = MailTM(http)
    try:
        box = await provider.create_mailbox(
            MailboxSpec(address="user@mail.tm", password="secret")
        )
        assert box.provider == "mail.tm"
        assert box.address == "user@mail.tm"
        assert box.token == "jwt-token"
        assert box.provider_account_id == "acc1"
        assert box.password == "secret"
        assert posts[0][0] == "accounts"
        assert posts[0][1] == {"address": "user@mail.tm", "password": "secret"}
        assert posts[1][0] == "token"
        assert posts[1][1] == {"address": "user@mail.tm", "password": "secret"}
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_list_messages_maps_hydra_to_summary():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/messages"
        assert request.headers["Authorization"] == "Bearer jwt-token"
        assert request.url.params["page"] == "1"
        return httpx.Response(
            200,
            json={
                "hydra:member": [
                    {
                        "id": "m1",
                        "subject": "Hello",
                        "from": {"name": "A", "address": "a@b.c"},
                        "to": [{"name": "", "address": "user@mail.tm"}],
                        "intro": "hi",
                        "seen": False,
                        "hasAttachments": True,
                        "size": 12,
                        "createdAt": "2024-01-15T12:30:45+00:00",
                    }
                ]
            },
        )

    http = _http(handler)
    provider = MailTM(http)
    mailbox = MailboxInfo(provider="mail.tm", address="user@mail.tm", token="jwt-token")
    try:
        msgs = await provider.list_messages(mailbox)
        assert len(msgs) == 1
        msg = msgs[0]
        assert msg.id == "m1"
        assert msg.subject == "Hello"
        assert msg.from_.address == "a@b.c"
        assert msg.to[0].address == "user@mail.tm"
        assert msg.intro == "hi"
        assert msg.seen is False
        assert msg.has_attachments is True
        assert msg.size == 12
        assert msg.received_at is not None
        assert msg.received_at.year == 2024
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_get_message_quotes_slash_in_id():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.raw_path == b"/messages/a%2Fb"
        return httpx.Response(
            200,
            json={
                "id": "a/b",
                "subject": "x",
                "from": {},
                "to": [],
                "createdAt": "2024-01-15T12:30:45+00:00",
            },
        )

    http = _http(handler)
    provider = MailTM(http)
    mailbox = MailboxInfo(provider="mail.tm", address="user@mail.tm", token="jwt-token")
    try:
        detail = await provider.get_message(mailbox, "a/b")
        assert detail.id == "a/b"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_delete_mailbox_and_messages():
    deleted_paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        deleted_paths.append((request.method, request.url.path))
        if request.method == "DELETE":
            return httpx.Response(204)
        if request.method == "PATCH":
            return httpx.Response(200, json={"seen": True})
        if request.method == "GET" and "/sources/" in request.url.path:
            return httpx.Response(
                200,
                json={
                    "id": "src1",
                    "data": "raw-source-data",
                    "downloadUrl": "http://dl",
                },
            )
        return httpx.Response(404)

    http = _http(handler)
    provider = MailTM(http)
    mailbox = MailboxInfo(
        provider="mail.tm",
        address="user@mail.tm",
        token="jwt-token",
        provider_account_id="acc123",
    )
    try:
        # Delete mailbox
        ok = await provider.delete_mailbox(mailbox)
        assert ok is True
        assert ("DELETE", "/accounts/acc123") in deleted_paths

        # Delete mailbox with no account id
        no_acc_box = MailboxInfo(
            provider="mail.tm", address="user@mail.tm", token="jwt-token"
        )
        assert await provider.delete_mailbox(no_acc_box) is False

        # Delete message
        msg_ok = await provider.delete_message(mailbox, "msg1")
        assert msg_ok is True
        assert ("DELETE", "/messages/msg1") in deleted_paths

        # Mark read
        read_ok = await provider.mark_read(mailbox, "msg1")
        assert read_ok is True

        # Get source
        src = await provider.get_source(mailbox, "msg1")
        assert src.id == "src1"
        assert src.data == "raw-source-data"
        assert src.download_url == "http://dl"
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_create_mailbox_auto_domain():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/domains":
            return httpx.Response(
                200,
                json={"hydra:member": [{"domain": "autodomain.com", "isActive": True}]},
            )
        if request.method == "POST" and request.url.path == "/accounts":
            body = json.loads(request.content)
            return httpx.Response(
                201, json={"id": "acc_auto", "address": body["address"]}
            )
        if request.method == "POST" and request.url.path == "/token":
            return httpx.Response(200, json={"token": "auto_jwt"})
        return httpx.Response(404)

    http = _http(handler)
    provider = MailTM(http)
    try:
        box = await provider.create_mailbox(MailboxSpec())
        assert box.address.endswith("@autodomain.com")
        assert box.token == "auto_jwt"
    finally:
        await http.close()
