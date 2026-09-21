from __future__ import annotations

import base64
import logging
from typing import Any

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
    Target,
    TargetKind,
    parse_from_value,
    parse_iso,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = 600.0
_RD_MAX_ITERATIONS = 100  # верхний предел попыток собрать все домены
_RD_STOP_AFTER = 15  # стоп после N подряд вызовов, вернувших уже известный домен
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
    """Провайдер noopmail.org.

    noopmail.org защищён Cloudflare; для работы в бою требуются куки
    cf_clearance (получи их в браузере и передавай через HttpClient/proxy-настройки).
    Если API отвечает 403/Cloudflare-challenge — причина в отсутствии/протухшей
    cf_clearance.
    """

    slug = "noopmail.org"
    kind: TargetKind = "domain"
    cache_ttl = _CACHE_TTL
    default_headers = _HEADERS
    BASE_URL = "https://noopmail.org"

    async def _fetch_targets(self) -> list[Target]:
        seen: set[str] = set()
        dupes = 0
        # Хитрость: /api/rd возвращает ОДИН случайный домен за запрос.
        # Тянем повторно, пока не наберём все уникальные dm; когда 15 подряд
        # вызовов вернули уже известный домен — считаем набор полным.
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
        # Эндпоинта создания ящика у noopmail нет — адрес просто начинает
        # существовать. Api-token тоже нет, поэтому token="".
        return MailboxInfo(
            provider=self.slug,
            address=address,
            token="",
            provider_account_id=address,
            password=spec.password,
        )

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        # У noopmail нет эндпоинта удаления ящика — no-op.
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        local, _, domain = mailbox.address.partition("@")
        data = await self._post_json(f"{self.BASE_URL}/api/c", body={"e": local, "d": domain})
        if not isinstance(data, list):
            return []
        return [_summary(m) for m in data if isinstance(m, dict)]

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        data = await self._get_json(f"{self.BASE_URL}/api/i/{message_id}")
        if not isinstance(data, dict) or not data.get("id"):
            raise MailNotFoundError(
                f"noopmail.org: message {message_id!r} not found",
                status_code=404,
            )
        return _detail(data)

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        # Эндпоинт удаления требует id и m_id: /api/i/{id}/{m_id}.
        # Список и удаление ходят по-разному, поэтому m_id достаём из детали.
        try:
            data = await self._get_json(f"{self.BASE_URL}/api/i/{message_id}")
            m_id = data.get("m_id") if isinstance(data, dict) else None
            url = f"{self.BASE_URL}/api/i/{message_id}"
            if m_id:
                url += f"/{m_id}"
            await self._http.delete(url, headers=self._headers())
        except MailNotFoundError:
            pass
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        # У noopmail нет флага "прочитано" — no-op.
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        data = await self._get_json(f"{self.BASE_URL}/api/i/{message_id}")
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
        raw = await self._get_raw(f"{self.BASE_URL}/raw/{m_id}")
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
        # Снимаем base64-обёртку, если это валидный base64; иначе возвращаем как есть.
        if isinstance(payload, str):
            try:
                return base64.b64decode(payload).decode("utf-8")
            except Exception:
                return payload
        return str(payload)
