"""
High-performance async HTTP session.

Wraps aiohttp.ClientSession with:
  - TCPConnector: connection pool limits + DNS cache TTL
  - ClientTimeout: structured timeouts (total / connect / read)
  - HTTP status → typed exception mapping
  - Transparent proxy support
  - SSL toggle (mail.tm requires ssl=False)

Typical use::

    async with AsyncHTTPSession() as http:
        resp = await http.get("https://api.mail.tm/domains")
        data = await resp.json()
"""
from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector

from ..utils.exceptions import (
    MailAPIError,
    MailAuthError,
    MailConflictError,
    MailNotFoundError,
    MailRateLimitError,
    MailServerError,
    MailTimeoutError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Defaults — tuned for high-concurrency temp-mail use-cases
# ---------------------------------------------------------------------------
_DEFAULT_TOTAL_LIMIT: int = 100        # max open TCP connections
_DEFAULT_PER_HOST_LIMIT: int = 30      # max connections to a single host
_DEFAULT_TTL_DNS_CACHE: int = 300      # seconds to cache DNS answers
_DEFAULT_TIMEOUT = ClientTimeout(
    total=30,      # wall-clock cap per request
    connect=10,    # time to establish TCP + TLS handshake
    sock_read=20,  # time waiting for first byte after sending request
)


class AsyncHTTPSession:
    """
    Reusable, connection-pooled async HTTP session.

    The session owns its underlying ``aiohttp.ClientSession`` unless an
    external one is passed via *session*.  Always call ``close()`` or use
    this as an async context manager to release resources cleanly.
    """

    __slots__ = (
        "_session",
        "_ssl",
        "_proxy",
        "_owns_session",
        "_total_connections",
        "_per_host",
        "_ttl_dns_cache",
        "_timeout",
    )

    def __init__(
        self,
        *,
        session: ClientSession | None = None,
        proxy: str | None = None,
        ssl: bool = False,
        total_connections: int = _DEFAULT_TOTAL_LIMIT,
        per_host: int = _DEFAULT_PER_HOST_LIMIT,
        ttl_dns_cache: int = _DEFAULT_TTL_DNS_CACHE,
        timeout: ClientTimeout = _DEFAULT_TIMEOUT,
    ) -> None:
        self._ssl = ssl
        self._proxy = proxy
        self._total_connections = total_connections
        self._per_host = per_host
        self._ttl_dns_cache = ttl_dns_cache
        self._timeout = timeout

        if session is not None:
            self._session: ClientSession | None = session
            self._owns_session = False
        else:
            # Defer session creation to first use — TCPConnector requires a
            # running event loop, so we cannot create it in __init__.
            self._session = None
            self._owns_session = True

    def _get_session(self) -> ClientSession:
        """Return (or lazily create) the underlying aiohttp ClientSession."""
        if self._session is None:
            connector = TCPConnector(
                limit=self._total_connections,
                limit_per_host=self._per_host,
                ttl_dns_cache=self._ttl_dns_cache,
                enable_cleanup_closed=True,
            )
            self._session = ClientSession(
                connector=connector,
                timeout=self._timeout,
                headers={
                    "Accept": "application/ld+json",
                    "Content-Type": "application/json",
                },
            )
        return self._session

    # ------------------------------------------------------------------
    # Async context manager
    # ------------------------------------------------------------------

    async def __aenter__(self) -> "AsyncHTTPSession":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.close()

    async def close(self) -> None:
        """Release the session and its connector. Safe to call multiple times."""
        if self._owns_session and self._session is not None and not self._session.closed:
            await self._session.close()
            # Give SSL transports a moment to drain before the event loop moves on.
            # Prevents "Unclosed client session" ResourceWarnings.
            await asyncio.sleep(0.05)
            self._session = None

    # ------------------------------------------------------------------
    # HTTP verbs — all delegate to _request()
    # ------------------------------------------------------------------

    async def get(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self._request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self._request("POST", url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self._request("PUT", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self._request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> aiohttp.ClientResponse:
        return await self._request("DELETE", url, **kwargs)

    # ------------------------------------------------------------------
    # Core request + error mapping
    # ------------------------------------------------------------------

    async def _request(
        self,
        method: str,
        url: str,
        **kwargs: Any,
    ) -> aiohttp.ClientResponse:
        """
        Execute an HTTP request and map HTTP errors to typed exceptions.

        SSL and proxy defaults are injected unless overridden in kwargs.
        Network-level errors (timeouts, connection refused) are also caught
        and wrapped in typed exceptions.
        """
        kwargs.setdefault("ssl", self._ssl)
        if self._proxy:
            kwargs.setdefault("proxy", self._proxy)

        try:
            response = await self._get_session().request(method, url, **kwargs)
        except asyncio.TimeoutError as exc:
            raise MailTimeoutError(
                f"Request timed out: {method} {url}",
                status_code=None,
            ) from exc
        except aiohttp.ClientConnectionError as exc:
            raise MailAPIError(
                f"Connection error for {method} {url}: {exc}",
                status_code=None,
            ) from exc

        await self._raise_for_status(response, method, url)
        return response

    @staticmethod
    async def _raise_for_status(
        response: aiohttp.ClientResponse,
        method: str,
        url: str,
    ) -> None:
        """Map HTTP 4xx/5xx responses to typed exceptions."""
        if response.status < 400:
            return

        try:
            body = await response.json(content_type=None)
            if not isinstance(body, dict):
                body = {"detail": str(body)}
        except Exception:
            body = {"detail": await response.text()}

        detail: str = (
            body.get("detail")
            or body.get("message")
            or body.get("hydra:description")
            or f"HTTP {response.status}"
        )
        code = response.status

        logger.debug("HTTP %d %s %s — %s", code, method, url, detail)

        if code in (401, 403):
            raise MailAuthError(detail, status_code=code, response_data=body)
        if code == 404:
            raise MailNotFoundError(detail, status_code=code, response_data=body)
        if code == 429:
            retry_after: float | None = None
            if raw_ra := response.headers.get("Retry-After"):
                try:
                    retry_after = float(raw_ra)
                except ValueError:
                    pass
            raise MailRateLimitError(
                detail, retry_after=retry_after, status_code=code, response_data=body
            )
        if code in (409, 422):
            raise MailConflictError(detail, status_code=code, response_data=body)
        if code >= 500:
            raise MailServerError(detail, status_code=code, response_data=body)

        raise MailAPIError(detail, status_code=code, response_data=body)
