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


def _as_naive(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


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


async def _commit_short(session: AsyncSession) -> None:
    """Commit the current unit of work right away (releases the write lock)."""
    await retry_on_lock(session.commit)


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

        # reap soft-deleted rows (provider side already removed at API time)
        await session.execute(
            delete(Message).where(
                or_(
                    Message.is_deleted.is_(True),
                    Message.mailbox_id.in_(select(Mailbox.id).where(Mailbox.is_deleted.is_(True))),
                )
            )
        )
        await session.execute(delete(Mailbox).where(Mailbox.is_deleted.is_(True)))
        # commit before the provider-sync loops: they run network I/O and must
        # not hold the SQLite write lock for the whole sweep
        await _commit_short(session)

        # expired mailboxes
        for provider, ttl in mailbox_ttl.items():
            cutoff = utcnow_naive() - timedelta(hours=ttl)
            rows = list(
                (
                    await session.execute(
                        select(Mailbox).where(
                            Mailbox.provider == provider, Mailbox.is_deleted.is_(False)
                        )
                    )
                ).scalars()
            )
            for row in rows:
                created_at = _as_naive(row.created_at)
                if created_at is None or created_at >= cutoff:
                    continue
                try:
                    prov = registry.get(provider)
                    await prov.delete_mailbox(svc.to_mailbox_info(row, secret))
                except Exception as exc:  # noqa: BLE001 - best-effort sync with provider
                    logger.warning("retention: provider delete failed for %s: %s", row.address, exc)
                await session.delete(row)
                await _commit_short(session)
                mailboxes_deleted += 1
                mailbox_deletes[provider] = mailbox_deletes.get(provider, 0) + 1
                logger.info("retention: expired mailbox %s deleted", row.address)

        # expired messages
        for provider, ttl in message_ttl.items():
            cutoff = utcnow_naive() - timedelta(hours=ttl)
            msg_rows = list(
                (
                    await session.execute(
                        select(Message)
                        .join(Mailbox, Message.mailbox_id == Mailbox.id)
                        .where(
                            Message.provider == provider,
                            Mailbox.is_deleted.is_(False),
                            Message.is_deleted.is_(False),
                        )
                    )
                ).scalars()
            )
            for msg in msg_rows:
                received_at = _as_naive(msg.received_at)
                if received_at is None or received_at >= cutoff:
                    continue
                try:
                    prov = registry.get(provider)
                    mailbox_row = await session.get(Mailbox, msg.mailbox_id)
                    if mailbox_row is None:
                        # orphaned message: drop it locally without notifying a provider
                        await session.delete(msg)
                        await _commit_short(session)
                        messages_deleted += 1
                        message_deletes[provider] = message_deletes.get(provider, 0) + 1
                        logger.info("retention: orphaned message %s deleted", msg.message_api_id)
                        continue
                    await prov.delete_message(
                        svc.to_mailbox_info(mailbox_row, secret),
                        msg.message_api_id,
                    )
                except Exception as exc:  # noqa: BLE001 - best-effort sync with provider
                    logger.warning(
                        "retention: provider message delete failed for %s/%s: %s",
                        msg.message_api_id,
                        msg.provider,
                        exc,
                    )
                await session.delete(msg)
                await _commit_short(session)
                messages_deleted += 1
                message_deletes[provider] = message_deletes.get(provider, 0) + 1
                logger.info("retention: expired message %s deleted", msg.message_api_id)

        # ledger bookkeeping: TTL deletes survive here after the rows are gone,
        # and rows outside the reporting window are pruned
        for provider, n in mailbox_deletes.items():
            await record(session, provider=provider, event=EVENT_MAILBOX_DELETED, count=n)
        for provider, n in message_deletes.items():
            await record(session, provider=provider, event=EVENT_MESSAGE_DELETED, count=n)
        await prune(session)

        await _commit_short(session)
        return {"mailboxes_deleted": mailboxes_deleted, "messages_deleted": messages_deleted}


async def retention_worker(sweep: Callable[[], Awaitable[dict]], interval_seconds: float) -> None:
    while True:
        try:
            await sweep()
        except Exception:  # noqa: BLE001 - worker must never die
            logger.exception("retention sweep failed")
        await asyncio.sleep(interval_seconds)
