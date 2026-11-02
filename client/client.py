# -=- THIS FILE IS GENERATED from src/maily/standalone_client.py -=-
# Do not edit by hand; edit the canonical file and run:
#   python scripts/build_client.py
"""maily standalone client — CANONICAL single-file implementation.

Single canonical source of truth for the client. Two ways to use this code:

    1. Inside the server package — via the thin proxy `maily.client`
       (this module is imported from there).
    2. Outside — the `client/client.py` file in the repo root, which
       is generated from this module via `scripts/build_client.py`
       (adds only the 'generated' banner). Do not edit `client/client.py`
       by hand — edit here and regenerate; parity is enforced by
       `tests/test_client_standalone.py::test_standalone_mirror_is_current`.

Self-contained: does not pull in server dependencies (FastAPI, SQLAlchemy,
uvicorn, etc.), requires only httpx, loguru, and pydantic.

    pip install "maily-client @ git+https://github.com/stormsia/maily.git#subdirectory=client"
    # or copy the file into your project:
    #   curl -O https://raw.githubusercontent.com/stormsia/maily/main/client/client.py

Self-update: the client can check the version on git and update itself from
    the repo's client/client.py:

        maily-client check           # check if a new version is on git
        maily-client update          # download and install the new version

    (or `python client.py check/update` if running locally).

    From code:

        import client
        from client import Maily, self_update, check_update

        self_update()          # async-free, updates the client file on disk
        up = check_update()    # (current, remote) if an update is available, else None
"""

from __future__ import annotations

import asyncio
import builtins
import os
import re
import sys
import threading
import time
from collections.abc import AsyncIterator, Callable, Iterator, Mapping
from contextlib import suppress
from typing import Any
from urllib.parse import quote

import httpx
from loguru import logger
from pydantic import BaseModel, ConfigDict, Field

__version__ = "0.3.0"

# Where the client fetches itself for self-updates (override with env var).
CLIENT_SOURCE = os.environ.get(
    "MAILY_CLIENT_SOURCE",
    "https://raw.githubusercontent.com/stormsia/maily/main/client/client.py",
)

__all__ = [
    # Client and sections
    "Maily",
    "SyncMaily",
    "SyncHealthAPI",
    "SyncConfigAPI",
    "SyncProvidersAPI",
    "SyncMailboxesAPI",
    "SyncMessagesAPI",
    "SyncGmailAPI",
    "SyncAdminAPI",
    "SyncKeysAPI",
    "HealthAPI",
    "ConfigAPI",
    "ProvidersAPI",
    "MailboxesAPI",
    "MessagesAPI",
    "GmailAPI",
    "AdminAPI",
    "KeysAPI",
    # Errors
    "ClientError",
    "WaitTimeoutError",
    "ApiError",
    "AuthenticationError",
    "ForbiddenError",
    "NotFoundError",
    "ValidationError",
    "RateLimitError",
    "UpstreamProviderError",
    # Data models
    "HealthOut",
    "Provider",
    "ProviderOut",
    "ProviderCapabilities",
    "Target",
    "TargetOut",
    "Mailbox",
    "MailboxOut",
    "MessageSummary",
    "MessageOut",
    "MessageDetail",
    "MessageDetailOut",
    "MessageSource",
    "SourceOut",
    "GmailAccount",
    "GmailAccountOut",
    "OAuthStart",
    "OAuthStartOut",
    "GmailCreds",
    "GmailCredsOut",
    "Retention",
    "RetentionOut",
    "SweepResult",
    "DomainCacheProvider",
    "DomainCacheProviderOut",
    "DomainCache",
    "DomainCacheOut",
    "DomainCacheRun",
    "ApiKeyOut",
    "ApiKeyCreatedOut",
    "ApiKeyMeOut",
    "KeyScopeOut",
    "KeyRetentionOut",
    "ExtractedConfirmation",
    # Update utilities
    "check_update",
    "self_update",
]


# --------------------------------------------------------------------------- #
# Response models (self-contained — do not depend on maily.schemas)
# --------------------------------------------------------------------------- #
class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")


class HealthOut(_Base):
    status: str = ""


class ProviderCapabilities(_Base):
    can_choose_username: bool = True
    can_choose_domain: bool = True
    can_set_password: bool = False
    supports_delete_mailbox: bool = True
    supports_delete_message: bool = True
    supports_mark_read: bool = False
    supports_source: bool = True
    supports_attachments: bool = True


class ProviderOut(_Base):
    slug: str
    kind: str
    capabilities: ProviderCapabilities | None = None


class TargetOut(_Base):
    id: str
    kind: str
    provider: str
    label: str


class MailboxOut(_Base):
    id: int
    provider: str
    address: str
    parent_id: int | None = None
    is_active: bool
    created_at: Any = None
    parent_status: str | None = None


class MessageOut(_Base):
    id: int
    message_api_id: str
    subject: str = ""
    from_address: str = ""
    from_name: str = ""
    seen: bool = False
    has_attachments: bool = False
    size: int = 0
    received_at: Any = None


class MessageDetailOut(MessageOut):
    text: str = ""
    html: list[str] = []


class SourceOut(_Base):
    id: str
    data: str
    download_url: str = ""


class GmailAccountOut(_Base):
    id: int
    email: str
    status: str
    send_as: list[str] = []


class OAuthStartOut(_Base):
    auth_url: str
    state: str


class GmailCredsOut(_Base):
    configured: bool
    source: str
    client_id: str | None = None
    redirect_uri: str = ""


class RetentionOut(_Base):
    provider: str
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class SweepResult(_Base):
    mailboxes_deleted: int = 0
    messages_deleted: int = 0


class DomainCacheProviderOut(_Base):
    provider: str
    kind: str = "domain"
    domains_count: int = 0
    updated_at: Any = None
    error: str | None = None


class DomainCacheOut(_Base):
    enabled: bool = True
    interval_seconds: int = 1800
    providers: list[DomainCacheProviderOut] = []


class DomainCacheRun(_Base):
    refreshed: list[str] = []
    failed: list[str] = []


class KeyScopeOut(_Base):
    providers: list[str] = Field(default_factory=list)
    parent_ids: list[int] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class KeyRetentionOut(_Base):
    provider: str
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class ApiKeyOut(_Base):
    id: int
    name: str
    prefix: str
    scope: KeyScopeOut = Field(default_factory=KeyScopeOut)
    expires_at: Any = None
    created_at: Any = None
    updated_at: Any = None
    key_retention: list[KeyRetentionOut] = Field(default_factory=list)


class ApiKeyCreatedOut(ApiKeyOut):
    secret: str


class ApiKeyMeOut(_Base):
    is_root: bool = False
    name: str = ""
    expires_at: Any = None
    scope: KeyScopeOut | None = None
    key_retention: list[KeyRetentionOut] = Field(default_factory=list)


class ExtractedConfirmation(_Base, Mapping[str, Any]):
    message_id: str
    from_address: str
    subject: str
    confirmation_link: str | None = None
    confirmation_code: str | None = None

    def __getitem__(self, key: str) -> Any:
        if key in type(self).model_fields:
            return getattr(self, key)
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:  # type: ignore[override]
        return iter(type(self).model_fields)

    def __len__(self) -> int:
        return len(type(self).model_fields)


Provider = ProviderOut
Target = TargetOut
Mailbox = MailboxOut
MessageSummary = MessageOut
MessageDetail = MessageDetailOut
MessageSource = SourceOut
GmailAccount = GmailAccountOut
OAuthStart = OAuthStartOut
GmailCreds = GmailCredsOut
Retention = RetentionOut
DomainCacheProvider = DomainCacheProviderOut
DomainCache = DomainCacheOut

_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)


# --------------------------------------------------------------------------- #
# Errors
# --------------------------------------------------------------------------- #
class ClientError(Exception):
    """Base client error for maily."""


class WaitTimeoutError(ClientError, TimeoutError):
    """Timed out waiting for incoming email, confirmation link, or verification code."""


class ApiError(ClientError):
    """Service HTTP error response: non-2xx status with detail from the response body."""

    def __init__(self, status_code: int | None, detail: str = "") -> None:
        self.status_code = status_code
        self.detail = detail or (f"HTTP {status_code}" if status_code else "request failed")
        super().__init__(self.detail)


class AuthenticationError(ApiError):
    """HTTP 401: Invalid or missing API key."""


class ForbiddenError(ApiError):
    """HTTP 403: Access forbidden (insufficient key permissions for resource/action)."""


class NotFoundError(ApiError):
    """HTTP 404: Requested resource not found."""


class ValidationError(ApiError):
    """HTTP 400 or 422: Request parameter validation error."""


class RateLimitError(ApiError):
    """HTTP 429: Rate limit exceeded."""


class UpstreamProviderError(ApiError):
    """HTTP 502/504: Upstream email provider failure or timeout."""


# --------------------------------------------------------------------------- #
# Git self-update
# --------------------------------------------------------------------------- #
def _parse_version(text: str) -> str | None:
    match = re.search(r"^__version__\s*=\s*[\"']([^\"']+)[\"']", text, re.MULTILINE)
    return match.group(1) if match else None


def _fetch_client(source_url: str | None) -> str:
    url = source_url or CLIENT_SOURCE
    resp = httpx.get(url, timeout=15.0, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


def check_update(source_url: str | None = None) -> tuple[str, str] | None:
    """Return (local, remote) versions if a newer version exists on git, else None."""
    remote = _parse_version(_fetch_client(source_url))
    if not remote:
        raise ClientError("could not read __version__ from the client source")
    if remote == __version__:
        return None
    return (__version__, remote)


def _atomic_replace(path: str, text: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="") as fh:
        fh.write(text)
    if os.name == "nt":
        with (
            open(tmp, encoding="utf-8") as src,
            open(path, "w", encoding="utf-8", newline="") as dst,
        ):
            dst.write(src.read())
        with suppress(OSError):
            os.remove(tmp)
    else:
        os.replace(tmp, path)


def self_update(
    source_url: str | None = None,
    *,
    after: Callable[[], None] | None = None,
) -> bool:
    """Update the client file with the new version from git.

    Returns True if the file was replaced, False if the version is already current.
    The source URL can be overridden with the MAILY_CLIENT_SOURCE env var.
    """
    text = _fetch_client(source_url)
    remote = _parse_version(text)
    if not remote:
        raise ClientError("could not read __version__ from the client source")
    if remote == __version__:
        return False

    import inspect

    path = inspect.getsourcefile(Maily) or __file__
    _atomic_replace(path, text)
    logger.info("client updated {} -> {} ({})", __version__, remote, path)
    if after is not None:
        after()
    return True


# --------------------------------------------------------------------------- #
# Transport
# --------------------------------------------------------------------------- #
_TRANSIENT_NETWORK_ERRORS = (httpx.ConnectTimeout, httpx.ConnectError, httpx.NetworkError)


def _parse_retry_after(header_val: str | None, attempt: int, backoff: float) -> float:
    """Parse HTTP Retry-After header as seconds (float/int).

    Falls back to exponential backoff `backoff * (2 ** attempt)` if missing or invalid.
    """
    if header_val is not None:
        try:
            val = float(header_val.strip())
            if val >= 0:
                return val
        except (ValueError, TypeError):
            pass
    return max(0.0, backoff * (2**attempt))


class _Transport:
    """Common HTTP transport layer: shared AsyncClient, API key, logging, error handling."""

    def __init__(
        self,
        base_url: str,
        api_key: str = "",
        timeout: float = 30.0,
        *,
        client: httpx.AsyncClient | None = None,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
    ) -> None:
        self._client = client or httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout)
        self._owns_client = client is None
        self._headers: dict[str, str] = {}
        if api_key:
            self._headers["X-API-Key"] = api_key
        self.max_retries = max(0, int(max_retries))
        self.retry_backoff = max(0.0, float(retry_backoff))

    def set_api_key(self, api_key: str) -> None:
        """Update the API key dynamically (empty string to remove)."""
        if api_key:
            self._headers["X-API-Key"] = api_key
        else:
            self._headers.pop("X-API-Key", None)

    def _parse_retry_after(self, header_val: str | None, attempt: int) -> float:
        return _parse_retry_after(header_val, attempt, self.retry_backoff)

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
    ) -> Any:
        for attempt in range(self.max_retries + 1):
            started = time.perf_counter()
            try:
                resp = await self._client.request(
                    method, path, params=params, json=json, headers=self._headers
                )
            except _TRANSIENT_NETWORK_ERRORS as exc:
                if attempt < self.max_retries:
                    delay = self.retry_backoff * (2**attempt)
                    logger.warning(
                        "{} {} transient connection error ({}), retrying in {:.2f}s (attempt {}/{})",
                        method,
                        path,
                        exc,
                        delay,
                        attempt + 1,
                        self.max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                logger.opt(exception=False).warning("{} {} failed: {}", method, path, exc)
                raise ApiError(None, f"network error: {exc}") from exc
            except httpx.HTTPError as exc:
                logger.opt(exception=False).warning("{} {} failed: {}", method, path, exc)
                raise ApiError(None, f"network error: {exc}") from exc

            elapsed = (time.perf_counter() - started) * 1000
            if resp.status_code >= 400:
                detail = _extract_detail(resp)
                logger.warning(
                    "{} {} -> {} ({:.0f}ms): {}", method, path, resp.status_code, elapsed, detail
                )
                if resp.status_code == 429 and attempt < self.max_retries:
                    delay = self._parse_retry_after(resp.headers.get("Retry-After"), attempt)
                    logger.warning(
                        "{} {} rate limited (429), retrying in {:.2f}s (attempt {}/{})",
                        method,
                        path,
                        delay,
                        attempt + 1,
                        self.max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                if resp.status_code in (502, 504) and attempt < self.max_retries:
                    delay = self.retry_backoff * (2**attempt)
                    logger.warning(
                        "{} {} upstream error ({}), retrying in {:.2f}s (attempt {}/{})",
                        method,
                        path,
                        resp.status_code,
                        delay,
                        attempt + 1,
                        self.max_retries,
                    )
                    await asyncio.sleep(delay)
                    continue
                if resp.status_code == 401:
                    raise AuthenticationError(resp.status_code, detail)
                if resp.status_code == 403:
                    raise ForbiddenError(resp.status_code, detail)
                if resp.status_code == 404:
                    raise NotFoundError(resp.status_code, detail)
                if resp.status_code in (400, 422):
                    raise ValidationError(resp.status_code, detail)
                if resp.status_code == 429:
                    raise RateLimitError(resp.status_code, detail)
                if resp.status_code in (502, 504):
                    raise UpstreamProviderError(resp.status_code, detail)
                raise ApiError(resp.status_code, detail)

            logger.debug("{} {} -> {} ({:.0f}ms)", method, path, resp.status_code, elapsed)
            if resp.status_code == 204:
                return None
            return resp.json()
        raise ApiError(None, "retries exhausted")

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> _Transport:
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        await self.close()


def _extract_detail(resp: httpx.Response) -> str:
    try:
        body = resp.json()
    except Exception:
        text = resp.text[:300] if resp.text else ""
        return text if text.strip() else f"HTTP {resp.status_code}"

    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, str) and detail:
            return detail
        if isinstance(detail, list):
            formatted: list[str] = []
            for item in detail:
                if isinstance(item, dict):
                    loc = item.get("loc")
                    msg = item.get("msg") or ""
                    field = ""
                    if isinstance(loc, (list, tuple)):
                        parts = [str(p) for p in loc]
                        if parts and parts[0] in ("body", "query", "path", "header", "cookie"):
                            parts = parts[1:]
                        field = ".".join(parts)
                    if field and msg:
                        formatted.append(f"{field}: {msg}")
                    elif msg:
                        formatted.append(str(msg))
                    elif field:
                        formatted.append(field)
                    else:
                        formatted.append(str(item))
                elif isinstance(item, str):
                    formatted.append(item)
                else:
                    formatted.append(str(item))
            if formatted:
                return "; ".join(formatted)
        if detail is not None and not (isinstance(detail, (dict, list, str)) and not detail):
            return str(detail)[:300]
        return str(body)[:300]

    return str(body)[:300]


def _mailbox_id_val(mailbox_id: int | MailboxOut) -> int:
    return mailbox_id.id if hasattr(mailbox_id, "id") else int(mailbox_id)


# --------------------------------------------------------------------------- #
# Resource APIs
# --------------------------------------------------------------------------- #
class HealthAPI:
    """GET /health — service health check (no API key required)."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def ping(self) -> HealthOut:
        return HealthOut.model_validate(await self._t.request("GET", "/health"))


class ConfigAPI:
    """GET /v1/config — public server facts (no API key required)."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def get(self) -> dict[str, Any]:
        return await self._t.request("GET", "/v1/config")


class ProvidersAPI:
    """Providers and targets (domains / parent accounts)."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def list(self) -> list[Provider]:
        """All available providers."""
        return [Provider.model_validate(p) for p in await self._t.request("GET", "/v1/providers")]

    async def targets(self, provider: str | None = None) -> builtins.list[Target]:
        """Mailbox creation targets: domains (domain providers) or Gmail accounts."""
        params = {"provider": provider} if provider else None
        return [
            Target.model_validate(t)
            for t in await self._t.request("GET", "/v1/targets", params=params)
        ]


class MailboxesAPI:
    """Mailbox creation, listing, retrieval, and deletion."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def create(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
        parent_id: int | None = None,
        address: str | None = None,
        password: str | None = None,
    ) -> Mailbox:
        """Create a mailbox. Use domain for domain providers, or parent_id for Gmail."""
        payload = {
            k: v
            for k, v in {
                "provider": provider,
                "domain": domain,
                "parent_id": parent_id,
                "address": address,
                "password": password,
            }.items()
            if v is not None
        }
        return Mailbox.model_validate(await self._t.request("POST", "/v1/mailboxes", json=payload))

    async def list(
        self,
        *,
        provider: str | None = None,
        active: bool | None = None,
        q: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Mailbox]:
        """List mailboxes. active=None returns all (including deleted)."""
        params: dict[str, Any] = {}
        if provider:
            params["provider"] = provider
        if active is not None:
            params["active"] = str(active).lower()
        if q:
            params["q"] = q
        if limit is not None:
            params["limit"] = str(limit)
        if offset is not None:
            params["offset"] = str(offset)
        return [
            Mailbox.model_validate(m)
            for m in await self._t.request("GET", "/v1/mailboxes", params=params or None)
        ]

    async def get(self, mailbox_id: int | Mailbox) -> Mailbox:
        mid = _mailbox_id_val(mailbox_id)
        return Mailbox.model_validate(await self._t.request("GET", f"/v1/mailboxes/{mid}"))

    async def by_address(self, email: str) -> Mailbox:
        """Find mailbox by full email address."""
        return Mailbox.model_validate(
            await self._t.request("GET", f"/v1/mailboxes/by-address/{quote(email, safe='')}")
        )

    async def delete(self, mailbox_id: int | Mailbox) -> None:
        """Delete mailbox (both upstream at provider and locally)."""
        mid = _mailbox_id_val(mailbox_id)
        await self._t.request("DELETE", f"/v1/mailboxes/{mid}")


class MessagesAPI:
    """Mailbox messages: list, read, mark, delete, and wait for incoming mail."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def list(self, mailbox_id: int | Mailbox, page: int = 1) -> list[MessageSummary]:
        """List messages (paginated)."""
        mid = _mailbox_id_val(mailbox_id)
        return [
            MessageSummary.model_validate(m)
            for m in await self._t.request(
                "GET", f"/v1/mailboxes/{mid}/messages", params={"page": page}
            )
        ]

    async def get(self, mailbox_id: int | Mailbox, message_id: str) -> MessageDetail:
        """Full message detail including plain text and HTML."""
        mid = _mailbox_id_val(mailbox_id)
        return MessageDetail.model_validate(
            await self._t.request(
                "GET", f"/v1/mailboxes/{mid}/messages/{quote(message_id, safe='')}"
            )
        )

    async def mark_read(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSummary:
        mid = _mailbox_id_val(mailbox_id)
        return MessageSummary.model_validate(
            await self._t.request(
                "POST", f"/v1/mailboxes/{mid}/messages/{quote(message_id, safe='')}/read"
            )
        )

    async def delete(self, mailbox_id: int | Mailbox, message_id: str) -> None:
        mid = _mailbox_id_val(mailbox_id)
        await self._t.request(
            "DELETE", f"/v1/mailboxes/{mid}/messages/{quote(message_id, safe='')}"
        )

    async def source(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSource:
        """Raw message source (RFC 822 / MIME)."""
        mid = _mailbox_id_val(mailbox_id)
        return MessageSource.model_validate(
            await self._t.request(
                "GET", f"/v1/mailboxes/{mid}/messages/{quote(message_id, safe='')}/source"
            )
        )

    async def wait_for(
        self,
        mailbox_id: int | Mailbox,
        *,
        timeout: float = 120.0,
        interval: float = 2.0,
        predicate: Callable[[MessageSummary], bool] | None = None,
        mark_seen: bool = False,
    ) -> MessageSummary:
        """Poll the message list until a matching message arrives (defaults to any).

        When mark_seen=True, the found message is immediately marked as read.
        Raises WaitTimeoutError (also a TimeoutError) when timeout expires.
        """
        mid = _mailbox_id_val(mailbox_id)
        deadline = time.monotonic() + timeout
        while True:
            for m in await self.list(mid):
                if predicate is None or predicate(m):
                    if mark_seen:
                        await self.mark_read(mid, m.message_api_id)
                    return m
            if time.monotonic() >= deadline:
                raise WaitTimeoutError(f"no message arrived within {timeout}s")
            await asyncio.sleep(interval)

    async def wait_for_confirmation_email(
        self,
        mailbox_id: int | Mailbox,
        *,
        sender_domain: str | None = None,
        url_contain: builtins.list[str] | None = None,
        digit_code_mask: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 5.0,
    ) -> ExtractedConfirmation | None:
        """Wait for a confirmation email and extract confirmation link and/or code.

        Parameters (all optional, but either `url_contain` or `digit_code_mask` is needed):
            sender_domain    — filter by sender domain, e.g. "gmail.com"
            url_contain      — substrings that must be in the link,
                                e.g. ["confirm", "verify", "activate", "token"]
            digit_code_mask  — regex pattern for the confirmation code

        Returns an ExtractedConfirmation instance (supporting both attribute
        and dictionary mapping access) or None when timeout expires.
        """
        mid = _mailbox_id_val(mailbox_id)
        if timeout < 0:
            raise ValueError("timeout must be >= 0")
        if check_interval <= 0:
            raise ValueError("check_interval must be > 0")

        keywords: list[str] = []
        for keyword in url_contain or []:
            if keyword:
                keywords.append(keyword.casefold())
        try:
            code_pattern = re.compile(digit_code_mask, re.IGNORECASE) if digit_code_mask else None
        except re.error as exc:
            raise ValueError(
                f"Invalid regular expression digit_code_mask: {digit_code_mask!r}"
            ) from exc

        loop = asyncio.get_running_loop()
        deadline = loop.time() + timeout

        def _is_from_domain(address: str, domain: str) -> bool:
            match = re.search(r"<([^>]+)>", address)
            email = match.group(1) if match else address
            email_domain = email.rsplit("@", 1)[-1].strip().casefold()
            return email_domain == domain.casefold().lstrip("@")

        examined: set[str] = set()

        while loop.time() < deadline:
            for msg in await self.list(mid):
                message_id = msg.message_api_id
                if message_id in examined:
                    continue
                if sender_domain and not _is_from_domain(msg.from_address, sender_domain):
                    examined.add(message_id)
                    continue

                try:
                    detail = await self.get(mid, message_id)
                except Exception:
                    logger.exception("Failed to load message details for %s", message_id)
                    continue

                examined.add(message_id)

                body = "\n".join(filter(None, [detail.text or "", *detail.html]))

                urls = _URL_RE.findall(body)
                confirmation_link = next(
                    (
                        url
                        for url in urls
                        if not keywords or any(kw in url.casefold() for kw in keywords)
                    ),
                    None,
                )

                confirmation_code = None
                if code_pattern:
                    match = code_pattern.search(body)
                    if match:
                        confirmation_code = match.group(1) if match.lastindex else match.group(0)

                if confirmation_link is None and confirmation_code is None:
                    continue

                logger.info(
                    "Confirmation email found from %s (subject: %s)",
                    msg.from_address,
                    msg.subject,
                )
                return ExtractedConfirmation(
                    message_id=message_id,
                    from_address=msg.from_address,
                    subject=msg.subject,
                    confirmation_link=confirmation_link,
                    confirmation_code=confirmation_code,
                )

            remaining = deadline - loop.time()
            if remaining <= 0:
                break
            await asyncio.sleep(min(check_interval, remaining))

        return None

    async def wait_for_code(
        self,
        mailbox_id: int | Mailbox,
        *,
        pattern: str = r"\b(\d{4,8})\b",
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Wait for an email and return the digit confirmation code as a string.

        Raises WaitTimeoutError when timeout expires.
        """
        res = await self.wait_for_confirmation_email(
            mailbox_id,
            sender_domain=sender_domain,
            digit_code_mask=pattern,
            timeout=timeout,
            check_interval=check_interval,
        )
        if not res or not res.get("confirmation_code"):
            raise WaitTimeoutError(f"no verification code arrived within {timeout}s")
        return str(res["confirmation_code"])

    async def wait_for_link(
        self,
        mailbox_id: int | Mailbox,
        *,
        url_contain: builtins.list[str] | None = None,
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Wait for an email and return the confirmation URL.

        Raises WaitTimeoutError when timeout expires.
        """
        res = await self.wait_for_confirmation_email(
            mailbox_id,
            sender_domain=sender_domain,
            url_contain=url_contain or ["http"],
            timeout=timeout,
            check_interval=check_interval,
        )
        if not res or not res.get("confirmation_link"):
            raise WaitTimeoutError(f"no confirmation link arrived within {timeout}s")
        return str(res["confirmation_link"])

    async def iter_messages(
        self,
        mailbox_id: int | Mailbox,
        *,
        poll_interval: float = 3.0,
        timeout: float | None = None,
    ) -> AsyncIterator[MessageSummary]:
        """Async generator: continuously polls the mailbox and yields new messages as they arrive."""
        mid = _mailbox_id_val(mailbox_id)
        seen_ids: set[str] = set()
        loop = asyncio.get_running_loop()
        deadline = (loop.time() + timeout) if timeout is not None else None

        for m in await self.list(mid):
            seen_ids.add(m.message_api_id)

        while True:
            if deadline is not None and loop.time() >= deadline:
                break
            for m in await self.list(mid):
                if m.message_api_id not in seen_ids:
                    seen_ids.add(m.message_api_id)
                    yield m
            if deadline is not None and loop.time() + poll_interval >= deadline:
                break
            await asyncio.sleep(poll_interval)


class GmailAPI:
    """OAuth flow and Gmail account management."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def oauth_start(self) -> OAuthStart:
        """OAuth authorization URL: open in browser to link any Google account."""
        return OAuthStart.model_validate(await self._t.request("POST", "/v1/gmail/oauth/start"))

    async def import_account(
        self,
        *,
        refresh_token: str | None = None,
        token_json: Any = None,
    ) -> GmailAccount:
        """Import an existing token (refresh_token or token_json)."""
        payload: dict[str, Any] = {}
        if refresh_token:
            payload["refresh_token"] = refresh_token
        if token_json is not None:
            payload["token_json"] = token_json
        return GmailAccount.model_validate(
            await self._t.request("POST", "/v1/gmail/accounts/import", json=payload)
        )

    async def accounts(self) -> list[GmailAccount]:
        return [
            GmailAccount.model_validate(a)
            for a in await self._t.request("GET", "/v1/gmail/accounts")
        ]

    async def delete_account(self, parent_id: int) -> None:
        await self._t.request("DELETE", f"/v1/gmail/accounts/{parent_id}")

    async def sync(self, parent_id: int) -> GmailAccount:
        """Sync account profile and send-as aliases."""
        return GmailAccount.model_validate(
            await self._t.request("POST", f"/v1/gmail/accounts/{parent_id}/sync")
        )


class KeysAPI:
    """API key management: list, create, view, rotate, delete."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport

    async def list(self) -> builtins.list[ApiKeyOut]:
        """Root only. List issued keys (without secrets)."""
        data = await self._t.request("GET", "/v1/admin/keys")
        return [ApiKeyOut.model_validate(k) for k in data]

    async def create(
        self,
        *,
        name: str,
        expires_at: str | None = None,
        scope: dict[str, Any] | None = None,
        retention: builtins.list[dict[str, Any]] | None = None,
    ) -> ApiKeyCreatedOut:
        """Root only. Create a key (secret returned once in creation response)."""
        payload: dict[str, Any] = {
            "name": name,
            "expires_at": expires_at,
            "scope": scope or {"providers": [], "parent_ids": [], "actions": []},
            "retention": retention or [],
        }
        return ApiKeyCreatedOut.model_validate(
            await self._t.request("POST", "/v1/admin/keys", json=payload)
        )

    async def get(self, key_id: int) -> ApiKeyOut:
        """Root only. Get key details by ID (without secret)."""
        return ApiKeyOut.model_validate(await self._t.request("GET", f"/v1/admin/keys/{key_id}"))

    async def me(self) -> ApiKeyMeOut:
        """Get current active key details (from X-API-Key header)."""
        return ApiKeyMeOut.model_validate(await self._t.request("GET", "/v1/admin/keys/me"))

    async def secret(self, key_id: int) -> str:
        """Root only. Reveal key secret."""
        data = await self._t.request("GET", f"/v1/admin/keys/{key_id}/secret")
        return str(data.get("secret") or "")

    async def update(
        self,
        key_id: int,
        *,
        name: str,
        expires_at: str | None = None,
        scope: dict[str, Any] | None = None,
    ) -> ApiKeyOut:
        """Root only. Update key name, expiration date, or scope."""
        payload = {
            "name": name,
            "expires_at": expires_at,
            "scope": scope or {"providers": [], "parent_ids": [], "actions": []},
        }
        return ApiKeyOut.model_validate(
            await self._t.request("PATCH", f"/v1/admin/keys/{key_id}", json=payload)
        )

    async def retention_set(
        self, key_id: int, retention: builtins.list[dict[str, Any]]
    ) -> builtins.list[KeyRetentionOut]:
        """Root only. Set custom retention TTL rules for the key."""
        data = await self._t.request("PUT", f"/v1/admin/keys/{key_id}/retention", json=retention)
        return [KeyRetentionOut.model_validate(r) for r in data]

    async def rotate(self, key_id: int) -> ApiKeyCreatedOut:
        """Root only. Rotate key secret (revokes old secret, returns new secret once)."""
        return ApiKeyCreatedOut.model_validate(
            await self._t.request("POST", f"/v1/admin/keys/{key_id}/rotate")
        )

    async def delete(self, key_id: int) -> None:
        """Root only. Delete key."""
        await self._t.request("DELETE", f"/v1/admin/keys/{key_id}")


class AdminAPI:
    """Admin API: statistics, retention (TTL cleanup), domain cache, Gmail credentials, keys."""

    def __init__(self, transport: _Transport) -> None:
        self._t = transport
        self.keys_api = KeysAPI(transport)

    async def stats(self) -> dict:
        """Statistics: mailboxes, messages, providers, and 7-day trend."""
        return await self._t.request("GET", "/v1/admin/stats")

    async def retention_list(self) -> list[Retention]:
        return [
            Retention.model_validate(r) for r in await self._t.request("GET", "/v1/admin/retention")
        ]

    async def retention_set(
        self,
        provider: str,
        *,
        mailbox_ttl_hours: int | None = None,
        message_ttl_hours: int | None = None,
    ) -> Retention:
        """Enable or update retention TTL for a provider (at least one TTL required)."""
        payload = {
            k: v
            for k, v in {
                "mailbox_ttl_hours": mailbox_ttl_hours,
                "message_ttl_hours": message_ttl_hours,
            }.items()
            if v is not None
        }
        return Retention.model_validate(
            await self._t.request(
                "PUT", f"/v1/admin/retention/{quote(provider, safe='')}", json=payload
            )
        )

    async def retention_disable(self, provider: str) -> None:
        await self._t.request("DELETE", f"/v1/admin/retention/{quote(provider, safe='')}")

    async def retention_run(self, *, force_maintenance: bool = False) -> SweepResult:
        """Run cleanup now: sweep expired mailboxes and messages."""
        return SweepResult.model_validate(
            await self._t.request(
                "POST",
                "/v1/admin/retention/run",
                params={"force_maintenance": "true"} if force_maintenance else None,
            )
        )

    async def domain_cache(self) -> DomainCache:
        """Current domain cache status (enabled, interval, providers)."""
        return DomainCache.model_validate(await self._t.request("GET", "/v1/admin/domain-cache"))

    async def domain_cache_save(
        self,
        *,
        enabled: bool | None = None,
        interval_seconds: int | None = None,
    ) -> DomainCache:
        """Update domain cache settings (at least one parameter required)."""
        payload = {
            k: v
            for k, v in {
                "enabled": enabled,
                "interval_seconds": interval_seconds,
            }.items()
            if v is not None
        }
        return DomainCache.model_validate(
            await self._t.request("PUT", "/v1/admin/domain-cache", json=payload)
        )

    async def domain_cache_run(self) -> DomainCacheRun:
        """Force refresh domain cache now."""
        return DomainCacheRun.model_validate(
            await self._t.request("POST", "/v1/admin/domain-cache/run")
        )

    async def gmail_creds(self) -> GmailCreds:
        return GmailCreds.model_validate(await self._t.request("GET", "/v1/admin/gmail/creds"))

    async def gmail_creds_save(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None = None,
    ) -> GmailCreds:
        payload: dict[str, str] = {"client_id": client_id, "client_secret": client_secret}
        if redirect_uri:
            payload["redirect_uri"] = redirect_uri
        return GmailCreds.model_validate(
            await self._t.request("PUT", "/v1/admin/gmail/creds", json=payload)
        )

    async def gmail_creds_clear(self) -> None:
        await self._t.request("DELETE", "/v1/admin/gmail/creds")

    async def keys(self) -> list[dict[str, Any]]:
        """Root only. Lists keys; the secret is not in the response."""
        return await self._t.request("GET", "/v1/admin/keys")

    async def key_create(
        self,
        *,
        name: str,
        expires_at: str | None,
        scope: dict[str, Any],
        retention: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Root only. Creates a key; the response includes the secret once."""
        return await self._t.request(
            "POST",
            "/v1/admin/keys",
            json={
                "name": name,
                "expires_at": expires_at,
                "scope": scope,
                "retention": retention,
            },
        )

    async def key_get(self, key_id: int) -> dict[str, Any]:
        """Root only. Returns one key without the secret."""
        return await self._t.request("GET", f"/v1/admin/keys/{key_id}")

    async def key_me(self) -> dict[str, Any]:
        """Any authenticated key. Root gets is_root; an issued key gets no secret."""
        return await self._t.request("GET", "/v1/admin/keys/me")

    async def key_secret(self, key_id: int) -> dict[str, Any]:
        """Root only. Reveals the secret."""
        return await self._t.request("GET", f"/v1/admin/keys/{key_id}/secret")

    async def key_update(
        self,
        key_id: int,
        *,
        name: str,
        expires_at: str | None,
        scope: dict[str, Any],
    ) -> dict[str, Any]:
        """Root only. Updates name, expiry, and scope; the secret is unchanged."""
        return await self._t.request(
            "PATCH",
            f"/v1/admin/keys/{key_id}",
            json={"name": name, "expires_at": expires_at, "scope": scope},
        )

    async def key_retention_set(
        self, key_id: int, retention: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Root only. Replaces that key's retention rows."""
        return await self._t.request("PUT", f"/v1/admin/keys/{key_id}/retention", json=retention)

    async def key_rotate(self, key_id: int) -> dict[str, Any]:
        """Root only. Rotates the secret; the response includes the new secret once."""
        return await self._t.request("POST", f"/v1/admin/keys/{key_id}/rotate")

    async def key_delete(self, key_id: int) -> None:
        """Root only. Deletes the key."""
        await self._t.request("DELETE", f"/v1/admin/keys/{key_id}")


# --------------------------------------------------------------------------- #
# Public client
# --------------------------------------------------------------------------- #
class Maily:
    """Async client for maily. Use via `async with` or close manually.

        async with Maily("http://127.0.0.1:8477", api_key="sk-…") as api:
            box = await api.create_temp_mailbox()
            code = await api.wait_for_code(box)
            print("Verification code:", code)

    Sections: .health, .config, .providers, .mailboxes, .messages, .gmail, .admin, .keys
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8477",
        api_key: str = "",
        timeout: float = 30.0,
        *,
        client: httpx.AsyncClient | None = None,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
    ) -> None:
        self._transport = _Transport(
            base_url,
            api_key,
            timeout,
            client=client,
            max_retries=max_retries,
            retry_backoff=retry_backoff,
        )
        self.health = HealthAPI(self._transport)
        self.config = ConfigAPI(self._transport)
        self.providers = ProvidersAPI(self._transport)
        self.mailboxes = MailboxesAPI(self._transport)
        self.messages = MessagesAPI(self._transport)
        self.gmail = GmailAPI(self._transport)
        self.admin = AdminAPI(self._transport)
        self.keys = KeysAPI(self._transport)

    @property
    def max_retries(self) -> int:
        """Client-side retry limit for transient network/server/rate-limit errors."""
        return self._transport.max_retries

    @max_retries.setter
    def max_retries(self, value: int) -> None:
        self._transport.max_retries = max(0, int(value))

    @property
    def retry_backoff(self) -> float:
        """Base backoff in seconds for exponential retry backoff."""
        return self._transport.retry_backoff

    @retry_backoff.setter
    def retry_backoff(self, value: float) -> None:
        self._transport.retry_backoff = max(0.0, float(value))

    def set_api_key(self, api_key: str) -> None:
        """Update API key dynamically."""
        self._transport.set_api_key(api_key)

    async def check_client_version(self) -> str:
        """Server version from /v1/config. Warns on version mismatch."""
        cfg = await self.config.get()
        remote = str(cfg.get("client_version") or "")
        if remote and remote != __version__:
            logger.warning(
                "client {} != server {} — update client: `maily-client update`",
                __version__,
                remote,
            )
        return remote

    async def create_temp_mailbox(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
    ) -> Mailbox:
        """Convenience helper: create a temporary mailbox in one call.

        If domain is omitted, automatically picks the first available provider domain.
        """
        if not domain and not provider:
            targets = await self.providers.targets()
            domain_targets = [t for t in targets if t.kind == "domain"]
            if domain_targets:
                domain = domain_targets[0].label
                provider = domain_targets[0].provider
        elif not domain and provider:
            targets = await self.providers.targets(provider=provider)
            if targets:
                domain = targets[0].label
        return await self.mailboxes.create(provider=provider, domain=domain)

    async def wait_for_code(
        self,
        mailbox_id: int | Mailbox,
        *,
        pattern: str = r"\b(\d{4,8})\b",
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Poll mailbox until an email with a digit verification code arrives."""
        return await self.messages.wait_for_code(
            mailbox_id,
            pattern=pattern,
            sender_domain=sender_domain,
            timeout=timeout,
            check_interval=check_interval,
        )

    async def wait_for_link(
        self,
        mailbox_id: int | Mailbox,
        *,
        url_contain: builtins.list[str] | None = None,
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Poll mailbox until an email with a confirmation link arrives."""
        return await self.messages.wait_for_link(
            mailbox_id,
            url_contain=url_contain,
            sender_domain=sender_domain,
            timeout=timeout,
            check_interval=check_interval,
        )

    async def wait_for_confirmation_email(
        self,
        mailbox_id: int | Mailbox,
        *,
        sender_domain: str | None = None,
        url_contain: builtins.list[str] | None = None,
        digit_code_mask: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 5.0,
    ) -> ExtractedConfirmation | None:
        """Wait for a confirmation email and extract confirmation link and/or code."""
        return await self.messages.wait_for_confirmation_email(
            mailbox_id,
            sender_domain=sender_domain,
            url_contain=url_contain,
            digit_code_mask=digit_code_mask,
            timeout=timeout,
            check_interval=check_interval,
        )

    async def close(self) -> None:
        await self._transport.close()

    async def __aenter__(self) -> Maily:
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        await self.close()

    # --- SDK-compatible flat methods (deprecated, use sections above) ---

    async def create_mailbox(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
        parent_id: int | None = None,
        address: str | None = None,
        password: str | None = None,
    ) -> Mailbox:
        return await self.mailboxes.create(
            provider=provider,
            domain=domain,
            parent_id=parent_id,
            address=address,
            password=password,
        )

    async def list_mailboxes(
        self, provider: str | None = None, active: bool | None = None
    ) -> list[Mailbox]:
        return await self.mailboxes.list(provider=provider, active=active)

    async def mailbox(self, mailbox_id: int | Mailbox) -> Mailbox:
        return await self.mailboxes.get(mailbox_id)

    async def mailbox_by_address(self, email: str) -> Mailbox:
        return await self.mailboxes.by_address(email)

    async def delete_mailbox(self, mailbox_id: int | Mailbox) -> None:
        await self.mailboxes.delete(mailbox_id)

    async def list_messages(self, mailbox_id: int | Mailbox, page: int = 1) -> list[MessageSummary]:
        return await self.messages.list(mailbox_id, page=page)

    async def get_message(self, mailbox_id: int | Mailbox, message_id: str) -> MessageDetail:
        return await self.messages.get(mailbox_id, message_id)

    async def mark_read(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSummary:
        return await self.messages.mark_read(mailbox_id, message_id)

    async def delete_message(self, mailbox_id: int | Mailbox, message_id: str) -> None:
        await self.messages.delete(mailbox_id, message_id)

    async def get_source(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSource:
        return await self.messages.source(mailbox_id, message_id)

    async def gmail_oauth_start(self) -> OAuthStart:
        return await self.gmail.oauth_start()

    async def gmail_import_account(
        self, *, refresh_token: str | None = None, token_json: Any = None
    ) -> GmailAccount:
        return await self.gmail.import_account(refresh_token=refresh_token, token_json=token_json)

    async def list_gmail_accounts(self) -> list[GmailAccount]:
        return await self.gmail.accounts()

    async def delete_gmail_account(self, parent_id: int) -> None:
        await self.gmail.delete_account(parent_id)

    async def sync_gmail_account(self, parent_id: int) -> GmailAccount:
        return await self.gmail.sync(parent_id)

    async def domain_cache_settings(self) -> DomainCache:
        return await self.admin.domain_cache()

    async def save_domain_cache_settings(
        self, *, enabled: bool | None = None, interval_seconds: int | None = None
    ) -> DomainCache:
        return await self.admin.domain_cache_save(
            enabled=enabled, interval_seconds=interval_seconds
        )

    async def refresh_domain_cache(self) -> DomainCacheRun:
        return await self.admin.domain_cache_run()

    async def wait_for_message(
        self,
        mailbox_id: int | Mailbox,
        *,
        timeout: float = 120.0,
        interval: float = 2.0,
        predicate: Callable[[MessageSummary], bool] | None = None,
    ) -> MessageSummary:
        return await self.messages.wait_for(
            mailbox_id, timeout=timeout, interval=interval, predicate=predicate
        )


# --------------------------------------------------------------------------- #
# Synchronous section wrappers
# --------------------------------------------------------------------------- #
class SyncHealthAPI:
    """GET /health — service health check (no API key required)."""

    def __init__(self, async_api: HealthAPI, run: Callable[[Any], Any]) -> None:
        self._async = async_api
        self._run = run

    def ping(self) -> HealthOut:
        return self._run(self._async.ping())


class SyncConfigAPI:
    """GET /v1/config — public server facts (no API key required)."""

    def __init__(self, async_api: ConfigAPI, run: Callable[[Any], Any]) -> None:
        self._async = async_api
        self._run = run

    def get(self) -> dict[str, Any]:
        return self._run(self._async.get())


class SyncProvidersAPI:
    """Providers and targets (domains / parent accounts)."""

    def __init__(self, async_api: ProvidersAPI, run: Callable[[Any], Any]) -> None:
        self._async = async_api
        self._run = run

    def list(self) -> list[Provider]:
        """All available providers."""
        return self._run(self._async.list())

    def targets(self, provider: str | None = None) -> builtins.list[Target]:
        """Mailbox creation targets: domains (domain providers) or Gmail accounts."""
        return self._run(self._async.targets(provider=provider))


class SyncMailboxesAPI:
    """Mailbox creation, listing, retrieval, and deletion."""

    def __init__(self, async_api: MailboxesAPI, run: Callable[[Any], Any]) -> None:
        self._async = async_api
        self._run = run

    def create(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
        parent_id: int | None = None,
        address: str | None = None,
        password: str | None = None,
    ) -> Mailbox:
        """Create a mailbox. Use domain for domain providers, or parent_id for Gmail."""
        return self._run(
            self._async.create(
                provider=provider,
                domain=domain,
                parent_id=parent_id,
                address=address,
                password=password,
            )
        )

    def list(
        self,
        *,
        provider: str | None = None,
        active: bool | None = None,
        q: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[Mailbox]:
        """List mailboxes. active=None returns all (including deleted)."""
        return self._run(
            self._async.list(
                provider=provider,
                active=active,
                q=q,
                limit=limit,
                offset=offset,
            )
        )

    def get(self, mailbox_id: int | Mailbox) -> Mailbox:
        return self._run(self._async.get(mailbox_id))

    def by_address(self, email: str) -> Mailbox:
        """Find mailbox by full email address."""
        return self._run(self._async.by_address(email))

    def delete(self, mailbox_id: int | Mailbox) -> None:
        """Delete mailbox (both upstream at provider and locally)."""
        return self._run(self._async.delete(mailbox_id))


class SyncMessagesAPI:
    """Mailbox messages: list, read, mark, delete, and wait for incoming mail."""

    def __init__(self, async_api: MessagesAPI, run: Callable[[Any], Any]) -> None:
        self._async = async_api
        self._run = run

    def list(self, mailbox_id: int | Mailbox, page: int = 1) -> list[MessageSummary]:
        """List messages (paginated)."""
        return self._run(self._async.list(mailbox_id, page=page))

    def get(self, mailbox_id: int | Mailbox, message_id: str) -> MessageDetail:
        """Full message detail including plain text and HTML."""
        return self._run(self._async.get(mailbox_id, message_id))

    def mark_read(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSummary:
        return self._run(self._async.mark_read(mailbox_id, message_id))

    def delete(self, mailbox_id: int | Mailbox, message_id: str) -> None:
        return self._run(self._async.delete(mailbox_id, message_id))

    def source(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSource:
        """Raw message source (RFC 822 / MIME)."""
        return self._run(self._async.source(mailbox_id, message_id))

    def wait_for(
        self,
        mailbox_id: int | Mailbox,
        *,
        timeout: float = 120.0,
        interval: float = 2.0,
        predicate: Callable[[MessageSummary], bool] | None = None,
        mark_seen: bool = False,
    ) -> MessageSummary:
        """Poll the message list until a matching message arrives (defaults to any)."""
        return self._run(
            self._async.wait_for(
                mailbox_id,
                timeout=timeout,
                interval=interval,
                predicate=predicate,
                mark_seen=mark_seen,
            )
        )

    def wait_for_confirmation_email(
        self,
        mailbox_id: int | Mailbox,
        *,
        sender_domain: str | None = None,
        url_contain: builtins.list[str] | None = None,
        digit_code_mask: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 5.0,
    ) -> ExtractedConfirmation | None:
        """Wait for a confirmation email and extract confirmation link and/or code."""
        return self._run(
            self._async.wait_for_confirmation_email(
                mailbox_id,
                sender_domain=sender_domain,
                url_contain=url_contain,
                digit_code_mask=digit_code_mask,
                timeout=timeout,
                check_interval=check_interval,
            )
        )

    def wait_for_code(
        self,
        mailbox_id: int | Mailbox,
        *,
        pattern: str = r"\b(\d{4,8})\b",
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Wait for an email and return the digit confirmation code as a string."""
        return self._run(
            self._async.wait_for_code(
                mailbox_id,
                pattern=pattern,
                sender_domain=sender_domain,
                timeout=timeout,
                check_interval=check_interval,
            )
        )

    def wait_for_link(
        self,
        mailbox_id: int | Mailbox,
        *,
        url_contain: builtins.list[str] | None = None,
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Wait for an email and return the confirmation URL."""
        return self._run(
            self._async.wait_for_link(
                mailbox_id,
                url_contain=url_contain,
                sender_domain=sender_domain,
                timeout=timeout,
                check_interval=check_interval,
            )
        )

    def iter_messages(
        self,
        mailbox_id: int | Mailbox,
        *,
        poll_interval: float = 3.0,
        timeout: float | None = None,
    ) -> Iterator[MessageSummary]:
        """Continuously poll mailbox and yield new messages as they arrive."""
        mid = _mailbox_id_val(mailbox_id)
        seen_ids: set[str] = set()
        deadline = (time.monotonic() + timeout) if timeout is not None else None

        for m in self.list(mid):
            seen_ids.add(m.message_api_id)

        while True:
            if deadline is not None and time.monotonic() >= deadline:
                break
            for m in self.list(mid):
                if m.message_api_id not in seen_ids:
                    seen_ids.add(m.message_api_id)
                    yield m
            if deadline is not None and time.monotonic() + poll_interval >= deadline:
                break
            time.sleep(poll_interval)


class SyncGmailAPI:
    """OAuth flow and Gmail account management."""

    def __init__(self, async_api: GmailAPI, run: Callable[[Any], Any]) -> None:
        self._async = async_api
        self._run = run

    def oauth_start(self) -> OAuthStart:
        """OAuth authorization URL: open in browser to link any Google account."""
        return self._run(self._async.oauth_start())

    def import_account(
        self,
        *,
        refresh_token: str | None = None,
        token_json: Any = None,
    ) -> GmailAccount:
        """Import an existing token (refresh_token or token_json)."""
        return self._run(
            self._async.import_account(refresh_token=refresh_token, token_json=token_json)
        )

    def accounts(self) -> list[GmailAccount]:
        return self._run(self._async.accounts())

    def delete_account(self, parent_id: int) -> None:
        return self._run(self._async.delete_account(parent_id))

    def sync(self, parent_id: int) -> GmailAccount:
        """Sync account profile and send-as aliases."""
        return self._run(self._async.sync(parent_id))


class SyncKeysAPI:
    """API key management: list, create, view, rotate, delete."""

    def __init__(self, async_api: KeysAPI, run: Callable[[Any], Any]) -> None:
        self._async = async_api
        self._run = run

    def list(self) -> builtins.list[ApiKeyOut]:
        """Root only. List issued keys (without secrets)."""
        return self._run(self._async.list())

    def create(
        self,
        *,
        name: str,
        expires_at: str | None = None,
        scope: dict[str, Any] | None = None,
        retention: builtins.list[dict[str, Any]] | None = None,
    ) -> ApiKeyCreatedOut:
        """Root only. Create a key (secret returned once in creation response)."""
        return self._run(
            self._async.create(
                name=name,
                expires_at=expires_at,
                scope=scope,
                retention=retention,
            )
        )

    def get(self, key_id: int) -> ApiKeyOut:
        """Root only. Get key details by ID (without secret)."""
        return self._run(self._async.get(key_id))

    def me(self) -> ApiKeyMeOut:
        """Get current active key details (from X-API-Key header)."""
        return self._run(self._async.me())

    def secret(self, key_id: int) -> str:
        """Root only. Reveal key secret."""
        return self._run(self._async.secret(key_id))

    def update(
        self,
        key_id: int,
        *,
        name: str,
        expires_at: str | None = None,
        scope: dict[str, Any] | None = None,
    ) -> ApiKeyOut:
        """Root only. Update key name, expiration date, or scope."""
        return self._run(
            self._async.update(
                key_id,
                name=name,
                expires_at=expires_at,
                scope=scope,
            )
        )

    def retention_set(
        self, key_id: int, retention: builtins.list[dict[str, Any]]
    ) -> builtins.list[KeyRetentionOut]:
        """Root only. Set custom retention TTL rules for the key."""
        return self._run(self._async.retention_set(key_id, retention))

    def rotate(self, key_id: int) -> ApiKeyCreatedOut:
        """Root only. Rotate key secret (revokes old secret, returns new secret once)."""
        return self._run(self._async.rotate(key_id))

    def delete(self, key_id: int) -> None:
        """Root only. Delete key."""
        return self._run(self._async.delete(key_id))


class SyncAdminAPI:
    """Admin API: statistics, retention (TTL cleanup), domain cache, Gmail credentials, keys."""

    def __init__(self, async_api: AdminAPI, run: Callable[[Any], Any]) -> None:
        self._async = async_api
        self._run = run
        self.keys_api = SyncKeysAPI(async_api.keys_api, run)

    def stats(self) -> dict:
        """Statistics: mailboxes, messages, providers, and 7-day trend."""
        return self._run(self._async.stats())

    def retention_list(self) -> list[Retention]:
        return self._run(self._async.retention_list())

    def retention_set(
        self,
        provider: str,
        *,
        mailbox_ttl_hours: int | None = None,
        message_ttl_hours: int | None = None,
    ) -> Retention:
        """Enable or update retention TTL for a provider (at least one TTL required)."""
        return self._run(
            self._async.retention_set(
                provider,
                mailbox_ttl_hours=mailbox_ttl_hours,
                message_ttl_hours=message_ttl_hours,
            )
        )

    def retention_disable(self, provider: str) -> None:
        return self._run(self._async.retention_disable(provider))

    def retention_run(self, *, force_maintenance: bool = False) -> SweepResult:
        """Run cleanup now: sweep expired mailboxes and messages."""
        return self._run(self._async.retention_run(force_maintenance=force_maintenance))

    def domain_cache(self) -> DomainCache:
        """Current domain cache status (enabled, interval, providers)."""
        return self._run(self._async.domain_cache())

    def domain_cache_save(
        self,
        *,
        enabled: bool | None = None,
        interval_seconds: int | None = None,
    ) -> DomainCache:
        """Update domain cache settings (at least one parameter required)."""
        return self._run(
            self._async.domain_cache_save(
                enabled=enabled,
                interval_seconds=interval_seconds,
            )
        )

    def domain_cache_run(self) -> DomainCacheRun:
        """Force refresh domain cache now."""
        return self._run(self._async.domain_cache_run())

    def gmail_creds(self) -> GmailCreds:
        return self._run(self._async.gmail_creds())

    def gmail_creds_save(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None = None,
    ) -> GmailCreds:
        return self._run(
            self._async.gmail_creds_save(
                client_id,
                client_secret,
                redirect_uri=redirect_uri,
            )
        )

    def gmail_creds_clear(self) -> None:
        return self._run(self._async.gmail_creds_clear())

    def keys(self) -> list[dict[str, Any]]:
        """Root only. Lists keys; the secret is not in the response."""
        return self._run(self._async.keys())

    def key_create(
        self,
        *,
        name: str,
        expires_at: str | None,
        scope: dict[str, Any],
        retention: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Root only. Creates a key; the response includes the secret once."""
        return self._run(
            self._async.key_create(
                name=name,
                expires_at=expires_at,
                scope=scope,
                retention=retention,
            )
        )

    def key_get(self, key_id: int) -> dict[str, Any]:
        """Root only. Returns one key without the secret."""
        return self._run(self._async.key_get(key_id))

    def key_me(self) -> dict[str, Any]:
        """Any authenticated key. Root gets is_root; an issued key gets no secret."""
        return self._run(self._async.key_me())

    def key_secret(self, key_id: int) -> dict[str, Any]:
        """Root only. Reveals the secret."""
        return self._run(self._async.key_secret(key_id))

    def key_update(
        self,
        key_id: int,
        *,
        name: str,
        expires_at: str | None,
        scope: dict[str, Any],
    ) -> dict[str, Any]:
        """Root only. Updates name, expiry, and scope; the secret is unchanged."""
        return self._run(
            self._async.key_update(
                key_id,
                name=name,
                expires_at=expires_at,
                scope=scope,
            )
        )

    def key_retention_set(
        self, key_id: int, retention: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Root only. Replaces that key's retention rows."""
        return self._run(self._async.key_retention_set(key_id, retention))

    def key_rotate(self, key_id: int) -> dict[str, Any]:
        """Root only. Rotates the secret; the response includes the new secret once."""
        return self._run(self._async.key_rotate(key_id))

    def key_delete(self, key_id: int) -> None:
        """Root only. Deletes the key."""
        return self._run(self._async.key_delete(key_id))


# --------------------------------------------------------------------------- #
# Synchronous client facade
# --------------------------------------------------------------------------- #
class SyncMaily:
    """Synchronous client facade for maily.

    Runs a dedicated background daemon thread with a persistent asyncio event loop,
    allowing synchronous callers to execute all client operations safely without
    manual asyncio.run() or event loop closure issues.

    Example:
        with SyncMaily("http://127.0.0.1:8477", api_key="sk-...") as api:
            box = api.create_temp_mailbox()
            code = api.wait_for_code(box)
            print("Verification code:", code)

    Sections: .health, .config, .providers, .mailboxes, .messages, .gmail, .admin, .keys
    """

    health: SyncHealthAPI
    config: SyncConfigAPI
    providers: SyncProvidersAPI
    mailboxes: SyncMailboxesAPI
    messages: SyncMessagesAPI
    gmail: SyncGmailAPI
    admin: SyncAdminAPI
    keys: SyncKeysAPI

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8477",
        api_key: str = "",
        timeout: float = 30.0,
        *,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._loop = asyncio.new_event_loop()
        self._closed = False
        self._async_client: Maily | None = None

        ready = threading.Event()
        init_err: list[BaseException] = []

        def _run_loop() -> None:
            asyncio.set_event_loop(self._loop)
            try:
                try:
                    self._async_client = Maily(
                        base_url=base_url,
                        api_key=api_key,
                        timeout=timeout,
                        max_retries=max_retries,
                        retry_backoff=retry_backoff,
                        client=client,
                    )
                except BaseException as exc:
                    init_err.append(exc)
                    ready.set()
                    return

                self._loop.call_soon(ready.set)
                self._loop.run_forever()
            finally:
                with suppress(Exception):
                    pending = [t for t in asyncio.all_tasks(self._loop) if not t.done()]
                    for task in pending:
                        task.cancel()
                    if pending:
                        self._loop.run_until_complete(
                            asyncio.gather(*pending, return_exceptions=True)
                        )
                self._loop.close()

        self._thread = threading.Thread(target=_run_loop, name="SyncMaily-worker", daemon=True)
        self._thread.start()
        ready.wait()

        if init_err:
            self._closed = True
            if self._thread.is_alive():
                self._thread.join(timeout=5.0)
            raise init_err[0]

        assert self._async_client is not None
        self.health = SyncHealthAPI(self._async_client.health, self._run)
        self.config = SyncConfigAPI(self._async_client.config, self._run)
        self.providers = SyncProvidersAPI(self._async_client.providers, self._run)
        self.mailboxes = SyncMailboxesAPI(self._async_client.mailboxes, self._run)
        self.messages = SyncMessagesAPI(self._async_client.messages, self._run)
        self.gmail = SyncGmailAPI(self._async_client.gmail, self._run)
        self.admin = SyncAdminAPI(self._async_client.admin, self._run)
        self.keys = SyncKeysAPI(self._async_client.keys, self._run)

    @property
    def max_retries(self) -> int:
        """Client-side retry limit for transient network/server/rate-limit errors."""
        assert self._async_client is not None
        return self._async_client.max_retries

    @max_retries.setter
    def max_retries(self, value: int) -> None:
        if self._async_client:
            self._async_client.max_retries = max(0, int(value))

    @property
    def retry_backoff(self) -> float:
        """Base backoff in seconds for exponential retry backoff."""
        assert self._async_client is not None
        return self._async_client.retry_backoff

    @retry_backoff.setter
    def retry_backoff(self, value: float) -> None:
        if self._async_client:
            self._async_client.retry_backoff = max(0.0, float(value))

    def _run(self, coro: Any) -> Any:
        if self._closed or not self._loop.is_running():
            if asyncio.iscoroutine(coro):
                coro.close()
            raise ClientError("SyncMaily is closed")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def set_api_key(self, api_key: str) -> None:
        """Update API key dynamically."""
        if self._closed or not self._async_client:
            raise ClientError("SyncMaily is closed")
        self._async_client.set_api_key(api_key)

    def check_client_version(self) -> str:
        """Server version from /v1/config. Warns on version mismatch."""
        assert self._async_client is not None
        return self._run(self._async_client.check_client_version())

    def create_temp_mailbox(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
    ) -> Mailbox:
        """Convenience helper: create a temporary mailbox in one call."""
        assert self._async_client is not None
        return self._run(self._async_client.create_temp_mailbox(provider=provider, domain=domain))

    def wait_for_code(
        self,
        mailbox_id: int | Mailbox,
        *,
        pattern: str = r"\b(\d{4,8})\b",
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Poll mailbox until an email with a digit verification code arrives."""
        assert self._async_client is not None
        return self._run(
            self._async_client.wait_for_code(
                mailbox_id,
                pattern=pattern,
                sender_domain=sender_domain,
                timeout=timeout,
                check_interval=check_interval,
            )
        )

    def wait_for_link(
        self,
        mailbox_id: int | Mailbox,
        *,
        url_contain: builtins.list[str] | None = None,
        sender_domain: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 3.0,
    ) -> str:
        """Poll mailbox until an email with a confirmation link arrives."""
        assert self._async_client is not None
        return self._run(
            self._async_client.wait_for_link(
                mailbox_id,
                url_contain=url_contain,
                sender_domain=sender_domain,
                timeout=timeout,
                check_interval=check_interval,
            )
        )

    def wait_for_confirmation_email(
        self,
        mailbox_id: int | Mailbox,
        *,
        sender_domain: str | None = None,
        url_contain: builtins.list[str] | None = None,
        digit_code_mask: str | None = None,
        timeout: float = 60.0,
        check_interval: float = 5.0,
    ) -> ExtractedConfirmation | None:
        """Wait for a confirmation email and extract confirmation link and/or code."""
        assert self._async_client is not None
        return self._run(
            self._async_client.messages.wait_for_confirmation_email(
                mailbox_id,
                sender_domain=sender_domain,
                url_contain=url_contain,
                digit_code_mask=digit_code_mask,
                timeout=timeout,
                check_interval=check_interval,
            )
        )

    def close(self) -> None:
        """Close the synchronous client and terminate its background event loop thread."""
        if self._closed:
            return
        self._closed = True
        if self._async_client and self._loop.is_running():
            with suppress(Exception):
                future = asyncio.run_coroutine_threadsafe(self._async_client.close(), self._loop)
                future.result(timeout=10.0)
        if self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread.is_alive() and threading.current_thread() is not self._thread:
            self._thread.join(timeout=5.0)

    def __enter__(self) -> SyncMaily:
        return self

    def __exit__(self, *_exc: Any) -> None:
        self.close()

    def __del__(self) -> None:
        with suppress(Exception):
            self.close()

    # --- Synchronous SDK-compatible flat methods ---

    def create_mailbox(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
        parent_id: int | None = None,
        address: str | None = None,
        password: str | None = None,
    ) -> Mailbox:
        assert self._async_client is not None
        return self._run(
            self._async_client.create_mailbox(
                provider=provider,
                domain=domain,
                parent_id=parent_id,
                address=address,
                password=password,
            )
        )

    def list_mailboxes(
        self, provider: str | None = None, active: bool | None = None
    ) -> list[Mailbox]:
        assert self._async_client is not None
        return self._run(self._async_client.list_mailboxes(provider=provider, active=active))

    def mailbox(self, mailbox_id: int | Mailbox) -> Mailbox:
        assert self._async_client is not None
        return self._run(self._async_client.mailbox(mailbox_id))

    def mailbox_by_address(self, email: str) -> Mailbox:
        assert self._async_client is not None
        return self._run(self._async_client.mailbox_by_address(email))

    def delete_mailbox(self, mailbox_id: int | Mailbox) -> None:
        assert self._async_client is not None
        return self._run(self._async_client.delete_mailbox(mailbox_id))

    def list_messages(self, mailbox_id: int | Mailbox, page: int = 1) -> list[MessageSummary]:
        assert self._async_client is not None
        return self._run(self._async_client.list_messages(mailbox_id, page=page))

    def get_message(self, mailbox_id: int | Mailbox, message_id: str) -> MessageDetail:
        assert self._async_client is not None
        return self._run(self._async_client.get_message(mailbox_id, message_id))

    def mark_read(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSummary:
        assert self._async_client is not None
        return self._run(self._async_client.mark_read(mailbox_id, message_id))

    def delete_message(self, mailbox_id: int | Mailbox, message_id: str) -> None:
        assert self._async_client is not None
        return self._run(self._async_client.delete_message(mailbox_id, message_id))

    def get_source(self, mailbox_id: int | Mailbox, message_id: str) -> MessageSource:
        assert self._async_client is not None
        return self._run(self._async_client.get_source(mailbox_id, message_id))

    def gmail_oauth_start(self) -> OAuthStart:
        assert self._async_client is not None
        return self._run(self._async_client.gmail_oauth_start())

    def gmail_import_account(
        self, *, refresh_token: str | None = None, token_json: Any = None
    ) -> GmailAccount:
        assert self._async_client is not None
        return self._run(
            self._async_client.gmail_import_account(
                refresh_token=refresh_token, token_json=token_json
            )
        )

    def list_gmail_accounts(self) -> list[GmailAccount]:
        assert self._async_client is not None
        return self._run(self._async_client.list_gmail_accounts())

    def delete_gmail_account(self, parent_id: int) -> None:
        assert self._async_client is not None
        return self._run(self._async_client.delete_gmail_account(parent_id))

    def sync_gmail_account(self, parent_id: int) -> GmailAccount:
        assert self._async_client is not None
        return self._run(self._async_client.sync_gmail_account(parent_id))

    def domain_cache_settings(self) -> DomainCache:
        assert self._async_client is not None
        return self._run(self._async_client.domain_cache_settings())

    def save_domain_cache_settings(
        self, *, enabled: bool | None = None, interval_seconds: int | None = None
    ) -> DomainCache:
        assert self._async_client is not None
        return self._run(
            self._async_client.save_domain_cache_settings(
                enabled=enabled, interval_seconds=interval_seconds
            )
        )

    def refresh_domain_cache(self) -> DomainCacheRun:
        assert self._async_client is not None
        return self._run(self._async_client.refresh_domain_cache())

    def wait_for_message(
        self,
        mailbox_id: int | Mailbox,
        *,
        timeout: float = 120.0,
        interval: float = 2.0,
        predicate: Callable[[MessageSummary], bool] | None = None,
    ) -> MessageSummary:
        assert self._async_client is not None
        return self._run(
            self._async_client.wait_for_message(
                mailbox_id, timeout=timeout, interval=interval, predicate=predicate
            )
        )


# --------------------------------------------------------------------------- #
# CLI: python client.py check|update|version
# --------------------------------------------------------------------------- #
def _main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else list(argv)
    if not args or args[0] in ("-h", "--help", "help"):
        print(__doc__.split("\n\n")[1].strip(), file=sys.stderr)
        print(
            "\nusage:\n"
            "  maily-client version     - show version\n"
            "  maily-client check       - check git for a newer version\n"
            "  maily-client update      - update client file from git\n"
            "  (or: python client.py check/update)\n",
            file=sys.stderr,
        )
        return 0
    if args[0] == "version":
        print(__version__)
        return 0
    if args[0] == "check":
        try:
            result = check_update(args[1] if len(args) > 1 else None)
        except Exception as exc:
            print(f"check failed: {exc}", file=sys.stderr)
            return 1
        if result is None:
            print(f"client is up to date ({__version__})")
            return 0
        print(f"update available: {result[0]} -> {result[1]}")
        return 2
    if args[0] == "update":
        try:
            updated = self_update(args[1] if len(args) > 1 else None)
        except Exception as exc:
            print(f"update failed: {exc}", file=sys.stderr)
            return 1
        if not updated:
            print(f"client is up to date ({__version__})")
            return 0
        print("updated. Restart your scripts.")
        return 0
    print(f"unknown command: {args[0]}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(_main())
