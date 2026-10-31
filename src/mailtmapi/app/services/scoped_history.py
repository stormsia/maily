"""10-day activity grouped from one key's mailbox and message rows and the activity ledger."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timedelta, timezone
from typing import TypedDict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from ...db.models import Mailbox, Message, StatsEvent
from .stats_history import (
    ALL_EVENTS,
    EVENT_MAILBOX_CREATED,
    EVENT_MAILBOX_DELETED,
    EVENT_MESSAGE_DELETED,
    EVENT_MESSAGE_RECEIVED,
    WINDOW_DAYS,
    extract_domain,
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
    by_domain: dict[str, EventCounts]


def zero_events() -> EventCounts:
    return {
        "mailbox_created": 0,
        "mailbox_deleted": 0,
        "message_received": 0,
        "message_deleted": 0,
    }


def _zero_dict() -> dict[str, int]:
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


async def owned_history(
    session: AsyncSession,
    owned: ColumnElement[bool],
    *,
    key_id: int | None = None,
    providers: Sequence[str] | None = None,
) -> HistoryView:
    """Group this key's activity: merges persistent ledger counters (which survive
    retention sweeps) with live rows (for pre-ledger or direct insertions) at the
    granular (day, provider, domain) bucket level."""
    start = _today() - timedelta(days=WINDOW_DAYS - 1)

    # 1. Query persistent ledger rows for this key
    owner_id = key_id or 0
    ledger_qry = select(StatsEvent).where(
        StatsEvent.day >= start,
        StatsEvent.owner_key_id == owner_id,
    )
    if providers is not None:
        ledger_qry = ledger_qry.where(StatsEvent.provider.in_(providers))
    ledger_rows = list((await session.execute(ledger_qry)).scalars().all())

    ledger_buckets: dict[tuple[date, str, str], dict[str, int]] = {}
    for r in ledger_rows:
        b = ledger_buckets.setdefault((r.day, r.provider, r.domain), _zero_dict())
        b[r.event] = b.get(r.event, 0) + r.count

    # 2. Fold live rows for this key
    live_buckets: dict[tuple[date, str, str], dict[str, int]] = {}
    await _fold_mailboxes(session, owned, start, live_buckets)
    await _fold_messages(session, owned, start, live_buckets)

    # 3. Merge at granular (day, provider, domain) bucket level
    all_keys = set(ledger_buckets.keys()) | set(live_buckets.keys())
    merged_buckets: dict[tuple[date, str, str], EventCounts] = {}
    for k in all_keys:
        (d, prov, dom) = k
        if providers is not None and prov not in providers:
            continue
        l_counts = ledger_buckets.get(k, {})
        v_counts = live_buckets.get(k, {})
        merged_buckets[k] = {
            "mailbox_created": max(
                l_counts.get("mailbox_created", 0), v_counts.get("mailbox_created", 0)
            ),
            "mailbox_deleted": max(
                l_counts.get("mailbox_deleted", 0), v_counts.get("mailbox_deleted", 0)
            ),
            "message_received": max(
                l_counts.get("message_received", 0), v_counts.get("message_received", 0)
            ),
            "message_deleted": max(
                l_counts.get("message_deleted", 0), v_counts.get("message_deleted", 0)
            ),
        }

    # 4. Derive rollups from the merged granular buckets
    by_day: dict[date, EventCounts] = {}
    totals = zero_events()
    by_provider: dict[str, EventCounts] = {}
    by_domain: dict[str, EventCounts] = {}

    for (day, prov, dom), counts in merged_buckets.items():
        d_bucket = by_day.setdefault(day, zero_events())
        p_bucket = by_provider.setdefault(prov, zero_events())
        dom_bucket = by_domain.setdefault(dom, zero_events())
        for ev in ALL_EVENTS:
            val = counts[ev]  # type: ignore[literal-required]
            if val:
                d_bucket[ev] += val  # type: ignore[literal-required]
                p_bucket[ev] += val  # type: ignore[literal-required]
                dom_bucket[ev] += val  # type: ignore[literal-required]
                totals[ev] += val  # type: ignore[literal-required]

    # 5. Continuous day list
    days: list[HistoryDay] = []
    cur = start
    today = _today()
    while cur <= today:
        days.append(_history_day(cur, by_day.get(cur) or zero_events()))
        cur += timedelta(days=1)

    ranked_provs = sorted(by_provider, key=lambda slug: -_event_total(by_provider[slug]))
    ranked_doms = sorted(by_domain, key=lambda d: -_event_total(by_domain[d]))

    return {
        "window_days": WINDOW_DAYS,
        "days": days,
        "totals": totals,
        "by_provider": {slug: by_provider[slug] for slug in ranked_provs},
        "by_domain": {dom: by_domain[dom] for dom in ranked_doms},
    }


async def _fold_mailboxes(
    session: AsyncSession,
    owned: ColumnElement[bool],
    start: date,
    buckets: dict[tuple[date, str, str], dict[str, int]],
) -> None:
    created = (
        await session.execute(
            select(Mailbox.provider, Mailbox.address, func.date(Mailbox.created_at), func.count())
            .where(owned, Mailbox.created_at >= start)
            .group_by(Mailbox.provider, Mailbox.address, func.date(Mailbox.created_at))
        )
    ).all()
    for provider, address, day, count in created:
        dom = extract_domain(address)
        d = _as_date(day)
        b = buckets.setdefault((d, str(provider), dom), _zero_dict())
        b[EVENT_MAILBOX_CREATED] += int(count)

    deleted = (
        await session.execute(
            select(Mailbox.provider, Mailbox.address, func.date(Mailbox.updated_at), func.count())
            .where(owned, Mailbox.is_deleted.is_(True), Mailbox.updated_at >= start)
            .group_by(Mailbox.provider, Mailbox.address, func.date(Mailbox.updated_at))
        )
    ).all()
    for provider, address, day, count in deleted:
        dom = extract_domain(address)
        d = _as_date(day)
        b = buckets.setdefault((d, str(provider), dom), _zero_dict())
        b[EVENT_MAILBOX_DELETED] += int(count)


async def _fold_messages(
    session: AsyncSession,
    owned: ColumnElement[bool],
    start: date,
    buckets: dict[tuple[date, str, str], dict[str, int]],
) -> None:
    received = (
        await session.execute(
            select(Message.provider, Mailbox.address, func.date(Message.received_at), func.count())
            .join(Mailbox, Message.mailbox_id == Mailbox.id)
            .where(owned, Message.received_at.is_not(None), Message.received_at >= start)
            .group_by(Message.provider, Mailbox.address, func.date(Message.received_at))
        )
    ).all()
    for provider, address, day, count in received:
        dom = extract_domain(address)
        d = _as_date(day)
        b = buckets.setdefault((d, str(provider), dom), _zero_dict())
        b[EVENT_MESSAGE_RECEIVED] += int(count)

    deleted = (
        await session.execute(
            select(Message.provider, Mailbox.address, func.date(Message.cached_at), func.count())
            .join(Mailbox, Message.mailbox_id == Mailbox.id)
            .where(owned, Message.is_deleted.is_(True), Message.cached_at >= start)
            .group_by(Message.provider, Mailbox.address, func.date(Message.cached_at))
        )
    ).all()
    for provider, address, day, count in deleted:
        dom = extract_domain(address)
        d = _as_date(day)
        b = buckets.setdefault((d, str(provider), dom), _zero_dict())
        b[EVENT_MESSAGE_DELETED] += int(count)


def _event_total(counts: EventCounts) -> int:
    return (
        counts["mailbox_created"]
        + counts["mailbox_deleted"]
        + counts["message_received"]
        + counts["message_deleted"]
    )
