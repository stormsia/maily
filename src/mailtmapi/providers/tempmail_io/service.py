from __future__ import annotations

from typing import Any
from urllib.parse import quote

from ...exceptions import MailAPIError, MailNotFoundError, MailValidationError
from ...http import HttpClient
from ...utils.misc import random_string
from ..base import (
    Attachment,
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

_CACHE_TTL = 600.0
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:155.0) Gecko/20100101 Firefox/155.0",
    "Accept": "*/*",
    "Content-Type": "application/json",
    "Application-Name": "web",
    "Application-Version": "4.0.0",
    "Referer": "https://temp-mail.io/",
    "Origin": "https://temp-mail.io",
}


def _summary(raw: dict[str, Any]) -> MessageSummary:
    body_text = str(raw.get("body_text") or "")
    body_html = str(raw.get("body_html") or "")
    return MessageSummary(
        id=str(raw.get("id") or ""),
        subject=str(raw.get("subject") or ""),
        from_=parse_from_value(str(raw.get("from") or "")),
        to=[Party(address=str(raw.get("to") or ""))],
        intro=body_text.split("\n", 1)[0][:200] if body_text else "",
        seen=False,
        has_attachments=bool(raw.get("attachments")),
        size=len(body_text) + len(body_html),
        received_at=parse_iso(raw.get("created_at")),
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
                download_url="",
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


class TempMailIO(HttpProvider):
    slug = "temp-mail.io"
    name = "TempMail.io"
    website = "https://temp-mail.io"
    kind: TargetKind = "domain"
    cache_ttl = _CACHE_TTL
    default_headers = _HEADERS
    BASE_URL = "https://api.internal.temp-mail.io"
    capabilities = ProviderCapabilities(
        can_choose_username=True,
        can_choose_domain=True,
        can_set_password=False,
        supports_delete_mailbox=True,
        supports_delete_message=True,
        supports_mark_read=False,
        supports_source=True,
        supports_attachments=True,
    )

    def __init__(
        self,
        http: HttpClient | None = None,
        proxy: str | None = None,
    ) -> None:
        super().__init__(http=http, proxy=proxy)
        self._cors_token = ""

    def set_headers(self, headers: dict[str, str]) -> None:
        self._cors_token = headers.get("X-CORS-Header") or ""

    def _headers(self) -> dict[str, str]:
        headers = dict(self.default_headers)
        if self._cors_token:
            headers["X-CORS-Header"] = self._cors_token
        return headers

    async def _fetch_targets(self, *, known: set[str] | None = None) -> list[Target]:
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
        address = spec.address
        if not address:
            domain = spec.domain
            if not domain:
                targets = await self.list_targets()
                if not targets:
                    raise MailValidationError("temp-mail.io: no domains available", status_code=400)
                domain = targets[0].label
            address = f"{random_string(10)}@{domain}"
        name, sep, domain = address.partition("@")
        if not sep or not domain:
            raise MailValidationError(
                f"temp-mail.io: address {address!r} is not name@domain",
                status_code=400,
            )
        data = await self._post_json(
            f"{self.BASE_URL}/api/v3/email/new",
            body={"name": name, "domain": domain},
        )
        if not isinstance(data, dict) or not data.get("token"):
            raise MailValidationError(
                "temp-mail.io: failed to create mailbox (no token in response)",
                status_code=400,
            )
        address = str(data.get("email") or "") or address
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
                headers=self._headers(),
            )
        except MailNotFoundError:
            pass
        except MailAPIError as exc:
            if "not exist" in str(exc).lower() or "not found" in str(exc).lower():
                pass
            else:
                raise
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        email = quote(mailbox.address, safe="@")
        data = await self._get_json(f"{self.BASE_URL}/api/v3/email/{email}/messages")
        if not isinstance(data, list):
            return []
        return [_summary(m) for m in data if isinstance(m, dict)]

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        data = await self._get_json(f"{self.BASE_URL}/api/v3/message/{quote(message_id, safe='')}")
        if not isinstance(data, dict) or not data.get("id"):
            raise MailNotFoundError(
                f"temp-mail.io: message {message_id!r} not found",
                status_code=404,
            )
        return _detail(data)

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        try:
            await self._http.delete(
                f"{self.BASE_URL}/api/v3/message/{quote(message_id, safe='')}",
                json={"token": mailbox.token},
                headers=self._headers(),
            )
        except MailNotFoundError:
            pass
        except MailAPIError as exc:
            if "not exist" in str(exc).lower() or "not found" in str(exc).lower():
                pass
            else:
                raise
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        data = await self._get_json(
            f"{self.BASE_URL}/api/v3/message/{quote(message_id, safe='')}/source_code"
        )
        if not isinstance(data, dict) or "data" not in data:
            raise MailNotFoundError(
                f"temp-mail.io: source for message {message_id!r} not found",
                status_code=404,
            )
        return MessageSource(id=message_id, data=str(data["data"]), download_url="")
