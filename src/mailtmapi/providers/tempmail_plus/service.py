from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from ...exceptions import MailAPIError, MailNotFoundError, MailValidationError
from ...http import HttpClient
from ...utils.misc import random_string
from ...utils.retry import async_retry
from ..base import (
    Attachment,
    HttpProvider,
    MailboxInfo,
    MailboxSpec,
    MessageDetail,
    MessageSource,
    MessageSummary,
    Party,
    Target,
    TargetKind,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = 600.0
_HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://tempmail.plus/",
    "X-Requested-With": "XMLHttpRequest",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
}

_DOMAIN_RE = re.compile(
    r'class=["\'][^"\']*dropdown-item[^"\']*["\'][^>]*>@?([\w.-]+\.[a-z]{2,})',
    re.IGNORECASE,
)
_DOMAIN_FALLBACK_RE = re.compile(r"@([\w-]+\.[\w.]{2,})")


def _parse_domains_from_html(html: str) -> list[str]:
    domains: list[str] = []
    for m in _DOMAIN_RE.finditer(html):
        d = m.group(1).strip().lower()
        if d and d not in domains:
            domains.append(d)
    if domains:
        return domains
    seen: set[str] = set()
    for m in _DOMAIN_FALLBACK_RE.finditer(html):
        d = m.group(1).strip().lower()
        if d not in seen and "tempmail" not in d and "example" not in d:
            seen.add(d)
            domains.append(d)
    return domains


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None


def _summary(raw: dict[str, Any], address: str) -> MessageSummary:
    return MessageSummary(
        id=str(raw.get("mail_id") or ""),
        subject=str(raw.get("subject") or ""),
        from_=Party(name=str(raw.get("from_name") or ""), address=str(raw.get("from_mail") or "")),
        to=[Party(address=address)],
        intro="",
        seen=not raw.get("is_new", True),
        has_attachments=bool(raw.get("attachments")),
        size=int(raw.get("mail_size") or 0),
        received_at=_parse_date(raw.get("date")),
    )


def _detail(raw: dict[str, Any], address: str) -> MessageDetail:
    html_body = str(raw.get("html") or "")
    text_body = str(raw.get("text") or "")
    attachments: list[Attachment] = []
    for a in raw.get("attachments") or []:
        if not isinstance(a, dict):
            continue
        attachments.append(
            Attachment(
                id=str(a.get("id") or ""),
                filename=str(a.get("name") or ""),
                content_type=str(a.get("content_type") or ""),
                size=int(a.get("size") or 0),
                download_url=str(a.get("url") or ""),
            )
        )
    s = _summary(raw, address)
    return MessageDetail(
        id=s.id,
        subject=s.subject,
        from_=s.from_,
        to=s.to,
        intro=s.intro,
        seen=s.seen,
        has_attachments=bool(attachments) or s.has_attachments,
        size=int(raw.get("mail_size") or (len(html_body) + len(text_body))),
        received_at=s.received_at,
        text=text_body,
        html=[html_body] if html_body else [],
        attachments=attachments,
    )


class TempMailPlus(HttpProvider):
    slug = "tempmail.plus"
    kind: TargetKind = "domain"
    cache_ttl = _CACHE_TTL
    default_headers = _HEADERS
    BASE_URL = "https://tempmail.plus"
    API_URL = "https://tempmail.plus/api"

    def __init__(
        self,
        http: HttpClient | None = None,
        proxy: str | None = None,
        epin: str = "",
    ) -> None:
        super().__init__(http=http, proxy=proxy)
        self._epin = epin

    def _params(self, email: str, **extra: Any) -> dict[str, Any]:
        return {"email": email, "epin": self._epin, **extra}

    @async_retry()
    async def _get_json(self, url: str, params: dict[str, Any] | None = None) -> dict:
        return (await self._http.get(url, params=params, headers=self._headers())).json()

    async def _fetch_targets(self) -> list[Target]:
        resp = await self._http.get(
            f"{self.BASE_URL}/en/",
            headers={**self._headers(), "Accept": "text/html,application/xhtml+xml", "X-Requested-With": ""},
        )
        domains = _parse_domains_from_html(resp.text)
        if not domains:
            raise MailAPIError("tempmail.plus: could not parse any domains from HTML")
        return [Target(id=d, kind="domain", provider=self.slug, label=d) for d in domains]

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        address = spec.address
        if not address:
            domain = spec.domain
            if not domain:
                targets = await self.list_targets()
                if not targets:
                    raise MailValidationError("tempmail.plus: no domains available")
                domain = targets[0].label
            address = f"{random_string(10)}@{domain}"
        data = await self._get_json(f"{self.API_URL}/mails", params=self._params(address, limit=1))
        if "err" in data:
            err = data["err"]
            msg = err.get("msg", err) if isinstance(err, dict) else err
            raise MailValidationError(
                f"tempmail.plus rejected address {address!r}: {msg}",
                status_code=400,
            )
        return MailboxInfo(
            provider=self.slug,
            address=address,
            token=address,
            provider_account_id=address,
            password=spec.password,
        )

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        try:
            seen: set[str] = set()
            for _ in range(20):
                messages = await self.list_messages(mailbox, page=1)
                ids = [m.id for m in messages if m.id not in seen]
                if not ids:
                    break
                for msg_id in ids:
                    seen.add(msg_id)
                    await self.delete_message(mailbox, msg_id)
            else:
                logger.warning("tempmail.plus: inbox clear hit page cap for %s", mailbox.address)
        except Exception as exc:
            logger.warning("tempmail.plus: failed to clear inbox on account deletion: %s", exc)
            return False
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        limit = 20
        data = await self._get_json(
            f"{self.API_URL}/mails",
            params=self._params(mailbox.token, limit=limit, offset=(page - 1) * limit),
        )
        if "err" in data:
            raise MailAPIError(f"tempmail.plus get_messages error: {data['err']}", status_code=400)
        return [_summary(m, mailbox.address) for m in data.get("mail_list") or [] if isinstance(m, dict)]

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        data = await self._get_json(
            f"{self.API_URL}/mails/{message_id}",
            params=self._params(mailbox.token),
        )
        if "err" in data or "mail_id" not in data:
            raise MailNotFoundError(
                f"tempmail.plus: message {message_id!r} not found",
                status_code=404,
                response_data=data if isinstance(data, dict) else {},
            )
        return _detail(data, mailbox.address)

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        data = await self._delete_json(
            f"{self.API_URL}/mails/{message_id}",
            data=self._params(mailbox.token),
        )
        return bool(data.get("result", False))

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        detail = await self.get_message(mailbox, message_id)
        return MessageSource(
            id=message_id,
            data="\n".join(detail.html) if detail.html else detail.text,
            download_url=f"{self.API_URL}/mails/{message_id}?email={mailbox.token}&epin={self._epin}",
        )
