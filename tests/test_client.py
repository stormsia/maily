from __future__ import annotations

import json

import httpx
import pytest

from mailtmapi.client import ApiError, MailTMAPI

BASE = "http://test"


def _api(handler) -> MailTMAPI:
    return MailTMAPI(
        base_url=BASE,
        api_key="secret",
        client=httpx.AsyncClient(base_url=BASE, transport=httpx.MockTransport(handler)),
    )


def _router(routes: dict[tuple[str, str], httpx.Response]) -> httpx.Response:
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
                        {"id": "g1", "kind": "parent", "provider": "gmail", "label": "me@gmail.com"},
                        {"id": "d1", "kind": "domain", "provider": "mail.tm", "label": "mail.tm"},
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
                json={"id": 1, "provider": "mail.tm", "address": "x@mail.tm", "is_active": True},
            )
        if request.method == "GET" and path == "/v1/mailboxes/by-address/x@mail.tm":
            return httpx.Response(
                200,
                json={"id": 1, "provider": "mail.tm", "address": "x@mail.tm", "is_active": True},
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
            1, timeout=5, interval=0.01, predicate=lambda m: m.subject == "Hi"
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
                200, json={"auth_url": "https://accounts.google.com/o/oauth2/…", "state": "s1"}
            )
        if request.method == "POST" and path == "/v1/gmail/accounts/import":
            body = json.loads(request.content)
            assert body.get("refresh_token") == "rt"
            return httpx.Response(
                201,
                json={"id": 2, "email": "me@gmail.com", "status": "active", "send_as": []},
            )
        if request.method == "GET" and path == "/v1/gmail/accounts":
            return httpx.Response(200, json=[])
        if request.method == "POST" and path == "/v1/gmail/accounts/2/sync":
            return httpx.Response(
                200,
                json={"id": 2, "email": "me@gmail.com", "status": "active", "send_as": ["a@b.c"]},
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
                json={"provider": "mail.tm", "mailbox_ttl_hours": 24, "message_ttl_hours": None},
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
            return httpx.Response(200, json={"enabled": False, "interval_seconds": 60, "providers": []})
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
            return httpx.Response(200, json={"configured": True, "source": "db", "client_id": "new"})
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
    api = _api(_router({("GET", "/v1/mailboxes/1"): httpx.Response(404, json={"detail": "no box"})}))
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
        _router({("GET", "/v1/mailboxes/1"): httpx.Response(500, text="internal oops", headers={"Content-Type": "text/plain"})})
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
