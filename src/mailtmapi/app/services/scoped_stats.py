"""Live mailbox, message, and Gmail counts for one issued key."""

from __future__ import annotations

from typing import TypedDict

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from ...db.models import GmailAccount, Mailbox, Message
from .scoped_history import HistoryView, owned_history

_TREND_DAYS = 7


class MailboxCounts(TypedDict):
    total: int
    active: int
    deleted: int


class MessageCounts(TypedDict):
    total: int
    deleted: int


class ProviderCounts(TypedDict):
    mailboxes_total: int
    mailboxes_active: int
    mailboxes_deleted: int
    messages_total: int


class GmailCounts(TypedDict):
    total: int
    active: int


class TrendPoint(TypedDict):
    date: str
    count: int


class ScopedStats(TypedDict):
    mailboxes: MailboxCounts
    messages: MessageCounts
    by_provider: dict[str, ProviderCounts]
    gmail_accounts: GmailCounts
    messages_last_7_days: list[TrendPoint]
    history: HistoryView


def _sum_or_zero(value: int | None) -> int:
    return value or 0


def _blank_provider() -> ProviderCounts:
    return {
        "mailboxes_total": 0,
        "mailboxes_active": 0,
        "mailboxes_deleted": 0,
        "messages_total": 0,
    }


async def owned_report(
    session: AsyncSession,
    *,
    key_id: int,
    parent_ids: tuple[int, ...],
) -> ScopedStats:
    """Counts and row-grouped history for mail this key owns. Never reads the ledger."""
    owned = Mailbox.owner_key_id == key_id
    mailboxes, messages, by_provider = await _live_counts(session, owned)
    history = await owned_history(session, owned)
    trend = [
        TrendPoint(date=day["date"], count=day["message_received"])
        for day in history["days"][-_TREND_DAYS:]
        if day["message_received"]
    ]
    return {
        "mailboxes": mailboxes,
        "messages": messages,
        "by_provider": by_provider,
        "gmail_accounts": await _gmail_counts(session, key_id, parent_ids),
        "messages_last_7_days": trend or [TrendPoint(date="no-data", count=0)],
        "history": history,
    }


async def _live_counts(
    session: AsyncSession,
    owned: ColumnElement[bool],
) -> tuple[MailboxCounts, MessageCounts, dict[str, ProviderCounts]]:
    active = case((Mailbox.is_active.is_(True), 1), else_=0)
    deleted_box = case((Mailbox.is_deleted.is_(True), 1), else_=0)
    deleted_msg = case((Message.is_deleted.is_(True), 1), else_=0)
    mb_total, mb_active, mb_deleted = (
        await session.execute(select(func.count(), func.sum(active), func.sum(deleted_box)).where(owned))
    ).one()
    joined = select(func.count(), func.sum(deleted_msg)).join(Mailbox, Message.mailbox_id == Mailbox.id)
    msg_total, msg_deleted = (await session.execute(joined.where(owned))).one()
    by_provider = await _providers(session, owned, active, deleted_box)
    return (
        {
            "total": _sum_or_zero(mb_total),
            "active": _sum_or_zero(mb_active),
            "deleted": _sum_or_zero(mb_deleted),
        },
        {"total": _sum_or_zero(msg_total), "deleted": _sum_or_zero(msg_deleted)},
        by_provider,
    )


async def _providers(
    session: AsyncSession,
    owned: ColumnElement[bool],
    active: ColumnElement[int],
    deleted_box: ColumnElement[int],
) -> dict[str, ProviderCounts]:
    by_provider: dict[str, ProviderCounts] = {}
    boxes = (
        await session.execute(
            select(Mailbox.provider, func.count(), func.sum(active), func.sum(deleted_box))
            .where(owned)
            .group_by(Mailbox.provider)
        )
    ).all()
    for provider, total, live, deleted in boxes:
        counts = _blank_provider()
        counts["mailboxes_total"] = _sum_or_zero(total)
        counts["mailboxes_active"] = _sum_or_zero(live)
        counts["mailboxes_deleted"] = _sum_or_zero(deleted)
        by_provider[str(provider)] = counts
    messages = (
        await session.execute(
            select(Message.provider, func.count())
            .join(Mailbox, Message.mailbox_id == Mailbox.id)
            .where(owned, Message.is_deleted.is_(False))
            .group_by(Message.provider)
        )
    ).all()
    for provider, msg_count in messages:
        bucket = by_provider.setdefault(str(provider), _blank_provider())
        bucket["messages_total"] = _sum_or_zero(msg_count)
    return by_provider


async def _gmail_counts(
    session: AsyncSession,
    key_id: int,
    parent_ids: tuple[int, ...],
) -> GmailCounts:
    granted = GmailAccount.id.in_(parent_ids) if parent_ids else False
    visible = or_(GmailAccount.owner_key_id == key_id, _root_granted(granted))
    active = case((GmailAccount.status == "active", 1), else_=0)
    total, live = (await session.execute(select(func.count(), func.sum(active)).where(visible))).one()
    return {"total": _sum_or_zero(total), "active": _sum_or_zero(live)}


def _root_granted(granted: ColumnElement[bool] | bool) -> ColumnElement[bool]:
    """Root parents whose id is in parent_ids. An empty grant matches nothing."""
    return (GmailAccount.owner_key_id.is_(None)) & granted
