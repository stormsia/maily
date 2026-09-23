"""Activity ledger behind the dashboard's history stats.

Mailboxes/messages have their own rows *and* we increment a counter here on
every meaningful event (create/delete/receive). Deletes keep their counters
even after the retention sweep hard-deletes the rows, so the dashboard can
always answer "what happened in the last 10 days" — deleted items included.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import StatsEvent

#: Event kinds recorded in the ledger.
EVENT_MAILBOX_CREATED = "mailbox_created"
EVENT_MAILBOX_DELETED = "mailbox_deleted"
EVENT_MESSAGE_RECEIVED = "message_received"
EVENT_MESSAGE_DELETED = "message_deleted"

ALL_EVENTS = (
    EVENT_MAILBOX_CREATED,
    EVENT_MAILBOX_DELETED,
    EVENT_MESSAGE_RECEIVED,
    EVENT_MESSAGE_DELETED,
)

#: How long a ledger window is reported/kept for.
WINDOW_DAYS = 10


def _day_utc(when: datetime | None = None) -> date:
    if when is None:
        when = datetime.now(timezone.utc)
    if when.tzinfo is not None:
        when = when.astimezone(timezone.utc).replace(tzinfo=None)
    return when.date()


async def record(
    session: AsyncSession,
    *,
    provider: str,
    event: str,
    count: int = 1,
    when: datetime | None = None,
) -> None:
    """Increment the day/provider/event counter in place (one row per bucket)."""
    if count <= 0:
        return
    day = _day_utc(when)
    row = (
        await session.execute(
            select(StatsEvent).where(
                StatsEvent.day == day,
                StatsEvent.provider == provider,
                StatsEvent.event == event,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        session.add(StatsEvent(day=day, provider=provider, event=event, count=count))
    else:
        row.count += count


async def prune(session: AsyncSession, *, days: int = WINDOW_DAYS) -> None:
    """Drop ledger rows older than the retention window."""
    cutoff = _day_utc() - timedelta(days=days)
    await session.execute(delete(StatsEvent).where(StatsEvent.day < cutoff))


def _zero() -> dict[str, int]:
    return dict.fromkeys(ALL_EVENTS, 0)


async def report(session: AsyncSession, *, days: int = WINDOW_DAYS, today_only: bool = True) -> dict[str, Any]:
    """Aggregated ledger view: daily buckets + totals + per-provider totals.

    ``today_only`` also includes the current (possibly partial) day so the
    dashboard reflects activity as it happens.
    """
    start = _day_utc()
    if today_only:
        start = start - timedelta(days=days - 1)
    rows = (
        await session.execute(
            select(StatsEvent).where(StatsEvent.day >= start)
        )
    ).scalars()
    by_day: dict[str, dict[str, int]] = {}
    totals = _zero()
    by_provider: dict[str, dict[str, int]] = {}
    for r in rows:
        day_key = r.day.isoformat()
        by_day.setdefault(day_key, _zero())[r.event] += r.count
        by_provider.setdefault(r.provider, _zero())[r.event] += r.count
        totals[r.event] += r.count

    # fill days that have no activity so charts can stay continuous
    ordered: list[dict[str, Any]] = []
    day = start
    while day <= _day_utc():
        key = day.isoformat()
        ordered.append({"date": key, **(by_day.get(key) or _zero())})
        day += timedelta(days=1)
    return {
        "window_days": min(days, WINDOW_DAYS),
        "days": ordered,
        "totals": totals,
        "by_provider": {
            p: by_provider[p]
            for p in sorted(by_provider, key=lambda x: -sum(by_provider[x].values()))
        },
    }
