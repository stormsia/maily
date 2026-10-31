from __future__ import annotations

import logging
import random
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ...crypto import decrypt, encrypt
from ...db.models import Mailbox, Message
from ...exceptions import MailConflictError, MailNotFoundError, MailValidationError
from ...providers.base import MailboxInfo, MailboxSpec, MessageDetail, MessageSummary
from ...providers.registry import ProviderRegistry
from ...settings import Settings
from . import domain_cache as dc
from .stats_history import (
    EVENT_MAILBOX_CREATED,
    EVENT_MESSAGE_RECEIVED,
    extract_domain,
    record,
)

logger = logging.getLogger("mailtmapi.mailboxes")


async def _undo_provider_create(prov, info: MailboxInfo) -> None:
    """Best-effort delete of an account the provider already created."""
    try:
        await prov.delete_mailbox(info)
    except Exception as exc:  # noqa: BLE001 - cleanup must not hide the original error
        logger.warning("create_mailbox: provider cleanup failed for %s: %s", info.address, exc)


def as_naive_utc(dt: datetime | None) -> datetime | None:
    """Normalize any datetime to naive UTC (the storage convention everywhere).

    Avoids mixing zone-aware (`…+00:00`) and naive values in the SQLite
    columns, which would break SQL date functions and comparisons.
    """
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _received_bucket(dt: datetime | None, now: datetime) -> date:
    """Receipt date for ledger bucketing.

    Falls back to *today* when the provider sent no timestamp or a clearly
    broken one (epoch, far future) — otherwise a garbage date would silently
    drop the message out of the 7-day chart window.
    """
    rec = as_naive_utc(dt)
    if rec is None or rec < now - timedelta(days=30) or rec > now + timedelta(days=1):
        return now.date()
    return rec.date()


def to_mailbox_info(row: Mailbox, secret: str) -> MailboxInfo:
    password = decrypt(secret, row.password_enc) if row.password_enc else None
    return MailboxInfo(
        provider=row.provider,
        address=row.address,
        token=decrypt(secret, row.mailbox_token_enc),
        provider_account_id=row.provider_account_id,
        password=password,
        parent_id=row.parent_id,
    )


def _is_valid_address(address: str) -> bool:
    """local@domain — единственный формат, который попадает в БД."""
    parts = address.split("@")
    return len(parts) == 2 and all(parts)


async def get_mailbox(session: AsyncSession, mailbox_id: int) -> Mailbox:
    row = await session.get(Mailbox, mailbox_id)
    if row is None or row.is_deleted:
        raise MailNotFoundError(f"mailbox {mailbox_id} not found")
    return row


async def get_mailbox_by_address(session: AsyncSession, email: str) -> Mailbox:
    row = (
        await session.execute(
            select(Mailbox).where(Mailbox.address == email, Mailbox.is_deleted.is_(False))
        )
    ).scalar_one_or_none()
    if row is None:
        raise MailNotFoundError(f"mailbox {email} not found")
    return row


async def create_mailbox(
    session: AsyncSession,
    registry: ProviderRegistry,
    settings: Settings,
    *,
    provider: str | None,
    domain: str | None,
    parent_id: int | None,
    address: str | None,
    password: str | None,
    owner_key_id: int | None = None,
    allowed_parent_ids: list[int] | None = None,
) -> Mailbox:
    slug = provider
    if not slug and domain:
        slug = await dc.find_provider_for_domain(session, registry, settings, domain)
    if not slug:
        providers = registry.all()
        if not providers:
            raise MailValidationError("no providers registered")
        slug = random.choice(providers).slug
    prov = registry.get(slug)
    # Domain lookup may have committed already; either way the provider call
    # must not run inside an open write transaction.
    await session.commit()
    spec = MailboxSpec(
        address=address,
        domain=domain,
        parent_id=parent_id,
        password=password,
        allowed_parent_ids=(
            tuple(allowed_parent_ids)
            if slug == "gmail" and allowed_parent_ids is not None
            else None
        ),
    )
    info = await prov.create_mailbox(spec)
    if info is None or not getattr(info, "address", None) or not _is_valid_address(info.address):
        addr_repr = getattr(info, "address", None) if info is not None else None
        raise MailValidationError(
            f"provider {slug!r} returned invalid address {addr_repr!r}; expected local@domain"
        )
    if slug == "gmail" and "+" not in info.address.split("@", 1)[0]:
        raise MailValidationError("gmail address must be a plus-alias")
    secret = settings.resolved_secret_key()
    row = Mailbox(
        provider=info.provider,
        address=info.address,
        parent_id=info.parent_id,
        password_enc=encrypt(secret, info.password) if info.password else None,
        mailbox_token_enc=encrypt(secret, info.token or ""),
        provider_account_id=info.provider_account_id,
        is_active=True,
        is_deleted=False,
        owner_key_id=owner_key_id,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        await _undo_provider_create(prov, info)
        raise MailConflictError(f"mailbox {info.address} already exists") from exc
    except Exception:
        await session.rollback()
        await _undo_provider_create(prov, info)
        raise
    await record(
        session,
        provider=row.provider,
        domain=extract_domain(row.address),
        owner_key_id=row.owner_key_id,
        event=EVENT_MAILBOX_CREATED,
    )
    return row


async def upsert_messages(
    session: AsyncSession, mailbox: Mailbox, summaries: list[MessageSummary]
) -> list[Message]:
    out: list[Message] = []
    new_by_day: dict[date, int] = {}
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    ids = [s.id for s in summaries]
    existing_rows = (
        (
            await session.execute(
                select(Message).where(
                    Message.mailbox_id == mailbox.id,
                    Message.message_api_id.in_(ids),
                )
            )
        )
        .scalars()
        .all()
        if ids
        else []
    )
    by_id = {row.message_api_id: row for row in existing_rows}
    for s in summaries:
        existing = by_id.get(s.id)
        if existing is None:
            existing = Message(
                mailbox_id=mailbox.id,
                provider=mailbox.provider,
                message_api_id=s.id,
            )
            session.add(existing)
            day = _received_bucket(s.received_at, now)
            new_by_day[day] = new_by_day.get(day, 0) + 1
        existing.subject = s.subject or ""
        existing.from_address = s.from_.address or ""
        existing.from_name = s.from_.name or ""
        if s.seen:  # provider flag never downgrades a locally-marked read
            existing.seen = True
        existing.has_attachments = s.has_attachments
        existing.size = s.size
        existing.received_at = as_naive_utc(s.received_at)
        if isinstance(s, MessageDetail):
            if s.text:
                existing.body_text = s.text
            if s.html:
                existing.body_html = "\n".join(s.html)
        out.append(existing)
    # Bucket the "received" event by the message's actual receipt date (not the
    # sync date) so the 7-day incoming chart reflects the true per-day inflow —
    # and survives later retention deletes, since receive events live in the ledger.
    mailbox_domain = extract_domain(mailbox.address)
    for day, count in new_by_day.items():
        await record(
            session,
            provider=mailbox.provider,
            domain=mailbox_domain,
            owner_key_id=mailbox.owner_key_id,
            event=EVENT_MESSAGE_RECEIVED,
            count=count,
            when=day,
        )
    await session.flush()
    return out
