"""SQLAlchemy implementation of the telemetry outbox."""

from __future__ import annotations

import json
import uuid
from collections import defaultdict
from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import async_sessionmaker

from ..db.engine import retry_on_lock
from ..db.models import TelemetryEvent as TelemetryEventRow
from ..db.models import TelemetryReport as TelemetryReportRow
from ..db.models import TelemetryState as TelemetryStateRow
from .models import (
    OutboxCounts,
    TelemetryEvent,
    TelemetryReport,
    TelemetryState,
)
from .ports import Clock, TelemetryRepository

_SENDING_LEASE_SECONDS = 300


def _state_dataclass(row: TelemetryStateRow) -> TelemetryState:
    return TelemetryState(
        id=row.id,
        installation_id=row.installation_id,
        created_at=row.created_at,
        app_start_count=row.app_start_count,
        first_version=row.first_version,
        last_version=row.last_version,
        last_start_at=row.last_start_at,
        last_flush_at=row.last_flush_at,
        last_snapshot_day=row.last_snapshot_day,
        setup_completed_at=row.setup_completed_at,
        geo_json=row.geo_json,
        geo_updated_at=row.geo_updated_at,
        last_error=row.last_error,
        updated_at=row.updated_at,
    )


def _event_dataclass(row: TelemetryEventRow) -> TelemetryEvent:
    try:
        properties = json.loads(row.properties_json) if row.properties_json else {}
    except (ValueError, TypeError):
        properties = {}
    if not isinstance(properties, dict):
        properties = {}
    return TelemetryEvent(
        event_uuid=row.event_uuid,
        event_name=row.event_name,
        distinct_id=row.distinct_id,
        properties=properties,
        occurred_at=row.occurred_at,
        row_id=row.id,
        report_id=row.report_id,
        status=row.status,
        attempts=row.attempts,
        next_attempt_at=row.next_attempt_at,
        created_at=row.created_at,
        sent_at=row.sent_at,
    )


def _properties_json(properties: dict[str, Any]) -> str:
    return json.dumps(properties, default=str, separators=(",", ":"))


class SqlTelemetryRepository(TelemetryRepository):
    def __init__(
        self,
        factory: async_sessionmaker[Any],
        clock: Clock,
    ) -> None:
        self._factory = factory
        self._clock = clock

    async def _transaction(self, operation: Any) -> Any:
        """Run one short transaction with SQLite lock retry."""
        result: list[Any] = []

        async def _do() -> None:
            async with self._factory() as session:
                outcome = await operation(session)
                await session.commit()
                result.append(outcome)

        await retry_on_lock(_do)
        return result[0] if result else None

    async def _read(self, operation: Any) -> Any:
        async with self._factory() as session:
            return await operation(session)

    async def ensure_state(self) -> TelemetryState:
        async def _op(session: Any) -> None:
            stmt = sqlite_insert(TelemetryStateRow).values(
                id=1,
                installation_id=str(uuid.uuid4()),
                created_at=self._clock.now_utc(),
                app_start_count=0,
                first_version="",
                last_version="",
                geo_json="{}",
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=["id"])
            await session.execute(stmt)

        await self._transaction(_op)
        state = await self.load_state()
        if state is None:  # pragma: no cover - defensive
            raise RuntimeError("telemetry state could not be created")
        return state

    async def load_state(self) -> TelemetryState | None:
        async def _op(session: Any) -> TelemetryState | None:
            row = await session.get(TelemetryStateRow, 1)
            return _state_dataclass(row) if row is not None else None

        return await self._read(_op)

    async def update_state(self, **fields: Any) -> None:
        async def _op(session: Any) -> None:
            row = await session.get(TelemetryStateRow, 1)
            if row is None:
                return
            for key, value in fields.items():
                if key == "id":
                    continue
                setattr(row, key, value)

        await self._transaction(_op)

    async def mark_setup_completed(self) -> bool:
        async def _op(session: Any) -> bool:
            result = await session.execute(
                update(TelemetryStateRow)
                .where(
                    TelemetryStateRow.id == 1,
                    TelemetryStateRow.setup_completed_at.is_(None),
                )
                .values(setup_completed_at=self._clock.now_utc())
            )
            return bool(result.rowcount)

        return bool(await self._transaction(_op))

    async def enqueue_events(self, events: Sequence[TelemetryEvent]) -> int:
        if not events:
            return 0
        now = self._clock.now_utc()
        rows = [
            {
                "event_uuid": event.event_uuid,
                "event_name": event.event_name,
                "distinct_id": event.distinct_id,
                "properties_json": _properties_json(event.properties),
                "occurred_at": event.occurred_at,
                "report_id": None,
                "status": "pending",
                "attempts": 0,
                "next_attempt_at": now,
                "created_at": now,
            }
            for event in events
        ]

        async def _op(session: Any) -> int:
            stmt = sqlite_insert(TelemetryEventRow).values(rows)
            stmt = stmt.on_conflict_do_nothing(index_elements=["event_uuid"])
            result = await session.execute(stmt)
            return int(result.rowcount or 0)

        return int(await self._transaction(_op) or 0)

    async def create_report(self, day: date, events: Sequence[TelemetryEvent]) -> int | None:
        if not events:
            return None
        now = self._clock.now_utc()

        async def _op(session: Any) -> int | None:
            existing = (
                await session.execute(
                    select(TelemetryReportRow).where(TelemetryReportRow.report_day == day)
                )
            ).scalar_one_or_none()
            if existing is not None:
                return None
            report = TelemetryReportRow(
                report_day=day,
                status="pending",
                attempts=0,
                next_attempt_at=now,
                created_at=now,
            )
            session.add(report)
            await session.flush()
            for event in events:
                session.add(
                    TelemetryEventRow(
                        report_id=report.id,
                        event_uuid=event.event_uuid,
                        event_name=event.event_name,
                        distinct_id=event.distinct_id,
                        properties_json=_properties_json(event.properties),
                        occurred_at=event.occurred_at,
                        status="pending",
                        attempts=0,
                        next_attempt_at=now,
                        created_at=now,
                    )
                )
            return report.id

        return await self._transaction(_op)

    async def claim_due_events(self, limit: int) -> list[TelemetryEvent]:
        if limit <= 0:
            return []
        now = self._clock.now_utc()

        async def _op(session: Any) -> list[TelemetryEvent]:
            rows = (
                (
                    await session.execute(
                        select(TelemetryEventRow)
                        .where(
                            TelemetryEventRow.report_id.is_(None),
                            TelemetryEventRow.status == "pending",
                            TelemetryEventRow.next_attempt_at <= now,
                        )
                        .order_by(TelemetryEventRow.next_attempt_at)
                        .limit(limit)
                    )
                )
                .scalars()
                .all()
            )
            if not rows:
                return []
            ids = [row.id for row in rows]
            await session.execute(
                update(TelemetryEventRow)
                .where(TelemetryEventRow.id.in_(ids))
                .values(
                    status="sending",
                    attempts=TelemetryEventRow.attempts + 1,
                    next_attempt_at=now + timedelta(seconds=_SENDING_LEASE_SECONDS),
                )
            )
            claimed = (
                (
                    await session.execute(
                        select(TelemetryEventRow)
                        .where(TelemetryEventRow.id.in_(ids))
                        .order_by(TelemetryEventRow.id)
                    )
                )
                .scalars()
                .all()
            )
            return [_event_dataclass(row) for row in claimed]

        return await self._transaction(_op)

    async def claim_due_reports(self, limit: int) -> list[TelemetryReport]:
        if limit <= 0:
            return []
        now = self._clock.now_utc()

        async def _op(session: Any) -> list[TelemetryReport]:
            rows = (
                (
                    await session.execute(
                        select(TelemetryReportRow)
                        .where(
                            TelemetryReportRow.status == "pending",
                            TelemetryReportRow.next_attempt_at <= now,
                        )
                        .order_by(TelemetryReportRow.next_attempt_at)
                        .limit(limit)
                    )
                )
                .scalars()
                .all()
            )
            if not rows:
                return []
            ids = [row.id for row in rows]
            await session.execute(
                update(TelemetryReportRow)
                .where(TelemetryReportRow.id.in_(ids))
                .values(
                    status="sending",
                    attempts=TelemetryReportRow.attempts + 1,
                    next_attempt_at=now + timedelta(seconds=_SENDING_LEASE_SECONDS),
                )
            )
            reports = (
                (
                    await session.execute(
                        select(TelemetryReportRow)
                        .where(TelemetryReportRow.id.in_(ids))
                        .order_by(TelemetryReportRow.id)
                    )
                )
                .scalars()
                .all()
            )
            event_rows = (
                (
                    await session.execute(
                        select(TelemetryEventRow)
                        .where(TelemetryEventRow.report_id.in_(ids))
                        .order_by(TelemetryEventRow.id)
                    )
                )
                .scalars()
                .all()
            )
            by_report: dict[int, list[TelemetryEvent]] = defaultdict(list)
            for row in event_rows:
                by_report[row.report_id].append(_event_dataclass(row))
            return [
                TelemetryReport(
                    id=row.id,
                    report_day=row.report_day,
                    status=row.status,
                    attempts=row.attempts,
                    next_attempt_at=row.next_attempt_at,
                    last_error=row.last_error,
                    created_at=row.created_at,
                    sent_at=row.sent_at,
                    events=by_report[row.id],
                )
                for row in reports
            ]

        return await self._transaction(_op)

    async def mark_events_sent(self, ids: Sequence[int]) -> None:
        if not ids:
            return
        now = self._clock.now_utc()

        async def _op(session: Any) -> None:
            await session.execute(
                update(TelemetryEventRow)
                .where(TelemetryEventRow.id.in_(ids))
                .values(status="sent", sent_at=now, last_error=None)
            )

        await self._transaction(_op)

    async def mark_events_retry(
        self, ids: Sequence[int], error: str, next_attempt_at: datetime
    ) -> None:
        if not ids:
            return

        async def _op(session: Any) -> None:
            await session.execute(
                update(TelemetryEventRow)
                .where(TelemetryEventRow.id.in_(ids))
                .values(status="pending", next_attempt_at=next_attempt_at, last_error=error)
            )

        await self._transaction(_op)

    async def mark_events_failed(self, ids: Sequence[int], error: str) -> None:
        if not ids:
            return

        async def _op(session: Any) -> None:
            await session.execute(
                update(TelemetryEventRow)
                .where(TelemetryEventRow.id.in_(ids))
                .values(status="failed", last_error=error)
            )

        await self._transaction(_op)

    async def mark_report_sent(self, report_id: int, event_ids: Sequence[int]) -> None:
        now = self._clock.now_utc()

        async def _op(session: Any) -> None:
            await session.execute(
                update(TelemetryReportRow)
                .where(TelemetryReportRow.id == report_id)
                .values(status="sent", sent_at=now, last_error=None)
            )
            await session.execute(
                update(TelemetryEventRow)
                .where(TelemetryEventRow.report_id == report_id)
                .values(status="sent", sent_at=now, last_error=None)
            )

        await self._transaction(_op)

    async def mark_report_retry(
        self,
        report_id: int,
        event_ids: Sequence[int],
        error: str,
        next_attempt_at: datetime,
    ) -> None:
        async def _op(session: Any) -> None:
            await session.execute(
                update(TelemetryReportRow)
                .where(TelemetryReportRow.id == report_id)
                .values(status="pending", next_attempt_at=next_attempt_at, last_error=error)
            )
            await session.execute(
                update(TelemetryEventRow)
                .where(TelemetryEventRow.report_id == report_id)
                .values(status="pending", next_attempt_at=next_attempt_at, last_error=error)
            )

        await self._transaction(_op)

    async def mark_report_failed(
        self, report_id: int, event_ids: Sequence[int], error: str
    ) -> None:
        async def _op(session: Any) -> None:
            await session.execute(
                update(TelemetryReportRow)
                .where(TelemetryReportRow.id == report_id)
                .values(status="failed", last_error=error)
            )
            await session.execute(
                update(TelemetryEventRow)
                .where(TelemetryEventRow.report_id == report_id)
                .values(status="failed", last_error=error)
            )

        await self._transaction(_op)

    async def counts(self) -> OutboxCounts:
        async def _op(session: Any) -> OutboxCounts:
            pending_events = await session.scalar(
                select(func.count())
                .select_from(TelemetryEventRow)
                .where(TelemetryEventRow.status == "pending")
            )
            failed_events = await session.scalar(
                select(func.count())
                .select_from(TelemetryEventRow)
                .where(TelemetryEventRow.status == "failed")
            )
            sent_events = await session.scalar(
                select(func.count())
                .select_from(TelemetryEventRow)
                .where(TelemetryEventRow.status == "sent")
            )
            pending_reports = await session.scalar(
                select(func.count())
                .select_from(TelemetryReportRow)
                .where(TelemetryReportRow.status == "pending")
            )
            failed_reports = await session.scalar(
                select(func.count())
                .select_from(TelemetryReportRow)
                .where(TelemetryReportRow.status == "failed")
            )
            return OutboxCounts(
                pending_events=int(pending_events or 0),
                failed_events=int(failed_events or 0),
                sent_events=int(sent_events or 0),
                pending_reports=int(pending_reports or 0),
                failed_reports=int(failed_reports or 0),
            )

        return await self._read(_op)

    async def reset_stale_sending(self, older_than_seconds: int) -> None:
        now = self._clock.now_utc()
        cutoff = now - timedelta(seconds=older_than_seconds)

        async def _op(session: Any) -> None:
            await session.execute(
                update(TelemetryEventRow)
                .where(
                    TelemetryEventRow.status == "sending",
                    TelemetryEventRow.next_attempt_at < cutoff,
                )
                .values(status="pending", next_attempt_at=now)
            )
            await session.execute(
                update(TelemetryReportRow)
                .where(
                    TelemetryReportRow.status == "sending",
                    TelemetryReportRow.next_attempt_at < cutoff,
                )
                .values(status="pending", next_attempt_at=now)
            )

        await self._transaction(_op)
