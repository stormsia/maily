from __future__ import annotations

import json

import httpx
import pytest

from mailtmapi.http import HttpClient
from mailtmapi.providers.base import MailboxInfo, MailboxSpec
from mailtmapi.providers.mailtm import MailTM


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
        box = await provider.create_mailbox(MailboxSpec(address="user@mail.tm", password="secret"))
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
