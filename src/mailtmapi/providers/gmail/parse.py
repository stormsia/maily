from __future__ import annotations

import base64
import email.utils
from contextlib import suppress
from datetime import datetime, timezone

from mailtmapi.exceptions import MailValidationError
from mailtmapi.providers.base import Attachment, MessageDetail, MessageSource, MessageSummary, Party

_API_BASE = "https://gmail.googleapis.com/gmail/v1/users/me"
_RECIPIENT_HEADERS = ("to", "cc", "delivered-to")
_PLUS_ALIAS_DETAIL = "gmail address must be a plus-alias"


def decode_body(data: str) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def is_base_or_alias(address: str, bases: list[str]) -> bool:
    if "@" not in address:
        return False
    stripped = strip_plus(address).lower()
    return any(strip_plus(base).lower() == stripped for base in bases)


def require_plus_alias(address: str) -> None:
    """Reject a Gmail mailbox whose local part has no plus tag."""
    local = address.split("@", 1)[0]
    if "+" not in local:
        raise MailValidationError(_PLUS_ALIAS_DETAIL)


def addressed_to(raw: dict, mailbox_address: str) -> bool:
    """True when To, Cc, or Delivered-To contains the full mailbox address."""
    wanted = mailbox_address.lower()
    headers = {
        str(header.get("name", "")).lower(): str(header.get("value", ""))
        for header in raw.get("payload", {}).get("headers", [])
    }
    for name in _RECIPIENT_HEADERS:
        parsed = email.utils.getaddresses([headers.get(name, "")])
        if any(address.lower() == wanted for _name, address in parsed):
            return True
    return False


def strip_plus(email: str) -> str:
    if "@" not in email:
        return email
    local, domain = email.rsplit("@", 1)
    return f"{local.split('+', 1)[0]}@{domain}"


def extract_parts(payload: dict) -> tuple[list[str], list[str], list[dict]]:
    text: list[str] = []
    html: list[str] = []
    attachments: list[dict] = []
    parts = payload.get("parts", [])

    if not parts:
        mime = payload.get("mimeType", "")
        body = payload.get("body", {})
        data = body.get("data")
        if data and mime == "text/plain":
            text.append(decode_body(data))
        elif data and mime == "text/html":
            html.append(decode_body(data))
        return text, html, attachments

    for part in parts:
        mime = part.get("mimeType", "")
        part_body = part.get("body", {})
        data = part_body.get("data")
        filename = part.get("filename", "")
        attachment_id = part_body.get("attachmentId")

        if mime == "text/plain" and not attachment_id and not filename:
            if data:
                text.append(decode_body(data))
        elif mime == "text/html" and not attachment_id and not filename:
            if data:
                html.append(decode_body(data))
        elif attachment_id or filename:
            attachments.append({
                "id": attachment_id or "",
                "filename": filename,
                "mimeType": mime,
                "size": part_body.get("size", 0),
            })

        if part.get("parts"):
            sub_text, sub_html, sub_attachments = extract_parts(part)
            text.extend(sub_text)
            html.extend(sub_html)
            attachments.extend(sub_attachments)

    return text, html, attachments


def extract_headers(payload: dict) -> dict:
    header_map: dict[str, str] = {}
    for h in payload.get("headers", []):
        header_map[h.get("name", "").lower()] = h.get("value", "")

    from_name, from_email = email.utils.parseaddr(header_map.get("from", ""))
    to_list: list[Party] = []
    for name, addr in email.utils.getaddresses([header_map.get("to", "")]):
        to_list.append(Party(name=name, address=addr))
    to_addr = header_map.get("to", "")
    if not to_list and to_addr:
        to_list.append(Party(address=to_addr))

    date_dt: datetime | None = None
    date_raw = header_map.get("date", "")
    if date_raw:
        with suppress(Exception):
            date_dt = email.utils.parsedate_to_datetime(date_raw)

    return {
        "from": Party(name=from_name, address=from_email),
        "to": to_list,
        "subject": header_map.get("subject", ""),
        "date": date_dt,
    }


def _received_at(raw: dict, fallback: datetime | None) -> datetime | None:
    internal_date_ms = raw.get("internalDate", "0")
    try:
        return datetime.fromtimestamp(int(internal_date_ms) / 1000, tz=timezone.utc)
    except (ValueError, TypeError):
        return fallback


def raw_to_summary(raw: dict) -> MessageSummary:
    headers = extract_headers(raw.get("payload", {}))
    label_ids: list[str] = raw.get("labelIds", [])
    return MessageSummary(
        id=raw.get("id", ""),
        subject=headers["subject"],
        from_=headers["from"],
        to=headers["to"],
        intro=raw.get("snippet", ""),
        seen="UNREAD" not in label_ids,
        has_attachments="ATTACHMENTS" in label_ids,
        size=raw.get("sizeEstimate", 0) or 0,
        received_at=_received_at(raw, headers["date"]),
    )


def raw_to_detail(raw: dict) -> MessageDetail:
    summary = raw_to_summary(raw)
    text_parts, html_parts, attachment_dicts = extract_parts(raw.get("payload", {}))
    msgid = summary.id
    attachments = [
        Attachment(
            id=a["id"],
            filename=a["filename"],
            content_type=a.get("mimeType", ""),
            size=a.get("size", 0),
            download_url=(
                f"{_API_BASE}/messages/{msgid}/attachments/{a['id']}" if a["id"] else ""
            ),
        )
        for a in attachment_dicts
    ]
    return MessageDetail(
        id=summary.id,
        subject=summary.subject,
        from_=summary.from_,
        to=summary.to,
        intro=summary.intro,
        seen=summary.seen,
        has_attachments=bool(attachments) or summary.has_attachments,
        size=summary.size,
        received_at=summary.received_at,
        text=" ".join(text_parts) if text_parts else "",
        html=html_parts,
        attachments=attachments,
    )


def raw_to_source(raw: dict, message_id: str) -> MessageSource:
    raw_b64 = raw.get("raw", "") or ""
    return MessageSource(id=message_id, data=decode_body(raw_b64), download_url="")
