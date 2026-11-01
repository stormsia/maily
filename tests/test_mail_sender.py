"""Unit tests for autonomous test email sender (test_mail_sender)."""

from __future__ import annotations

import httpx
import pytest
from test_mail_sender.exceptions import (
    AllProvidersFailedError,
    FallbackProviderError,
    InvalidEmailError,
    PrimaryProviderError,
)
from test_mail_sender.fallback import XeraMailProvider
from test_mail_sender.models import AttemptInfo, EmailSendResult
from test_mail_sender.primary import WeSendTestMailProvider
from test_mail_sender.sender import TestEmailSender


class MockTransport(httpx.AsyncBaseTransport):
    """Simple mock transport for httpx responses."""

    def __init__(self, handler) -> None:
        self.handler = handler

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        return await self.handler(request)


@pytest.mark.asyncio
async def test_wesendtestmail_success() -> None:
    csrf_html = '<html><head><meta name="csrf-token" content="mock-csrf-tok-123"></head><body></body></html>'

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, text=csrf_html)
        if request.url.path == "/send-mail":
            assert request.headers.get("x-csrf-token") == "mock-csrf-tok-123"
            return httpx.Response(200, json={"success": True, "message": "Email sent"})
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=MockTransport(mock_handler))
    provider = WeSendTestMailProvider(client=client)

    result = await provider.send("test@example.com")
    assert result.success is True
    assert result.provider == "wesendtestmail"
    assert result.fallback_used is False
    assert result.detail == "Email sent"
    assert len(result.attempts) == 1
    assert result.attempts[0].success is True


@pytest.mark.asyncio
async def test_wesendtestmail_retry_on_csrf_419() -> None:
    call_count = {"send": 0, "get": 0}

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            call_count["get"] += 1
            tok = f"csrf-token-{call_count['get']}"
            return httpx.Response(
                200,
                text=f'<input type="hidden" name="_token" value="{tok}">',
            )
        if request.url.path == "/send-mail":
            call_count["send"] += 1
            if call_count["send"] == 1:
                return httpx.Response(419, text="CSRF token mismatch")
            return httpx.Response(
                200, json={"success": True, "message": "Email sent after refresh"}
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=MockTransport(mock_handler))
    provider = WeSendTestMailProvider(client=client)

    result = await provider.send("test@example.com")
    assert result.success is True
    assert call_count["send"] == 2
    assert call_count["get"] == 2
    assert result.detail == "Email sent after refresh"


@pytest.mark.asyncio
async def test_wesendtestmail_validation_error() -> None:
    csrf_html = '<meta name="csrf-token" content="mock-tok">'

    async def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, text=csrf_html)
        if request.url.path == "/send-mail":
            return httpx.Response(
                422,
                json={"errors": {"email": ["The email field must be a valid email address."]}},
            )
        return httpx.Response(404)

    client = httpx.AsyncClient(transport=MockTransport(mock_handler))
    provider = WeSendTestMailProvider(client=client)

    with pytest.raises(PrimaryProviderError) as exc_info:
        await provider.send("bad-email@example.com")
    assert "The email field must be a valid email address" in str(exc_info.value)
    assert exc_info.value.status_code == 422


@pytest.mark.asyncio
async def test_xeramail_success() -> None:
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/send-test-email"
        assert b'"to":"test@example.com"' in request.content
        return httpx.Response(200, json={"success": True, "messageId": "<msg-12345@xeramail.com>"})

    client = httpx.AsyncClient(transport=MockTransport(mock_handler))
    provider = XeraMailProvider(client=client)

    result = await provider.send("test@example.com")
    assert result.success is True
    assert result.provider == "xeramail"
    assert result.fallback_used is True
    assert result.message_id == "<msg-12345@xeramail.com>"


@pytest.mark.asyncio
async def test_xeramail_failure() -> None:
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"success": False, "error": "Internal SMTP down"})

    client = httpx.AsyncClient(transport=MockTransport(mock_handler))
    provider = XeraMailProvider(client=client)

    with pytest.raises(FallbackProviderError) as exc_info:
        await provider.send("test@example.com")
    assert "Internal SMTP down" in str(exc_info.value)


@pytest.mark.asyncio
async def test_sender_auto_failover_to_fallback() -> None:
    # Primary fails with 500 Server Error
    async def primary_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, text='<meta name="csrf-token" content="tok">')
        return httpx.Response(500, text="Internal Server Error")

    # Fallback succeeds
    async def fallback_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": True, "messageId": "<fallback-id>"})

    primary_client = httpx.AsyncClient(transport=MockTransport(primary_handler))
    fallback_client = httpx.AsyncClient(transport=MockTransport(fallback_handler))

    primary = WeSendTestMailProvider(client=primary_client)
    fallback = XeraMailProvider(client=fallback_client)

    async with TestEmailSender(primary_provider=primary, fallback_provider=fallback) as sender:
        res = await sender.send("recipient@example.com")
        assert res.success is True
        assert res.provider == "xeramail"
        assert res.fallback_used is True
        assert res.message_id == "<fallback-id>"
        # Should contain diagnostic history of both attempts
        assert len(res.attempts) == 2
        assert res.attempts[0].provider == "wesendtestmail"
        assert res.attempts[0].success is False
        assert res.attempts[1].provider == "xeramail"
        assert res.attempts[1].success is True


@pytest.mark.asyncio
async def test_sender_all_providers_fail() -> None:
    # Primary fails
    async def primary_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="Service Unavailable")

    # Fallback fails
    async def fallback_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"success": False, "error": "SMTP quota reached"})

    primary = WeSendTestMailProvider(
        client=httpx.AsyncClient(transport=MockTransport(primary_handler))
    )
    fallback = XeraMailProvider(client=httpx.AsyncClient(transport=MockTransport(fallback_handler)))

    async with TestEmailSender(primary_provider=primary, fallback_provider=fallback) as sender:
        with pytest.raises(AllProvidersFailedError) as exc_info:
            await sender.send("target@example.com")

        err = exc_info.value
        assert err.email == "target@example.com"
        assert len(err.attempts) == 2
        assert err.attempts[0].provider == "wesendtestmail"
        assert err.attempts[1].provider == "xeramail"


@pytest.mark.asyncio
async def test_sender_invalid_email() -> None:
    async with TestEmailSender() as sender:
        with pytest.raises(InvalidEmailError):
            await sender.send("not-an-email")


@pytest.mark.asyncio
async def test_sender_batch_send_all() -> None:
    async def mock_handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/":
            return httpx.Response(200, text='<meta name="csrf-token" content="tok">')
        return httpx.Response(200, json={"success": True, "message": "Batch ok"})

    client = httpx.AsyncClient(transport=MockTransport(mock_handler))
    primary = WeSendTestMailProvider(client=client)

    async with TestEmailSender(primary_provider=primary) as sender:
        emails = ["a@x.com", "b@x.com", "c@x.com", "invalid-one"]
        results = await sender.send_all(emails, concurrency=2)
        assert len(results) == 4
        assert isinstance(results[0], EmailSendResult)
        assert results[0].success is True
        assert isinstance(results[3], InvalidEmailError)


@pytest.mark.asyncio
async def test_models_to_dict() -> None:
    attempt = AttemptInfo(
        provider="wesendtestmail", success=True, status_code=200, duration_ms=12.5
    )
    result = EmailSendResult(
        email="test@example.com",
        success=True,
        provider="wesendtestmail",
        attempts=[attempt],
    )
    d = result.to_dict()
    assert d["email"] == "test@example.com"
    assert d["attempts"][0]["provider"] == "wesendtestmail"
