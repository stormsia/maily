"""Activity ledger behind the dashboard's history stats.

Mailboxes/messages have their own rows *and* we increment a counter here on
every meaningful event (create/delete/receive). Deletes keep their counters
even after the retention sweep hard-deletes the rows, so the dashboard can
always answer "what happened in the last 10 days" — deleted items included.
Counters are tracked per day, provider, domain, and owner_key_id.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import Mailbox, Message, StatsEvent

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


def extract_domain(address: str | None) -> str:
    """Extract and normalize domain from an email address (e.g. 'foo@bar.com' -> 'bar.com')."""
    if not address or "@" not in address:
        return ""
    return address.split("@", 1)[1].strip().lower()


def _day_utc(when: datetime | date | None = None) -> date:
    if when is None:
        when = datetime.now(timezone.utc)
    if isinstance(when, datetime):
        if when.tzinfo is not None:
            when = when.astimezone(timezone.utc).replace(tzinfo=None)
        return when.date()
    return when  # already a plain date


async def record(
    session: AsyncSession,
    *,
    provider: str,
    domain: str = "",
    owner_key_id: int | None = None,
    event: str,
    count: int = 1,
    when: datetime | date | None = None,
) -> None:
    """Increment the day/provider/domain/owner/event counter (one row per bucket).

    Atomic upsert: two concurrent writes of the same bucket cannot
    insert duplicate rows.
    """
    if count <= 0:
        return
    day = _day_utc(when)
    dom = (domain or "").strip().lower()
    owner_id = owner_key_id or 0
    stmt = sqlite_insert(StatsEvent).values(
        day=day,
        provider=provider,
        domain=dom,
        owner_key_id=owner_id,
        event=event,
        count=count,
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["day", "provider", "domain", "owner_key_id", "event"],
        set_={"count": StatsEvent.count + count},
    )
    await session.execute(stmt)


async def prune(session: AsyncSession, *, days: int = WINDOW_DAYS) -> None:
    """Drop ledger rows older than the retention window."""
    cutoff = _day_utc() - timedelta(days=days)
    await session.execute(delete(StatsEvent).where(StatsEvent.day < cutoff))


async def backfill_received(session: AsyncSession, *, days: int = WINDOW_DAYS) -> int:
    """Seed the ledger's ``message_received`` counters from stored messages.

    Migration aid for rows that predate the ledger: without receive-events the
    7-day incoming chart falls back to the live table, and a later retention
    sweep hard-deletes those rows, silently erasing past chart days.

    Only fills (day, provider, domain, owner_key_id) buckets that have no receive counter yet,
    so repeated calls and restarts never double-count. Messages already erased by
    retention are gone from the live table and cannot be reconstructed here.
    """
    start = _day_utc() - timedelta(days=days - 1)
    msg_rows = (
        await session.execute(
            select(
                Message.provider,
                Mailbox.address,
                Mailbox.owner_key_id,
                func.date(Message.received_at).label("d"),
                func.count(),
            )
            .join(Mailbox, Message.mailbox_id == Mailbox.id)
            .where(Message.received_at.is_not(None), Message.received_at >= start)
            .group_by(Message.provider, Mailbox.address, Mailbox.owner_key_id, "d")
        )
    ).all()

    # Aggregate by normalized (day, provider, domain, owner_key_id)
    live_counts: dict[tuple[date, str, str, int], int] = {}
    for provider, address, owner_key_id, day_str, count in msg_rows:
        day = date.fromisoformat(day_str)
        dom = extract_domain(address)
        owner_id = owner_key_id or 0
        k = (day, provider, dom, owner_id)
        live_counts[k] = live_counts.get(k, 0) + int(count)

    existing = {
        (r[0], r[1], r[2], r[3])
        for r in (
            await session.execute(
                select(
                    StatsEvent.day, StatsEvent.provider, StatsEvent.domain, StatsEvent.owner_key_id
                ).where(
                    StatsEvent.event == EVENT_MESSAGE_RECEIVED,
                    StatsEvent.day >= start,
                )
            )
        ).all()
    }

    inserted = 0
    for (day, provider, dom, owner_id), count in live_counts.items():
        if (day, provider, dom, owner_id) in existing:
            continue
        session.add(
            StatsEvent(
                day=day,
                provider=provider,
                domain=dom,
                owner_key_id=owner_id,
                event=EVENT_MESSAGE_RECEIVED,
                count=count,
            )
        )
        existing.add((day, provider, dom, owner_id))
        inserted += 1
    return inserted


def _zero() -> dict[str, int]:
    return dict.fromkeys(ALL_EVENTS, 0)


async def report(
    session: AsyncSession,
    *,
    days: int = WINDOW_DAYS,
    today_only: bool = True,
    owner_key_id: int | None = None,
    filter_owner: bool = False,
    providers: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Aggregated ledger view: daily buckets + totals + per-provider + per-domain totals.

    ``today_only`` also includes the current (possibly partial) day so the
    dashboard reflects activity as it happens.
    ``filter_owner`` restricts events to a specific key (or root if owner_key_id is None/0).
    ``providers`` restricts events to allowed providers.
    """
    start = _day_utc()
    if today_only:
        start = start - timedelta(days=days - 1)
    qry = select(StatsEvent).where(StatsEvent.day >= start)
    if filter_owner:
        owner_id = owner_key_id or 0
        qry = qry.where(StatsEvent.owner_key_id == owner_id)
    if providers is not None:
        qry = qry.where(StatsEvent.provider.in_(providers))
    rows = list((await session.execute(qry)).scalars().all())
    by_day: dict[str, dict[str, int]] = {}
    totals = _zero()
    by_provider: dict[str, dict[str, int]] = {}
    by_domain: dict[str, dict[str, int]] = {}
    for r in rows:
        day_key = r.day.isoformat()
        by_day.setdefault(day_key, _zero())[r.event] += r.count
        by_provider.setdefault(r.provider, _zero())[r.event] += r.count
        by_domain.setdefault(r.domain, _zero())[r.event] += r.count
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
        "by_domain": {
            d: by_domain[d] for d in sorted(by_domain, key=lambda x: -sum(by_domain[x].values()))
        },
    }
