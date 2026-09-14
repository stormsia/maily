from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import Any

from ...exceptions import MailValidationError
from ...http import HttpClient
from ...utils.misc import random_password, random_string
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

_CACHE_TTL = 300.0


def _party(raw: Any) -> Party:
    if not isinstance(raw, dict):
        return Party()
    return Party(name=str(raw.get("name") or ""), address=str(raw.get("address") or ""))


def _parties(raw: Any) -> list[Party]:
    if not isinstance(raw, list):
        return []
    return [_party(p) for p in raw]


def _parse_iso(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _summary(raw: dict[str, Any]) -> MessageSummary:
    return MessageSummary(
        id=str(raw.get("id") or ""),
        subject=str(raw.get("subject") or ""),
        from_=_party(raw.get("from")),
        to=_parties(raw.get("to")),
        intro=str(raw.get("intro") or ""),
        seen=bool(raw.get("seen")),
        has_attachments=bool(raw.get("hasAttachments")),
        size=int(raw.get("size") or 0),
        received_at=_parse_iso(raw.get("createdAt")),
    )


def _detail(raw: dict[str, Any]) -> MessageDetail:
    html = raw.get("html") or []
    if isinstance(html, str):
        html = [html]
    attachments: list[Attachment] = []
    for a in raw.get("attachments") or []:
        if not isinstance(a, dict):
            continue
        attachments.append(
            Attachment(
                id=str(a.get("id") or ""),
                filename=str(a.get("filename") or ""),
                content_type=str(a.get("contentType") or ""),
                size=int(a.get("size") or 0),
                download_url=str(a.get("downloadUrl") or ""),
            )
        )
    s = _summary(raw)
    return MessageDetail(
        id=s.id,
        subject=s.subject,
        from_=s.from_,
        to=s.to,
        intro=s.intro,
        seen=s.seen,
        has_attachments=s.has_attachments,
        size=s.size,
        received_at=s.received_at,
        text=str(raw.get("text") or ""),
        html=list(html),
        attachments=attachments,
    )


class MailTM:
    slug = "mail.tm"
    kind = "domain"
    API_URL = "https://api.mail.tm"

    def __init__(self, http: HttpClient | None = None, proxy: str | None = None) -> None:
        self._owns_http = http is None
        self._http = http or HttpClient(proxy=proxy)
        self._targets: list[Target] = []
        self._targets_at = 0.0
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        if self._owns_http:
            await self._http.close()

    def _auth(self, mailbox: MailboxInfo) -> dict[str, str]:
        return {"Authorization": f"Bearer {mailbox.token}"}

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
        data = (await self._http.get(f"{self.API_URL}/domains")).json()
        targets: list[Target] = []
        for m in data.get("hydra:member") or []:
            domain = str(m.get("domain") or "")
            if not domain or m.get("isActive") is False:
                continue
            targets.append(Target(id=domain, kind="domain", provider=self.slug, label=domain))
        return targets

    @async_retry()
    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        address = spec.address
        if not address:
            domain = spec.domain
            if not domain:
                targets = await self.list_targets()
                if not targets:
                    raise MailValidationError("mail.tm: no domains available")
                domain = targets[0].label
            address = f"{random_string(10)}@{domain}"
        password = spec.password or random_password()
        account = (
            await self._http.post(
                f"{self.API_URL}/accounts",
                json={"address": address, "password": password},
            )
        ).json()
        token = (
            await self._http.post(
                f"{self.API_URL}/token",
                json={"address": address, "password": password},
            )
        ).json()
        return MailboxInfo(
            provider=self.slug,
            address=address,
            token=str(token["token"]),
            provider_account_id=str(account["id"]),
            password=password,
        )

    @async_retry()
    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        account_id = mailbox.provider_account_id
        if not account_id:
            return False
        resp = await self._http.delete(
            f"{self.API_URL}/accounts/{account_id}",
            headers=self._auth(mailbox),
        )
        return resp.status_code == 204

    @async_retry()
    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        data = (
            await self._http.get(
                f"{self.API_URL}/messages",
                params={"page": page},
                headers=self._auth(mailbox),
            )
        ).json()
        return [_summary(m) for m in data.get("hydra:member") or [] if isinstance(m, dict)]

    @async_retry()
    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        data = (
            await self._http.get(
                f"{self.API_URL}/messages/{message_id}",
                headers=self._auth(mailbox),
            )
        ).json()
        return _detail(data)

    @async_retry()
    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        resp = await self._http.delete(
            f"{self.API_URL}/messages/{message_id}",
            headers=self._auth(mailbox),
        )
        return resp.status_code == 204

    @async_retry()
    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        data = (
            await self._http.patch(
                f"{self.API_URL}/messages/{message_id}",
                headers={**self._auth(mailbox), "Content-Type": "application/merge-patch+json"},
                json={"seen": True},
            )
        ).json()
        return data.get("seen") is True

    @async_retry()
    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        data = (
            await self._http.get(
                f"{self.API_URL}/sources/{message_id}",
                headers=self._auth(mailbox),
            )
        ).json()
        return MessageSource(
            id=str(data.get("id") or message_id),
            data=str(data.get("data") or ""),
            download_url=str(data.get("downloadUrl") or ""),
        )
