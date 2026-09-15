from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime
from typing import Any
from urllib.parse import quote

from ...exceptions import MailAPIError, MailNotFoundError, MailValidationError
from ...http import HttpClient
from ...utils.misc import random_string
from ...utils.retry import async_retry
from ..base import (
    Attachment,
    MailboxInfo,
    MailboxSpec,
    MessageDetail,
    MessageSource,
    MessageSummary,
    Party,
    Target,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = 600.0
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0",
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Application-Name": "web",
    "Application-Version": "4.0.0",
    "X-CORS-Header": "iaWg3pchvFx48fY",
    "Referer": "https://temp-mail.io/",
    "Origin": "https://temp-mail.io",
}

_FROM_RE = re.compile(r"<([^>]+)>")


def _parse_from(value: str) -> Party:
    m = _FROM_RE.search(value)
    if not m:
        return Party(address=value, name=None)
    name = value[: m.start()].strip().strip('"').strip().strip("'").strip()
    return Party(name=name or None, address=m.group(1).strip())


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


def _summary(raw: dict[str, Any]) -> MessageSummary:
    body_text = str(raw.get("body_text") or "")
    body_html = str(raw.get("body_html") or "")
    return MessageSummary(
        id=str(raw.get("id") or ""),
        subject=str(raw.get("subject") or ""),
        from_=_parse_from(str(raw.get("from") or "")),
        to=[Party(address=str(raw.get("to") or ""))],
        intro=body_text.split("\n", 1)[0][:200] if body_text else "",
        seen=False,
        has_attachments=bool(raw.get("attachments")),
        size=len(body_text) + len(body_html),
        received_at=_parse_iso(raw.get("created_at")),
    )


def _detail(raw: dict[str, Any]) -> MessageDetail:
    s = _summary(raw)
    body_text = str(raw.get("body_text") or "")
    body_html = str(raw.get("body_html") or "")
    attachments: list[Attachment] = []
    for i, a in enumerate(raw.get("attachments") or []):
        if not isinstance(a, dict):
            continue
        attachments.append(
            Attachment(
                id=str(a.get("id") or i),
                filename=str(a.get("filename") or ""),
                content_type=str(a.get("content_type") or ""),
                size=int(a.get("size") or 0),
                download_url=None,
            )
        )
    return MessageDetail(
        id=s.id,
        subject=s.subject,
        from_=s.from_,
        to=s.to,
        intro=s.intro,
        seen=s.seen,
        has_attachments=bool(attachments) or s.has_attachments,
        size=s.size,
        received_at=s.received_at,
        text=body_text,
        html=[body_html] if body_html else [],
        attachments=attachments,
    )


class TempMailIO:
    slug = "temp-mail.io"
    kind = "domain"
    BASE_URL = "https://api.internal.temp-mail.io"

    def __init__(
        self,
        http: HttpClient | None = None,
        proxy: str | None = None,
    ) -> None:
        self._owns_http = http is None
        self._http = http or HttpClient(proxy=proxy, headers=_HEADERS)
        self._targets: list[Target] = []
        self._targets_at = 0.0
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        if self._owns_http:
            await self._http.close()

    @async_retry()
    async def _get_json(self, url: str) -> Any:
        resp = await self._http.get(url, headers=_HEADERS)
        try:
            return resp.json()
        except ValueError:
            return None

    @async_retry()
    async def _post_json(self, url: str, body: dict[str, Any]) -> Any:
        resp = await self._http.post(url, json=body, headers=_HEADERS)
        try:
            return resp.json()
        except ValueError:
            return None

    async def list_targets(self) -> list[Target]:
        now = time.monotonic()
        if self._targets and now - self._targets_at < _CACHE_TTL:
            return list(self._targets)
        async with self._lock:
            if self._targets and time.monotonic() - self._targets_at < _CACHE_TTL:
                return list(self._targets)
            targets = await self._fetch_targets()
            self._targets = targets
            self._targets_at = time.monotonic()
            return list(targets)

    @async_retry()
    async def _fetch_targets(self) -> list[Target]:
        data = await self._get_json(f"{self.BASE_URL}/api/v4/domains")
        domains = data.get("domains") if isinstance(data, dict) else None
        if not domains:
            raise MailAPIError("temp-mail.io: could not parse domains from response")
        return [
            Target(id=d["name"], kind="domain", provider=self.slug, label=d["name"])
            for d in domains
            if isinstance(d, dict) and d.get("name")
        ]

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        if spec.address:
            name, sep, domain = spec.address.partition("@")
            if not sep or not domain:
                raise MailValidationError(
                    f"temp-mail.io: address {spec.address!r} is not name@domain",
                    status_code=400,
                )
        else:
            name = random_string(10)
            domain = spec.domain
            if not domain:
                targets = await self.list_targets()
                if not targets:
                    raise MailValidationError("temp-mail.io: no domains available", status_code=400)
                domain = targets[0].label
        data = await self._post_json(
            f"{self.BASE_URL}/api/v3/email/new",
            body={"name": name, "domain": domain},
        )
        if not isinstance(data, dict) or not data.get("token"):
            raise MailValidationError(
                "temp-mail.io: failed to create mailbox (no token in response)",
                status_code=400,
            )
        address = str(data.get("email") or "") or f"{name}@{domain}"
        return MailboxInfo(
            provider=self.slug,
            address=address,
            token=str(data["token"]),
            provider_account_id=address,
            password=spec.password,
        )

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        email = quote(mailbox.address, safe="@")
        try:
            await self._http.delete(
                f"{self.BASE_URL}/api/v3/email/{email}",
                json={"token": mailbox.token},
                headers=_HEADERS,
            )
        except MailNotFoundError:
            pass
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        email = quote(mailbox.address, safe="@")
        data = await self._get_json(f"{self.BASE_URL}/api/v3/email/{email}/messages")
        if not isinstance(data, list):
            return []
        return [_summary(m) for m in data if isinstance(m, dict)]

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        data = await self._get_json(f"{self.BASE_URL}/api/v3/message/{message_id}")
        if not isinstance(data, dict) or not data.get("id"):
            raise MailNotFoundError(
                f"temp-mail.io: message {message_id!r} not found",
                status_code=404,
            )
        return _detail(data)

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        try:
            await self._http.delete(
                f"{self.BASE_URL}/api/v3/message/{message_id}",
                json={"token": mailbox.token},
                headers=_HEADERS,
            )
        except MailNotFoundError:
            pass
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        data = await self._get_json(
            f"{self.BASE_URL}/api/v3/message/{message_id}/source_code"
        )
        if not isinstance(data, dict) or "data" not in data:
            raise MailNotFoundError(
                f"temp-mail.io: source for message {message_id!r} not found",
                status_code=404,
            )
        return MessageSource(id=message_id, data=str(data["data"]), download_url=None)