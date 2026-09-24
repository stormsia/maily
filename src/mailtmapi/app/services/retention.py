from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker as AsyncSessionFactory

from ...db.engine import retry_on_lock
from ...db.models import Mailbox, Message, Retention
from ...exceptions import MailValidationError
from ...providers.registry import ProviderRegistry
from ...settings import Settings
from ..services import mailboxes as svc
from ..services.stats_history import (
    EVENT_MAILBOX_DELETED,
    EVENT_MESSAGE_DELETED,
    prune,
    record,
)

logger = logging.getLogger("mailtmapi.retention")

_sweep_lock = asyncio.Lock()


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def get_retention(session) -> list[Retention]:
    return list((await session.execute(select(Retention).order_by(Retention.provider))).scalars())


async def set_retention(
    session,
    provider: str,
    mailbox_ttl_hours: int | None,
    message_ttl_hours: int | None,
) -> Retention:
    for name, ttl in (("mailbox_ttl_hours", mailbox_ttl_hours), ("message_ttl_hours", message_ttl_hours)):
        if ttl is not None and ttl < 1:
            raise MailValidationError(f"{name} must be >= 1 or null")
    if mailbox_ttl_hours is None and message_ttl_hours is None:
        raise MailValidationError("at least one ttl required")
    row = await session.get(Retention, provider)
    if row is None:
        row = Retention(provider=provider)
        session.add(row)
    row.mailbox_ttl_hours = mailbox_ttl_hours
    row.message_ttl_hours = message_ttl_hours
    await session.flush()
    return row


async def delete_retention(session, provider: str) -> bool:
    row = await session.get(Retention, provider)
    if row is None:
        return False
    await session.delete(row)
    return True


async def _write(factory: AsyncSessionFactory[AsyncSession], operation: Callable[[AsyncSession], Awaitable[None]]) -> None:
    """One short write transaction in a fresh session, retried on SQLITE_BUSY.

    Retrying ``session.commit`` on a session that already failed is useless:
    the transaction is dead. A new session is the only retry that works.
    """

    async def _do() -> None:
        async with factory() as session:
            await operation(session)
            await session.commit()

    await retry_on_lock(_do)


async def run_sweep(
    factory: AsyncSessionFactory[AsyncSession],
    registry: ProviderRegistry,
    settings: Settings,
) -> dict:
    async with _sweep_lock, factory() as session:
        mailboxes_deleted = 0
        messages_deleted = 0
        mailbox_deletes: dict[str, int] = {}
        message_deletes: dict[str, int] = {}
        secret = settings.resolved_secret_key()
        retentions = list((await session.execute(select(Retention))).scalars())
        mailbox_ttl = {r.provider: r.mailbox_ttl_hours for r in retentions if r.mailbox_ttl_hours}
        message_ttl = {r.provider: r.message_ttl_hours for r in retentions if r.message_ttl_hours}

    # Soft-deleted rows were already removed upstream. One write, then the
    # session is closed before any provider I/O.
    async def _reap(s: AsyncSession) -> None:
        await s.execute(
            delete(Message).where(
                or_(
                    Message.is_deleted.is_(True),
                    Message.mailbox_id.in_(select(Mailbox.id).where(Mailbox.is_deleted.is_(True))),
                )
            )
        )
        await s.execute(delete(Mailbox).where(Mailbox.is_deleted.is_(True)))

    await _write(factory, _reap)

    # expired mailboxes — cutoff is applied in SQL so a large provider
    # doesn't load every live mailbox into memory just to skip most of them
    for provider, ttl in mailbox_ttl.items():
        cutoff = utcnow_naive() - timedelta(hours=ttl)
        async with factory() as read:
            rows = list(
                (
                    await read.execute(
                        select(Mailbox).where(
                            Mailbox.provider == provider,
                            Mailbox.is_deleted.is_(False),
                            Mailbox.created_at.is_not(None),
                            Mailbox.created_at < cutoff,
                        )
                    )
                ).scalars()
            )
        for row in rows:
            info = svc.to_mailbox_info(row, secret)
            try:
                prov = registry.get(provider)
                await prov.delete_mailbox(info)
            except Exception as exc:  # noqa: BLE001 - best-effort sync with provider
                logger.warning("retention: provider delete failed for %s: %s", row.address, exc)

            async def _drop_box(s: AsyncSession, box_id: int = row.id) -> None:
                found = await s.get(Mailbox, box_id)
                if found is not None:
                    await s.delete(found)

            await _write(factory, _drop_box)
            mailboxes_deleted += 1
            mailbox_deletes[provider] = mailbox_deletes.get(provider, 0) + 1
            logger.info("retention: expired mailbox %s deleted", row.address)

    # expired messages — mailbox is joined in so we don't re-fetch it per row
    for provider, ttl in message_ttl.items():
        cutoff = utcnow_naive() - timedelta(hours=ttl)
        async with factory() as read:
            msg_rows = list(
                (
                    await read.execute(
                        select(Message, Mailbox)
                        .join(Mailbox, Message.mailbox_id == Mailbox.id)
                        .where(
                            Message.provider == provider,
                            Mailbox.is_deleted.is_(False),
                            Message.is_deleted.is_(False),
                            Message.received_at.is_not(None),
                            Message.received_at < cutoff,
                        )
                    )
                ).all()
            )
        for msg, mailbox_row in msg_rows:
            info = svc.to_mailbox_info(mailbox_row, secret)
            msg_id = msg.message_api_id
            try:
                prov = registry.get(provider)
                await prov.delete_message(info, msg_id)
            except Exception as exc:  # noqa: BLE001 - best-effort sync with provider
                logger.warning(
                    "retention: provider message delete failed for %s/%s: %s",
                    msg_id,
                    msg.provider,
                    exc,
                )

            async def _drop_msg(s: AsyncSession, mid: int = msg.id) -> None:
                found = await s.get(Message, mid)
                if found is not None:
                    await s.delete(found)

            await _write(factory, _drop_msg)
            messages_deleted += 1
            message_deletes[provider] = message_deletes.get(provider, 0) + 1
            logger.info("retention: expired message %s deleted", msg_id)

    async def _ledger(s: AsyncSession) -> None:
        for prov_slug, n in mailbox_deletes.items():
            await record(s, provider=prov_slug, event=EVENT_MAILBOX_DELETED, count=n)
        for prov_slug, n in message_deletes.items():
            await record(s, provider=prov_slug, event=EVENT_MESSAGE_DELETED, count=n)
        await prune(s)

    await _write(factory, _ledger)
    return {"mailboxes_deleted": mailboxes_deleted, "messages_deleted": messages_deleted}


async def retention_worker(sweep: Callable[[], Awaitable[dict]], interval_seconds: float) -> None:
    while True:
        try:
            await sweep()
        except Exception:  # noqa: BLE001 - worker must never die
            logger.exception("retention sweep failed")
        await asyncio.sleep(interval_seconds)
