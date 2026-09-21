from __future__ import annotations

import httpx
import pytest

from mailtmapi.client import ApiError, MailTMAPI
from mailtmapi.exceptions import MailAPIError


def _client(handler) -> httpx.AsyncClient:
    return httpx.AsyncClient(
        base_url="http://test",
        transport=httpx.MockTransport(handler),
    )


@pytest.mark.asyncio
async def test_wait_for_message_polls_until_hit():
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        assert request.url.path == "/v1/mailboxes/1/messages"
        if calls["n"] < 3:
            return httpx.Response(200, json=[])
        return httpx.Response(
            200,
            json=[{"id": 9, "message_api_id": "9", "subject": "Code", "from_address": "a@b.c"}],
        )

    client = _client(handler)
    api = MailTMAPI(client=client)
    try:
        msg = await api.wait_for_message(1, timeout=5, interval=0.01)
        assert msg.id == 9
        assert msg.subject == "Code"
        assert calls["n"] == 3
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_wait_for_message_times_out():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[])

    client = _client(handler)
    api = MailTMAPI(client=client)
    try:
        with pytest.raises(TimeoutError):
            await api.wait_for_message(1, timeout=0.05, interval=0.01)
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_error_mapping_raises_api_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "mailbox 404 not found"})

    client = _client(handler)
    api = MailTMAPI(client=client)
    try:
        with pytest.raises(ApiError) as exc:
            await api.mailbox(404)
        assert exc.value.status_code == 404
        assert "mailbox 404 not found" in str(exc.value)
    finally:
        await api.close()


@pytest.mark.asyncio
async def test_refresh_domain_cache_posts_and_parses():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == "/v1/admin/domain-cache/run"
        return httpx.Response(
            200,
            json={"refreshed": ["mail.tm"], "failed": []},
        )

    client = _client(handler)
    api = MailTMAPI(client=client)
    try:
        result = await api.refresh_domain_cache()
        assert result.refreshed == ["mail.tm"]
        assert result.failed == []
    finally:
        await api.close()


def test_sdk_shim_still_importable_with_deprecation_warning():
    import warnings

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        from mailtmapi.sdk import MailTMAPI as SdkMailTMAPI

        assert SdkMailTMAPI is MailTMAPI
        assert any(issubclass(w.category, DeprecationWarning) for w in caught)


def test_client_error_is_distinct_from_server_error():
    assert MailAPIError is not ApiError
    assert issubclass(ApiError, Exception)
