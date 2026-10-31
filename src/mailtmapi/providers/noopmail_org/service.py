from __future__ import annotations

import base64
import logging
from typing import Any
from urllib.parse import quote

from ...exceptions import MailAPIError, MailNotFoundError, MailValidationError
from ...utils.misc import random_string
from ...utils.retry import async_retry
from ..base import (
    HttpProvider,
    MailboxInfo,
    MailboxSpec,
    MessageDetail,
    MessageSource,
    MessageSummary,
    Party,
    ProviderCapabilities,
    Target,
    TargetKind,
    parse_from_value,
    parse_iso,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = 600.0
_RD_MAX_ITERATIONS = 100  # upper limit of attempts to collect all domains
_RD_STOP_AFTER = 15  # stop after N consecutive calls returning an already known domain
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0",
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Referer": "https://noopmail.org/",
    "Origin": "https://noopmail.org",
}


def _summary(raw: dict[str, Any]) -> MessageSummary:
    text = str(raw.get("text") or "")
    html = str(raw.get("html") or "")
    return MessageSummary(
        id=str(raw.get("id") or ""),
        subject=str(raw.get("subject") or ""),
        from_=parse_from_value(str(raw.get("from") or "")),
        to=[Party(address=str(raw.get("to") or ""))],
        intro=text.split("\n", 1)[0][:200] if text else "",
        seen=False,
        has_attachments=bool(raw.get("hasAttm")),
        size=len(text) + len(html),
        received_at=parse_iso(raw.get("date")),
    )


def _detail(raw: dict[str, Any]) -> MessageDetail:
    s = _summary(raw)
    body_text = str(raw.get("text") or "")
    body_html = str(raw.get("html") or "")
    return MessageDetail(
        id=s.id,
        subject=s.subject,
        from_=s.from_,
        to=s.to,
        intro=s.intro,
        seen=s.seen,
        has_attachments=bool(raw.get("hasAttm")),
        size=len(body_text) + len(body_html),
        received_at=s.received_at,
        text=body_text,
        html=[body_html] if body_html else [],
        attachments=[],
    )


class NoopMail(HttpProvider):
    """noopmail.org provider.

    noopmail.org is protected by Cloudflare; live requests require cf_clearance cookies
    (obtain them in a browser and pass via HttpClient/proxy settings).
    If the API responds with 403/Cloudflare challenge, it is due to a missing or expired
    cf_clearance.
    """

    slug = "noopmail.org"
    kind: TargetKind = "domain"
    cache_ttl = _CACHE_TTL
    default_headers = _HEADERS
    BASE_URL = "https://noopmail.org"
    capabilities = ProviderCapabilities(
        can_choose_username=True,
        can_choose_domain=True,
        can_set_password=False,
        supports_delete_mailbox=False,
        supports_delete_message=True,
        supports_mark_read=False,
        supports_source=True,
        supports_attachments=False,
    )

    async def _fetch_targets(self, *, known: set[str] | None = None) -> list[Target]:
        seen: set[str] = set(known or ())
        dupes = 0
        # /api/rd returns ONE random domain per call. Keep pulling until 15
        # calls in a row are domains we already have — that is the full set.
        # `known` is the previous cache: without it a refresh that already
        # holds every domain stops on the first duplicate and writes nothing new.
        for _ in range(_RD_MAX_ITERATIONS):
            data = await self._get_json(f"{self.BASE_URL}/api/rd")
            if not isinstance(data, dict) or not data.get("dm"):
                continue
            dm = str(data["dm"])
            if dm in seen:
                dupes += 1
                if dupes >= _RD_STOP_AFTER:
                    break
                continue
            seen.add(dm)
            dupes = 0
        if not seen:
            raise MailAPIError("noopmail.org: could not collect any domains from /api/rd")
        return [Target(id=dm, kind="domain", provider=self.slug, label=dm) for dm in sorted(seen)]

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        address = spec.address
        if not address:
            domain = spec.domain
            if not domain:
                targets = await self.list_targets()
                if not targets:
                    raise MailValidationError("noopmail.org: no domains available", status_code=400)
                domain = targets[0].label
            address = f"{random_string(10)}@{domain}"
        # noopmail has no mailbox creation endpoint — the address simply starts
        # existing. There is also no api-token, hence token="".
        return MailboxInfo(
            provider=self.slug,
            address=address,
            token="",
            provider_account_id=address,
            password=spec.password,
        )

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        # noopmail has no mailbox deletion endpoint — no-op.
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        local, _, domain = mailbox.address.partition("@")
        data = await self._post_json(f"{self.BASE_URL}/api/c", body={"e": local, "d": domain})
        if not isinstance(data, list):
            return []
        return [_summary(m) for m in data if isinstance(m, dict)]

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        data = await self._get_json(f"{self.BASE_URL}/api/i/{quote(message_id, safe='')}")
        if not isinstance(data, dict) or not data.get("id"):
            raise MailNotFoundError(
                f"noopmail.org: message {message_id!r} not found",
                status_code=404,
            )
        return _detail(data)

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        # Deletion endpoint requires id and m_id: /api/i/{id}/{m_id}.
        # List and delete use different identifiers, so m_id is retrieved from detail.
        try:
            data = await self._get_json(f"{self.BASE_URL}/api/i/{quote(message_id, safe='')}")
            m_id = data.get("m_id") if isinstance(data, dict) else None
            url = f"{self.BASE_URL}/api/i/{quote(message_id, safe='')}"
            if m_id:
                url += f"/{quote(str(m_id), safe='')}"
            await self._http.delete(url, headers=self._headers())
        except MailNotFoundError:
            pass
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        # noopmail has no "read" flag — no-op.
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        data = await self._get_json(f"{self.BASE_URL}/api/i/{quote(message_id, safe='')}")
        if not isinstance(data, dict) or not data.get("id"):
            raise MailNotFoundError(
                f"noopmail.org: message {message_id!r} not found",
                status_code=404,
            )
        m_id = data.get("m_id")
        if not m_id:
            raise MailNotFoundError(
                f"noopmail.org: raw source for message {message_id!r} not found",
                status_code=404,
            )
        raw = await self._get_raw(f"{self.BASE_URL}/raw/{quote(str(m_id), safe='')}")
        return MessageSource(id=message_id, data=raw, download_url="")

    @async_retry()
    async def _get_raw(self, url: str) -> str:
        resp = await self._http.get(url, headers=self._headers())
        try:
            payload = resp.json()
        except ValueError:
            payload = resp.text
        if isinstance(payload, dict):
            payload = payload.get("data") or ""
        # Unwrap base64 if valid; otherwise return as is.
        if isinstance(payload, str):
            try:
                return base64.b64decode(payload).decode("utf-8")
            except Exception:
                return payload
        return str(payload)
