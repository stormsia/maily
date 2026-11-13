"""Tests for the telemetry retention cleanup (runs inside the main sweep)."""

from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select

from maily.app.services.retention import run_sweep
from maily.db.engine import SessionFactory, make_engine
from maily.db.models import (
    Base,
    TelemetryEvent,
    TelemetryReport,
    TelemetryState,
)
from maily.providers.registry import ProviderRegistry
from maily.settings import Settings
from maily.telemetry.retention import prune_telemetry

NOW = datetime(2026, 3, 10, 12, 0, 0)


async def _engine(tmp_path: Path, name: str = "telemetry_retention.db"):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / name}")
    factory = SessionFactory(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, factory


def _settings(tmp_path: Path, **overrides) -> Settings:
    base = {
        "database_url": f"sqlite+aiosqlite:///{tmp_path / 'telemetry_retention.db'}",
        "secret_key": "s" * 32,
        "_env_file": None,
        "db_maintenance_enabled": False,
        "telemetry_sent_retention_days": 7,
        "telemetry_unsent_retention_days": 30,
    }
    base.update(overrides)
    return Settings(**base)


@pytest.mark.asyncio
async def test_prune_keeps_fresh_rows_and_drops_old_ones(tmp_path: Path):
    """Sent rows live 7 days, unsent rows 30 days."""
    engine, factory = await _engine(tmp_path)
    try:
        async with factory() as session:
            session.add(TelemetryState(id=1, installation_id="inst-1", created_at=NOW))
            old_sent = TelemetryEvent(
                event_uuid="aaaaaaaa-0000-4000-8000-000000000001",
                event_name="maily_daily_snapshot",
                distinct_id="inst-1",
                properties_json="{}",
                occurred_at=NOW - timedelta(days=10),
                status="sent",
                created_at=NOW - timedelta(days=10),
                sent_at=NOW - timedelta(days=8),
                next_attempt_at=NOW - timedelta(days=8),
            )
            fresh_sent = TelemetryEvent(
                event_uuid="aaaaaaaa-0000-4000-8000-000000000002",
                event_name="maily_daily_snapshot",
                distinct_id="inst-1",
                properties_json="{}",
                occurred_at=NOW - timedelta(days=2),
                status="sent",
                created_at=NOW - timedelta(days=2),
                sent_at=NOW - timedelta(days=2),
                next_attempt_at=NOW - timedelta(days=2),
            )
            old_unsent = TelemetryEvent(
                event_uuid="aaaaaaaa-0000-4000-8000-000000000003",
                event_name="maily_first_mailbox_created",
                distinct_id="inst-1",
                properties_json="{}",
                occurred_at=NOW - timedelta(days=31),
                status="pending",
                created_at=NOW - timedelta(days=31),
                next_attempt_at=NOW - timedelta(days=31),
            )
            fresh_unsent = TelemetryEvent(
                event_uuid="aaaaaaaa-0000-4000-8000-000000000004",
                event_name="maily_first_mailbox_created",
                distinct_id="inst-1",
                properties_json="{}",
                occurred_at=NOW - timedelta(days=29),
                status="pending",
                created_at=NOW - timedelta(days=29),
                next_attempt_at=NOW - timedelta(days=29),
            )
            session.add_all([old_sent, fresh_sent, old_unsent, fresh_unsent])
            await session.commit()

        async with factory() as session:
            await prune_telemetry(session, sent_days=7, unsent_days=30, now=NOW)
            await session.commit()
            rows = list((await session.execute(select(TelemetryEvent))).scalars().all())
            uuids = {row.event_uuid for row in rows}
            assert "aaaaaaaa-0000-4000-8000-000000000001" not in uuids
            assert "aaaaaaaa-0000-4000-8000-000000000003" not in uuids
            assert "aaaaaaaa-0000-4000-8000-000000000002" in uuids
            assert "aaaaaaaa-0000-4000-8000-000000000004" in uuids
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_prune_removes_report_with_its_events(tmp_path: Path):
    """Deleting a sent report cascades to the events that belong to it."""
    engine, factory = await _engine(tmp_path, "telemetry_cascade.db")
    try:
        async with factory() as session:
            session.add(TelemetryState(id=1, installation_id="inst-1", created_at=NOW))
            report = TelemetryReport(
                report_day=datetime(2026, 3, 1).date(),
                status="sent",
                attempts=1,
                next_attempt_at=NOW - timedelta(days=9),
                created_at=NOW - timedelta(days=9),
                sent_at=NOW - timedelta(days=9),
            )
            session.add(report)
            await session.flush()
            session.add(
                TelemetryEvent(
                    report_id=report.id,
                    event_uuid="bbbbbbbb-0000-4000-8000-000000000001",
                    event_name="maily_daily_snapshot",
                    distinct_id="inst-1",
                    properties_json="{}",
                    occurred_at=NOW - timedelta(days=9),
                    status="sent",
                    created_at=NOW - timedelta(days=9),
                    sent_at=NOW - timedelta(days=9),
                    next_attempt_at=NOW - timedelta(days=9),
                )
            )
            await session.commit()

        async with factory() as session:
            await prune_telemetry(session, sent_days=7, unsent_days=30, now=NOW)
            await session.commit()
            reports = list((await session.execute(select(TelemetryReport))).scalars().all())
            events = list((await session.execute(select(TelemetryEvent))).scalars().all())
            assert reports == []
            assert events == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_only_the_root_sweep_prunes_telemetry(tmp_path: Path):
    """A per-key sweep must not touch instance-wide telemetry rows."""
    engine, factory = await _engine(tmp_path, "telemetry_sweep.db")
    try:
        async with factory() as session:
            session.add(TelemetryState(id=1, installation_id="inst-1", created_at=NOW))
            session.add(
                TelemetryEvent(
                    event_uuid="cccccccc-0000-4000-8000-000000000001",
                    event_name="maily_daily_snapshot",
                    distinct_id="inst-1",
                    properties_json="{}",
                    occurred_at=NOW - timedelta(days=40),
                    status="sent",
                    created_at=NOW - timedelta(days=40),
                    sent_at=NOW - timedelta(days=40),
                    next_attempt_at=NOW - timedelta(days=40),
                )
            )
            await session.commit()

        settings = _settings(tmp_path)
        registry = ProviderRegistry()
        await run_sweep(factory, registry, settings, only_key_id=7)
        async with factory() as session:
            rows = list((await session.execute(select(TelemetryEvent))).scalars().all())
            assert len(rows) == 1

        await run_sweep(factory, registry, settings)
        async with factory() as session:
            rows = list((await session.execute(select(TelemetryEvent))).scalars().all())
            assert rows == []
    finally:
        await engine.dispose()
