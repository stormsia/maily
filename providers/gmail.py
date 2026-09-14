"""
Gmail provider implementation.

Uses OAuth 2.0 for authentication and the Gmail API v1.
Plus-addressing model: any user+alias@gmail.com is delivered to the
same inbox; creating an alias = generating an address with no API call.

Token.token stores the alias address itself (same trick as tempmail_plus).
"""
from __future__ import annotations

import asyncio
import base64
import email.utils
import json
import logging
import secrets
import threading
import time
import urllib.parse
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from ..core.base_provider import MailProvider
from ..core.http import AsyncHTTPSession
from ..schemas.account import Account, Token
from ..schemas.domains import Domain
from ..schemas.message import (
    Attachment,
    Message,
    MessageFromTo,
    Messages,
    MessageSource,
    OneMessage,
)
from ..utils.exceptions import MailAPIError
from ..utils.misc import random_string
from ..utils.retry import async_retry

logger = logging.getLogger(__name__)

_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
# gmail.modify = read + modify labels/trash; gmail.settings.basic = read
# the user's sendAs aliases so they can be used as plus-alias bases.
_SCOPES_DEFAULT: list[str] = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]
_TOKEN_URI = "https://oauth2.googleapis.com/token"

_BASES_CACHE_TTL: float = 300.0  # seconds before refreshing base aliases


class GmailProvider(MailProvider):
    """
    Concrete ``MailProvider`` implementation for Gmail.

    Uses OAuth 2.0 with the Gmail API v1.  Plus-addressing is the core
    design: any ``user+alias@gmail.com`` is a valid, immediately usable
    inbox delivered to the same account.  ``Token.token`` stores the
    alias address itself (the same trick as ``tempmail_plus``).

    Authentication is lazy — no network activity happens in ``__init__``
    or ``get_domains``.  An access token is only obtained when a
    message/account operation needs it.
    """

    def __init__(
        self,
        *,
        credentials_path: str | Path,
        token_path: str | Path | None = None,
        scopes: list[str] | None = None,
        session: AsyncHTTPSession | None = None,
    ) -> None:
        self._credentials_path = Path(credentials_path)
        if token_path is None:
            self._token_path = self._credentials_path.parent / "gmail_token.json"
        else:
            self._token_path = Path(token_path)
        self._scopes = scopes or _SCOPES_DEFAULT
        self._http: AsyncHTTPSession = session or AsyncHTTPSession(ssl=False)

        # OAuth creds dict
        self._creds: dict[str, Any] = {}
        self._creds_lock = asyncio.Lock()

        # Load existing token file if present
        self._load_token_file()

        # Cached profile email
        self._base_email: str | None = None

        # Base addresses for plus-alias generation: profile email + the
        # user's own sendAs aliases (where plus-addressing actually works).
        # TTL-cached; round-robin counter spreads aliases across them.
        self._bases: list[str] = []
        self._bases_at: float = 0.0
        self._rr_index: int = 0

        # Pagination page tokens per alias
        self._page_tokens: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Provider identity
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "gmail"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self._http.close()

    # ------------------------------------------------------------------
    # OAuth token management
    # ------------------------------------------------------------------

    async def _ensure_access(self) -> str:
        """Return a valid access token, refreshing or logging in as needed."""
        async with self._creds_lock:
            if not self._creds:
                self._load_token_file()
            if self._creds and self._creds.get("access_token"):
                expires_at = self._creds.get("expires_at", 0)
                if expires_at > time.time() + 60:
                    return self._creds["access_token"]

            if self._creds and self._creds.get("refresh_token"):
                return await self._refresh_token()

            # No creds at all — full interactive login
            self._creds = await asyncio.to_thread(self._interactive_login)
            self._save_token_file()
            return self._creds["access_token"]

    async def _refresh_token(self) -> str:
        """Refresh the access token using the stored refresh token."""
        client_info = self._load_client_info()
        payload: dict[str, str] = {
            "grant_type": "refresh_token",
            "refresh_token": self._creds["refresh_token"],
            "client_id": client_info["client_id"],
            "client_secret": client_info["client_secret"],
        }
        # Explicit form content-type: session default is application/json,
        # which Google's token endpoint rejects for urlencoded bodies.
        resp = await self._http.post(
            _TOKEN_URI,
            data=urllib.parse.urlencode(payload),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        data: dict[str, Any] = await resp.json(content_type=None)
        self._creds["access_token"] = data["access_token"]
        self._creds["expires_at"] = time.time() + data["expires_in"]
        if "refresh_token" in data:
            self._creds["refresh_token"] = data["refresh_token"]
        self._save_token_file()
        return self._creds["access_token"]

    def _load_client_info(self) -> dict[str, str]:
        """Load the Google Desktop client OAuth config from credentials_path."""
        with open(self._credentials_path) as f:
            raw = json.load(f)
        installed = raw.get("installed", raw)
        return {
            "client_id": installed["client_id"],
            "client_secret": installed["client_secret"],
            "redirect_uris": installed.get("redirect_uris", ["http://localhost"]),
            "auth_uri": installed["auth_uri"],
            "token_uri": installed["token_uri"],
        }

    def _interactive_login(self) -> dict[str, Any]:
        """
        Run the full OAuth 2.0 interactive login flow synchronously.

        Uses only stdlib: urllib, http.server, threading, json, secrets,
        webbrowser.  Called via ``asyncio.to_thread``.
        """
        client_info = self._load_client_info()
        state = secrets.token_urlsafe(16)

        code_event = threading.Event()
        code: str | None = [None]
        received_state: str | None = [None]

        class _Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                query = urllib.parse.urlparse(self.path).query
                params = urllib.parse.parse_qs(query)
                received_state[0] = params.get("state", [""])[0]
                code[0] = params.get("code", [None])[0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(
                    b"Success, you can close this tab."
                )
                code_event.set()

            def log_message(self, *args, **kwargs):
                pass  # suppress server logs

        # Bind first so we can advertise the ACTUAL port in redirect_uri.
        # Google's Desktop OAuth client accepts loopback redirect URIs with
        # any port, so the registered URI host is what matters, not its port.
        port = 0
        server = HTTPServer(("127.0.0.1", port), _Handler)
        port = server.server_address[1]
        redirect_uri = f"http://127.0.0.1:{port}/"

        auth_url = (
            f"{client_info['auth_uri']}"
            f"?client_id={urllib.parse.quote(client_info['client_id'])}"
            f"&redirect_uri={urllib.parse.quote(redirect_uri)}"
            f"&response_type=code"
            f"&scope={urllib.parse.quote(' '.join(self._scopes))}"
            f"&state={state}"
            f"&access_type=offline"
            f"&prompt=consent"
        )

        # Open browser in a separate thread so it doesn't block the server
        threading.Thread(
            target=webbrowser.open,
            args=(auth_url,),
            daemon=True,
        ).start()

        # Serve until code received
        served = threading.Thread(
            target=server.serve_forever,
            kwargs={"poll_interval": 0.1},
            daemon=True,
        )
        served.start()

        if not code_event.wait(timeout=300):
            server.shutdown()
            raise MailAPIError("OAuth login timed out")

        server.shutdown()
        server.server_close()

        if received_state[0] != state:
            raise MailAPIError("OAuth state mismatch")

        # Exchange code for tokens
        token_payload: dict[str, str] = {
            "code": code[0],
            "client_id": client_info["client_id"],
            "client_secret": client_info["client_secret"],
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        # Use urllib for the sync token exchange
        req = urllib.request.Request(
            client_info["token_uri"],
            data=urllib.parse.urlencode(token_payload).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        with urllib.request.urlopen(req) as resp:
            token_data: dict[str, Any] = json.loads(resp.read().decode())

        return {
            "access_token": token_data["access_token"],
            "refresh_token": token_data.get("refresh_token", ""),
            "expires_at": time.time() + token_data["expires_in"],
        }

    def _save_token_file(self) -> None:
        """Persist OAuth creds to token_path as pretty JSON."""
        data = {
            "access_token": self._creds["access_token"],
            "refresh_token": self._creds.get("refresh_token", ""),
            "expires_at": self._creds["expires_at"],
        }
        with open(self._token_path, "w") as f:
            json.dump(data, f, indent=2)

    def _load_token_file(self) -> bool:
        """Load OAuth creds from token_path if it exists. Returns True on success."""
        if not self._token_path.exists():
            return False
        try:
            with open(self._token_path) as f:
                self._creds = json.load(f)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # API base + auth helpers
    # ------------------------------------------------------------------

    async def _api_get(self, url: str, params: dict | None = None) -> dict[str, Any]:
        """GET with Bearer auth, return JSON dict."""
        headers = {"Authorization": f"Bearer {await self._ensure_access()}"}
        resp = await self._http.get(url, params=params, headers=headers)
        return await resp.json(content_type=None)

    async def _api_post(self, url: str, json_body: dict | None = None) -> dict[str, Any]:
        """POST with Bearer auth, return JSON dict."""
        headers = {"Authorization": f"Bearer {await self._ensure_access()}"}
        resp = await self._http.post(url, json=json_body, headers=headers)
        return await resp.json(content_type=None)

    # ------------------------------------------------------------------
    # Domains
    # ------------------------------------------------------------------

    async def get_domains(self) -> list[Domain]:
        """
        Return Gmail's single domain.

        Gmail has exactly one domain (gmail.com); aliases are
        plus-addressing on the user's own domain.
        """
        return [Domain(id="gmail.com", domain="gmail.com", isActive=True, isPrivate=False)]

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def get_account_token(self, address: str, password: str) -> Token:
        """Return Token(id=address, token=address) — the address IS the token."""
        return Token(id=address, token=address)

    # ------------------------------------------------------------------
    # Account CRUD
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3)
    async def create_account(
        self, address: str | None = None, password: str | None = None
    ) -> Account:
        """
        Create a Gmail alias account (plus-addressing).

        Bases are the profile email plus the user's own sendAs aliases on
        the same domain (plus-addressing only delivers on Google-hosted
        domains this account owns).  MailClient passes a random
        ``user@domain`` address — it is replaced with a ``base+tag@domain``
        alias, round-robined across all bases.  No 99-alias cap.
        """
        bases = await self._get_base_addresses()  # triggers login if needed

        if not (address and _is_base_or_alias(address, bases)):
            address = self._next_alias(bases)

        return Account(
            id=address,
            address=address,
            password=password,
            quota=0,
            used=0,
            isDisabled=False,
            isDeleted=False,
            token=Token(id=address, token=address),
        )

    async def _get_base_addresses(self) -> list[str]:
        """
        Return usable base addresses for plus-alias generation, TTL-cached.

        Bases = profile email + the user's own sendAs aliases restricted to
        the same domain (a custom-SMTP domain isn't Google-hosted, so
        ``alias+tag@custom.tld`` would not be delivered here).
        """
        if self._bases and time.time() - self._bases_at < _BASES_CACHE_TTL:
            return self._bases

        profile = await self._api_get(f"{_API_BASE}/profile")
        self._base_email = profile["emailAddress"]
        domain = self._base_email.rsplit("@", 1)[-1].lower()

        bases = [self._base_email]
        try:
            settings = await self._api_get(f"{_API_BASE}/settings/sendAs")
            for send_as in settings.get("sendAs", []):
                alias_addr = send_as.get("sendAsEmail", "")
                if alias_addr and alias_addr.rsplit("@", 1)[-1].lower() == domain:
                    bases.append(alias_addr)
        except Exception as exc:
            logger.warning(
                "gmail: could not list sendAs aliases (%s); using profile only", exc
            )

        seen: set[str] = set()
        self._bases = [b for b in bases if not (b in seen or seen.add(b))]
        self._bases_at = time.time()
        logger.debug("gmail: %d base alias address(es): %s", len(self._bases), self._bases)
        return self._bases

    def _next_alias(self, bases: list[str]) -> str:
        """Generate the next plus-alias, round-robin across *bases* (no cap)."""
        if not bases:
            raise MailAPIError("gmail: no base address available")
        base = bases[self._rr_index % len(bases)]
        self._rr_index += 1
        base_local, base_domain = base.rsplit("@", 1)
        return f"{base_local}+{random_string(10)}@{base_domain}"

    @async_retry(max_attempts=3)
    async def get_account_by_id(self, account_id: str, token: str) -> Account:
        """Return Account with account_id as id and token as the bearer token."""
        address = account_id or token
        return Account(
            id=account_id,
            address=address,
            password=None,
            quota=0,
            used=0,
            isDisabled=False,
            isDeleted=False,
            token=Token(id=account_id, token=token),
        )

    async def delete_account(self, account_id: str, token: str) -> bool:
        """
        No-op for Gmail plus-addressing.

        Plus-aliases are forever valid — there is no API to delete an
        individual alias.  Deletion is meaningless in this model.
        """
        return True

    @async_retry(max_attempts=3)
    async def get_me(self, token: str) -> Account:
        """Fetch the profile and return Account for the authenticated user."""
        profile = await self._api_get(f"{_API_BASE}/profile")
        email = profile["emailAddress"]
        self._base_email = email
        return Account(
            id=email,
            address=email,
            password=None,
            quota=0,
            used=0,
            isDisabled=False,
            isDeleted=False,
            token=Token(id=email, token=token),
        )

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3)
    async def get_messages(self, alias: str, page: int = 1) -> Messages:
        """
        Fetch messages for the given alias.

        Uses q filter `to:("alias")`.  Page tokens are cached per alias
        for pagination.
        """
        params: dict[str, Any] = {
            "q": f'to:("{alias}")',
            "maxResults": 100,
        }
        if page > 1:
            stored = self._page_tokens.get(alias)
            if stored:
                params["pageToken"] = stored
            else:
                return Messages(**{"hydra:member": [], "hydra:totalItems": 0})

        try:
            data = await self._api_get(f"{_API_BASE}/messages", params=params)
        except Exception:
            # Invalid pageToken → retry once without it
            if "pageToken" in params:
                params.pop("pageToken")
                data = await self._api_get(f"{_API_BASE}/messages", params=params)
            else:
                raise

        # Store nextPageToken for the next call
        self._page_tokens[alias] = data.get("nextPageToken", "")

        message_list: list[dict] = data.get("messages") or []
        n = data.get("resultSizeEstimate", len(message_list))

        # Fetch full details concurrently
        members: list[Message] = []
        tasks = []
        for msg_entry in message_list:
            msg_id = msg_entry["id"]
            tasks.append(self._http.get(
                f"{_API_BASE}/messages/{msg_id}",
                params={"format": "full"},
                headers={"Authorization": f"Bearer {await self._ensure_access()}"},
            ))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception):
                logger.warning("Failed to fetch message detail: %s", result)
                continue
            raw_detail: dict = await result.json(content_type=None)
            member = _raw_to_message(raw_detail, alias, detail=False)
            if member:
                members.append(member)

        return Messages(
            **{
                "hydra:member": [m.model_dump(by_alias=True) for m in members],
                "hydra:totalItems": n,
            }
        )

    @async_retry(max_attempts=3)
    async def get_message_by_id(self, message_id: str, token: str) -> OneMessage:
        """Fetch full message detail including body and attachments."""
        data = await self._api_get(
            f"{_API_BASE}/messages/{message_id}",
            params={"format": "full"},
        )
        return _raw_to_one_message(data, token)

    @async_retry(max_attempts=3)
    async def delete_message(self, message_id: str, token: str) -> bool:
        """
        Trash a message.

        Gmail API only supports trashing (not permanent delete) for
        messages via this endpoint.
        """
        result = await self._api_post(
            f"{_API_BASE}/messages/{message_id}/trash"
        )
        return "id" in result or "threadId" in result

    @async_retry(max_attempts=3)
    async def mark_message_read(self, message_id: str, token: str) -> bool:
        """Mark a message as read by removing the UNREAD label."""
        result = await self._api_post(
            f"{_API_BASE}/messages/{message_id}/modify",
            json_body={"removeLabelIds": ["UNREAD"]},
        )
        return "id" in result or "threadId" in result

    @async_retry(max_attempts=3)
    async def get_message_source(self, message_id: str, token: str) -> MessageSource:
        """Fetch the raw MIME source of a message."""
        data = await self._api_get(
            f"{_API_BASE}/messages/{message_id}",
            params={"format": "raw"},
        )
        raw_b64 = data["raw"]
        # Decode base64url with padding
        padded = raw_b64 + "=" * (-len(raw_b64) % 4)
        raw_mime = base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")
        return MessageSource(
            id=message_id,
            downloadUrl="",
            data=raw_mime,
        )


# ---------------------------------------------------------------------------
# MIME body extraction — pure helper functions at module level
# ---------------------------------------------------------------------------


def _decode_body(data: str) -> str:
    """Base64url decode a string, handling missing padding."""
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _extract_parts(payload: dict) -> tuple[list[str], list[str], list[dict]]:
    """
    Recursively walk payload parts and extract text, html, and attachment dicts.

    Returns (text_parts, html_parts, attachment_dicts).
    """
    text: list[str] = []
    html: list[str] = []
    attachments: list[dict] = []
    parts = payload.get("parts", [])

    if not parts:
        # Single-part message
        mime = payload.get("mimeType", "")
        body = payload.get("body", {})
        data = body.get("data")
        if data and mime == "text/plain":
            text.append(_decode_body(data))
        elif data and mime == "text/html":
            html.append(_decode_body(data))
        return text, html, attachments

    for part in parts:
        mime = part.get("mimeType", "")
        part_body = part.get("body", {})
        data = part_body.get("data")
        filename = part.get("filename", "")
        attachment_id = part_body.get("attachmentId")

        if mime == "text/plain" and not attachment_id and not filename:
            if data:
                text.append(_decode_body(data))
        elif mime == "text/html" and not attachment_id and not filename:
            if data:
                html.append(_decode_body(data))
        elif attachment_id or filename:
            attachments.append({
                "id": attachment_id or "",
                "filename": filename,
                "mimeType": mime,
                "size": part_body.get("size", 0),
            })

        # Recurse into sub-parts
        sub_parts = part.get("parts", [])
        if sub_parts:
            sub_text, sub_html, sub_attachments = _extract_parts(part)
            text.extend(sub_text)
            html.extend(sub_html)
            attachments.extend(sub_attachments)

    return text, html, attachments


def _extract_from_headers(payload: dict) -> dict:
    """
    Extract from/to/subject/date from a payload's headers list.

    Returns {"from": MessageFromTo, "to": [MessageFromTo], "subject": str, "date": datetime|None}.
    """
    headers: list[dict] = payload.get("headers", [])

    header_map: dict[str, str] = {}
    for h in headers:
        name = h.get("name", "")
        value = h.get("value", "")
        header_map[name.lower()] = value

    # From
    from_addr = header_map.get("from", "")
    from_name, from_email = email.utils.parseaddr(from_addr)
    from_mf = MessageFromTo(name=from_name, address=from_email)

    # To
    to_addr = header_map.get("to", "")
    to_list: list[MessageFromTo] = []
    for name, addr in email.utils.getaddresses([to_addr]):
        to_list.append(MessageFromTo(name=name, address=addr))
    if not to_list and to_addr:
        to_list.append(MessageFromTo(name="", address=to_addr))

    # Subject
    subject = header_map.get("subject", "")

    # Date
    date_raw = header_map.get("date", "")
    date_dt: datetime | None = None
    if date_raw:
        try:
            date_dt = email.utils.parsedate_to_datetime(date_raw)
        except Exception:
            pass

    return {"from": from_mf, "to": to_list, "subject": subject, "date": date_dt}


def _is_base_or_alias(address: str, bases: list[str]) -> bool:
    """
    True if *address* is one of the bases itself or a ``base+tag`` variant.

    Used by create_account to honor explicit calls that target a known
    base alias; anything else (e.g. a random ``xyz@gmail.com`` generated
    by MailClient) is replaced with a regenerated plus-alias.
    """
    if "@" not in address:
        return False
    local = address.rsplit("@", 1)[0]
    for base in bases:
        base_local = base.rsplit("@", 1)[0]
        if local == base_local or local.startswith(base_local + "+"):
            return True
    return False


def _raw_to_message(raw: dict, alias: str, detail: bool = False) -> Message | OneMessage:
    """
    Convert a Gmail API message dict to Message or OneMessage.

    If *detail* is True, returns a OneMessage with body/attachments.
    Otherwise returns a Message (list item).
    """
    msgid = raw.get("id", "")
    label_ids: list[str] = raw.get("labelIds", [])
    seen = "UNREAD" not in label_ids

    # Extract headers from payload
    headers_info = _extract_from_headers(raw.get("payload", {}))

    # Date
    internal_date_ms = raw.get("internalDate", "0")
    try:
        created_at = datetime.fromtimestamp(int(internal_date_ms) / 1000, tz=timezone.utc)
    except (ValueError, TypeError):
        created_at = None

    snippet = raw.get("snippet", "")
    size_estimate = raw.get("sizeEstimate", 0)

    if detail:
        payload = raw.get("payload", {})
        text_parts, html_parts, attachment_dicts = _extract_parts(payload)

        text_body = " ".join(text_parts) if text_parts else ""
        html_body_list = html_parts if html_parts else []

        attachments: list[Attachment] | None = None
        if attachment_dicts:
            api_base = f"https://gmail.googleapis.com/gmail/v1/users/me"
            attachments = [
                Attachment(
                    id=a["id"],
                    filename=a["filename"],
                    contentType=a.get("mimeType", ""),
                    disposition="attachment",
                    transferEncoding="base64",
                    related=False,
                    size=a.get("size", 0),
                    downloadUrl=f"{api_base}/messages/{msgid}/attachments/{a['id']}" if a["id"] else "",
                )
                for a in attachment_dicts
            ]

        return OneMessage(
            **{
                "id": msgid,
                "accountId": alias,
                "msgid": msgid,
                "from": headers_info["from"],
                "to": headers_info["to"],
                "cc": [],
                "bcc": [],
                "subject": headers_info["subject"],
                "flagged": False,
                "isDeleted": False,
                "verifications": {},
                "retention": False,
                "retentionDate": None,
                "text": text_body,
                "html": html_body_list,
                "hasAttachments": bool(attachments),
                "attachments": attachments or None,
                "size": size_estimate,
                "downloadUrl": "",
                "createdAt": created_at,
                "updatedAt": created_at,
            }
        )
    else:
        has_attachments = "ATTACHMENTS" in label_ids
        return Message(
            **{
                "id": msgid,
                "accountId": alias,
                "msgid": msgid,
                "from": headers_info["from"],
                "to": headers_info["to"],
                "subject": headers_info["subject"],
                "intro": snippet,
                "seen": seen,
                "isDeleted": False,
                "hasAttachments": has_attachments,
                "size": size_estimate,
                "downloadUrl": "",
                "createdAt": created_at,
                "updatedAt": created_at,
            }
        )


def _raw_to_one_message(raw: dict, token: str) -> OneMessage:
    """Convert a Gmail API full message dict to OneMessage."""
    return _raw_to_message(raw, token, detail=True)
