from __future__ import annotations

import asyncio
import re
import secrets
from contextlib import suppress
from typing import Any
from urllib.parse import quote

from ...exceptions import MailAPIError, MailNotFoundError, MailValidationError
from ...http import HttpClient
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

_CACHE_TTL = 600.0
_BASE_URL = "https://anonymmail.net"

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:158.0) Gecko/20100101 Firefox/158.0"

_HEADERS = {
    "User-Agent": _UA,
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": f"{_BASE_URL}/",
    "Origin": _BASE_URL,
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}


def _extract_csrf(html: str) -> str | None:
    m = re.search(r'name=["\']csrf_test_name["\'][^>]+value=["\']([^"\']+)["\']', html)
    if m:
        return m.group(1)
    m = re.search(r'csrf_test_name["\']?\s*[:=]\s*["\']([^"\']+)["\']', html)
    if m:
        return m.group(1)
    return None


def _extract_csrf_from_cookie(http: HttpClient) -> str | None:
    try:
        jar = getattr(http._client, "cookies", None)
        if jar is not None:
            try:
                v = jar.get("csrf_cookie_name")
                if v:
                    return v
            except Exception:
                pass
            try:
                for cookie in jar:
                    name = getattr(cookie, "name", None) or (
                        cookie.name if hasattr(cookie, "name") else None
                    )
                    if name == "csrf_cookie_name":
                        return getattr(cookie, "value", None)
            except Exception:
                pass
    except Exception:
        pass
    return None


def _extract_cookie(resp: Any, name: str) -> str | None:
    try:
        jar = getattr(resp, "cookies", None)
        if jar is not None:
            val = jar.get(name)
            if val:
                return val
    except Exception:
        pass
    try:
        set_cookie = resp.headers.get("set-cookie") or ""
        for part in set_cookie.split(";"):
            part = part.strip()
            if part.startswith(f"{name}="):
                return part.split("=", 1)[1]
    except Exception:
        pass
    return None


def _parse_mailbox_token(raw_token: str | None) -> tuple[str | None, str | None]:
    """Parse combined token format 'ci_session:am_uid'."""
    if not raw_token or ":" not in raw_token:
        return None, None
    ci_session, _, am_uid = raw_token.partition(":")
    return (ci_session.strip() or None), (am_uid.strip() or None)


def _parse_messages(raw: dict[str, Any], mailbox_address: str) -> list[MessageSummary]:
    out: list[MessageSummary] = []
    # Response is like {email: {created_at: ..., emails: [...]}}
    for _key, val in raw.items():
        if not isinstance(val, dict):
            continue
        emails = val.get("emails") or []
        if not isinstance(emails, list):
            continue
        for e in emails:
            if not isinstance(e, dict):
                continue
            from_raw = str(e.get("from") or "")
            party = (
                parse_from_value(from_raw)
                if "<" in from_raw or "@" in from_raw
                else Party(name=None, address=from_raw)
            )
            # Try to extract address if just name
            if party.address and "@" not in party.address and from_raw:
                m = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", from_raw)
                if m:
                    party.address = m.group(0)
            msg_id = str(e.get("token") or e.get("id") or "")
            if not msg_id:
                continue
            out.append(
                MessageSummary(
                    id=msg_id,
                    subject=str(e.get("subject") or ""),
                    from_=party,
                    to=[Party(address=mailbox_address)],
                    intro="",
                    seen=bool(e.get("read")),
                    has_attachments=bool(e.get("images")),
                    size=0,
                    received_at=parse_iso(e.get("date")) if e.get("date") else None,
                )
            )
    return out


class AnonymMailNet(HttpProvider):
    slug = "anonymmail.net"
    kind: TargetKind = "domain"
    cache_ttl = _CACHE_TTL
    default_headers = _HEADERS
    BASE_URL = _BASE_URL
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

    def __init__(self, http: HttpClient | None = None, proxy: str | None = None) -> None:
        super().__init__(http=http, proxy=proxy)
        self._csrf_token: str | None = None
        self._csrf_lock = asyncio.Lock()
        self._messages: dict[str, dict[str, MessageDetail]] = {}

    async def _ensure_session(self) -> str:
        if self._csrf_token:
            return self._csrf_token
        async with self._csrf_lock:
            if self._csrf_token:
                return self._csrf_token
            token = _extract_csrf_from_cookie(self._http)
            if token:
                self._csrf_token = token
                return token
            try:
                headers = dict(self.default_headers)
                headers["Accept"] = (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
                )
                headers["Sec-Fetch-Dest"] = "document"
                headers["Sec-Fetch-Mode"] = "navigate"
                headers["Sec-Fetch-Site"] = "none"
                headers["Sec-Fetch-User"] = "?1"
                headers["Upgrade-Insecure-Requests"] = "1"
                headers.pop("X-Requested-With", None)
                resp = await self._http._client.get(
                    f"{self.BASE_URL}/", headers=headers, follow_redirects=True
                )
                html = resp.text
                token = _extract_csrf(html) or _extract_csrf_from_cookie(self._http)
                if not token:
                    try:
                        jar = getattr(self._http._client, "cookies", None)
                        if jar is not None:
                            token = jar.get("csrf_cookie_name")
                    except Exception:
                        pass
                if token:
                    self._csrf_token = token
                    return token
            except Exception:
                pass
            raise MailAPIError("anonymmail.net: could not obtain CSRF token")

    def _headers_with_csrf(self, token: str) -> dict[str, str]:
        headers = dict(self.default_headers)
        headers["X-CSRF-TOKEN"] = token
        headers["X-Requested-With"] = "XMLHttpRequest"
        return headers

    def _mailbox_headers(self, mailbox: MailboxInfo, csrf_token: str) -> dict[str, str]:
        headers = self._headers_with_csrf(csrf_token)
        ci_session, am_uid = _parse_mailbox_token(mailbox.token)
        cookies: list[str] = [f"csrf_cookie_name={csrf_token}"]
        if ci_session:
            cookies.append(f"ci_session={ci_session}")
        if am_uid:
            cookies.append(f"am_uid={am_uid}")
        if ci_session or am_uid:
            headers["Cookie"] = "; ".join(cookies)
        return headers

    @async_retry()
    async def _fetch_targets(self, *, known: set[str] | None = None) -> list[Target]:
        token = await self._ensure_session()
        headers = self._headers_with_csrf(token)
        headers["Accept"] = "*/*"
        headers.pop("Accept-Encoding", None)
        headers["Content-Length"] = "0"
        try:
            resp = await self._http._client.post(
                f"{self.BASE_URL}/api/getDomains", headers=headers, content=b""
            )
        except Exception as e:
            raise MailAPIError(f"anonymmail.net: failed to get domains: {e}") from e
        try:
            data = resp.json()
        except Exception as e:
            raise MailAPIError(f"anonymmail.net: failed to parse domains: {e}") from e
        if not isinstance(data, list):
            raise MailAPIError("anonymmail.net: unexpected domains response")
        targets: list[Target] = []
        for d in data:
            if isinstance(d, dict) and d.get("domain"):
                domain = str(d["domain"])
                targets.append(Target(id=domain, kind="domain", provider=self.slug, label=domain))
            elif isinstance(d, str):
                targets.append(Target(id=d, kind="domain", provider=self.slug, label=d))
        return targets

    @async_retry()
    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        address = spec.address
        if not address:
            domain = spec.domain
            if not domain:
                targets = await self.list_targets()
                if not targets:
                    raise MailValidationError(
                        "anonymmail.net: no domains available", status_code=400
                    )
                domain = targets[0].label
            address = f"{random_string(10)}@{domain}"
        name, sep, domain_part = address.partition("@")
        if not sep or not domain_part:
            raise MailValidationError(
                f"anonymmail.net: address {address!r} is not name@domain",
                status_code=400,
            )
        token = await self._ensure_session()
        am_uid = secrets.token_hex(32)
        headers = dict(self.default_headers)
        headers["X-CSRF-TOKEN"] = token
        headers["X-Requested-With"] = "XMLHttpRequest"
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        headers["Cookie"] = f"csrf_cookie_name={token}; am_uid={am_uid}"
        headers.pop("Accept-Encoding", None)
        data = f"email={quote(address)}"
        try:
            resp = await self._http._client.post(
                f"{self.BASE_URL}/api/create", headers=headers, content=data.encode("utf-8")
            )
        except Exception as e:
            raise MailAPIError(f"anonymmail.net: create failed: {e}") from e
        try:
            result = resp.json()
        except Exception as e:
            raise MailAPIError(f"anonymmail.net: create failed to parse response: {e}") from e
        if not isinstance(result, dict):
            raise MailAPIError("anonymmail.net: unexpected create response")
        if not result.get("success") or result.get("error"):
            msg = result.get("message") or result.get("error") or "failed to create mailbox"
            raise MailValidationError(f"anonymmail.net: {msg}", status_code=400)
        ci_session = _extract_cookie(resp, "ci_session")
        full_token = f"{ci_session}:{am_uid}" if ci_session else am_uid
        email = result.get("email") or address
        return MailboxInfo(
            provider=self.slug,
            address=email,
            token=full_token,
            provider_account_id=email,
            password=spec.password,
        )

    @async_retry()
    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        self._messages.pop(mailbox.address.strip().lower(), None)
        token = await self._ensure_session()
        headers = self._mailbox_headers(mailbox, token)
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        headers.pop("Accept-Encoding", None)
        data = f"email={quote(mailbox.address)}"
        try:
            await self._http._client.post(
                f"{self.BASE_URL}/api/delete", headers=headers, content=data.encode("utf-8")
            )
            return True
        except Exception:
            return True

    async def _fetch_message_body(
        self, message_id: str, mailbox: MailboxInfo | None = None
    ) -> tuple[str, str]:
        token = await self._ensure_session()
        if mailbox:
            headers = self._mailbox_headers(mailbox, token)
        else:
            headers = dict(self.default_headers)
            headers["X-CSRF-TOKEN"] = token
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers.pop("X-Requested-With", None)
        headers.pop("Accept-Encoding", None)
        try:
            resp = await self._http._client.get(
                f"{self.BASE_URL}/email?id={quote(message_id)}",
                headers=headers,
                follow_redirects=True,
            )
            if resp.status_code >= 400:
                raise MailNotFoundError(
                    f"anonymmail.net: message {message_id!r} not found", status_code=404
                )
            html = resp.text
            body_text = re.sub(r"<[^>]+>", " ", html)
            body_text = re.sub(r"\s+", " ", body_text).strip()
            return body_text, html
        except MailNotFoundError:
            raise
        except Exception as e:
            raise MailAPIError(f"anonymmail.net: failed to fetch message body: {e}") from e

    @async_retry()
    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        token = await self._ensure_session()
        headers = self._mailbox_headers(mailbox, token)
        headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        headers.pop("Accept-Encoding", None)
        data = f"email={quote(mailbox.address)}"
        try:
            resp = await self._http._client.post(
                f"{self.BASE_URL}/api/get", headers=headers, content=data.encode("utf-8")
            )
            try:
                result = resp.json()
            except Exception:
                return []
            if not isinstance(result, dict):
                return []
            summaries = _parse_messages(result, mailbox.address)
            addr = mailbox.address.strip().lower()
            box_cache = self._messages.setdefault(addr, {})
            details: list[MessageSummary] = []
            for s in summaries:
                body_text = ""
                html = ""
                with suppress(Exception):
                    body_text, html = await self._fetch_message_body(s.id, mailbox=mailbox)
                detail = MessageDetail(
                    id=s.id,
                    subject=s.subject,
                    from_=s.from_,
                    to=s.to,
                    intro=s.intro or (body_text[:200] if body_text else ""),
                    seen=s.seen,
                    has_attachments=s.has_attachments,
                    size=len(body_text) + len(html) if (body_text or html) else s.size,
                    received_at=s.received_at,
                    text=body_text,
                    html=[html] if html else [],
                    attachments=[],
                )
                box_cache[s.id] = detail
                details.append(detail)
            # Evict old mailboxes if overall cache grows excessively
            if len(self._messages) > 1000:
                for k in list(self._messages.keys())[:500]:
                    self._messages.pop(k, None)
            return details
        except MailNotFoundError:
            raise
        except Exception:
            return []

    @async_retry()
    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        addr = mailbox.address.strip().lower()
        box_cache = self._messages.setdefault(addr, {})
        if message_id in box_cache:
            detail = box_cache[message_id]
            if detail.text or detail.html:
                return detail
            try:
                body_text, html = await self._fetch_message_body(message_id, mailbox=mailbox)
                detail.text = body_text
                detail.html = [html] if html else []
                detail.size = len(body_text) + len(html)
                return detail
            except Exception:
                return detail

        # Try to fetch directly from upstream
        try:
            body_text, html = await self._fetch_message_body(message_id, mailbox=mailbox)
            detail = MessageDetail(
                id=message_id,
                subject="",
                from_=Party(name=None, address=""),
                to=[Party(address=mailbox.address)],
                intro=body_text[:200] if body_text else "",
                seen=False,
                has_attachments=False,
                size=len(body_text) + len(html),
                received_at=None,
                text=body_text,
                html=[html] if html else [],
                attachments=[],
            )
            box_cache[message_id] = detail
            return detail
        except Exception as e:
            raise MailNotFoundError(
                f"anonymmail.net: message {message_id!r} not found", status_code=404
            ) from e

    @async_retry()
    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        addr = mailbox.address.strip().lower()
        if addr in self._messages:
            self._messages[addr].pop(message_id, None)
        token = await self._ensure_session()
        headers = self._mailbox_headers(mailbox, token)
        headers["Content-Type"] = "application/x-www-form-urlencoded"
        headers["Referer"] = f"{self.BASE_URL}/"
        headers["Origin"] = self.BASE_URL
        headers.pop("X-Requested-With", None)
        headers.pop("Accept-Encoding", None)
        data = f"csrf_test_name={quote(token)}&delete=1"
        try:
            await self._http._client.post(
                f"{self.BASE_URL}/email?id={quote(message_id)}",
                headers=headers,
                content=data.encode("utf-8"),
                follow_redirects=True,
            )
            return True
        except Exception:
            return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        addr = mailbox.address.strip().lower()
        msg = self._messages.get(addr, {}).get(message_id)
        if msg:
            msg.seen = True
        return True

    @async_retry()
    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        try:
            detail = await self.get_message(mailbox, message_id)
            data = detail.html[0] if detail.html else detail.text
            return MessageSource(id=message_id, data=data, download_url="")
        except Exception as e:
            raise MailNotFoundError(
                f"anonymmail.net: source for message {message_id!r} not found", status_code=404
            ) from e
