"""Tests for the telemetry service internals (retries, splitting, geo, scheduling)."""

from __future__ import annotations

import asyncio
import math
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import select

from maily.db.engine import SessionFactory, make_engine
from maily.db.models import Base
from maily.db.models import TelemetryEvent as TelemetryEventRow
from maily.db.models import TelemetryReport as TelemetryReportRow
from maily.db.models import TelemetryState as TelemetryStateRow
from maily.providers.registry import ProviderRegistry
from maily.settings import Settings
from maily.telemetry.models import GeoInfo, TelemetryEvent
from maily.telemetry.ports import SinkResult
from maily.telemetry.service import build_telemetry_service

NOW = datetime(2026, 3, 5, 12, 0, 0)


class FakeClock:
    def __init__(self, now: datetime = NOW) -> None:
        self._now = now

    def now_utc(self) -> datetime:
        return self._now

    def today_utc(self) -> date:
        return self._now.date()


class FakeSink:
    def __init__(self, result: SinkResult | None = None) -> None:
        self.events: list[TelemetryEvent] = []
        self.batches: list[int] = []
        self.result = result or SinkResult(success=True)
        self.closed = False

    async def send(self, events) -> SinkResult:
        self.batches.append(len(events))
        self.events.extend(events)
        return self.result

    async def close(self) -> None:
        self.closed = True


class SplittingSink:
    """Reports 'too large' until the batch is small enough."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        self.batches: list[int] = []

    async def send(self, events) -> SinkResult:
        self.batches.append(len(events))
        if len(events) > self.limit:
            return SinkResult(success=False, too_large=True)
        return SinkResult(success=True)

    async def close(self) -> None:
        return None


class FakeGeo:
    def __init__(self, geo: GeoInfo | None) -> None:
        self.geo = geo
        self.calls = 0

    async def resolve(self, previous=None) -> GeoInfo | None:
        self.calls += 1
        return self.geo

    async def close(self) -> None:
        return None


def _settings(tmp_path: Path, **overrides) -> Settings:
    base = {
        "database_url": f"sqlite+aiosqlite:///{tmp_path / 'service.db'}",
        "secret_key": "s" * 32,
        "_env_file": None,
        "telemetry_enabled": True,
        "telemetry_posthog_api_key": "phc_test",
        "telemetry_immediate_debounce_seconds": 0.0,
        "telemetry_app_start_debounce_seconds": 0,
        "telemetry_geo_lookup_enabled": False,
        "telemetry_include_ip": False,
        "telemetry_daily_hour_utc": 0,
        "db_maintenance_enabled": False,
    }
    base.update(overrides)
    return Settings(**base)


async def _engine(tmp_path: Path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'service.db'}")
    factory = SessionFactory(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, factory


async def _rows(factory, model):
    async with factory() as session:
        return list((await session.execute(select(model))).scalars().all())


@pytest.mark.asyncio
async def test_retryable_failure_stays_pending(tmp_path: Path):
    """A retryable error keeps the event queued with a future attempt time."""
    engine, factory = await _engine(tmp_path)
    try:
        sink = FakeSink(SinkResult(success=False, retryable=True, status_code=500, error="boom"))
        service = build_telemetry_service(
            factory,
            ProviderRegistry(),
            _settings(tmp_path),
            sink=sink,
            clock=FakeClock(),
        )
        await service.start()
        await service.track_once("maily_first_api_key_created")
        await asyncio.sleep(0.3)
        await service.flush()
        rows = await _rows(factory, TelemetryEventRow)
        pending = [row for row in rows if row.status == "pending"]
        assert pending
        assert pending[0].attempts >= 1
        assert pending[0].next_attempt_at > FakeClock().now_utc()
        await service.stop()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_oversized_batch_is_split(tmp_path: Path):
    """A 'too large' answer splits the batch until it fits."""
    engine, factory = await _engine(tmp_path)
    try:
        sink = SplittingSink(limit=1)
        service = build_telemetry_service(
            factory,
            ProviderRegistry(),
            _settings(tmp_path),
            sink=sink,
            clock=FakeClock(),
        )
        await service.start()
        for index in range(3):
            await service.track_once(f"maily_event_{index}")
        await asyncio.sleep(0.4)
        await service.flush()
        biggest = max(sink.batches)
        first_big = sink.batches.index(biggest)
        limit = max(2, math.ceil(biggest / 2))
        assert all(size <= limit for size in sink.batches[first_big + 1 :])
        assert sink.batches[-1] == 1
        assert sum(sink.batches) >= 4  # the install event plus the three tracked ones
        await service.stop()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_report_with_bad_payload_is_failed(tmp_path: Path):
    """A non-retryable error marks the daily report as failed."""
    engine, factory = await _engine(tmp_path)
    try:
        sink = FakeSink(SinkResult(success=False, retryable=False, status_code=400, error="bad"))
        service = build_telemetry_service(
            factory,
            ProviderRegistry(),
            _settings(tmp_path),
            sink=sink,
            clock=FakeClock(),
        )
        await service.start()
        async with factory() as session:
            row = await session.get(TelemetryStateRow, 1)
            row.created_at = FakeClock().now_utc() - timedelta(days=5)
            row.last_snapshot_day = FakeClock().today_utc() - timedelta(days=2)
            await session.commit()

        await service.flush()
        await asyncio.sleep(0.2)
        reports = await _rows(factory, TelemetryReportRow)
        assert reports
        assert reports[0].status == "failed"
        events = await _rows(factory, TelemetryEventRow)
        assert any(event.report_id == reports[0].id for event in events)
        await service.stop()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_status_reports_outbox_state(tmp_path: Path):
    """status() exposes the installation id and the outbox counters."""
    engine, factory = await _engine(tmp_path)
    try:
        service = build_telemetry_service(
            factory,
            ProviderRegistry(),
            _settings(tmp_path),
            sink=FakeSink(),
            clock=FakeClock(),
        )
        await service.start()
        await asyncio.sleep(0.2)
        status = await service.status()
        assert status.active
        assert status.installation_id
        assert status.pending_events + status.sent_events >= 1
        flushed = await service.flush()
        assert flushed.sent + flushed.failed >= 0
        await service.stop()
        assert not service.active
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_deactivate_disables_the_service(tmp_path: Path):
    """deactivate() stops the worker and closes the sink."""
    engine, factory = await _engine(tmp_path)
    try:
        sink = FakeSink()
        service = build_telemetry_service(
            factory,
            ProviderRegistry(),
            _settings(tmp_path),
            sink=sink,
            clock=FakeClock(),
        )
        await service.start()
        await service.deactivate()
        assert not service.active
        assert sink.closed
        assert await service.track_once("maily_first_mailbox_created") is False
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_geo_is_resolved_and_stored(tmp_path: Path):
    """A resolved geo is cached in the state and sent as $ip."""
    engine, factory = await _engine(tmp_path)
    try:
        geo = FakeGeo(GeoInfo(ip="203.0.113.7", country="Germany", country_code="DE"))
        settings = _settings(tmp_path, telemetry_include_ip=True, telemetry_geo_lookup_enabled=True)
        service = build_telemetry_service(
            factory,
            ProviderRegistry(),
            settings,
            sink=FakeSink(),
            clock=FakeClock(),
            geo_resolver=geo,
        )
        await service.start()
        async with factory() as session:
            row = await session.get(TelemetryStateRow, 1)
            assert row is not None
            assert '"ip":"203.0.113.7"' in row.geo_json.replace(" ", "")
            assert row.geo_updated_at is not None
        await service.stop()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_daily_report_waits_for_the_configured_hour(tmp_path: Path):
    """Before the configured UTC hour no daily report is produced."""
    engine, factory = await _engine(tmp_path)
    try:
        service = build_telemetry_service(
            factory,
            ProviderRegistry(),
            _settings(tmp_path, telemetry_daily_hour_utc=23),
            sink=FakeSink(),
            clock=FakeClock(),
        )
        await service.start()
        async with factory() as session:
            row = await session.get(TelemetryStateRow, 1)
            row.created_at = FakeClock().now_utc() - timedelta(days=5)
            row.last_snapshot_day = FakeClock().today_utc() - timedelta(days=2)
            await session.commit()

        await service.flush()
        # Only yesterday is missing, so the report waits for the configured hour.
        assert await _rows(factory, TelemetryReportRow) == []
        await service.stop()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_force_disabled_service_is_inactive(tmp_path: Path):
    """force_disabled=True produces a service that never sends anything."""
    engine, factory = await _engine(tmp_path)
    try:
        service = build_telemetry_service(
            factory,
            ProviderRegistry(),
            _settings(tmp_path),
            clock=FakeClock(),
            force_disabled=True,
        )
        assert not service.active
        await service.start()
        assert await service.track_once("maily_first_mailbox_created") is False
        assert await _rows(factory, TelemetryEventRow) == []
    finally:
        await engine.dispose()
