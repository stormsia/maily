from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import quote

from ...exceptions import MailAPIError, MailAuthError, MailNotFoundError, MailValidationError
from ...http import HttpClient
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
_BASE_URL = "https://dispoemail.org"

_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:158.0) Gecko/20100101 Firefox/158.0",
    "Accept": "*/*",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Referer": "https://dispoemail.org/",
    "Origin": "https://dispoemail.org",
    "DNT": "1",
    "Sec-GPC": "1",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}


def _split_address(address: str) -> tuple[str, str]:
    mailbox, sep, domain = address.partition("@")
    if not sep or not mailbox or not domain:
        raise MailValidationError(
            f"dispoemail.org: address {address!r} is not mailbox@domain",
            status_code=400,
        )
    return mailbox, domain


def _parse_token(raw_token: str | None) -> tuple[str, str | None]:
    """Parse combined token format 'mailbox_token:astro_session' or bare 'mailbox_token'."""
    if not raw_token:
        return "", None
    token, sep, session = raw_token.partition(":")
    return token, (session if sep else None)


def _parse_summary(raw: dict[str, Any], mailbox_name: str, domain: str) -> MessageSummary:
    from_data = raw.get("from")
    if isinstance(from_data, dict):
        party = Party(
            name=str(from_data.get("name") or "") or None,
            address=str(from_data.get("address") or ""),
        )
    else:
        party = parse_from_value(str(from_data or ""))

    msg_id = str(raw.get("id") or "")
    preview = str(raw.get("preview") or "")
    return MessageSummary(
        id=msg_id,
        subject=str(raw.get("subject") or ""),
        from_=party,
        to=[Party(address=f"{mailbox_name}@{domain}")],
        intro=preview[:200] if preview else "",
        seen=False,
        has_attachments=bool(raw.get("attachments") or raw.get("hasHtml") is False),
        size=len(preview),
        received_at=parse_iso(raw.get("receivedAt")),
    )


class DispoEmailOrg(HttpProvider):
    """Провайдер dispoemail.org.

    Работает через JSON API dispoemail.org.
    Сервис защищён Cloudflare; для боевых запросов передаются куки/прокси.
    """

    slug = "dispoemail.org"
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

    def _auth_headers(self, mailbox_token_enc: str | None) -> dict[str, str]:
        headers = dict(self.default_headers)
        headers.pop("Origin", None)
        headers.pop("Content-Type", None)
        token, session = _parse_token(mailbox_token_enc)
        if token:
            headers["X-Mailbox-Token"] = token
        if session:
            headers["Cookie"] = f"astro-session={session}"
        else:
            headers["Cookie"] = ""
        return headers

    @async_retry()
    async def _fetch_targets(self, *, known: set[str] | None = None) -> list[Target]:
        headers = dict(self.default_headers)
        headers.pop("Origin", None)
        headers.pop("Content-Type", None)
        try:
            resp = await self._http._client.get(
                f"{self.BASE_URL}/api/active-domains", headers=headers
            )
        except Exception as e:
            raise MailAPIError(f"dispoemail.org: failed to get active domains: {e}") from e

        try:
            data = resp.json()
        except Exception as e:
            raise MailAPIError(f"dispoemail.org: failed to parse active domains: {e}") from e

        if not isinstance(data, dict) or "domains" not in data:
            raise MailAPIError("dispoemail.org: unexpected active domains response")

        domains = data.get("domains") or []
        targets: list[Target] = []
        for d in domains:
            domain = str(d).strip()
            if domain:
                targets.append(Target(id=domain, kind="domain", provider=self.slug, label=domain))
        return targets

    @async_retry()
    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        domain = spec.domain
        custom_mailbox: str | None = None
        if spec.address:
            custom_mailbox, domain = _split_address(spec.address)

        if not domain:
            targets = await self.list_targets()
            if not targets:
                raise MailValidationError("dispoemail.org: no domains available", status_code=400)
            domain = targets[0].label

        headers = dict(self.default_headers)
        headers["Content-Type"] = "application/json"
        headers["Cookie"] = ""
        body: dict[str, str] = {"domain": domain}
        if custom_mailbox:
            body["mailbox"] = custom_mailbox

        try:
            resp = await self._http._client.post(
                f"{self.BASE_URL}/api/session/mailboxes", headers=headers, json=body
            )
        except Exception as e:
            raise MailAPIError(f"dispoemail.org: create failed: {e}") from e

        try:
            result = resp.json()
        except Exception as e:
            raise MailAPIError(f"dispoemail.org: failed to parse create response: {e}") from e

        if not isinstance(result, dict) or not result.get("ok"):
            denied = result.get("denied") if isinstance(result, dict) else None
            msg = f"creation denied: {denied}" if denied else "failed to create mailbox"
            raise MailValidationError(f"dispoemail.org: {msg}", status_code=400)

        tokens = result.get("tokens") or {}
        if not tokens:
            raise MailValidationError(
                "dispoemail.org: failed to create mailbox (no tokens returned)", status_code=400
            )

        # Get generated/created address and token
        created_address = next(iter(tokens.keys()))
        mailbox_token = tokens[created_address] or ""

        # Extract astro-session cookie from response headers if present
        astro_session: str | None = None

        # 1. Check raw Set-Cookie headers using regex (handles Cloudflare multi-cookie and comma folding)
        raw_cookies: list[str] = []
        resp_headers = getattr(resp, "headers", None)
        if resp_headers is not None:
            if hasattr(resp_headers, "get_list"):
                raw_cookies = resp_headers.get_list("set-cookie")
            elif hasattr(resp_headers, "get"):
                val = resp_headers.get("set-cookie")
                if val:
                    raw_cookies = [val]

        for header_val in raw_cookies:
            match = re.search(r"(?:^|[;,\s])astro-session=([^;,\s]+)", header_val)
            if match:
                astro_session = match.group(1).strip().strip("\"'")
                break

        # 2. Fall back to cookie jar if not found in raw headers
        if not astro_session:
            try:
                jar = getattr(resp, "cookies", None)
                if jar is not None:
                    cookie_val = jar.get("astro-session")
                    if cookie_val:
                        astro_session = (
                            str(cookie_val).split(",")[0].split(";")[0].strip().strip("\"'")
                        )
            except Exception:
                pass

        full_token = f"{mailbox_token}:{astro_session}" if astro_session else mailbox_token

        return MailboxInfo(
            provider=self.slug,
            address=created_address,
            token=full_token,
            provider_account_id=created_address,
            password=spec.password,
        )

    @async_retry()
    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        mailbox_name, domain = _split_address(mailbox.address)
        headers = self._auth_headers(mailbox.token)

        url = f"{self.BASE_URL}/api/inboxes/{quote(mailbox_name)}?domain={quote(domain)}"
        try:
            resp = await self._http._client.delete(url, headers=headers)
            return resp.status_code < 400
        except Exception:
            return True

    @async_retry()
    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        if page > 1:
            return []

        mailbox_name, domain = _split_address(mailbox.address)
        headers = self._auth_headers(mailbox.token)

        url = f"{self.BASE_URL}/api/inboxes/{quote(mailbox_name)}?domain={quote(domain)}"
        try:
            resp = await self._http._client.get(url, headers=headers)
            if resp.status_code in (401, 403):
                raise MailAuthError(
                    f"dispoemail.org: access forbidden for mailbox {mailbox.address!r}",
                    status_code=resp.status_code,
                )
            if resp.status_code == 404:
                return []
            if resp.status_code >= 400:
                raise MailAPIError(
                    f"dispoemail.org: list messages returned status {resp.status_code}"
                )
            data = resp.json()
        except MailAPIError:
            raise
        except Exception as e:
            raise MailAPIError(f"dispoemail.org: failed to list messages: {e}") from e

        if not isinstance(data, dict):
            return []

        messages_raw = data.get("messages") or []
        summaries: list[MessageSummary] = []
        for m in messages_raw:
            if isinstance(m, dict):
                summaries.append(_parse_summary(m, mailbox_name, domain))
        return summaries

    @async_retry()
    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        mailbox_name, domain = _split_address(mailbox.address)
        headers = self._auth_headers(mailbox.token)

        url = f"{self.BASE_URL}/api/messages/{quote(message_id)}?mailbox={quote(mailbox_name)}&domain={quote(domain)}"
        try:
            resp = await self._http._client.get(url, headers=headers)
            if resp.status_code in (401, 403):
                raise MailAuthError(
                    f"dispoemail.org: access forbidden for message {message_id!r}",
                    status_code=resp.status_code,
                )
            if resp.status_code == 404:
                raise MailNotFoundError(
                    f"dispoemail.org: message {message_id!r} not found", status_code=404
                )
            if resp.status_code >= 400:
                raise MailAPIError(
                    f"dispoemail.org: get message returned status {resp.status_code}"
                )
            data = resp.json()
        except (MailNotFoundError, MailAPIError):
            raise
        except Exception as e:
            raise MailAPIError(f"dispoemail.org: failed to get message: {e}") from e

        if not isinstance(data, dict) or "message" not in data:
            raise MailNotFoundError(
                f"dispoemail.org: message {message_id!r} not found", status_code=404
            )

        msg = data["message"]
        if not isinstance(msg, dict):
            raise MailNotFoundError(
                f"dispoemail.org: message {message_id!r} not found", status_code=404
            )

        summary = _parse_summary(msg, mailbox_name, domain)
        body_text = str(msg.get("text") or "")
        body_html = str(msg.get("html") or "")

        return MessageDetail(
            id=summary.id,
            subject=summary.subject,
            from_=summary.from_,
            to=summary.to,
            intro=summary.intro,
            seen=summary.seen,
            has_attachments=summary.has_attachments,
            size=len(body_text) + len(body_html) if (body_text or body_html) else summary.size,
            received_at=summary.received_at,
            text=body_text,
            html=[body_html] if body_html else [],
            attachments=[],
        )

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        # dispoemail.org has no message-level delete endpoint; deletion is handled locally in DB
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        # dispoemail.org has no read-status flag on upstream; marked locally in DB
        return True

    @async_retry()
    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        detail = await self.get_message(mailbox, message_id)
        data = detail.html[0] if detail.html else detail.text
        return MessageSource(id=message_id, data=data, download_url="")
