from __future__ import annotations

import asyncio
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal, Protocol, runtime_checkable
from urllib.parse import urlencode

from ..http import HttpClient
from ..utils.retry import async_retry

TargetKind = Literal["domain", "parent"]

_FROM_RE = re.compile(r"<([^>]+)>")


def parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def parse_from_value(value: str) -> Party:
    m = _FROM_RE.search(value)
    if not m:
        return Party(address=value, name=None)
    name = value[: m.start()].strip().strip('"').strip().strip("'").strip()
    return Party(name=name or None, address=m.group(1).strip())


@dataclass
class Target:
    id: str
    kind: TargetKind
    provider: str
    label: str  # domain hostname or parent email
    owner_key_id: int | None = None  # Gmail parent owner; None is root


@dataclass
class MailboxSpec:
    address: str | None = None
    domain: str | None = None
    parent_id: int | None = None
    password: str | None = None
    # None: root / unfiltered auto-pick. () denies every parent. A tuple limits auto-pick.
    allowed_parent_ids: tuple[int, ...] | None = None


@dataclass
class MailboxInfo:
    provider: str
    address: str
    token: str
    provider_account_id: str | None = None
    password: str | None = None
    parent_id: int | None = None


@dataclass
class Party:
    name: str | None = ""
    address: str = ""


@dataclass
class Attachment:
    id: str = ""
    filename: str = ""
    content_type: str = ""
    size: int = 0
    download_url: str = ""


@dataclass
class MessageSummary:
    id: str
    subject: str = ""
    from_: Party = field(default_factory=Party)
    to: list[Party] = field(default_factory=list)
    intro: str = ""
    seen: bool = False
    has_attachments: bool = False
    size: int = 0
    received_at: datetime | None = None


@dataclass
class MessageDetail(MessageSummary):
    text: str = ""
    html: list[str] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)


@dataclass
class MessageSource:
    id: str
    data: str
    download_url: str = ""


@runtime_checkable
class MailProvider(Protocol):
    slug: str
    kind: TargetKind

    async def close(self) -> None: ...

    async def list_targets(self, *, fresh: bool = False) -> list[Target]: ...

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo: ...

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool: ...

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]: ...

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail: ...

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool: ...

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool: ...

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource: ...


class HttpProvider:
    """Shared scaffolding for HTTP provider adapters: HttpClient ownership,
    double-checked-lock target cache, and JSON/HTML fetch helpers."""

    slug: str = ""
    kind: TargetKind = "domain"
    cache_ttl: float = 300.0
    default_headers: dict[str, str] | None = None

    def __init__(
        self,
        http: HttpClient | None = None,
        proxy: str | None = None,
    ) -> None:
        self._owns_http = http is None
        self._http = http or HttpClient(proxy=proxy, headers=self.default_headers)
        self._targets: list[Target] = []
        self._targets_at = 0.0
        self._lock = asyncio.Lock()

    def _headers(self) -> dict[str, str]:
        return dict(self.default_headers or {})

    async def close(self) -> None:
        if self._owns_http:
            await self._http.close()

    async def list_targets(self, *, fresh: bool = False) -> list[Target]:
        now = time.monotonic()
        if not fresh and self._targets and now - self._targets_at < self.cache_ttl:
            return list(self._targets)
        async with self._lock:
            if not fresh and self._targets and time.monotonic() - self._targets_at < self.cache_ttl:
                return list(self._targets)
            # `known` is the previous in-memory list. noopmail uses it so a
            # random /api/rd refresh doesn't stop on the first already-seen
            # domain; full-list providers ignore it.
            known = {t.label for t in self._targets} if fresh and self._targets else None
            targets = await self._fetch_targets(known=known)
            self._targets = targets
            self._targets_at = time.monotonic()
            return list(targets)

    async def _fetch_targets(self, *, known: set[str] | None = None) -> list[Target]:
        raise NotImplementedError

    @async_retry()
    async def _get_json(self, url: str, params: dict[str, Any] | None = None) -> Any:
        resp = await self._http.get(url, params=params, headers=self._headers())
        try:
            return resp.json()
        except ValueError:
            return None

    @async_retry()
    async def _post_json(self, url: str, body: dict[str, Any]) -> Any:
        resp = await self._http.post(url, json=body, headers=self._headers())
        try:
            return resp.json()
        except ValueError:
            return None

    @async_retry()
    async def _delete_json(self, url: str, data: dict[str, Any] | None = None) -> dict:
        headers = self._headers()
        content = None
        if data:
            content = urlencode(data)
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        resp = await self._http.delete(
            url,
            content=content.encode() if content else None,
            headers=headers,
        )
        try:
            body = resp.json()
        except Exception:
            return {}
        return body if isinstance(body, dict) else {}
