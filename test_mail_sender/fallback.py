"""Fallback email sending provider: https://xeramail.com"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

import httpx

from .exceptions import FallbackProviderError
from .models import AttemptInfo, EmailSendResult

logger = logging.getLogger("test_mail_sender.xeramail")

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0"
SEND_URL = "https://xeramail.com/api/send-test-email"
REFERER_URL = "https://xeramail.com/send-test-email"
ORIGIN_URL = "https://xeramail.com"


class XeraMailProvider:
    """Fallback provider using https://xeramail.com.

    Sends direct JSON payload `{"to": "<email>"}` to the API endpoint.
    Optionally accepts a Cloudflare `cf_clearance` cookie token if needed in
    strict environments.
    """

    provider_name = "xeramail"

    def __init__(
        self,
        *,
        timeout: float = 20.0,
        proxy: str | None = None,
        client: httpx.AsyncClient | None = None,
        cf_clearance: str | None = None,
    ) -> None:
        self.timeout = timeout
        self.proxy = proxy
        self.cf_clearance = cf_clearance or os.environ.get("XERAMAIL_CF_CLEARANCE")
        self._owned_client = client is None

        cookies: dict[str, str] = {}
        if self.cf_clearance:
            cookies["cf_clearance"] = self.cf_clearance

        self._client = client or httpx.AsyncClient(
            proxy=proxy or None,
            timeout=httpx.Timeout(timeout, connect=min(10.0, timeout)),
            follow_redirects=True,
            cookies=cookies,
            headers={
                "User-Agent": DEFAULT_UA,
                "Accept": "application/json, text/plain, */*",
                "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
                "Referer": REFERER_URL,
                "Origin": ORIGIN_URL,
            },
        )

    async def __aenter__(self) -> XeraMailProvider:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client if created internally."""
        if self._owned_client:
            await self._client.aclose()

    async def send(self, email: str) -> EmailSendResult:
        """Send a test email via xeramail API."""
        start_time = time.monotonic()
        payload = {"to": email}

        try:
            resp = await self._client.post(SEND_URL, json=payload)
        except httpx.TimeoutException as exc:
            duration_ms = (time.monotonic() - start_time) * 1000.0
            attempt = AttemptInfo(
                provider=self.provider_name,
                success=False,
                error=f"Timeout: {exc}",
                duration_ms=duration_ms,
            )
            raise FallbackProviderError(f"Request to {SEND_URL} timed out") from exc
        except httpx.RequestError as exc:
            duration_ms = (time.monotonic() - start_time) * 1000.0
            attempt = AttemptInfo(
                provider=self.provider_name,
                success=False,
                error=f"Network error: {exc}",
                duration_ms=duration_ms,
            )
            raise FallbackProviderError(
                f"Network error communicating with {SEND_URL}: {exc}"
            ) from exc

        duration_ms = (time.monotonic() - start_time) * 1000.0

        if resp.status_code == 403 and "cloudflare" in resp.text.lower():
            attempt = AttemptInfo(
                provider=self.provider_name,
                success=False,
                status_code=403,
                error="Cloudflare challenge encountered. Set XERAMAIL_CF_CLEARANCE if required.",
                duration_ms=duration_ms,
            )
            raise FallbackProviderError(
                "Cloudflare clearance challenge encountered",
                status_code=403,
                response_text=resp.text[:300],
            )

        try:
            data = resp.json()
        except Exception:
            data = {}

        if resp.status_code == 200 and data.get("success") is True:
            msg_id = data.get("messageId")
            attempt = AttemptInfo(
                provider=self.provider_name,
                success=True,
                status_code=200,
                duration_ms=duration_ms,
            )
            return EmailSendResult(
                email=email,
                success=True,
                provider=self.provider_name,
                fallback_used=True,
                message_id=str(msg_id) if msg_id else None,
                detail=f"Test email sent via {self.provider_name} (messageId: {msg_id})",
                duration_ms=duration_ms,
                attempts=[attempt],
            )

        err_msg = data.get("error") or data.get("message") or f"HTTP {resp.status_code}"
        attempt = AttemptInfo(
            provider=self.provider_name,
            success=False,
            status_code=resp.status_code,
            error=str(err_msg),
            duration_ms=duration_ms,
        )

        raise FallbackProviderError(
            str(err_msg),
            status_code=resp.status_code,
            response_text=resp.text[:300],
        )
