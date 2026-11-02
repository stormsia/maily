from __future__ import annotations

import json
import logging
from typing import Any

import httpx
import pytest

from maily.client import (
    ApiError,
    AuthenticationError,
    ClientError,
    ExtractedConfirmation,
    ForbiddenError,
    Mailbox,
    Maily,
    NotFoundError,
    RateLimitError,
    SyncMaily,
    UpstreamProviderError,
    ValidationError,
    WaitTimeoutError,
)
from maily.standalone_client import _extract_detail, _parse_retry_after, _Transport

BASE = "http://test"


def _api(handler) -> Maily:
    return Maily(
        base_url=BASE,
        api_key="secret",
        client=httpx.AsyncClient(base_url=BASE, transport=httpx.MockTransport(handler)),
    )


def _router(routes: dict[tuple[str, str], httpx.Response]) -> Any:
    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        if key not in routes:
            return httpx.Response(404, json={"detail": f"no route for {key}"})
        return routes[key]

    return handler


@pytest.mark.asyncio
async def test_health():
    api = _api(_router({("GET", "/health"): httpx.Response(200, json={"status": "ok"})}))
    try:
        h = await api.health.ping()
        assert h.status == "ok"
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_providers_and_targets():
    api = _api(
        _router(
            {
                (
                    "GET",
                    "/v1/providers",
                ): httpx.Response(200, json=[{"slug": "mail.tm", "kind": "domain"}]),
                ("GET", "/v1/targets"): httpx.Response(
                    200,
                    json=[
                        {
                            "id": "g1",
                            "kind": "parent",
                            "provider": "gmail",
                            "label": "me@gmail.com",
                        },
                        {
                            "id": "d1",
                            "kind": "domain",
                            "provider": "mail.tm",
                            "label": "mail.tm",
                        },
                    ],
                ),
            }
        )
    )
    try:
        provs = await api.providers.list()
        assert provs[0].slug == "mail.tm"

        targets = await api.providers.targets()
        assert targets[0].kind == "parent"
        assert targets[1].label == "mail.tm"

        # provider filter is forwarded as query param
        async def filter_handler(request: httpx.Request) -> httpx.Response:
            assert request.url.params["provider"] == "gmail"
            return httpx.Response(200, json=[])

        api2 = _api(filter_handler)
        try:
            assert await api2.providers.targets("gmail") == []
        finally:
            await api2.close()
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_mailbox_lifecycle():
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and path == "/v1/mailboxes":
            body = json.loads(request.content)
            assert body == {"provider": "mail.tm", "domain": "mail.tm"}
            return httpx.Response(
                201,
                json={
                    "id": 1,
                    "provider": "mail.tm",
                    "address": "x@mail.tm",
                    "is_active": True,
                    "created_at": "2026-01-01T00:00:00Z",
                },
            )
        if request.method == "GET" and path == "/v1/mailboxes":
            if "active" in request.url.params:
                assert request.url.params["active"] == "true"
            return httpx.Response(200, json=[])
        if request.method == "GET" and path == "/v1/mailboxes/1":
            return httpx.Response(
                200,
                json={
                    "id": 1,
                    "provider": "mail.tm",
                    "address": "x@mail.tm",
                    "is_active": True,
                },
            )
        if request.method == "GET" and path == "/v1/mailboxes/by-address/x@mail.tm":
            return httpx.Response(
                200,
                json={
                    "id": 1,
                    "provider": "mail.tm",
                    "address": "x@mail.tm",
                    "is_active": True,
                },
            )
        if request.method == "DELETE" and path == "/v1/mailboxes/1":
            return httpx.Response(204)
        return httpx.Response(404)

    api = _api(handler)
    try:
        mb = await api.mailboxes.create(provider="mail.tm", domain="mail.tm")
        assert mb.id == 1
        assert mb.address == "x@mail.tm"

        box = await api.mailboxes.get(1)
        assert box.id == 1

        same = await api.mailboxes.by_address("x@mail.tm")
        assert same.id == 1

        assert await api.mailboxes.list(active=True) == []

        await api.mailboxes.delete(1)

        # flat deprecated-compat methods behave identically
        mb2 = await api.create_mailbox(provider="mail.tm", domain="mail.tm")
        assert mb2.id == 1
        assert (await api.list_mailboxes()) == []
        assert (await api.mailbox(1)).id == 1
        assert (await api.mailbox_by_address("x@mail.tm")).id == 1
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_messages_flow_and_wait_for():
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path == "/v1/mailboxes/1/messages":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 10,
                        "message_api_id": "m1",
                        "subject": "Hi",
                        "from_address": "a@b.c",
                        "from_name": "",
                        "seen": False,
                    }
                ],
            )
        if request.method == "GET" and path == "/v1/mailboxes/1/messages/m1":
            return httpx.Response(
                200,
                json={
                    "id": 10,
                    "message_api_id": "m1",
                    "subject": "Hi",
                    "from_address": "a@b.c",
                    "text": "body",
                    "html": [],
                    "seen": False,
                },
            )
        if request.method == "POST" and path == "/v1/mailboxes/1/messages/m1/read":
            return httpx.Response(
                200,
                json={
                    "id": 10,
                    "message_api_id": "m1",
                    "subject": "Hi",
                    "from_address": "a@b.c",
                    "seen": True,
                },
            )
        if request.method == "GET" and path == "/v1/mailboxes/1/messages/m1/source":
            return httpx.Response(
                200, json={"id": "m1", "data": "From: a@b.c\n", "download_url": ""}
            )
        if request.method == "DELETE" and path == "/v1/mailboxes/1/messages/m1":
            return httpx.Response(204)
        return httpx.Response(404)

    api = _api(handler)
    try:
        msgs = await api.messages.list(1)
        assert len(msgs) == 1
        assert msgs[0].message_api_id == "m1"
        assert msgs[0].subject == "Hi"

        detail = await api.messages.get(1, "m1")
        assert detail.text == "body"
        assert detail.from_address == "a@b.c"

        marked = await api.messages.mark_read(1, "m1")
        assert marked.seen is True

        src = await api.messages.source(1, "m1")
        assert src.data == "From: a@b.c\n"

        found = await api.messages.wait_for(
            1, timeout=10.0, interval=0.001, predicate=lambda m: m.subject == "Hi"
        )
        assert found.message_api_id == "m1"

        await api.messages.delete(1, "m1")

    finally:
        await api.close()


@pytest.mark.asyncio
async def test_gmail_flow():
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "POST" and path == "/v1/gmail/oauth/start":
            return httpx.Response(
                200,
                json={
                    "auth_url": "https://accounts.google.com/o/oauth2/…",
                    "state": "s1",
                },
            )
        if request.method == "POST" and path == "/v1/gmail/accounts/import":
            body = json.loads(request.content)
            assert body.get("refresh_token") == "rt"
            return httpx.Response(
                201,
                json={
                    "id": 2,
                    "email": "me@gmail.com",
                    "status": "active",
                    "send_as": [],
                },
            )
        if request.method == "GET" and path == "/v1/gmail/accounts":
            return httpx.Response(200, json=[])
        if request.method == "POST" and path == "/v1/gmail/accounts/2/sync":
            return httpx.Response(
                200,
                json={
                    "id": 2,
                    "email": "me@gmail.com",
                    "status": "active",
                    "send_as": ["a@b.c"],
                },
            )
        if request.method == "DELETE" and path == "/v1/gmail/accounts/2":
            return httpx.Response(204)
        return httpx.Response(404)

    api = _api(handler)
    try:
        start = await api.gmail.oauth_start()
        assert start.state == "s1"
        assert start.auth_url.startswith("https://accounts.google.com")

        acc = await api.gmail.import_account(refresh_token="rt")
        assert acc.email == "me@gmail.com"
        assert acc.status == "active"

        assert await api.gmail.accounts() == []

        synced = await api.gmail.sync(2)
        assert synced.send_as == ["a@b.c"]

        await api.gmail.delete_account(2)
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_admin_flow():
    async def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if request.method == "GET" and path == "/v1/admin/stats":
            return httpx.Response(200, json={"mailboxes": {"total": 1}})
        if request.method == "GET" and path == "/v1/admin/retention":
            return httpx.Response(200, json=[])
        if request.method == "PUT" and path == "/v1/admin/retention/mail.tm":
            return httpx.Response(
                200,
                json={
                    "provider": "mail.tm",
                    "mailbox_ttl_hours": 24,
                    "message_ttl_hours": None,
                },
            )
        if request.method == "DELETE" and path == "/v1/admin/retention/mail.tm":
            return httpx.Response(204)
        if request.method == "POST" and path == "/v1/admin/retention/run":
            return httpx.Response(200, json={"mailboxes_deleted": 2, "messages_deleted": 5})
        if request.method == "GET" and path == "/v1/admin/domain-cache":
            return httpx.Response(
                200,
                json={
                    "enabled": True,
                    "interval_seconds": 1800,
                    "providers": [{"provider": "mail.tm", "kind": "domain", "domains_count": 3}],
                },
            )
        if request.method == "PUT" and path == "/v1/admin/domain-cache":
            return httpx.Response(
                200, json={"enabled": False, "interval_seconds": 60, "providers": []}
            )
        if request.method == "POST" and path == "/v1/admin/domain-cache/run":
            return httpx.Response(200, json={"refreshed": ["mail.tm"], "failed": []})
        if request.method == "GET" and path == "/v1/admin/gmail/creds":
            return httpx.Response(
                200,
                json={
                    "configured": True,
                    "source": "db",
                    "client_id": "cid.apps.googleusercontent.com",
                    "redirect_uri": "http://x/callback",
                },
            )
        if request.method == "PUT" and path == "/v1/admin/gmail/creds":
            return httpx.Response(
                200, json={"configured": True, "source": "db", "client_id": "new"}
            )
        if request.method == "DELETE" and path == "/v1/admin/gmail/creds":
            return httpx.Response(204)
        return httpx.Response(404)

    api = _api(handler)
    try:
        stats = await api.admin.stats()
        assert stats["mailboxes"]["total"] == 1

        assert await api.admin.retention_list() == []
        r = await api.admin.retention_set("mail.tm", mailbox_ttl_hours=24)
        assert r.mailbox_ttl_hours == 24
        await api.admin.retention_disable("mail.tm")
        sweep = await api.admin.retention_run()
        assert sweep.mailboxes_deleted == 2

        dc = await api.admin.domain_cache()
        assert dc.providers[0].domains_count == 3
        dc2 = await api.admin.domain_cache_save(enabled=False, interval_seconds=60)
        assert dc2.enabled is False
        run = await api.admin.domain_cache_run()
        assert run.failed == []

        creds = await api.admin.gmail_creds()
        assert creds.configured is True
        c2 = await api.admin.gmail_creds_save("new", "sec")
        assert c2.client_id == "new"
        await api.admin.gmail_creds_clear()
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_error_mapping_with_detail():
    api = _api(
        _router({("GET", "/v1/mailboxes/1"): httpx.Response(404, json={"detail": "no box"})})
    )
    try:
        with pytest.raises(ApiError) as exc:
            await api.mailboxes.get(1)
        assert exc.value.status_code == 404
        assert exc.value.detail == "no box"
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_error_mapping_without_json_body():
    api = _api(
        _router(
            {
                ("GET", "/v1/mailboxes/1"): httpx.Response(
                    500, text="internal oops", headers={"Content-Type": "text/plain"}
                )
            }
        )
    )
    try:
        with pytest.raises(ApiError) as exc:
            await api.mailboxes.get(1)
        assert exc.value.status_code == 500
        assert "internal oops" in exc.value.detail
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_network_error_maps_to_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    api = _api(handler)
    try:
        with pytest.raises(ApiError) as exc:
            await api.health.ping()
        assert exc.value.status_code is None
        assert "network error" in exc.value.detail
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_set_api_key_updates_header():
    seen: list[str] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request.headers.get("X-API-Key", ""))
        return httpx.Response(200, json=[])

    api = _api(handler)
    try:
        await api.mailboxes.list()
        api.set_api_key("other")
        await api.mailboxes.list()
        api.set_api_key("")
        await api.mailboxes.list()
        assert seen == ["secret", "other", ""]
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_url_quoting_for_message_ids():
    def handler(request: httpx.Request) -> httpx.Response:
        raw = request.url.raw_path.decode()
        assert raw == "/v1/mailboxes/1/messages/..%2F..%2Fetc/source"
        return httpx.Response(200, json={"id": "1", "data": ""})

    api = _api(handler)
    try:
        await api.messages.source(1, "../../etc")
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_granular_error_hierarchy():
    routes = {
        ("GET", "/v1/err/401"): httpx.Response(401, json={"detail": "Unauthorized"}),
        ("GET", "/v1/err/403"): httpx.Response(403, json={"detail": "Forbidden"}),
        ("GET", "/v1/err/404"): httpx.Response(404, json={"detail": "Not found"}),
        ("GET", "/v1/err/422"): httpx.Response(422, json={"detail": "Bad entity"}),
        ("GET", "/v1/err/429"): httpx.Response(429, json={"detail": "Rate limit"}),
        ("GET", "/v1/err/502"): httpx.Response(502, json={"detail": "Bad gateway"}),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        return routes.get(key, httpx.Response(404))

    api = _api(handler)
    try:
        with pytest.raises(AuthenticationError) as e:
            await api._transport.request("GET", "/v1/err/401")
        assert e.value.status_code == 401
        assert isinstance(e.value, ApiError)

        with pytest.raises(ForbiddenError):
            await api._transport.request("GET", "/v1/err/403")

        with pytest.raises(NotFoundError):
            await api._transport.request("GET", "/v1/err/404")

        with pytest.raises(ValidationError):
            await api._transport.request("GET", "/v1/err/422")

        with pytest.raises(RateLimitError):
            await api._transport.request("GET", "/v1/err/429")

        with pytest.raises(UpstreamProviderError):
            await api._transport.request("GET", "/v1/err/502")
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_keys_api_typed():
    async def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if request.method == "GET" and p == "/v1/admin/keys":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "name": "test-key",
                        "prefix": "sk-test",
                        "scope": {
                            "providers": ["mail.tm"],
                            "parent_ids": [],
                            "actions": ["read"],
                        },
                        "key_retention": [],
                    }
                ],
            )
        if request.method == "POST" and p == "/v1/admin/keys":
            return httpx.Response(
                201,
                json={
                    "id": 2,
                    "name": "new-key",
                    "prefix": "sk-new",
                    "secret": "sk-new-secret",
                    "scope": {"providers": [], "parent_ids": [], "actions": []},
                    "key_retention": [],
                },
            )
        if request.method == "GET" and p == "/v1/admin/keys/1":
            return httpx.Response(
                200,
                json={
                    "id": 1,
                    "name": "test-key",
                    "prefix": "sk-test",
                    "scope": {
                        "providers": ["mail.tm"],
                        "parent_ids": [],
                        "actions": ["read"],
                    },
                    "key_retention": [],
                },
            )
        if request.method == "GET" and p == "/v1/admin/keys/me":
            return httpx.Response(200, json={"is_root": True, "name": "root"})
        if request.method == "GET" and p == "/v1/admin/keys/1/secret":
            return httpx.Response(200, json={"secret": "full-secret"})
        if request.method == "PATCH" and p == "/v1/admin/keys/1":
            return httpx.Response(
                200,
                json={
                    "id": 1,
                    "name": "renamed",
                    "prefix": "sk-test",
                    "scope": {
                        "providers": ["mail.tm"],
                        "parent_ids": [],
                        "actions": [],
                    },
                    "key_retention": [],
                },
            )
        if request.method == "POST" and p == "/v1/admin/keys/1/rotate":
            return httpx.Response(
                200,
                json={
                    "id": 1,
                    "name": "test-key",
                    "prefix": "sk-test",
                    "secret": "rotated-secret",
                    "scope": {"providers": [], "parent_ids": [], "actions": []},
                    "key_retention": [],
                },
            )
        if request.method == "DELETE" and p == "/v1/admin/keys/1":
            return httpx.Response(204)
        return httpx.Response(404)

    api = _api(handler)
    try:
        keys = await api.keys.list()
        assert len(keys) == 1
        assert keys[0].id == 1
        assert keys[0].scope.providers == ["mail.tm"]

        created = await api.keys.create(name="new-key")
        assert created.secret == "sk-new-secret"

        k1 = await api.keys.get(1)
        assert k1.name == "test-key"

        me = await api.keys.me()
        assert me.is_root is True

        sec = await api.keys.secret(1)
        assert sec == "full-secret"

        up = await api.keys.update(1, name="renamed")
        assert up.name == "renamed"

        rot = await api.keys.rotate(1)
        assert rot.secret == "rotated-secret"

        await api.keys.delete(1)
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_wait_for_code_and_link():
    box = Mailbox(id=1, provider="mail.tm", address="test@mail.tm", is_active=True)

    async def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if request.method == "GET" and p == "/v1/mailboxes/1/messages":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 10,
                        "message_api_id": "m1",
                        "subject": "Verify code",
                        "from_address": "support@service.com",
                    }
                ],
            )
        if request.method == "GET" and p == "/v1/mailboxes/1/messages/m1":
            return httpx.Response(
                200,
                json={
                    "id": 10,
                    "message_api_id": "m1",
                    "subject": "Verify code",
                    "from_address": "support@service.com",
                    "text": "Your verification code is 849201. Click https://service.com/confirm?token=xyz to confirm.",
                    "html": [],
                },
            )
        return httpx.Response(404)

    api = _api(handler)
    try:
        code = await api.wait_for_code(box, timeout=10.0, check_interval=0.001)
        assert code == "849201"

        link = await api.wait_for_link(box, timeout=10.0, check_interval=0.001)
        assert "https://service.com/confirm?token=xyz" in link

        # Timeout scenario
        with pytest.raises(WaitTimeoutError):
            await api.wait_for_code(
                box, sender_domain="other.com", timeout=0.05, check_interval=0.01
            )
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_iter_messages():
    box = Mailbox(id=5, provider="mail.tm", address="box@mail.tm", is_active=True)
    counter = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal counter
        counter += 1
        msgs = [{"id": 1, "message_api_id": "msg-init", "subject": "Init"}]
        if counter > 1:
            msgs.append({"id": 2, "message_api_id": f"msg-new-{counter}", "subject": "New!"})
        return httpx.Response(200, json=msgs)

    api = _api(handler)
    try:
        collected = []
        async for msg in api.messages.iter_messages(box, poll_interval=0.001, timeout=10.0):
            collected.append(msg.message_api_id)
            if len(collected) >= 2:
                break
        assert len(collected) >= 1
        assert "msg-init" not in collected
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_create_temp_mailbox():
    async def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if request.method == "GET" and p == "/v1/targets":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "d1",
                        "kind": "domain",
                        "provider": "mail.tm",
                        "label": "mail.tm",
                    }
                ],
            )
        if request.method == "POST" and p == "/v1/mailboxes":
            return httpx.Response(
                201,
                json={
                    "id": 99,
                    "provider": "mail.tm",
                    "address": "auto@mail.tm",
                    "is_active": True,
                },
            )
        return httpx.Response(404)

    api = _api(handler)
    try:
        box = await api.create_temp_mailbox()
        assert box.id == 99
        assert box.address == "auto@mail.tm"
    finally:
        await api.close()


# =========================================================================== #
# Milestone 3 Test Suite Expansion: Facades, Sync, Retries, 422, Edge Cases
# =========================================================================== #

# --- 1. All 16 Flat Facade Shortcuts on Maily ---


@pytest.mark.asyncio
async def test_all_16_facade_shortcut_methods():
    mailbox_data = {
        "id": 42,
        "provider": "mail.tm",
        "address": "shortcut@mail.tm",
        "is_active": True,
        "created_at": "2026-01-01T00:00:00Z",
    }
    message_summary_data = {
        "id": 100,
        "message_api_id": "msg_shortcut_1",
        "subject": "Verification Alert",
        "from_address": "notify@example.com",
        "from_name": "Alerts",
        "seen": False,
        "has_attachments": False,
        "size": 128,
        "received_at": "2026-01-01T00:01:00Z",
    }
    message_detail_data = {
        **message_summary_data,
        "text": "Your verification code is 123456",
        "html": ["<p>Your verification code is 123456</p>"],
    }
    message_source_data = {
        "id": "msg_shortcut_1",
        "data": "From: notify@example.com\nSubject: Verification Alert\n\nYour code is 123456",
        "download_url": "http://test/download",
    }
    gmail_account_data = {
        "id": 7,
        "email": "user@gmail.com",
        "status": "active",
        "send_as": ["alias@gmail.com"],
    }
    domain_cache_data = {
        "enabled": True,
        "interval_seconds": 900,
        "providers": [{"provider": "mail.tm", "kind": "domain", "domains_count": 5}],
    }

    recorded_calls: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        method = request.method
        path = request.url.path
        recorded_calls.append((method, path))

        # 1. create_mailbox -> POST /v1/mailboxes
        if method == "POST" and path == "/v1/mailboxes":
            return httpx.Response(201, json=mailbox_data)

        # 2. delete_mailbox -> DELETE /v1/mailboxes/42
        if method == "DELETE" and path == "/v1/mailboxes/42":
            return httpx.Response(204)

        # 3. list_messages & 16. wait_for_message -> GET /v1/mailboxes/42/messages
        if method == "GET" and path == "/v1/mailboxes/42/messages":
            return httpx.Response(200, json=[message_summary_data])

        # 4. get_message -> GET /v1/mailboxes/42/messages/msg_shortcut_1
        if method == "GET" and path == "/v1/mailboxes/42/messages/msg_shortcut_1":
            return httpx.Response(200, json=message_detail_data)

        # 5. mark_read -> POST /v1/mailboxes/42/messages/msg_shortcut_1/read
        if method == "POST" and path == "/v1/mailboxes/42/messages/msg_shortcut_1/read":
            read_summary = {**message_summary_data, "seen": True}
            return httpx.Response(200, json=read_summary)

        # 6. delete_message -> DELETE /v1/mailboxes/42/messages/msg_shortcut_1
        if method == "DELETE" and path == "/v1/mailboxes/42/messages/msg_shortcut_1":
            return httpx.Response(204)

        # 7. get_source -> GET /v1/mailboxes/42/messages/msg_shortcut_1/source
        if method == "GET" and path == "/v1/mailboxes/42/messages/msg_shortcut_1/source":
            return httpx.Response(200, json=message_source_data)

        # 8. gmail_oauth_start -> POST /v1/gmail/oauth/start
        if method == "POST" and path == "/v1/gmail/oauth/start":
            return httpx.Response(
                200,
                json={
                    "auth_url": "https://accounts.google.com/oauth",
                    "state": "st123",
                },
            )

        # 9. gmail_import_account -> POST /v1/gmail/accounts/import
        if method == "POST" and path == "/v1/gmail/accounts/import":
            return httpx.Response(201, json=gmail_account_data)

        # 10. list_gmail_accounts -> GET /v1/gmail/accounts
        if method == "GET" and path == "/v1/gmail/accounts":
            return httpx.Response(200, json=[gmail_account_data])

        # 11. delete_gmail_account -> DELETE /v1/gmail/accounts/7
        if method == "DELETE" and path == "/v1/gmail/accounts/7":
            return httpx.Response(204)

        # 12. sync_gmail_account -> POST /v1/gmail/accounts/7/sync
        if method == "POST" and path == "/v1/gmail/accounts/7/sync":
            return httpx.Response(200, json=gmail_account_data)

        # 13. domain_cache_settings -> GET /v1/admin/domain-cache
        if method == "GET" and path == "/v1/admin/domain-cache":
            return httpx.Response(200, json=domain_cache_data)

        # 14. save_domain_cache_settings -> PUT /v1/admin/domain-cache
        if method == "PUT" and path == "/v1/admin/domain-cache":
            body = json.loads(request.content)
            updated_cache = {
                **domain_cache_data,
                "enabled": body.get("enabled", domain_cache_data["enabled"]),
                "interval_seconds": body.get(
                    "interval_seconds", domain_cache_data["interval_seconds"]
                ),
            }
            return httpx.Response(200, json=updated_cache)

        # 15. refresh_domain_cache -> POST /v1/admin/domain-cache/run
        if method == "POST" and path == "/v1/admin/domain-cache/run":
            return httpx.Response(200, json={"refreshed": ["mail.tm"], "failed": []})

        return httpx.Response(404, json={"detail": f"Route not found: {method} {path}"})

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(base_url="http://test", api_key="secret", client=client)

    try:
        # Method 1: create_mailbox
        mb = await api.create_mailbox(provider="mail.tm", domain="mail.tm")
        assert mb.id == 42
        assert mb.address == "shortcut@mail.tm"

        # Method 3: list_messages (passing Mailbox object)
        msgs = await api.list_messages(mb, page=1)
        assert len(msgs) == 1
        assert msgs[0].message_api_id == "msg_shortcut_1"

        # Method 4: get_message
        detail = await api.get_message(mb, "msg_shortcut_1")
        assert detail.text == "Your verification code is 123456"

        # Method 5: mark_read
        marked = await api.mark_read(mb, "msg_shortcut_1")
        assert marked.seen is True

        # Method 7: get_source
        src = await api.get_source(mb, "msg_shortcut_1")
        assert "Verification Alert" in src.data

        # Method 16: wait_for_message
        polled = await api.wait_for_message(
            mb,
            timeout=10.0,
            interval=0.001,
            predicate=lambda m: "Alert" in m.subject,
        )
        assert polled.message_api_id == "msg_shortcut_1"

        # Method 6: delete_message
        await api.delete_message(mb, "msg_shortcut_1")

        # Method 2: delete_mailbox (accepts int or Mailbox)
        await api.delete_mailbox(mb)

        # Method 8: gmail_oauth_start
        oauth = await api.gmail_oauth_start()
        assert oauth.state == "st123"
        assert oauth.auth_url == "https://accounts.google.com/oauth"

        # Method 9: gmail_import_account (refresh_token and token_json)
        imported = await api.gmail_import_account(refresh_token="rt_test")
        assert imported.id == 7
        assert imported.email == "user@gmail.com"

        imported2 = await api.gmail_import_account(token_json={"token": "tok"})
        assert imported2.id == 7

        # Method 10: list_gmail_accounts
        accounts = await api.list_gmail_accounts()
        assert len(accounts) == 1
        assert accounts[0].id == 7

        # Method 12: sync_gmail_account
        synced = await api.sync_gmail_account(7)
        assert synced.send_as == ["alias@gmail.com"]

        # Method 11: delete_gmail_account
        await api.delete_gmail_account(7)

        # Method 13: domain_cache_settings
        dc = await api.domain_cache_settings()
        assert dc.enabled is True
        assert dc.interval_seconds == 900

        # Method 14: save_domain_cache_settings
        saved_dc = await api.save_domain_cache_settings(enabled=False, interval_seconds=1200)
        assert saved_dc.enabled is False
        assert saved_dc.interval_seconds == 1200

        # Method 15: refresh_domain_cache
        run_res = await api.refresh_domain_cache()
        assert run_res.refreshed == ["mail.tm"]
        assert run_res.failed == []

        assert len(recorded_calls) >= 16

    finally:
        await api.close()


@pytest.mark.asyncio
async def test_create_temp_mailbox_with_provider_only():
    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if request.method == "GET" and p == "/v1/targets":
            assert request.url.params.get("provider") == "mail.tm"
            return httpx.Response(
                200,
                json=[
                    {
                        "id": "d1",
                        "kind": "domain",
                        "provider": "mail.tm",
                        "label": "custom.tm",
                    }
                ],
            )
        if request.method == "POST" and p == "/v1/mailboxes":
            body = json.loads(request.content)
            assert body == {"provider": "mail.tm", "domain": "custom.tm"}
            return httpx.Response(
                201,
                json={
                    "id": 101,
                    "provider": "mail.tm",
                    "address": "test@custom.tm",
                    "is_active": True,
                },
            )
        return httpx.Response(404)

    api = _api(handler)
    try:
        box = await api.create_temp_mailbox(provider="mail.tm")
        assert box.id == 101
        assert box.address == "test@custom.tm"
    finally:
        await api.close()


# --- 2. SyncMaily Lifecycle & All 8 Sync Sections ---


def test_sync_client_lifecycle_and_post_close():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return httpx.Response(200, json={"status": "ok"})
        return httpx.Response(404)

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))

    with SyncMaily(client=client) as api:
        assert api.health.ping().status == "ok"
        assert api.max_retries == 0
        api.max_retries = 2
        assert api.max_retries == 2
        assert api.retry_backoff == 0.5
        api.retry_backoff = 0.1
        assert api.retry_backoff == 0.1
        api.set_api_key("sk-test")

    # Context manager exited, client is closed
    with pytest.raises(ClientError, match="SyncMaily is closed"):
        api.health.ping()

    with pytest.raises(ClientError, match="SyncMaily is closed"):
        api.set_api_key("new-key")

    with pytest.raises(ClientError, match="SyncMaily is closed"):
        api.create_mailbox()

    # Idempotent close
    api.close()


def test_sync_sections_and_facades():
    routes = {
        ("GET", "/health"): httpx.Response(200, json={"status": "ok"}),
        ("GET", "/v1/config"): httpx.Response(200, json={"client_version": "0.3.0"}),
        ("GET", "/v1/providers"): httpx.Response(200, json=[{"slug": "mail.tm", "kind": "domain"}]),
        ("GET", "/v1/targets"): httpx.Response(
            200,
            json=[
                {
                    "id": "d1",
                    "kind": "domain",
                    "provider": "mail.tm",
                    "label": "mail.tm",
                }
            ],
        ),
        ("POST", "/v1/mailboxes"): httpx.Response(
            201,
            json={
                "id": 1,
                "provider": "mail.tm",
                "address": "a@mail.tm",
                "is_active": True,
            },
        ),
        ("GET", "/v1/mailboxes"): httpx.Response(
            200,
            json=[
                {
                    "id": 1,
                    "provider": "mail.tm",
                    "address": "a@mail.tm",
                    "is_active": True,
                }
            ],
        ),
        ("GET", "/v1/mailboxes/1"): httpx.Response(
            200,
            json={
                "id": 1,
                "provider": "mail.tm",
                "address": "a@mail.tm",
                "is_active": True,
            },
        ),
        ("GET", "/v1/mailboxes/by-address/a@mail.tm"): httpx.Response(
            200,
            json={
                "id": 1,
                "provider": "mail.tm",
                "address": "a@mail.tm",
                "is_active": True,
            },
        ),
        ("DELETE", "/v1/mailboxes/1"): httpx.Response(204),
        ("GET", "/v1/mailboxes/1/messages"): httpx.Response(
            200,
            json=[
                {
                    "id": 10,
                    "message_api_id": "m1",
                    "subject": "Code 1234",
                    "from_address": "s@x.com",
                    "seen": False,
                }
            ],
        ),
        ("GET", "/v1/mailboxes/1/messages/m1"): httpx.Response(
            200,
            json={
                "id": 10,
                "message_api_id": "m1",
                "subject": "Code 1234",
                "from_address": "s@x.com",
                "text": "code is 1234 link https://x.com/c",
                "html": [],
                "seen": False,
            },
        ),
        ("POST", "/v1/mailboxes/1/messages/m1/read"): httpx.Response(
            200, json={"id": 10, "message_api_id": "m1", "seen": True}
        ),
        ("DELETE", "/v1/mailboxes/1/messages/m1"): httpx.Response(204),
        ("GET", "/v1/mailboxes/1/messages/m1/source"): httpx.Response(
            200, json={"id": "m1", "data": "raw"}
        ),
        ("POST", "/v1/gmail/oauth/start"): httpx.Response(
            200, json={"auth_url": "https://auth", "state": "s"}
        ),
        ("POST", "/v1/gmail/accounts/import"): httpx.Response(
            201,
            json={"id": 2, "email": "g@gmail.com", "status": "active", "send_as": []},
        ),
        ("GET", "/v1/gmail/accounts"): httpx.Response(200, json=[]),
        ("DELETE", "/v1/gmail/accounts/2"): httpx.Response(204),
        ("POST", "/v1/gmail/accounts/2/sync"): httpx.Response(
            200,
            json={"id": 2, "email": "g@gmail.com", "status": "active", "send_as": []},
        ),
        ("GET", "/v1/admin/stats"): httpx.Response(200, json={"total": 1}),
        ("GET", "/v1/admin/retention"): httpx.Response(200, json=[]),
        ("PUT", "/v1/admin/retention/mail.tm"): httpx.Response(
            200, json={"provider": "mail.tm", "mailbox_ttl_hours": 24}
        ),
        ("DELETE", "/v1/admin/retention/mail.tm"): httpx.Response(204),
        ("POST", "/v1/admin/retention/run"): httpx.Response(
            200, json={"mailboxes_deleted": 0, "messages_deleted": 0}
        ),
        ("GET", "/v1/admin/domain-cache"): httpx.Response(
            200, json={"enabled": True, "interval_seconds": 60, "providers": []}
        ),
        ("PUT", "/v1/admin/domain-cache"): httpx.Response(
            200, json={"enabled": False, "interval_seconds": 120, "providers": []}
        ),
        ("POST", "/v1/admin/domain-cache/run"): httpx.Response(
            200, json={"refreshed": [], "failed": []}
        ),
        ("GET", "/v1/admin/gmail/creds"): httpx.Response(
            200, json={"configured": True, "source": "db", "client_id": "c"}
        ),
        ("PUT", "/v1/admin/gmail/creds"): httpx.Response(
            200, json={"configured": True, "source": "db", "client_id": "c2"}
        ),
        ("DELETE", "/v1/admin/gmail/creds"): httpx.Response(204),
        ("GET", "/v1/admin/keys"): httpx.Response(200, json=[]),
        ("POST", "/v1/admin/keys"): httpx.Response(
            201,
            json={
                "id": 5,
                "name": "k",
                "prefix": "sk-5",
                "secret": "sk-5",
                "scope": {"providers": [], "parent_ids": [], "actions": []},
                "key_retention": [],
            },
        ),
        ("GET", "/v1/admin/keys/5"): httpx.Response(
            200,
            json={
                "id": 5,
                "name": "k",
                "prefix": "sk-5",
                "scope": {"providers": [], "parent_ids": [], "actions": []},
                "key_retention": [],
            },
        ),
        ("GET", "/v1/admin/keys/me"): httpx.Response(200, json={"is_root": True, "name": "root"}),
        ("GET", "/v1/admin/keys/5/secret"): httpx.Response(200, json={"secret": "full-sk"}),
        ("PATCH", "/v1/admin/keys/5"): httpx.Response(
            200,
            json={
                "id": 5,
                "name": "k2",
                "prefix": "sk-5",
                "scope": {"providers": [], "parent_ids": [], "actions": []},
                "key_retention": [],
            },
        ),
        ("PUT", "/v1/admin/keys/5/retention"): httpx.Response(200, json=[]),
        ("POST", "/v1/admin/keys/5/rotate"): httpx.Response(
            200,
            json={
                "id": 5,
                "name": "k",
                "prefix": "sk-rot",
                "secret": "sk-rot",
                "scope": {"providers": [], "parent_ids": [], "actions": []},
                "key_retention": [],
            },
        ),
        ("DELETE", "/v1/admin/keys/5"): httpx.Response(204),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        key = (request.method, request.url.path)
        return routes.get(key, httpx.Response(404, json={"detail": f"Route not found: {key}"}))

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    with SyncMaily(client=client) as api:
        # 1. Health & Config sections
        assert api.health.ping().status == "ok"
        assert api.config.get()["client_version"] == "0.3.0"
        assert api.check_client_version() == "0.3.0"

        # 2. Providers section
        assert len(api.providers.list()) == 1
        assert len(api.providers.targets()) == 1
        assert len(api.providers.targets(provider="mail.tm")) == 1

        # 3. Mailboxes section & flat shortcuts
        mb = api.mailboxes.create(domain="mail.tm")
        assert mb.id == 1
        assert (
            len(api.mailboxes.list(provider="mail.tm", active=True, q="a", limit=10, offset=0)) == 1
        )
        assert api.mailboxes.get(1).id == 1
        assert api.mailboxes.by_address("a@mail.tm").id == 1
        api.mailboxes.delete(1)

        # Facades
        assert api.create_mailbox(domain="mail.tm").id == 1
        assert len(api.list_mailboxes()) == 1
        assert api.mailbox(1).id == 1
        assert api.mailbox_by_address("a@mail.tm").id == 1
        api.delete_mailbox(1)
        assert api.create_temp_mailbox().id == 1

        # 4. Messages section & flat shortcuts
        assert len(api.messages.list(1)) == 1
        assert api.messages.get(1, "m1").text.startswith("code is")
        assert api.messages.mark_read(1, "m1").seen is True
        assert api.messages.source(1, "m1").data == "raw"
        assert (
            api.messages.wait_for(1, timeout=10.0, interval=0.001, mark_seen=True).message_api_id
            == "m1"
        )
        assert api.messages.wait_for_code(1, timeout=10.0, check_interval=0.001) == "1234"
        assert api.messages.wait_for_link(1, timeout=10.0, check_interval=0.001).startswith(
            "https://x.com/c"
        )
        conf = api.messages.wait_for_confirmation_email(
            1, digit_code_mask=r"\b(\d{4})\b", timeout=10.0, check_interval=0.001
        )
        assert conf is not None and conf["confirmation_code"] == "1234"
        api.messages.delete(1, "m1")

        # Facades
        assert len(api.list_messages(1)) == 1
        assert api.get_message(1, "m1").message_api_id == "m1"
        assert api.mark_read(1, "m1").seen is True
        assert api.get_source(1, "m1").data == "raw"
        assert api.wait_for_message(1, timeout=10.0, interval=0.001).message_api_id == "m1"
        assert api.wait_for_code(1, timeout=10.0, check_interval=0.001) == "1234"
        assert api.wait_for_link(1, timeout=10.0, check_interval=0.001).startswith(
            "https://x.com/c"
        )
        conf_facade = api.wait_for_confirmation_email(
            1, digit_code_mask=r"\b(\d{4})\b", timeout=10.0, check_interval=0.001
        )
        assert conf_facade is not None
        assert conf_facade["confirmation_code"] == "1234"
        api.delete_message(1, "m1")

        # 5. Gmail section & flat shortcuts
        assert api.gmail.oauth_start().state == "s"
        assert api.gmail.import_account(refresh_token="rt").email == "g@gmail.com"
        assert api.gmail.accounts() == []
        assert api.gmail.sync(2).id == 2
        api.gmail.delete_account(2)

        # Facades
        assert api.gmail_oauth_start().state == "s"
        assert api.gmail_import_account(token_json={"auth": 1}).email == "g@gmail.com"
        assert api.list_gmail_accounts() == []
        assert api.sync_gmail_account(2).id == 2
        api.delete_gmail_account(2)

        # 6. Admin section & flat shortcuts
        assert api.admin.stats()["total"] == 1
        assert api.admin.retention_list() == []
        assert api.admin.retention_set("mail.tm", mailbox_ttl_hours=24).mailbox_ttl_hours == 24
        api.admin.retention_disable("mail.tm")
        assert api.admin.retention_run().mailboxes_deleted == 0
        assert api.admin.domain_cache().enabled is True
        assert api.admin.domain_cache_save(enabled=False, interval_seconds=120).enabled is False
        assert api.admin.domain_cache_run().refreshed == []
        assert api.admin.gmail_creds().configured is True
        assert api.admin.gmail_creds_save(client_id="c2", client_secret="sec2").client_id == "c2"
        api.admin.gmail_creds_clear()

        # Admin untyped keys
        assert api.admin.keys() == []
        assert (
            api.admin.key_create(
                name="k",
                expires_at=None,
                scope={"providers": [], "parent_ids": [], "actions": []},
                retention=[],
            )["id"]
            == 5
        )
        assert api.admin.key_get(5)["id"] == 5
        assert api.admin.key_me()["is_root"] is True
        assert api.admin.key_secret(5) == {"secret": "full-sk"}
        assert (
            api.admin.key_update(
                5,
                name="k2",
                expires_at=None,
                scope={"providers": [], "parent_ids": [], "actions": []},
            )["id"]
            == 5
        )
        assert api.admin.key_retention_set(5, []) == []
        assert api.admin.key_rotate(5)["id"] == 5
        api.admin.key_delete(5)

        # Facades
        assert api.domain_cache_settings().enabled is True
        assert api.save_domain_cache_settings(enabled=False, interval_seconds=120).enabled is False
        assert api.refresh_domain_cache().refreshed == []

        # 7. Keys section (typed)
        assert api.keys.list() == []
        assert api.keys.create(name="k").secret == "sk-5"
        assert api.keys.get(5).id == 5
        assert api.keys.me().is_root is True
        assert api.keys.secret(5) == "full-sk"
        assert api.keys.update(5, name="k2").id == 5
        assert api.keys.retention_set(5, []) == []
        assert api.keys.rotate(5).secret == "sk-rot"
        api.keys.delete(5)


def test_sync_iter_messages():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                200, json=[{"id": 1, "message_api_id": "m-init", "subject": "Init"}]
            )
        return httpx.Response(
            200,
            json=[
                {"id": 1, "message_api_id": "m-init", "subject": "Init"},
                {"id": 2, "message_api_id": f"m-new-{calls}", "subject": "New"},
            ],
        )

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    with SyncMaily(client=client) as api:
        yielded = []
        for msg in api.messages.iter_messages(1, poll_interval=0.001, timeout=10.0):
            yielded.append(msg.message_api_id)
            if len(yielded) >= 2:
                break
        assert len(yielded) >= 1
        assert "m-init" not in yielded
        assert yielded[0].startswith("m-new-")


# --- 3. _Transport and Maily Retry Policies ---


@pytest.mark.asyncio
@pytest.mark.parametrize("err_cls", [httpx.ConnectTimeout, httpx.ConnectError, httpx.NetworkError])
async def test_transport_transient_network_errors_recovery(err_cls):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls <= 2:
            raise err_cls("transient connection glitch")
        return httpx.Response(200, json={"status": "recovered"})

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client, max_retries=3, retry_backoff=0.0001)
    res = await api._transport.request("GET", "/status")
    assert res == {"status": "recovered"}
    assert calls == 3


@pytest.mark.asyncio
async def test_transport_transient_network_errors_exhaustion():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("host unreachable")

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client, max_retries=2, retry_backoff=0.0001)
    with pytest.raises(ApiError) as exc_info:
        await api._transport.request("GET", "/status")
    assert exc_info.value.status_code is None
    assert "network error: host unreachable" in exc_info.value.detail
    assert calls == 3  # initial + 2 retries


@pytest.mark.asyncio
async def test_transport_read_timeout_no_retry():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("read timed out")

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client, max_retries=5, retry_backoff=0.0001)
    with pytest.raises(ApiError) as exc_info:
        await api._transport.request("GET", "/status")
    assert exc_info.value.status_code is None
    assert "network error: read timed out" in exc_info.value.detail
    assert calls == 1  # No retry performed on ReadTimeout!


@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [502, 504])
async def test_transport_502_504_recovery_and_exhaustion(status_code):
    # Recovery
    calls = 0

    def recovery_handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(status_code, text="Bad Gateway")
        return httpx.Response(200, json={"ok": True})

    client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(recovery_handler)
    )
    api = Maily(client=client, max_retries=2, retry_backoff=0.0001)
    res = await api._transport.request("GET", "/test")
    assert res == {"ok": True}
    assert calls == 2

    # Exhaustion
    calls = 0

    def exhaustion_handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status_code, text="Gateway Error")

    client2 = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(exhaustion_handler)
    )
    api2 = Maily(client=client2, max_retries=2, retry_backoff=0.0001)
    with pytest.raises(UpstreamProviderError) as exc_info:
        await api2._transport.request("GET", "/test")
    assert exc_info.value.status_code == status_code
    assert calls == 3


@pytest.mark.asyncio
async def test_transport_429_retry_after_header_parsing():
    # 1. Float Retry-After recovery
    calls = 0

    def h_float(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "0.001"},
                json={"detail": "Too many requests"},
            )
        return httpx.Response(200, json={"success": True})

    c1 = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(h_float))
    api1 = Maily(client=c1, max_retries=2, retry_backoff=0.0001)
    assert await api1._transport.request("GET", "/rate") == {"success": True}
    assert calls == 2

    # 2. Integer Retry-After recovery
    calls = 0

    def h_int(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                429, headers={"Retry-After": "0"}, json={"detail": "Too many requests"}
            )
        return httpx.Response(200, json={"success": True})

    c2 = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(h_int))
    api2 = Maily(client=c2, max_retries=1, retry_backoff=0.0001)
    assert await api2._transport.request("GET", "/rate") == {"success": True}
    assert calls == 2

    # 3. Invalid/negative Retry-After falls back to exponential backoff
    calls = 0

    def h_invalid(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                429,
                headers={"Retry-After": "invalid-chars"},
                json={"detail": "Slow down"},
            )
        return httpx.Response(200, json={"success": True})

    c3 = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(h_invalid))
    api3 = Maily(client=c3, max_retries=1, retry_backoff=0.0001)
    assert await api3._transport.request("GET", "/rate") == {"success": True}
    assert calls == 2

    # 4. Exhaustion raises RateLimitError
    calls = 0

    def h_exhaust(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(
            429, headers={"Retry-After": "0.001"}, json={"detail": "Limit exceeded"}
        )

    c4 = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(h_exhaust))
    api4 = Maily(client=c4, max_retries=2, retry_backoff=0.0001)
    with pytest.raises(RateLimitError) as exc_info:
        await api4._transport.request("GET", "/rate")
    assert exc_info.value.status_code == 429
    assert calls == 3


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "status,exc_type",
    [
        (400, ValidationError),
        (401, AuthenticationError),
        (403, ForbiddenError),
        (404, NotFoundError),
        (422, ValidationError),
    ],
)
async def test_transport_non_transient_errors_fail_immediately(status, exc_type):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(status, json={"detail": f"Error {status}"})

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client, max_retries=3)
    with pytest.raises(exc_type):
        await api._transport.request("GET", "/error")
    assert calls == 1


@pytest.mark.asyncio
async def test_transport_default_max_retries_zero():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("refused")

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client)
    assert api.max_retries == 0
    assert api.retry_backoff == 0.5
    api.max_retries = 3
    api.retry_backoff = 0.2
    assert api.max_retries == 3
    assert api.retry_backoff == 0.2
    api.max_retries = 0

    with pytest.raises(ApiError):
        await api._transport.request("GET", "/default")
    assert calls == 1


# --- 4. _extract_detail 422 Detail Parsing & Fallbacks ---


def test_extract_detail_fastapi_422_variations():
    # 1. Standard single field
    r1 = httpx.Response(
        422, json={"detail": [{"loc": ["body", "password"], "msg": "field required"}]}
    )
    assert _extract_detail(r1) == "password: field required"

    # 2. Multiple fields
    r2 = httpx.Response(
        422,
        json={
            "detail": [
                {"loc": ["body", "email"], "msg": "value is not a valid email"},
                {"loc": ["body", "age"], "msg": "ensure this value is greater than 0"},
            ]
        },
    )
    assert (
        _extract_detail(r2)
        == "email: value is not a valid email; age: ensure this value is greater than 0"
    )

    # 3. Deep nesting and integer index
    r3 = httpx.Response(
        422,
        json={
            "detail": [
                {
                    "loc": ["body", "users", 2, "profile", "bio"],
                    "msg": "cannot exceed 100 characters",
                }
            ]
        },
    )
    assert _extract_detail(r3) == "users.2.profile.bio: cannot exceed 100 characters"

    # 4. Root prefixes stripped (query, path, header, cookie, body)
    for prefix in ["body", "query", "path", "header", "cookie"]:
        r = httpx.Response(422, json={"detail": [{"loc": [prefix, "token"], "msg": "missing"}]})
        assert _extract_detail(r) == "token: missing"

    # 5. Non-stripped root prefix
    r5 = httpx.Response(422, json={"detail": [{"loc": ["custom", "field"], "msg": "invalid"}]})
    assert _extract_detail(r5) == "custom.field: invalid"


def test_extract_detail_edge_cases_and_fallbacks():
    # Missing loc
    r_no_loc = httpx.Response(422, json={"detail": [{"msg": "general error"}]})
    assert _extract_detail(r_no_loc) == "general error"

    # Missing msg
    r_no_msg = httpx.Response(422, json={"detail": [{"loc": ["body", "email"]}]})
    assert _extract_detail(r_no_msg) == "email"

    # Empty dict in detail list
    r_empty_item = httpx.Response(422, json={"detail": [{}]})
    assert _extract_detail(r_empty_item) == "{}"

    # Mixed list items (dict, string, int)
    r_mixed = httpx.Response(
        422,
        json={"detail": [{"loc": ["body", "k"], "msg": "bad"}, "plain string", 404]},
    )
    assert _extract_detail(r_mixed) == "k: bad; plain string; 404"

    # Empty detail list
    r_empty_list = httpx.Response(422, json={"detail": []})
    assert _extract_detail(r_empty_list) == "{'detail': []}"

    # String detail
    r_str = httpx.Response(400, json={"detail": "Bad username"})
    assert _extract_detail(r_str) == "Bad username"

    # Non-list, non-dict detail
    r_num = httpx.Response(400, json={"detail": 12345})
    assert _extract_detail(r_num) == "12345"

    # Non-JSON HTML/plain text
    r_html = httpx.Response(502, text="<html><body>Bad Gateway</body></html>")
    assert _extract_detail(r_html) == "<html><body>Bad Gateway</body></html>"

    # Non-JSON truncation (>300 chars)
    r_long = httpx.Response(500, text="A" * 400)
    assert _extract_detail(r_long) == "A" * 300
    assert len(_extract_detail(r_long)) == 300

    # Non-JSON empty body and whitespace body
    assert _extract_detail(httpx.Response(422, text="")) == "HTTP 422"
    assert _extract_detail(httpx.Response(404, text="   \n\t ")) == "HTTP 404"


# --- 5. ExtractedConfirmation Mapping Protocol & Dual Access ---


def test_extracted_confirmation_dual_access_and_mapping_protocol():
    conf = ExtractedConfirmation(
        message_id="msg-101",
        from_address="noreply@example.com",
        subject="Your Login Code",
        confirmation_code="491023",
        confirmation_link="https://example.com/activate?t=xyz",
    )

    # 1. Attribute access
    assert conf.message_id == "msg-101"
    assert conf.from_address == "noreply@example.com"
    assert conf.subject == "Your Login Code"
    assert conf.confirmation_code == "491023"
    assert conf.confirmation_link == "https://example.com/activate?t=xyz"

    # 2. Subscript mapping access
    assert conf["message_id"] == "msg-101"
    assert conf["from_address"] == "noreply@example.com"
    assert conf["subject"] == "Your Login Code"
    assert conf["confirmation_code"] == "491023"
    assert conf["confirmation_link"] == "https://example.com/activate?t=xyz"

    # 3. KeyError on nonexistent key
    with pytest.raises(KeyError):
        _ = conf["nonexistent_field"]

    # 4. .get() method
    assert conf.get("confirmation_code") == "491023"
    assert conf.get("nonexistent", "fallback") == "fallback"
    assert conf.get("missing") is None

    # 5. len, iter, membership
    assert len(conf) == 5
    field_names = list(conf)
    assert field_names == [
        "message_id",
        "from_address",
        "subject",
        "confirmation_link",
        "confirmation_code",
    ]
    assert "confirmation_code" in conf
    assert "token" not in conf

    # 6. keys, values, items
    assert list(conf.keys()) == field_names
    assert "msg-101" in list(conf.values())
    assert ("confirmation_code", "491023") in list(conf.items())

    # 7. dict conversion & **kwargs unpacking
    d = dict(conf)
    assert isinstance(d, dict)
    assert d["confirmation_code"] == "491023"

    def receiver(*, message_id: str, confirmation_code: str | None = None, **extra: Any) -> str:
        return f"{message_id}:{confirmation_code}"

    assert receiver(**conf) == "msg-101:491023"


# --- 6. Parameter Validation, Polling Scenarios & Async Context Managers ---


@pytest.mark.asyncio
async def test_wait_for_parameter_validations():
    client = httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=[])),
    )
    api = Maily(client=client)

    # 1. Negative timeout
    with pytest.raises(ValueError, match="timeout must be >= 0"):
        await api.messages.wait_for_confirmation_email(1, timeout=-1)

    with pytest.raises(ValueError, match="timeout must be >= 0"):
        await api.wait_for_code(1, timeout=-5)

    with pytest.raises(ValueError, match="timeout must be >= 0"):
        await api.wait_for_link(1, timeout=-0.1)

    # 2. Non-positive check_interval
    with pytest.raises(ValueError, match="check_interval must be > 0"):
        await api.messages.wait_for_confirmation_email(1, check_interval=0)

    with pytest.raises(ValueError, match="check_interval must be > 0"):
        await api.wait_for_code(1, check_interval=-1.0)

    with pytest.raises(ValueError, match="check_interval must be > 0"):
        await api.wait_for_link(1, check_interval=0)

    # 3. Invalid regular expression
    with pytest.raises(ValueError, match="Invalid regular expression digit_code_mask"):
        await api.messages.wait_for_confirmation_email(1, digit_code_mask="[invalid-regex(")


@pytest.mark.asyncio
async def test_wait_for_confirmation_email_polling_scenarios(
    caplog: pytest.LogCaptureFixture,
):
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        p = request.url.path
        if request.method == "GET" and p == "/v1/mailboxes/1/messages":
            calls += 1
            if calls == 1:
                # Message 1: wrong domain
                # Message 2: fails detail fetch
                return httpx.Response(
                    200,
                    json=[
                        {
                            "id": 1,
                            "message_api_id": "m_wrong_domain",
                            "subject": "Wrong",
                            "from_address": "User <user@other.com>",
                        },
                        {
                            "id": 2,
                            "message_api_id": "m_fail_detail",
                            "subject": "Fail",
                            "from_address": "test@service.com",
                        },
                    ],
                )
            if calls >= 2:
                # Message 3: no link, no code
                # Message 4: valid match
                return httpx.Response(
                    200,
                    json=[
                        {
                            "id": 3,
                            "message_api_id": "m_no_content",
                            "subject": "Empty",
                            "from_address": "test@service.com",
                        },
                        {
                            "id": 4,
                            "message_api_id": "m_valid",
                            "subject": "Activate",
                            "from_address": "test@service.com",
                        },
                    ],
                )
            return httpx.Response(200, json=[])

        if request.method == "GET" and p == "/v1/mailboxes/1/messages/m_fail_detail":
            return httpx.Response(500, text="Internal error")

        if request.method == "GET" and p == "/v1/mailboxes/1/messages/m_no_content":
            return httpx.Response(
                200,
                json={
                    "id": 3,
                    "message_api_id": "m_no_content",
                    "subject": "Empty",
                    "from_address": "test@service.com",
                    "text": "Hello, there is nothing here.",
                    "html": [],
                },
            )

        if request.method == "GET" and p == "/v1/mailboxes/1/messages/m_valid":
            return httpx.Response(
                200,
                json={
                    "id": 4,
                    "message_api_id": "m_valid",
                    "subject": "Activate",
                    "from_address": "test@service.com",
                    "text": "Your OTP is 789456 and link is https://service.com/activate?token=123",
                    "html": [],
                },
            )

        return httpx.Response(404)

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client)

    conf = await api.messages.wait_for_confirmation_email(
        1,
        sender_domain="service.com",
        digit_code_mask=r"OTP is (\d{6})",
        url_contain=["activate"],
        timeout=10.0,
        check_interval=0.001,
    )
    assert conf is not None
    assert conf.message_id == "m_valid"
    assert conf.confirmation_code == "789456"
    assert conf.confirmation_link == "https://service.com/activate?token=123"

    # Top-level facade method on Maily
    conf_facade = await api.wait_for_confirmation_email(
        1,
        sender_domain="service.com",
        digit_code_mask=r"OTP is (\d{6})",
        url_contain=["activate"],
        timeout=10.0,
        check_interval=0.001,
    )
    assert conf_facade is not None
    assert conf_facade.confirmation_code == "789456"

    # Timeout scenario returns None
    none_conf = await api.messages.wait_for_confirmation_email(
        1,
        sender_domain="never-seen.com",
        timeout=0.01,
        check_interval=0.001,
    )
    assert none_conf is None


@pytest.mark.asyncio
async def test_wait_for_link_timeout_and_iter_messages_timeout():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client)

    # wait_for_link timeout raises WaitTimeoutError
    with pytest.raises(WaitTimeoutError):
        await api.wait_for_link(1, timeout=0.01, check_interval=0.001)

    # iter_messages with timeout breaks loop
    collected = []
    async for msg in api.messages.iter_messages(1, timeout=0.01, poll_interval=0.002):
        collected.append(msg)
    assert collected == []


@pytest.mark.asyncio
async def test_async_context_manager_lifecycle():
    seen_closed = False

    class CustomTransport(httpx.AsyncBaseTransport):
        async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={"status": "ok"})

        async def aclose(self) -> None:
            nonlocal seen_closed
            seen_closed = True

    # 1. Owned client closed on exit
    async with Maily(base_url="http://test") as api:
        assert api._transport._owns_client is True

    # 2. External client not closed when _owns_client is False
    ext_client = httpx.AsyncClient(transport=CustomTransport())
    async with Maily(client=ext_client) as api:
        assert api._transport._owns_client is False
    assert seen_closed is False
    await ext_client.aclose()
    assert seen_closed is True

    # 3. _Transport context manager
    async with _Transport("http://test") as t:
        assert t is not None

    # 4. Exception propagation closes context
    with pytest.raises(RuntimeError, match="boom"):
        async with Maily(base_url="http://test"):
            raise RuntimeError("boom")


@pytest.mark.asyncio
async def test_check_client_version_scenarios(caplog: pytest.LogCaptureFixture):
    # 1. Matching version -> no warning
    c1 = httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"client_version": "0.3.0"})
        ),
    )
    api1 = Maily(client=c1)
    with caplog.at_level(logging.WARNING):
        v = await api1.check_client_version()
        assert v == "0.3.0"
        assert "update client" not in caplog.text

    # 2. Mismatched version -> logs warning
    caplog.clear()
    c2 = httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"client_version": "9.9.9"})
        ),
    )
    api2 = Maily(client=c2)
    with caplog.at_level(logging.WARNING):
        v2 = await api2.check_client_version()
        assert v2 == "9.9.9"

    # 3. Empty/missing config
    c3 = httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json={})),
    )
    api3 = Maily(client=c3)
    assert await api3.check_client_version() == ""


@pytest.mark.asyncio
async def test_admin_api_raw_dict_methods():
    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        m = request.method
        if m == "GET" and p == "/v1/admin/keys":
            return httpx.Response(200, json=[{"id": 10, "name": "k10"}])
        if m == "POST" and p == "/v1/admin/keys":
            return httpx.Response(201, json={"id": 11, "name": "k11", "secret": "sk-11"})
        if m == "GET" and p == "/v1/admin/keys/10":
            return httpx.Response(200, json={"id": 10, "name": "k10"})
        if m == "GET" and p == "/v1/admin/keys/me":
            return httpx.Response(200, json={"is_root": True})
        if m == "GET" and p == "/v1/admin/keys/10/secret":
            return httpx.Response(200, json={"secret": "sk-10-raw"})
        if m == "PATCH" and p == "/v1/admin/keys/10":
            return httpx.Response(200, json={"id": 10, "name": "k10-updated"})
        if m == "PUT" and p == "/v1/admin/keys/10/retention":
            return httpx.Response(200, json=[{"provider": "mail.tm", "ttl": 10}])
        if m == "POST" and p == "/v1/admin/keys/10/rotate":
            return httpx.Response(200, json={"id": 10, "secret": "sk-10-rotated"})
        if m == "DELETE" and p == "/v1/admin/keys/10":
            return httpx.Response(204)
        return httpx.Response(404)

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client)
    try:
        assert (await api.admin.keys()) == [{"id": 10, "name": "k10"}]
        created = await api.admin.key_create(
            name="k11",
            expires_at=None,
            scope={"providers": [], "parent_ids": [], "actions": []},
            retention=[],
        )
        assert created["id"] == 11
        assert (await api.admin.key_get(10))["id"] == 10
        assert (await api.admin.key_me())["is_root"] is True
        assert (await api.admin.key_secret(10))["secret"] == "sk-10-raw"
        updated = await api.admin.key_update(
            10,
            name="k10-updated",
            expires_at=None,
            scope={"providers": [], "parent_ids": [], "actions": []},
        )
        assert updated["name"] == "k10-updated"
        ret = await api.admin.key_retention_set(10, [{"provider": "mail.tm", "ttl": 10}])
        assert len(ret) == 1
        rot = await api.admin.key_rotate(10)
        assert rot["secret"] == "sk-10-rotated"
        await api.admin.key_delete(10)
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_mailboxes_list_params_and_wait_for_mark_seen():
    seen_params: dict[str, str] = {}
    marked_seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if request.method == "GET" and p == "/v1/mailboxes":
            seen_params.update(dict(request.url.params))
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "provider": "mail.tm",
                        "address": "test@mail.tm",
                        "is_active": False,
                    }
                ],
            )
        if request.method == "GET" and p == "/v1/mailboxes/1/messages":
            return httpx.Response(
                200,
                json=[
                    {
                        "id": 1,
                        "message_api_id": "m-seen",
                        "subject": "Seen test",
                        "from_address": "s@x.com",
                    }
                ],
            )
        if request.method == "POST" and p == "/v1/mailboxes/1/messages/m-seen/read":
            marked_seen.append("m-seen")
            return httpx.Response(
                200,
                json={
                    "id": 1,
                    "message_api_id": "m-seen",
                    "subject": "Seen test",
                    "from_address": "s@x.com",
                    "seen": True,
                },
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client)
    try:
        # Exercise all params: provider, active, q, limit, offset
        boxes = await api.mailboxes.list(
            provider="mail.tm", active=False, q="test", limit=5, offset=10
        )
        assert len(boxes) == 1
        assert seen_params["provider"] == "mail.tm"
        assert seen_params["active"] == "false"
        assert seen_params["q"] == "test"
        assert seen_params["limit"] == "5"
        assert seen_params["offset"] == "10"

        # Exercise wait_for with mark_seen=True
        msg = await api.messages.wait_for(1, timeout=10.0, interval=0.001, mark_seen=True)
        assert msg.message_api_id == "m-seen"
        assert marked_seen == ["m-seen"]
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_additional_edge_cases(monkeypatch: pytest.MonkeyPatch):
    # 1. _parse_retry_after branches
    assert _parse_retry_after(None, 0, 0.5) == 0.5
    assert _parse_retry_after("-5", 0, 0.5) == 0.5
    assert _parse_retry_after("10", 0, 0.5) == 10.0

    # 2. _extract_detail non-dict json body (e.g. list)
    resp_list = httpx.Response(400, json=["foo", "bar"])
    assert _extract_detail(resp_list) == "['foo', 'bar']"

    # 3. wait_for_confirmation_email empty string keyword in url_contain
    def handler(request: httpx.Request) -> httpx.Response:
        p = request.url.path
        if request.method == "GET" and p == "/v1/mailboxes/1/messages":
            return httpx.Response(200, json=[])
        if request.method == "GET" and p == "/v1/targets":
            return httpx.Response(200, json=[])
        if request.method == "POST" and p == "/v1/mailboxes":
            return httpx.Response(
                201,
                json={
                    "id": 99,
                    "provider": "mail.tm",
                    "address": "a@b.c",
                    "is_active": True,
                },
            )
        if request.method == "PUT" and p == "/v1/admin/gmail/creds":
            return httpx.Response(
                200,
                json={
                    "configured": True,
                    "source": "db",
                    "client_id": "c",
                    "redirect_uri": "https://r",
                },
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(base_url="http://test", transport=httpx.MockTransport(handler))
    api = Maily(client=client)
    try:
        # url_contain with empty string
        res = await api.messages.wait_for_confirmation_email(
            1, url_contain=["", "xyz"], timeout=0.001, check_interval=0.001
        )
        assert res is None

        # iter_messages with timeout expiring before poll
        iter_msgs = [
            m async for m in api.messages.iter_messages(1, timeout=0.001, poll_interval=0.05)
        ]
        assert iter_msgs == []

        # create_temp_mailbox when no domain targets found
        box1 = await api.create_temp_mailbox()
        assert box1.id == 99

        # create_temp_mailbox when provider given but no targets found
        box2 = await api.create_temp_mailbox(provider="unknown_p")
        assert box2.id == 99

        # admin.gmail_creds_save with redirect_uri
        creds = await api.admin.gmail_creds_save("cid", "sec", redirect_uri="https://r")
        assert creds.redirect_uri == "https://r"
    finally:
        await api.close()

    # 4. SyncMessagesAPI.iter_messages timeout break paths
    with SyncMaily(client=client) as sync_api:
        sync_msgs = list(sync_api.messages.iter_messages(1, timeout=0.001, poll_interval=0.05))
        assert sync_msgs == []

    # 5. SyncMaily init failure handling
    def broken_init(*args: Any, **kwargs: Any) -> None:
        raise ValueError("synthetic init crash")

    monkeypatch.setattr("maily.standalone_client.Maily.__init__", broken_init)
    with pytest.raises(ValueError, match="synthetic init crash"):
        SyncMaily()
