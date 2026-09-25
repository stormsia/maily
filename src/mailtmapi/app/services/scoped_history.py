"""10-day activity grouped from one key's mailbox and message rows."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import TypedDict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from ...db.models import Mailbox, Message
from .stats_history import (
    EVENT_MAILBOX_CREATED,
    EVENT_MAILBOX_DELETED,
    EVENT_MESSAGE_DELETED,
    EVENT_MESSAGE_RECEIVED,
    WINDOW_DAYS,
)


class EventCounts(TypedDict):
    mailbox_created: int
    mailbox_deleted: int
    message_received: int
    message_deleted: int


class HistoryDay(TypedDict):
    date: str
    mailbox_created: int
    mailbox_deleted: int
    message_received: int
    message_deleted: int


class HistoryView(TypedDict):
    window_days: int
    days: list[HistoryDay]
    totals: EventCounts
    by_provider: dict[str, EventCounts]


def zero_events() -> EventCounts:
    return {
        "mailbox_created": 0,
        "mailbox_deleted": 0,
        "message_received": 0,
        "message_deleted": 0,
    }


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _as_date(value: str | date) -> date:
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def _history_day(day: date, counts: EventCounts) -> HistoryDay:
    return {
        "date": day.isoformat(),
        "mailbox_created": counts["mailbox_created"],
        "mailbox_deleted": counts["mailbox_deleted"],
        "message_received": counts["message_received"],
        "message_deleted": counts["message_deleted"],
    }


async def owned_history(session: AsyncSession, owned: ColumnElement[bool]) -> HistoryView:
    """Group this key's own rows. Does not read the owner-less activity ledger."""
    start = _today() - timedelta(days=WINDOW_DAYS - 1)
    by_day: dict[date, EventCounts] = {}
    totals = zero_events()
    by_provider: dict[str, EventCounts] = {}
    await _fold_mailboxes(session, owned, start, by_day, totals, by_provider)
    await _fold_messages(session, owned, start, by_day, totals, by_provider)
    ranked = sorted(by_provider, key=lambda slug: -_event_total(by_provider[slug]))
    return {
        "window_days": WINDOW_DAYS,
        "days": _fill_days(start, by_day),
        "totals": totals,
        "by_provider": {slug: by_provider[slug] for slug in ranked},
    }


async def _fold_mailboxes(
    session: AsyncSession,
    owned: ColumnElement[bool],
    start: date,
    by_day: dict[date, EventCounts],
    totals: EventCounts,
    by_provider: dict[str, EventCounts],
) -> None:
    created = (
        await session.execute(
            select(Mailbox.provider, func.date(Mailbox.created_at), func.count())
            .where(owned, Mailbox.created_at >= start)
            .group_by(Mailbox.provider, func.date(Mailbox.created_at))
        )
    ).all()
    for provider, day, count in created:
        _bump(by_day, totals, by_provider, str(provider), _as_date(day), EVENT_MAILBOX_CREATED, int(count))
    deleted = (
        await session.execute(
            select(Mailbox.provider, func.date(Mailbox.updated_at), func.count())
            .where(owned, Mailbox.is_deleted.is_(True), Mailbox.updated_at >= start)
            .group_by(Mailbox.provider, func.date(Mailbox.updated_at))
        )
    ).all()
    for provider, day, count in deleted:
        _bump(by_day, totals, by_provider, str(provider), _as_date(day), EVENT_MAILBOX_DELETED, int(count))


async def _fold_messages(
    session: AsyncSession,
    owned: ColumnElement[bool],
    start: date,
    by_day: dict[date, EventCounts],
    totals: EventCounts,
    by_provider: dict[str, EventCounts],
) -> None:
    received = (
        await session.execute(
            select(Message.provider, func.date(Message.received_at), func.count())
            .join(Mailbox, Message.mailbox_id == Mailbox.id)
            .where(owned, Message.received_at.is_not(None), Message.received_at >= start)
            .group_by(Message.provider, func.date(Message.received_at))
        )
    ).all()
    for provider, day, count in received:
        _bump(by_day, totals, by_provider, str(provider), _as_date(day), EVENT_MESSAGE_RECEIVED, int(count))
    deleted = (
        await session.execute(
            select(Message.provider, func.date(Message.cached_at), func.count())
            .join(Mailbox, Message.mailbox_id == Mailbox.id)
            .where(owned, Message.is_deleted.is_(True), Message.cached_at >= start)
            .group_by(Message.provider, func.date(Message.cached_at))
        )
    ).all()
    for provider, day, count in deleted:
        _bump(by_day, totals, by_provider, str(provider), _as_date(day), EVENT_MESSAGE_DELETED, int(count))


def _bump(
    by_day: dict[date, EventCounts],
    totals: EventCounts,
    by_provider: dict[str, EventCounts],
    provider: str,
    day: date,
    event: str,
    count: int,
) -> None:
    _apply(by_day.setdefault(day, zero_events()), event, count)
    _apply(totals, event, count)
    _apply(by_provider.setdefault(provider, zero_events()), event, count)


def _event_total(counts: EventCounts) -> int:
    return (
        counts["mailbox_created"]
        + counts["mailbox_deleted"]
        + counts["message_received"]
        + counts["message_deleted"]
    )


def _apply(bucket: EventCounts, event: str, count: int) -> None:
    match event:
        case "mailbox_created":
            bucket["mailbox_created"] += count
        case "mailbox_deleted":
            bucket["mailbox_deleted"] += count
        case "message_received":
            bucket["message_received"] += count
        case "message_deleted":
            bucket["message_deleted"] += count


def _fill_days(start: date, by_day: dict[date, EventCounts]) -> list[HistoryDay]:
    days: list[HistoryDay] = []
    day = start
    today = _today()
    while day <= today:
        days.append(_history_day(day, by_day.get(day) or zero_events()))
        day += timedelta(days=1)
    return days
