"""Primary email sending provider: https://www.wesendtestmail.com"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Any

import httpx

from .exceptions import PrimaryProviderError
from .models import AttemptInfo, EmailSendResult

logger = logging.getLogger("test_mail_sender.wesendtestmail")

DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0"
PAGE_URL = "https://www.wesendtestmail.com/"
SEND_URL = "https://www.wesendtestmail.com/send-mail"

# Matches <meta name="csrf-token" content="..."> or <input type="hidden" name="_token" value="...">
CSRF_META_PATTERN = re.compile(
    r'<meta\s+name=["\']csrf-token["\']\s+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
CSRF_INPUT_PATTERN = re.compile(
    r'name=["\']_token["\']\s+value=["\']([^"\']+)["\']',
    re.IGNORECASE,
)


class WeSendTestMailProvider:
    """Primary provider using https://www.wesendtestmail.com.

    Handles automatic CSRF token extraction from the landing page, retains session
    cookies in the HTTP client cookie jar, and automatically refreshes tokens upon
    HTTP 419 (CSRF mismatch) responses.
    """

    provider_name = "wesendtestmail"

    def __init__(
        self,
        *,
        timeout: float = 20.0,
        proxy: str | None = None,
        client: httpx.AsyncClient | None = None,
        token_ttl_seconds: float = 3600.0,
    ) -> None:
        self.timeout = timeout
        self.proxy = proxy
        self.token_ttl_seconds = token_ttl_seconds
        self._owned_client = client is None
        self._client = client or httpx.AsyncClient(
            proxy=proxy or None,
            timeout=httpx.Timeout(timeout, connect=min(10.0, timeout)),
            follow_redirects=True,
            headers={
                "User-Agent": DEFAULT_UA,
                "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
            },
        )
        self._csrf_token: str | None = None
        self._token_fetched_at: float = 0.0
        self._token_lock = asyncio.Lock()

    async def __aenter__(self) -> WeSendTestMailProvider:
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the underlying HTTP client if created internally."""
        if self._owned_client:
            await self._client.aclose()

    async def _fetch_csrf_token(self, *, force_refresh: bool = False) -> str:
        """Fetch and cache CSRF token from the service landing page."""
        async with self._token_lock:
            now = time.monotonic()
            if (
                not force_refresh
                and self._csrf_token is not None
                and (now - self._token_fetched_at) < self.token_ttl_seconds
            ):
                return self._csrf_token

            logger.debug(f"Fetching fresh CSRF token from {PAGE_URL}")
            try:
                resp = await self._client.get(
                    PAGE_URL,
                    headers={
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    },
                )
            except httpx.TimeoutException as exc:
                raise PrimaryProviderError(
                    f"Timed out fetching landing page CSRF token from {PAGE_URL}"
                ) from exc
            except httpx.RequestError as exc:
                raise PrimaryProviderError(
                    f"Network error requesting landing page {PAGE_URL}: {exc}"
                ) from exc

            if resp.status_code != 200:
                raise PrimaryProviderError(
                    f"Landing page returned HTTP {resp.status_code}",
                    status_code=resp.status_code,
                    response_text=resp.text[:300],
                )

            # Extract CSRF token from meta tag or hidden input
            match = CSRF_META_PATTERN.search(resp.text) or CSRF_INPUT_PATTERN.search(resp.text)
            if not match:
                raise PrimaryProviderError(
                    "CSRF token could not be found in landing page HTML",
                    response_text=resp.text[:500],
                )

            token = match.group(1).strip()
            self._csrf_token = token
            self._token_fetched_at = now
            logger.debug(f"Obtained CSRF token: {token[:8]}...")
            return token

    async def send(self, email: str) -> EmailSendResult:
        """Send a test email to the specified target address.

        Automatically performs token refresh and retries if session/CSRF expires.
        """
        start_time = time.monotonic()
        attempts: list[AttemptInfo] = []

        for attempt_index in range(2):
            attempt_start = time.monotonic()
            token = await self._fetch_csrf_token(force_refresh=(attempt_index > 0))

            headers = {
                "Accept": "application/json",
                "Referer": PAGE_URL,
                "Origin": "https://www.wesendtestmail.com",
                "X-CSRF-TOKEN": token,
                "X-Requested-With": "XMLHttpRequest",
            }

            # Send as multipart/form-data with _token and email
            files = {
                "_token": (None, token),
                "email": (None, email),
            }

            try:
                resp = await self._client.post(SEND_URL, headers=headers, files=files)
            except httpx.TimeoutException as exc:
                duration_ms = (time.monotonic() - attempt_start) * 1000.0
                attempts.append(
                    AttemptInfo(
                        provider=self.provider_name,
                        success=False,
                        error=f"Timeout: {exc}",
                        duration_ms=duration_ms,
                    )
                )
                raise PrimaryProviderError(f"Request to {SEND_URL} timed out") from exc
            except httpx.RequestError as exc:
                duration_ms = (time.monotonic() - attempt_start) * 1000.0
                attempts.append(
                    AttemptInfo(
                        provider=self.provider_name,
                        success=False,
                        error=f"Network error: {exc}",
                        duration_ms=duration_ms,
                    )
                )
                raise PrimaryProviderError(
                    f"Network error communicating with {SEND_URL}: {exc}"
                ) from exc

            duration_ms = (time.monotonic() - attempt_start) * 1000.0

            # Laravel CSRF mismatch / session expiration is HTTP 419
            if resp.status_code == 419 and attempt_index == 0:
                logger.warning(
                    "Received HTTP 419 (CSRF mismatch) from wesendtestmail, refreshing token..."
                )
                attempts.append(
                    AttemptInfo(
                        provider=self.provider_name,
                        success=False,
                        status_code=419,
                        error="CSRF token expired (HTTP 419)",
                        duration_ms=duration_ms,
                    )
                )
                self._csrf_token = None
                continue

            try:
                data = resp.json()
            except Exception:
                data = {}

            if resp.status_code == 200 and data.get("success") is True:
                total_duration_ms = (time.monotonic() - start_time) * 1000.0
                msg = str(data.get("message") or "Test email sent successfully")
                attempts.append(
                    AttemptInfo(
                        provider=self.provider_name,
                        success=True,
                        status_code=200,
                        duration_ms=duration_ms,
                    )
                )
                return EmailSendResult(
                    email=email,
                    success=True,
                    provider=self.provider_name,
                    fallback_used=False,
                    detail=msg,
                    duration_ms=total_duration_ms,
                    attempts=attempts,
                )

            # Failure handling
            err_msg = data.get("message") or f"HTTP {resp.status_code}"
            if resp.status_code == 422 and "errors" in data and isinstance(data["errors"], dict):
                first_err = next(iter(data["errors"].values()), None)
                if first_err and isinstance(first_err, list) and first_err:
                    err_msg = str(first_err[0])

            attempts.append(
                AttemptInfo(
                    provider=self.provider_name,
                    success=False,
                    status_code=resp.status_code,
                    error=err_msg,
                    duration_ms=duration_ms,
                )
            )

            raise PrimaryProviderError(
                err_msg,
                status_code=resp.status_code,
                response_text=resp.text[:300],
            )

        raise PrimaryProviderError("Failed after token retry")
