from __future__ import annotations

import html as html_lib
import logging
import re
from typing import Any
from urllib.parse import urlencode

from ...exceptions import (
    MailAPIError,
    MailAuthError,
    MailNotFoundError,
    MailValidationError,
)
from ...http import HttpClient
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
    ProviderCapabilities,
    Target,
    TargetKind,
    parse_from_value,
    parse_iso,
    split_address,
)

logger = logging.getLogger(__name__)

_CACHE_TTL = 600.0
_BASE_URL = "https://temp.tf"

_DEFAULT_DOMAINS = ["outlook.com", "hotmail.com", "gmail.com", "high.edu.pl"]

_DOMAIN_TO_PROVIDER = {
    "outlook.com": "outlook",
    "hotmail.com": "hotmail",
    "gmail.com": "gmail",
    "high.edu.pl": "high.edu.pl",
}

_RESERVED_HIGH_EDU_PL = {
    "inbox",
    "catchall",
    "postmaster",
    "mail",
    "admin",
    "hostmaster",
    "webmaster",
    "noreply",
    "no-reply",
}

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/126.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "Referer": f"{_BASE_URL}/",
    "Origin": _BASE_URL,
}


def _extract_domains_from_html(html: str) -> list[str]:
    """Parse list of supported domains from temp.tf homepage HTML."""
    if not html:
        return list(_DEFAULT_DOMAINS)
    section = re.search(
        r"Providers.*?(?=Syntaxes|New address|<button|$)",
        html,
        re.DOTALL | re.IGNORECASE,
    )
    search_scope = section.group(0) if section else html
    candidates = re.findall(
        r"(?:>|\b)([a-zA-Z0-9.\-_]+\.[a-zA-Z]{2,}(?:\.[a-zA-Z]{2,})?)(?:<|\b)",
        search_scope,
    )
    domains: list[str] = []
    for c in candidates:
        c = c.strip(" \t\r\n<>.").lower()
        if (
            "." in c
            and not c.startswith(".")
            and not c.endswith(".")
            and c not in domains
            and not any(c.startswith(p) for p in ("slate", "text-", "font-", "bg-", "border-"))
        ):
            domains.append(c)
    return domains or list(_DEFAULT_DOMAINS)


def _extract_syntaxes_from_html(html: str) -> list[str]:
    """Parse list of supported syntaxes from temp.tf homepage HTML."""
    if not html:
        return ["dot", "plus"]
    section = re.search(
        r"Syntaxes.*?(?=New address|<button|$)",
        html,
        re.DOTALL | re.IGNORECASE,
    )
    if not section:
        return ["dot", "plus"]
    candidates = re.findall(r"<span>([a-zA-Z0-9]+)</span>", section.group(0), re.IGNORECASE)
    syntaxes = [c.strip().lower() for c in candidates if c.strip().lower() in ("dot", "plus")]
    return syntaxes or ["dot", "plus"]


def _validate_temp_tf_address(address: str) -> tuple[str, str]:
    """Validate that custom/recovered address conforms to temp.tf provider constraints."""
    user, domain = split_address(address)
    user_lower = user.strip().lower()
    domain_lower = domain.strip().lower()

    if domain_lower not in _DOMAIN_TO_PROVIDER:
        supported = ", ".join(sorted(_DOMAIN_TO_PROVIDER.keys()))
        raise MailValidationError(
            f"temp.tf: domain {domain!r} is not supported. Supported domains: {supported}",
            status_code=400,
        )

    if domain_lower in ("outlook.com", "hotmail.com"):
        if "+" not in user_lower or user_lower.startswith("+") or user_lower.endswith("+"):
            raise MailValidationError(
                f"temp.tf: {domain_lower} requires a plus alias (e.g. name+tag@{domain_lower})",
                status_code=400,
            )
        parts = user_lower.split("+")
        if len(parts) != 2 or not parts[1].isalnum():
            raise MailValidationError(
                f"temp.tf: invalid plus alias syntax for {domain_lower}",
                status_code=400,
            )

    elif domain_lower == "high.edu.pl":
        if "+" in user_lower or "." in user_lower:
            raise MailValidationError(
                "temp.tf: high.edu.pl does not support dot or plus aliases",
                status_code=400,
            )
        if not re.fullmatch(r"[a-z0-9]{1,10}", user_lower):
            raise MailValidationError(
                "temp.tf: high.edu.pl local part must be 1-10 alphanumeric characters",
                status_code=400,
            )
        if user_lower in _RESERVED_HIGH_EDU_PL:
            raise MailValidationError(
                f"temp.tf: username {user!r} is reserved on high.edu.pl",
                status_code=400,
            )

    elif domain_lower == "gmail.com":
        has_dot = "." in user_lower
        has_plus = "+" in user_lower
        if not (has_dot or has_plus):
            raise MailValidationError(
                "temp.tf: gmail.com addresses require a dot or plus alias (e.g. first.last@gmail.com or name+tag@gmail.com)",
                status_code=400,
            )
        if has_plus:
            parts = user_lower.split("+")
            if len(parts) != 2 or not parts[1].isalnum():
                raise MailValidationError(
                    "temp.tf: invalid plus alias syntax for gmail.com",
                    status_code=400,
                )

    return user_lower, domain_lower


def _resolve_provider_and_syntax(
    domain: str | None,
    gmail_dot: bool = True,
    gmail_plus: bool = True,
) -> tuple[str, str, str]:
    """Determine query parameters (providers, dot, plus) for /api/account.

    Rules according to temp.tf:
    - outlook / hotmail: require plus aliases, do not work without plus (dot=0, plus=1).
    - high.edu.pl: no aliases (dot=0, plus=0).
    - gmail: supports plus and dot aliases (dot=1, plus=1 or as configured).
    - If domain is not specified, all providers with dot=1, plus=1 are requested.
    """
    if not domain:
        dot_str = "1" if gmail_dot else "0"
        plus_str = "1" if gmail_plus else "0"
        if dot_str == "0" and plus_str == "0":
            dot_str, plus_str = "1", "1"
        return "outlook,hotmail,gmail,high.edu.pl", dot_str, plus_str

    domain_raw = domain.strip().lower()

    # Check for syntax modifier in domain specifier: e.g. "gmail.com:dot", "gmail:plus"
    modifier = None
    if ":" in domain_raw:
        domain_raw, modifier = domain_raw.split(":", 1)
    elif "+" in domain_raw:
        domain_raw, modifier = domain_raw.split("+", 1)

    prov_key = _DOMAIN_TO_PROVIDER.get(domain_raw)
    if not prov_key:
        if domain_raw in ("outlook", "hotmail", "gmail"):
            prov_key = domain_raw
        elif domain_raw in ("high.edu.pl", "high.edu", "highedupl"):
            prov_key = "high.edu.pl"
        else:
            raise MailValidationError(
                f"temp.tf: unsupported domain {domain!r}",
                status_code=400,
            )

    if prov_key in ("outlook", "hotmail"):
        return prov_key, "0", "1"
    elif prov_key == "high.edu.pl":
        return prov_key, "0", "0"
    elif prov_key == "gmail":
        modifier_map = {
            "dot": ("gmail", "1", "0"),
            "plus": ("gmail", "0", "1"),
            "both": ("gmail", "1", "1"),
        }
        if modifier in modifier_map:
            return modifier_map[modifier]
        dot_str = "1" if gmail_dot else "0"
        plus_str = "1" if gmail_plus else "0"
        if dot_str == "0" and plus_str == "0":
            dot_str, plus_str = "1", "1"
        return "gmail", dot_str, plus_str
    else:
        return prov_key, "0", "1"


def _clean_body_text(html_content: str) -> str:
    """Convert HTML message body to clean plain text, removing style/script blocks."""
    if not html_content:
        return ""
    # Strip script blocks, style blocks, and comments first
    text = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    # Convert block/break elements to line breaks
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(?:p|div|tr|h[1-6]|li)>", "\n\n", text)
    # Strip remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode HTML entities (&nbsp;, &amp;, etc.)
    text = html_lib.unescape(text)
    # Normalize whitespaces and consecutive newlines
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def _parse_message(
    raw: dict[str, Any],
    fallback_address: str,
    base_url: str,
) -> MessageDetail:
    msg_id = str(raw.get("id") or "")
    subject = str(raw.get("subject") or "")
    from_raw = str(raw.get("from") or "")
    party = parse_from_value(from_raw)
    to_addr = str(raw.get("to") or fallback_address)

    body_raw = str(raw.get("body") or "")
    content_type = str(raw.get("bodyContentType") or "").lower()

    if content_type == "html" or ("<" in body_raw and ">" in body_raw):
        html_list = [body_raw]
        text = _clean_body_text(body_raw)
    else:
        html_list = []
        text = body_raw

    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    intro = first_line[:200]

    attachments: list[Attachment] = []
    for a in raw.get("attachments") or []:
        if not isinstance(a, dict):
            continue
        att_id = str(a.get("id") or "")
        filename = str(a.get("filename") or a.get("name") or att_id or "")
        ct = str(a.get("contentType") or a.get("content_type") or "application/octet-stream")
        size = int(a.get("size") or 0)
        query = urlencode({"email": fallback_address, "messageId": msg_id, "attachmentId": att_id})
        dl_url = str(a.get("url") or a.get("download_url") or f"{base_url}/api/attachment?{query}")
        attachments.append(
            Attachment(
                id=att_id,
                filename=filename,
                content_type=ct,
                size=size,
                download_url=dl_url,
            )
        )

    return MessageDetail(
        id=msg_id,
        subject=subject,
        from_=party,
        to=[Party(address=to_addr)],
        intro=intro,
        seen=bool(raw.get("seen") or raw.get("read") or raw.get("is_read", False)),
        has_attachments=bool(attachments) or bool(raw.get("attachments")),
        size=int(raw.get("size") or len(body_raw)),
        received_at=parse_iso(raw.get("date") or raw.get("created_at")),
        text=text,
        html=html_list,
        attachments=attachments,
    )


class TempTF(HttpProvider):
    """temp.tf provider.

    The service generates temporary mailboxes on outlook.com, hotmail.com,
    gmail.com, and high.edu.pl domains using plus- and dot-aliases.
    """

    slug = "temp.tf"
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

    def __init__(
        self,
        http: HttpClient | None = None,
        proxy: str | None = None,
        *,
        gmail_dot: bool = True,
        gmail_plus: bool = True,
    ) -> None:
        super().__init__(http=http, proxy=proxy)
        self.gmail_dot = gmail_dot
        self.gmail_plus = gmail_plus
        # Mailbox-isolated cache: {mailbox_address: {message_id: MessageDetail}}
        self._messages: dict[str, dict[str, MessageDetail]] = {}

    @async_retry()
    async def _fetch_targets(self, *, known: set[str] | None = None) -> list[Target]:
        headers = dict(self.default_headers)
        headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        try:
            resp = await self._http.get(f"{self.BASE_URL}/", headers=headers)
            domains = _extract_domains_from_html(resp.text)
        except Exception as exc:
            logger.warning("temp.tf: failed to fetch targets HTML: %s; using defaults", exc)
            domains = list(_DEFAULT_DOMAINS)

        if not domains:
            raise MailAPIError("temp.tf: no targets available")

        return [Target(id=dm, kind="domain", provider=self.slug, label=dm) for dm in domains]

    @async_retry()
    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        if spec.address:
            user_lower, domain_lower = _validate_temp_tf_address(spec.address)
            normalized_address = f"{user_lower}@{domain_lower}"
            return MailboxInfo(
                provider=self.slug,
                address=normalized_address,
                token="",
                provider_account_id=normalized_address,
                password=spec.password,
            )

        providers, dot, plus = _resolve_provider_and_syntax(
            spec.domain,
            gmail_dot=self.gmail_dot,
            gmail_plus=self.gmail_plus,
        )
        params = {"providers": providers, "dot": dot, "plus": plus}
        data = await self._get_json(f"{self.BASE_URL}/api/account", params=params)
        if not isinstance(data, dict) or not data.get("email"):
            raise MailAPIError(f"temp.tf: failed to create mailbox (response: {data!r})")

        email = str(data["email"]).strip().lower()
        return MailboxInfo(
            provider=self.slug,
            address=email,
            token="",
            provider_account_id=email,
            password=spec.password,
        )

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        self._messages.pop(mailbox.address.strip().lower(), None)
        return True

    @async_retry()
    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        headers = dict(self.default_headers)
        headers["Content-Type"] = "application/json"
        body = {"email": mailbox.address, "wait": False}
        try:
            resp = await self._http.post(
                f"{self.BASE_URL}/api/check",
                json=body,
                headers=headers,
            )
            data = resp.json()
        except MailNotFoundError:
            return []
        except MailAuthError as exc:
            logger.warning("temp.tf: address %s rejected or unauthorized: %s", mailbox.address, exc)
            return []

        raw_messages = (
            data.get("data") if isinstance(data, dict) else (data if isinstance(data, list) else [])
        )
        if not isinstance(raw_messages, list):
            return []

        addr = mailbox.address.strip().lower()
        box_cache = self._messages.setdefault(addr, {})
        summaries: list[MessageSummary] = []
        for raw in raw_messages:
            if not isinstance(raw, dict):
                continue
            detail = _parse_message(raw, mailbox.address, self.BASE_URL)
            box_cache[detail.id] = detail
            summaries.append(detail)

        # Evict old mailboxes if overall cache grows excessively
        if len(self._messages) > 1000:
            for k in list(self._messages.keys())[:500]:
                self._messages.pop(k, None)

        return summaries

    @async_retry()
    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        addr = mailbox.address.strip().lower()
        box_cache = self._messages.get(addr, {})
        if message_id in box_cache:
            return box_cache[message_id]

        await self.list_messages(mailbox)
        box_cache = self._messages.get(addr, {})
        if message_id in box_cache:
            return box_cache[message_id]

        raise MailNotFoundError(
            f"temp.tf: message {message_id!r} not found for {mailbox.address}",
            status_code=404,
        )

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        addr = mailbox.address.strip().lower()
        if addr in self._messages:
            self._messages[addr].pop(message_id, None)
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        addr = mailbox.address.strip().lower()
        msg = self._messages.get(addr, {}).get(message_id)
        if msg:
            msg.seen = True
        return True

    @async_retry()
    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        detail = await self.get_message(mailbox, message_id)
        data = detail.html[0] if detail.html else detail.text
        return MessageSource(id=message_id, data=data, download_url="")


TempTf = TempTF
