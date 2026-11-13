"""Retention cleanup for telemetry rows, called from the main retention sweep."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import TelemetryEvent, TelemetryReport

_BATCH = 1000


async def prune_telemetry(
    session: AsyncSession,
    *,
    sent_days: int = 7,
    unsent_days: int = 30,
    now: datetime | None = None,
) -> tuple[int, int]:
    """Delete sent rows after ``sent_days`` and unsent rows after ``unsent_days``.

    Deleting a report cascades to its events, so sent reports and their linked
    events are removed together.
    """
    moment = now or datetime.now(timezone.utc).replace(tzinfo=None)
    sent_cutoff = moment - timedelta(days=sent_days)
    unsent_cutoff = moment - timedelta(days=unsent_days)

    reports_deleted = 0
    sent_report_ids = (
        select(TelemetryReport.id)
        .where(
            TelemetryReport.status == "sent",
            TelemetryReport.sent_at.is_not(None),
            TelemetryReport.sent_at < sent_cutoff,
        )
        .limit(_BATCH)
    )
    result = await session.execute(
        delete(TelemetryReport).where(TelemetryReport.id.in_(sent_report_ids))
    )
    reports_deleted += int(getattr(result, "rowcount", 0) or 0)

    unsent_report_ids = (
        select(TelemetryReport.id)
        .where(
            TelemetryReport.status != "sent",
            TelemetryReport.created_at < unsent_cutoff,
        )
        .limit(_BATCH)
    )
    result = await session.execute(
        delete(TelemetryReport).where(TelemetryReport.id.in_(unsent_report_ids))
    )
    reports_deleted += int(getattr(result, "rowcount", 0) or 0)

    events_deleted = 0
    sent_event_ids = (
        select(TelemetryEvent.id)
        .where(
            TelemetryEvent.status == "sent",
            TelemetryEvent.sent_at.is_not(None),
            TelemetryEvent.sent_at < sent_cutoff,
        )
        .limit(_BATCH)
    )
    result = await session.execute(
        delete(TelemetryEvent).where(TelemetryEvent.id.in_(sent_event_ids))
    )
    events_deleted += int(getattr(result, "rowcount", 0) or 0)

    unsent_event_ids = (
        select(TelemetryEvent.id)
        .where(
            TelemetryEvent.status != "sent",
            TelemetryEvent.created_at < unsent_cutoff,
        )
        .limit(_BATCH)
    )
    result = await session.execute(
        delete(TelemetryEvent).where(TelemetryEvent.id.in_(unsent_event_ids))
    )
    events_deleted += int(getattr(result, "rowcount", 0) or 0)

    if reports_deleted or events_deleted:
        logger.info(
            "telemetry: pruned %d report(s) and %d event(s)", reports_deleted, events_deleted
        )
    return reports_deleted, events_deleted
