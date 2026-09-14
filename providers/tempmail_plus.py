"""
tempmail.plus provider implementation.

API surface (reverse-engineered from https://tempmail.plus):
  - Domains    → parse HTML page, extract .dropdown-menu .dropdown-item
  - List mails → GET /api/mails?email=<addr>&limit=<n>&epin=
  - Get mail   → GET /api/mails/<id>?email=<addr>&epin=
  - Delete mail→ DELETE /api/mails/<id>?email=<addr>&epin=

Notes
-----
- tempmail.plus does not have an account registration/deletion API.
  "Accounts" are just email addresses — any address on an available domain
  can be used immediately.
- There is no bearer-token auth.  ``Token.token`` is set to the email
  address itself as an opaque identifier understood by the client.
- ``epin`` is an optional PIN parameter left empty here (public mailboxes).
- Domains are scraped from HTML and cached in-memory with a TTL.
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ..core.base_provider import MailProvider
from ..core.http import AsyncHTTPSession
from ..schemas.account import Account, Token
from ..schemas.domains import Domain
from ..schemas.message import Attachment, Message, MessageFromTo, Messages, MessageSource, OneMessage
from ..utils.exceptions import MailAPIError, MailNotFoundError, MailValidationError
from ..utils.misc import random_string
from ..utils.retry import async_retry

logger = logging.getLogger(__name__)

_DOMAIN_CACHE_TTL: float = 600.0   # 10 minutes (domains change rarely)
_DEFAULT_EPIN: str = ""             # public mailboxes have no PIN


class TempMailPlusProvider(MailProvider):
    """
    Concrete ``MailProvider`` implementation for https://tempmail.plus.

    tempmail.plus has no account registration API — any ``user@domain``
    address becomes a valid inbox on first use.  This provider generates a
    random address, validates it against the API (checks the inbox exists
    and is empty), then returns it as an ``Account``.

    The ``Token.token`` field stores the email address itself, since that
    is the only credential needed for subsequent API calls.
    """

    BASE_URL: str = "https://tempmail.plus"
    API_URL: str = "https://tempmail.plus/api"

    # Browser-like headers to avoid 403 from Cloudflare
    _HEADERS: dict[str, str] = {
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

    def __init__(
        self,
        *,
        proxy: str | None = None,
        ssl: bool = True,
        epin: str = _DEFAULT_EPIN,
        domain_cache_ttl: float = _DOMAIN_CACHE_TTL,
    ) -> None:
        # tempmail.plus needs real browser headers — override the aiohttp defaults
        from aiohttp import ClientSession, TCPConnector, ClientTimeout
        self._proxy = proxy
        self._ssl = ssl
        self._epin = epin
        self._domain_cache_ttl = domain_cache_ttl

        # Use a dedicated AsyncHTTPSession that we'll configure lazily
        self._http = AsyncHTTPSession(proxy=proxy, ssl=ssl)

        # Domain cache
        self._domain_cache: list[Domain] = []
        self._domain_cache_at: float = 0.0
        self._domain_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Provider identity
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "tempmail.plus"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self._http.close()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _auth_params(self, email: str) -> dict[str, str]:
        """Build the query-string params used in every authenticated call."""
        return {"email": email, "epin": self._epin}

    async def _get_json(self, url: str, params: dict | None = None) -> dict:
        """GET url, return JSON dict, raise on HTTP errors."""
        resp = await self._http.get(url, params=params, headers=self._HEADERS)
        return await resp.json(content_type=None)

    async def _delete_json(self, url: str, data: dict | None = None) -> dict:
        import urllib.parse
        headers = self._HEADERS.copy()
        
        payload = None
        if data:
            payload = urllib.parse.urlencode(data)
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
            headers["X-Requested-With"] = "XMLHttpRequest"
            
        resp = await self._http.delete(url, data=payload, headers=headers)
        try:
            return await resp.json(content_type=None)
        except Exception:
            return {}

    # ------------------------------------------------------------------
    # Domain scraping (HTML parse → cached list)
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3)
    async def get_domains(self) -> list[Domain]:
        """
        Scrape the tempmail.plus main page and extract available domains.

        Results are cached for ``domain_cache_ttl`` seconds.
        """
        from ..db.models import DomainRecord
        import datetime
        now = datetime.datetime.utcnow()
        async with self._domain_lock:
            latest = DomainRecord.select().where(DomainRecord.provider == self.provider_name).order_by(DomainRecord.cached_at.desc()).first()
            if latest and (now - latest.cached_at).total_seconds() < self._domain_cache_ttl:
                records = list(DomainRecord.select().where(DomainRecord.provider == self.provider_name))
                if records:
                    logger.debug(
                        "tempmail.plus domain cache hit from DB: %d domains", len(records)
                    )
                    return [
                        Domain(id=r.api_id or r.domain, domain=r.domain, isActive=r.is_active, isPrivate=r.is_private)
                        for r in records
                    ]

            # Fetch the HTML page (needs browser headers)
            resp = await self._http.get(
                f"{self.BASE_URL}/en/",
                headers={
                    **self._HEADERS,
                    "Accept": "text/html,application/xhtml+xml",
                    "X-Requested-With": "",
                },
            )
            html = await resp.text()

            # Parse domain list: <button class="dropdown-item">@domain.tld</button>
            domains = _parse_domains_from_html(html)
            if not domains:
                raise MailAPIError(
                    "tempmail.plus: could not parse any domains from HTML. "
                    "The page structure may have changed."
                )

            DomainRecord.delete().where(DomainRecord.provider == self.provider_name).execute()
            res = []
            for d in domains:
                DomainRecord.create(
                    provider=self.provider_name,
                    api_id=d,
                    domain=d,
                    is_active=True,
                    is_private=False,
                    cached_at=now
                )
                res.append(Domain(id=d, domain=d, isActive=True, isPrivate=False))
            
            logger.debug(
                "tempmail.plus domain cache refreshed in DB: %d domains", len(res)
            )
            return res

    # ------------------------------------------------------------------
    # Auth (no-op — email address IS the token)
    # ------------------------------------------------------------------

    async def get_account_token(self, address: str, password: str) -> Token:
        """
        tempmail.plus has no auth endpoint.

        The email address itself acts as the "token" — it is returned as
        ``Token.token`` so the rest of the client can work uniformly.
        """
        return Token(id=address, token=address)

    # ------------------------------------------------------------------
    # Account CRUD
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3)
    async def create_account(self, address: str, password: str) -> Account:
        """
        Validate that *address* is a usable tempmail.plus inbox.

        tempmail.plus does not register accounts — we simply verify the
        address is on a valid domain and the inbox is empty/accessible.

        Raises:
            MailValidationError: if the address is invalid or the API
                                 returns an error for it.
        """
        data = await self._get_json(
            f"{self.API_URL}/mails",
            params={**self._auth_params(address), "limit": 1},
        )

        if "err" in data:
            raise MailValidationError(
                f"tempmail.plus rejected address {address!r}: "
                f"{data['err'].get('msg', data['err'])}",
                status_code=400,
            )

        token = Token(id=address, token=address)
        return Account(
            id=address,
            address=address,
            password=password,
            quota=0,
            used=0,
            isDisabled=False,
            isDeleted=False,
            token=token,
        )

    @async_retry(max_attempts=3)
    async def get_account_by_id(self, account_id: str, token: str) -> Account:
        """
        ``account_id`` == ``token`` == email address for tempmail.plus.

        Verify the inbox is still accessible.
        """
        return await self.create_account(account_id, "")

    async def delete_account(self, account_id: str, token: str) -> bool:
        """
        tempmail.plus has no account deletion endpoint.

        Instead, we delete all messages currently in the inbox to clear it.
        Returns True if successful or unsuccessful since it doesn't matter.
        """

        try:
            while True:
                messages = await self.get_messages(token, page=1)
                if not messages.hydra_member:
                    break
                
                tasks = [self.delete_message(msg.id, token) for msg in messages.hydra_member]
                for t in tasks:
                    await t
                #await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as exc:
            logger.warning("tempmail.plus: failed to clear inbox on account deletion: %s", exc)
            return False

        logger.debug("tempmail.plus: cleared inbox for %s", account_id)
        return True

    @async_retry(max_attempts=3)
    async def get_me(self, token: str) -> Account:
        """Return the account that owns *token* (which is the email address)."""
        return await self.create_account(token, "")

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3)
    async def get_messages(self, token: str, page: int = 1) -> Messages:
        """
        Fetch inbox for the address stored in *token*.

        tempmail.plus uses offset-based pagination.  *page* is mapped to
        ``offset = (page - 1) * limit``.

        Response schema::

            {
              "first_id": 12345,        # 0 if inbox empty
              "mail_list": [
                {"mail_id": ..., "subject": ..., "from_mail": ...,
                 "from_name": ..., "date": "2024-01-01 12:00:00",
                 "is_new": true, "mail_size": 1234}
              ],
              "count": 3
            }
        """
        limit = 20
        offset = (page - 1) * limit
        data = await self._get_json(
            f"{self.API_URL}/mails",
            params={**self._auth_params(token), "limit": limit, "offset": offset},
        )

        if "err" in data:
            raise MailAPIError(
                f"tempmail.plus get_messages error: {data['err']}",
                status_code=400,
            )

        mail_list: list[dict] = data.get("mail_list") or []
        members: list[Message] = [_raw_to_message(m, token) for m in mail_list]

        return Messages(
            **{
                "hydra:member": [m.model_dump(by_alias=True) for m in members],
                "hydra:totalItems": data.get("count", len(members)),
            }
        )

    @async_retry(max_attempts=3)
    async def get_message_by_id(self, message_id: str, token: str) -> OneMessage:
        """
        Fetch full message detail.

        Response schema::

            {
              "mail_id": 12345,
              "subject": "...",
              "from_mail": "...",
              "from_name": "...",
              "date": "2024-01-01 12:00:00",
              "html": "<html>...</html>",
              "text": "...",
              "attachments": [...]
            }
        """
        data = await self._get_json(
            f"{self.API_URL}/mails/{message_id}",
            params=self._auth_params(token),
        )

        if "err" in data or "mail_id" not in data:
            raise MailNotFoundError(
                f"tempmail.plus: message {message_id!r} not found",
                status_code=404,
                response_data=data,
            )

        return _raw_to_one_message(data, token)

    @async_retry(max_attempts=3)
    async def delete_message(self, message_id: str, token: str) -> bool:
        """
        Delete a single message.

        API: DELETE /api/mails/<id> (requires email and epin in body)
        """
        logger.info("tempmail.plus: deleting message %s", message_id)
        data = await self._delete_json(
            f"{self.API_URL}/mails/{message_id}",
            data=self._auth_params(token),
        )
        logger.info("tempmail.plus: delete response %s", data)
        # API returns {"result": true} on success
        return bool(data.get("result", False))

    async def mark_message_read(self, message_id: str, token: str) -> bool:
        """
        tempmail.plus marks messages as read automatically on fetch.

        This is a no-op — returns True unconditionally.
        """
        return True

    @async_retry(max_attempts=3)
    async def get_message_source(self, message_id: str, token: str) -> MessageSource:
        """Return the raw HTML body of a message as MessageSource."""
        detail = await self.get_message_by_id(message_id, token)
        return MessageSource(
            id=message_id,
            downloadUrl=f"{self.API_URL}/mails/{message_id}?email={token}&epin={self._epin}",
            data="\n".join(detail.html) if detail.html else detail.text,
        )


# ---------------------------------------------------------------------------
# HTML domain parser (no external dep — pure stdlib re)
# ---------------------------------------------------------------------------

import re as _re

# Match dropdown items like: <button ...>@mailto.plus</button>
# or: <a class="dropdown-item" ...>@somemail.cc</a>
_DOMAIN_RE = _re.compile(
    r'class=["\'][^"\']*dropdown-item[^"\']*["\'][^>]*>@?([\w.-]+\.[a-z]{2,})',
    _re.IGNORECASE,
)
# Fallback: grab anything that looks like a @domain.tld in the page
_DOMAIN_FALLBACK_RE = _re.compile(r'@([\w-]+\.[\w.]{2,})')


def _parse_domains_from_html(html: str) -> list[str]:
    """Extract domain names from tempmail.plus HTML page."""
    domains: list[str] = []

    # Primary strategy: match dropdown-item elements
    for m in _DOMAIN_RE.finditer(html):
        d = m.group(1).strip().lower()
        if d and d not in domains:
            domains.append(d)

    if domains:
        return domains

    # Fallback: scan for @domain patterns (less precise)
    seen: set[str] = set()
    for m in _DOMAIN_FALLBACK_RE.finditer(html):
        d = m.group(1).strip().lower()
        if d not in seen and "tempmail" not in d and "example" not in d:
            seen.add(d)
            domains.append(d)

    return domains


# ---------------------------------------------------------------------------
# Response-to-schema converters
# ---------------------------------------------------------------------------

def _raw_to_message(raw: dict[str, Any], address: str) -> Message:
    """Convert a tempmail.plus mail_list item to a ``Message`` schema."""
    mail_id = str(raw.get("mail_id", ""))
    from_mail = raw.get("from_mail", "")
    from_name = raw.get("from_name", "")

    return Message(
        **{
            "id": mail_id,
            "accountId": address,
            "msgid": mail_id,
            "from": {"name": from_name, "address": from_mail},
            "to": [{"name": "", "address": address}],
            "subject": raw.get("subject", ""),
            "intro": "",
            "seen": not raw.get("is_new", True),
            "isDeleted": False,
            "hasAttachments": bool(raw.get("attachments")),
            "size": raw.get("mail_size", 0),
            "downloadUrl": "",
            "createdAt": _parse_date(raw.get("date")),
            "updatedAt": _parse_date(raw.get("date")),
        }
    )


def _raw_to_one_message(raw: dict[str, Any], address: str) -> OneMessage:
    """Convert a tempmail.plus full message response to ``OneMessage``."""
    mail_id = str(raw.get("mail_id", ""))
    from_mail = raw.get("from_mail", "")
    from_name = raw.get("from_name", "")

    html_body: str = raw.get("html", "") or ""
    text_body: str = raw.get("text", "") or ""

    raw_attachments: list[dict] = raw.get("attachments") or []
    attachments = [
        Attachment(
            id=str(a.get("id", "")),
            filename=a.get("name", ""),
            contentType=a.get("content_type", "application/octet-stream"),
            disposition="attachment",
            transferEncoding="base64",
            related=False,
            size=a.get("size", 0),
            downloadUrl=a.get("url", ""),
        )
        for a in raw_attachments
    ]

    created = _parse_date(raw.get("date"))

    return OneMessage(
        **{
            "id": mail_id,
            "accountId": address,
            "msgid": mail_id,
            "from": {"name": from_name, "address": from_mail},
            "to": [{"name": "", "address": address}],
            "cc": [],
            "bcc": [],
            "subject": raw.get("subject", ""),
            "flagged": False,
            "isDeleted": False,
            "verifications": {},
            "retention": False,
            "retentionDate": None,
            "text": text_body,
            "html": [html_body] if html_body else [],
            "hasAttachments": bool(attachments),
            "attachments": attachments or None,
            "size": raw.get("mail_size", len(html_body) + len(text_body)),
            "downloadUrl": "",
            "createdAt": created,
            "updatedAt": created,
        }
    )


def _parse_date(value: str | None):
    """Parse a tempmail.plus date string (``"2024-01-15 12:30:45"``) to datetime."""
    if not value:
        return None
    from datetime import datetime
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except (ValueError, TypeError):
        return None
