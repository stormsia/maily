from __future__ import annotations

import random
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...crypto import decrypt, encrypt
from ...db.models import Mailbox, Message
from ...exceptions import MailNotFoundError, MailValidationError
from ...providers.base import MailboxInfo, MailboxSpec, MessageSummary
from ...providers.registry import ProviderRegistry
from ...settings import Settings
from . import domain_cache as dc
from .stats_history import (
    EVENT_MAILBOX_CREATED,
    EVENT_MESSAGE_RECEIVED,
    record,
)


def as_naive_utc(dt: datetime | None) -> datetime | None:
    """Normalize any datetime to naive UTC (the storage convention everywhere).

    Avoids mixing zone-aware (`…+00:00`) and naive values in the SQLite
    columns, which would break SQL date functions and comparisons.
    """
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


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
        await session.execute(select(Mailbox).where(Mailbox.address == email))
    ).scalar_one_or_none()
    if row is None or row.is_deleted:
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
    info = await prov.create_mailbox(
        MailboxSpec(address=address, domain=domain, parent_id=parent_id, password=password)
    )
    if not _is_valid_address(info.address):
        raise MailValidationError(
            f"provider {slug!r} returned invalid address {info.address!r}; expected local@domain"
        )
    secret = settings.resolved_secret_key()
    row = Mailbox(
        provider=info.provider,
        address=info.address,
        parent_id=info.parent_id,
        password_enc=encrypt(secret, info.password) if info.password else None,
        mailbox_token_enc=encrypt(secret, info.token),
        provider_account_id=info.provider_account_id,
        is_active=True,
        is_deleted=False,
    )
    session.add(row)
    await session.flush()
    await record(session, provider=row.provider, event=EVENT_MAILBOX_CREATED)
    return row


async def upsert_messages(
    session: AsyncSession, mailbox: Mailbox, summaries: list[MessageSummary]
) -> list[Message]:
    out: list[Message] = []
    new_count = 0
    for s in summaries:
        existing = (
            await session.execute(
                select(Message).where(
                    Message.mailbox_id == mailbox.id,
                    Message.message_api_id == s.id,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            existing = Message(
                mailbox_id=mailbox.id,
                provider=mailbox.provider,
                message_api_id=s.id,
            )
            session.add(existing)
            new_count += 1
        existing.subject = s.subject or ""
        existing.from_address = s.from_.address or ""
        existing.from_name = s.from_.name or ""
        if s.seen:  # provider flag never downgrades a locally-marked read
            existing.seen = True
        existing.has_attachments = s.has_attachments
        existing.size = s.size
        existing.received_at = as_naive_utc(s.received_at)
        existing.is_deleted = False
        out.append(existing)
    if new_count:
        await record(session, provider=mailbox.provider, event=EVENT_MESSAGE_RECEIVED, count=new_count)
    await session.flush()
    return out
