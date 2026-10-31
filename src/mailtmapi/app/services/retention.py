from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker as AsyncSessionFactory

from ...db.engine import retry_on_lock
from ...db.maintenance import maybe_run_maintenance
from ...db.models import KeyRetention, Mailbox, Message, Retention
from ...exceptions import MailNotFoundError, MailValidationError
from ...providers.registry import ProviderRegistry
from ...settings import Settings
from ..services import mailboxes as svc
from ..services.retention_rules import load_sweep_rules, owner_clause
from ..services.stats_history import (
    EVENT_MAILBOX_DELETED,
    EVENT_MESSAGE_DELETED,
    extract_domain,
    prune,
    record,
)

logger = logging.getLogger("mailtmapi.retention")


def utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _check_ttls(mailbox_ttl_hours: int | None, message_ttl_hours: int | None) -> None:
    for name, ttl in (
        ("mailbox_ttl_hours", mailbox_ttl_hours),
        ("message_ttl_hours", message_ttl_hours),
    ):
        if ttl is not None and ttl < 1:
            raise MailValidationError(f"{name} must be >= 1 or null")
    if mailbox_ttl_hours is None and message_ttl_hours is None:
        raise MailValidationError("at least one ttl required")


async def get_retention(session) -> list[Retention]:
    return list((await session.execute(select(Retention).order_by(Retention.provider))).scalars())


async def get_key_retention(session, key_id: int) -> list[KeyRetention]:
    """Rows this issued key may read. Other keys and the global table stay hidden."""
    rows = await session.execute(
        select(KeyRetention).where(KeyRetention.key_id == key_id).order_by(KeyRetention.provider)
    )
    return list(rows.scalars())


async def set_retention(
    session,
    provider: str,
    mailbox_ttl_hours: int | None,
    message_ttl_hours: int | None,
) -> Retention:
    _check_ttls(mailbox_ttl_hours, message_ttl_hours)
    row = await session.get(Retention, provider)
    if row is None:
        row = Retention(provider=provider)
        session.add(row)
    row.mailbox_ttl_hours = mailbox_ttl_hours
    row.message_ttl_hours = message_ttl_hours
    await session.flush()
    return row


async def set_key_retention(
    session,
    key_id: int,
    provider: str,
    mailbox_ttl_hours: int | None,
    message_ttl_hours: int | None,
) -> KeyRetention:
    """Write this key's row only. Does not touch the global retention table."""
    _check_ttls(mailbox_ttl_hours, message_ttl_hours)
    row = await session.get(KeyRetention, (key_id, provider))
    if row is None:
        row = KeyRetention(key_id=key_id, provider=provider)
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


async def delete_key_retention(session, key_id: int, provider: str) -> bool:
    row = await session.get(KeyRetention, (key_id, provider))
    if row is None:
        return False
    await session.delete(row)
    return True


def _is_already_gone(exc: Exception) -> bool:
    """Return True if exc indicates the mailbox or message does not exist upstream."""
    if isinstance(exc, MailNotFoundError):
        return True
    msg = str(exc).lower()
    return any(
        phrase in msg
        for phrase in (
            "not exist",
            "not found",
            "doesn't exist",
            "does not exist",
            "unknown email",
            "unknown account",
            "no such email",
            "no such message",
        )
    )


async def _write(
    factory: AsyncSessionFactory[AsyncSession],
    operation: Callable[[AsyncSession], Awaitable[None]],
) -> None:
    """One short write transaction in a fresh session, retried on SQLITE_BUSY.

    Retrying ``session.commit`` on a session that already failed is useless:
    the transaction is dead. A new session is the only retry that works.
    """

    async def _do() -> None:
        async with factory() as session:
            await operation(session)
            await session.commit()

    await retry_on_lock(_do)


async def _do_sweep(
    factory: AsyncSessionFactory[AsyncSession],
    registry: ProviderRegistry,
    settings: Settings,
    *,
    only_key_id: int | None = None,
    force_maintenance: bool = False,
) -> dict:
    async with factory() as session:
        mailboxes_deleted = 0
        messages_deleted = 0
        mailbox_deletes: dict[tuple[str, str, int | None], int] = {}
        message_deletes: dict[tuple[str, str, int | None], int] = {}
        secret = settings.resolved_secret_key()
        mailbox_rules, message_rules = await load_sweep_rules(session, only_key_id)

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
    for rule in mailbox_rules:
        cutoff = utcnow_naive() - timedelta(hours=rule.hours)
        async with factory() as read:
            rows = list(
                (
                    await read.execute(
                        select(Mailbox).where(
                            Mailbox.provider == rule.provider,
                            owner_clause(rule.owner_key_id),
                            Mailbox.is_deleted.is_(False),
                            Mailbox.created_at.is_not(None),
                            Mailbox.created_at < cutoff,
                        )
                    )
                ).scalars()
            )
        for row in rows:
            info = svc.to_mailbox_info(row, secret)
            failed_upstream = False
            try:
                prov = registry.get(rule.provider)
                ok = await prov.delete_mailbox(info)
                if ok is False:
                    logger.warning(
                        "retention: provider delete returned False for %s; marking as deleted locally",
                        row.address,
                    )
                    failed_upstream = True
            except Exception as exc:  # noqa: BLE001 - best-effort sync with provider
                if _is_already_gone(exc):
                    logger.info(
                        "retention: provider mailbox %s already gone (%s), cleaning up locally",
                        row.address,
                        exc,
                    )
                else:
                    logger.warning(
                        "retention: provider delete failed for %s: %s; marking as deleted locally",
                        row.address,
                        exc,
                    )
                    failed_upstream = True

            if failed_upstream:
                async def _soft_drop_box(s: AsyncSession, box_id: int = row.id) -> None:
                    await s.execute(
                        update(Mailbox)
                        .where(Mailbox.id == box_id)
                        .values(
                            is_active=False,
                            is_deleted=True,
                            updated_at=utcnow_naive(),
                        )
                    )

                await _write(factory, _soft_drop_box)
            else:
                async def _drop_box(s: AsyncSession, box_id: int = row.id) -> None:
                    await s.execute(delete(Mailbox).where(Mailbox.id == box_id))

                await _write(factory, _drop_box)

            mailboxes_deleted += 1
            domain = extract_domain(row.address)
            box_key = (rule.provider, domain, row.owner_key_id)
            mailbox_deletes[box_key] = mailbox_deletes.get(box_key, 0) + 1
            logger.info("retention: expired mailbox %s deleted", row.address)

    # expired messages — mailbox is joined in so we don't re-fetch it per row
    for rule in message_rules:
        cutoff = utcnow_naive() - timedelta(hours=rule.hours)
        async with factory() as read:
            msg_rows = list(
                (
                    await read.execute(
                        select(Message, Mailbox)
                        .join(Mailbox, Message.mailbox_id == Mailbox.id)
                        .where(
                            Message.provider == rule.provider,
                            owner_clause(rule.owner_key_id),
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
                prov = registry.get(rule.provider)
                await prov.delete_message(info, msg_id)
            except Exception as exc:  # noqa: BLE001 - best-effort sync with provider
                if _is_already_gone(exc):
                    logger.info(
                        "retention: provider message %s/%s already gone (%s), cleaning up locally",
                        msg_id,
                        msg.provider,
                        exc,
                    )
                else:
                    logger.warning(
                        "retention: provider message delete failed for %s/%s: %s",
                        msg_id,
                        msg.provider,
                        exc,
                    )
                    continue

            async def _drop_msg(s: AsyncSession, mid: int = msg.id) -> None:
                await s.execute(delete(Message).where(Message.id == mid))

            await _write(factory, _drop_msg)
            messages_deleted += 1
            domain = extract_domain(mailbox_row.address)
            msg_key = (rule.provider, domain, mailbox_row.owner_key_id)
            message_deletes[msg_key] = message_deletes.get(msg_key, 0) + 1
            logger.info("retention: expired message %s deleted", msg_id)

    async def _ledger(s: AsyncSession) -> None:
        for (prov_slug, domain, owner_id), n in mailbox_deletes.items():
            await record(
                s,
                provider=prov_slug,
                domain=domain,
                owner_key_id=owner_id,
                event=EVENT_MAILBOX_DELETED,
                count=n,
            )
        for (prov_slug, domain, owner_id), n in message_deletes.items():
            await record(
                s,
                provider=prov_slug,
                domain=domain,
                owner_key_id=owner_id,
                event=EVENT_MESSAGE_DELETED,
                count=n,
            )
        await prune(s)

    await _write(factory, _ledger)
    if only_key_id is None:
        try:
            await maybe_run_maintenance(factory, settings, force=force_maintenance)
        except Exception:  # noqa: BLE001
            logger.exception("retention: unexpected error during database maintenance")
    return {
        "mailboxes_deleted": mailboxes_deleted,
        "messages_deleted": messages_deleted,
    }


async def run_sweep(
    factory: AsyncSessionFactory[AsyncSession],
    registry: ProviderRegistry,
    settings: Settings,
    *,
    only_key_id: int | None = None,
    force_maintenance: bool = False,
    lock: asyncio.Lock | None = None,
) -> dict:
    if lock is not None:
        async with lock:
            return await _do_sweep(
                factory,
                registry,
                settings,
                only_key_id=only_key_id,
                force_maintenance=force_maintenance,
            )
    return await _do_sweep(
        factory,
        registry,
        settings,
        only_key_id=only_key_id,
        force_maintenance=force_maintenance,
    )


async def retention_worker(sweep: Callable[[], Awaitable[dict]], interval_seconds: float) -> None:
    if interval_seconds <= 0:
        return
    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await sweep()
        except Exception:  # noqa: BLE001 - worker must never die
            logger.exception("retention sweep failed")
