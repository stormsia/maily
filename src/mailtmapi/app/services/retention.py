from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker as AsyncSessionFactory

from ...db.models import Mailbox, Message, Retention
from ...exceptions import MailValidationError
from ...providers.registry import ProviderRegistry
from ...settings import Settings
from ..services import mailboxes as svc

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


async def run_sweep(
    factory: AsyncSessionFactory[AsyncSession],
    registry: ProviderRegistry,
    settings: Settings,
) -> dict:
    async with _sweep_lock:
        async with factory() as session:
            mailboxes_deleted = 0
            messages_deleted = 0
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
                    if _as_naive(row.created_at) >= cutoff:
                        continue
                    try:
                        prov = registry.get(provider)
                        await prov.delete_mailbox(
                            svc.to_mailbox_info(row, settings.resolved_secret_key())
                        )
                    except Exception as exc:  # noqa: BLE001 - best-effort sync with provider
                        logger.warning("retention: provider delete failed for %s: %s", row.address, exc)
                    await session.delete(row)
                    mailboxes_deleted += 1
                    logger.info("retention: expired mailbox %s deleted", row.address)

            # expired messages
            for provider, ttl in message_ttl.items():
                cutoff = utcnow_naive() - timedelta(hours=ttl)
                rows = list(
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
                for msg in rows:
                    if _as_naive(msg.received_at) is None or _as_naive(msg.received_at) >= cutoff:
                        continue
                    try:
                        prov = registry.get(provider)
                        mailbox_row = await session.get(Mailbox, msg.mailbox_id)
                        await prov.delete_message(
                            svc.to_mailbox_info(mailbox_row, settings.resolved_secret_key()),
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
                    messages_deleted += 1
                    logger.info("retention: expired message %s deleted", msg.message_api_id)

            await session.commit()
            return {"mailboxes_deleted": mailboxes_deleted, "messages_deleted": messages_deleted}


async def retention_worker(sweep: Callable[[], Awaitable[dict]], interval_seconds: float) -> None:
    while True:
        try:
            await sweep()
        except Exception:  # noqa: BLE001 - worker must never die
            logger.exception("retention sweep failed")
        await asyncio.sleep(interval_seconds)