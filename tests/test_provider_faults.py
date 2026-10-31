"""Chaos and fault-injection tests for mail providers."""

import httpx
import pytest

from mailtmapi.exceptions import (
    MailAuthError,
    MailRateLimitError,
    MailTimeoutError,
)
from mailtmapi.http import HttpClient
from mailtmapi.providers.noopmail_org.service import NoopMail
from mailtmapi.providers.tempmail_plus.service import TempMailPlus


@pytest.mark.asyncio
async def test_tempmail_plus_cloudflare_challenge_handling():
    """Verify that Cloudflare HTML challenge pages raise MailAuthError (403)."""
    html_challenge = (
        "<!DOCTYPE html><html><head><title>Just a moment...</title></head>"
        "<body>Please enable JavaScript and Cookies to continue.</body></html>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text=html_challenge)

    transport = httpx.MockTransport(handler)
    http_client = HttpClient()
    http_client._client = httpx.AsyncClient(transport=transport)
    try:
        provider = TempMailPlus(http=http_client)
        with pytest.raises(MailAuthError) as exc_info:
            await provider.list_targets(fresh=True)
        assert exc_info.value.status_code == 403
    finally:
        await http_client.close()


@pytest.mark.asyncio
async def test_tempmail_plus_rate_limiting_handling():
    """Verify HTTP 429 Too Many Requests response handling."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "Too Many Requests"}, headers={"Retry-After": "60"})

    transport = httpx.MockTransport(handler)
    http_client = HttpClient()
    http_client._client = httpx.AsyncClient(transport=transport)
    try:
        provider = TempMailPlus(http=http_client)
        with pytest.raises(MailRateLimitError) as exc_info:
            await provider.list_targets(fresh=True)
        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60.0
    finally:
        await http_client.close()


@pytest.mark.asyncio
async def test_noopmail_network_timeout_handling():
    """Verify network connection and read timeouts map to MailTimeoutError."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("Read timed out from upstream provider")

    transport = httpx.MockTransport(handler)
    http_client = HttpClient()
    http_client._client = httpx.AsyncClient(transport=transport)
    try:
        provider = NoopMail(http=http_client)
        with pytest.raises(MailTimeoutError):
            await provider.list_targets(fresh=True)
    finally:
        await http_client.close()
