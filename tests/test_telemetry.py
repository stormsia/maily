"""Tests for the telemetry module (service, sink, events, privacy)."""

from __future__ import annotations

import asyncio
import inspect
import json
import time
from datetime import datetime, timedelta
from pathlib import Path

import httpx
import pytest
from sqlalchemy import select

from maily.db.engine import SessionFactory, make_engine
from maily.db.models import Base
from maily.db.models import TelemetryEvent as TelemetryEventRow
from maily.db.models import TelemetryState as TelemetryStateRow
from maily.providers.registry import ProviderRegistry
from maily.settings import Settings
from maily.telemetry.models import TelemetryEvent
from maily.telemetry.ports import SinkResult
from maily.telemetry.posthog import PostHogSink, normalize_host
from maily.telemetry.service import build_telemetry_service

NOW = datetime(2026, 3, 5, 12, 0, 0)


class FakeClock:
    def __init__(self, now: datetime = NOW) -> None:
        self._now = now

    def now_utc(self) -> datetime:
        return self._now

    def today_utc(self):
        return self._now.date()

    def advance(self, days: int = 0, hours: int = 0) -> None:
        self._now += timedelta(days=days, hours=hours)


class FakeSink:
    """Collects everything that would be sent to PostHog."""

    def __init__(self, result: SinkResult | None = None) -> None:
        self.events: list[TelemetryEvent] = []
        self.batches = 0
        self.closed = False
        self.result = result or SinkResult(success=True)

    async def send(self, events) -> SinkResult:
        self.batches += 1
        self.events.extend(events)
        return self.result

    async def close(self) -> None:
        self.closed = True

    def names(self) -> list[str]:
        return [event.event_name for event in self.events]


async def _wait_for(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        outcome = predicate()
        if inspect.isawaitable(outcome):
            outcome = await outcome
        if outcome:
            return True
        await asyncio.sleep(0.02)
    return False


async def _event_rows(factory, event_name: str) -> list[TelemetryEventRow]:
    async with factory() as session:
        return list(
            (
                await session.execute(
                    select(TelemetryEventRow).where(TelemetryEventRow.event_name == event_name)
                )
            )
            .scalars()
            .all()
        )


async def _wait_for_event_rows(factory, event_name: str, count: int = 1) -> bool:
    async def _check() -> bool:
        rows = await _event_rows(factory, event_name)
        return len(rows) == count

    return await _wait_for(_check)


async def _wait_for_status(factory, event_name: str, status: str, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        async with factory() as session:
            rows = list(
                (
                    await session.execute(
                        select(TelemetryEventRow).where(
                            TelemetryEventRow.event_name == event_name,
                            TelemetryEventRow.status == status,
                        )
                    )
                )
                .scalars()
                .all()
            )
        if rows:
            return True
        await asyncio.sleep(0.02)
    return False


def _settings(tmp_path: Path, **overrides) -> Settings:
    base = {
        "database_url": f"sqlite+aiosqlite:///{tmp_path / 'telemetry.db'}",
        "secret_key": "s" * 32,
        "_env_file": None,
        "telemetry_enabled": True,
        "telemetry_posthog_api_key": "phc_test_token",
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
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'telemetry.db'}")
    factory = SessionFactory(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, factory


@pytest.mark.asyncio
async def test_disabled_without_token_makes_no_calls(tmp_path: Path):
    """A placeholder token keeps telemetry completely inactive."""
    engine, factory = await _engine(tmp_path)
    try:
        settings = _settings(
            tmp_path, telemetry_posthog_api_key="phc_REPLACE_WITH_REAL_PROJECT_TOKEN"
        )
        service = build_telemetry_service(factory, ProviderRegistry(), settings)
        assert not service.active
        await service.start()
        assert await service.track_once("maily_first_mailbox_created") is False
        async with factory() as session:
            rows = (await session.execute(select(TelemetryEventRow))).scalars().all()
            assert rows == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_disabled_by_flag_makes_no_calls(tmp_path: Path):
    """MAILY_TELEMETRY_ENABLED=false switches telemetry off entirely."""
    engine, factory = await _engine(tmp_path)
    try:
        settings = _settings(tmp_path, telemetry_enabled=False)
        service = build_telemetry_service(factory, ProviderRegistry(), settings)
        assert not service.active
        await service.start()
        assert await service.track_once("maily_first_mailbox_created") is False
        async with factory() as session:
            rows = (await session.execute(select(TelemetryEventRow))).scalars().all()
            assert rows == []
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_install_event_and_start_upgrade(tmp_path: Path):
    """First boot emits the install event; later boots emit start/upgrade."""
    engine, factory = await _engine(tmp_path)
    try:
        settings = _settings(tmp_path)
        sink = FakeSink()
        service = build_telemetry_service(
            factory, ProviderRegistry(), settings, sink=sink, clock=FakeClock()
        )
        await service.start()
        assert await _wait_for(lambda: "maily_install_created" in sink.names())
        install = next(e for e in sink.events if e.event_name == "maily_install_created")
        assert install.properties["version"]
        assert install.properties["installation_id"]
        assert install.distinct_id == install.properties["installation_id"]
        await service.stop()

        # Pretend the previous run was an older version.
        async with factory() as session:
            row = await session.get(TelemetryStateRow, 1)
            row.last_version = "0.0.1"
            row.last_start_at = NOW - timedelta(days=1)
            await session.commit()

        sink2 = FakeSink()
        service2 = build_telemetry_service(
            factory, ProviderRegistry(), settings, sink=sink2, clock=FakeClock()
        )
        await service2.start()
        assert await _wait_for(lambda: "maily_version_upgraded" in sink2.names())
        assert await _wait_for(lambda: "maily_app_started" in sink2.names())
        upgraded = next(e for e in sink2.events if e.event_name == "maily_version_upgraded")
        assert upgraded.properties["from_version"] == "0.0.1"
        assert upgraded.properties["to_version"]
        await service2.stop()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_track_once_is_deduplicated(tmp_path: Path):
    """The same first-use event is stored only once."""
    engine, factory = await _engine(tmp_path)
    try:
        settings = _settings(tmp_path)
        sink = FakeSink()
        service = build_telemetry_service(
            factory, ProviderRegistry(), settings, sink=sink, clock=FakeClock()
        )
        await service.start()
        await service.track_once("maily_first_mailbox_created", provider="mailtm")
        await service.track_once("maily_first_mailbox_created", provider="mailtm")
        assert await _wait_for_event_rows(factory, "maily_first_mailbox_created")
        await service.flush()
        rows = await _event_rows(factory, "maily_first_mailbox_created")
        assert len(rows) == 1
        await service.stop()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_setup_completed_only_once(tmp_path: Path):
    """Setup completion is recorded once, no matter how many triggers fire."""
    engine, factory = await _engine(tmp_path)
    try:
        settings = _settings(tmp_path)
        sink = FakeSink()
        service = build_telemetry_service(
            factory, ProviderRegistry(), settings, sink=sink, clock=FakeClock()
        )
        await service.start()
        await service.mark_setup("first_mailbox", provider="mailtm")
        await service.mark_setup("first_mailbox", provider="mailtm")
        assert await _wait_for_event_rows(factory, "maily_setup_completed")
        await service.flush()
        rows = await _event_rows(factory, "maily_setup_completed")
        assert len(rows) == 1
        await service.stop()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_daily_report_is_generated_and_sent(tmp_path: Path):
    """A missing day produces a report with the global and provider events."""
    engine, factory = await _engine(tmp_path)
    try:
        settings = _settings(tmp_path)
        clock = FakeClock()
        sink = FakeSink()
        service = build_telemetry_service(
            factory, ProviderRegistry(), settings, sink=sink, clock=clock
        )
        await service.start()
        async with factory() as session:
            row = await session.get(TelemetryStateRow, 1)
            row.created_at = clock.now_utc() - timedelta(days=5)
            row.last_snapshot_day = clock.today_utc() - timedelta(days=2)
            await session.commit()

        await service.flush()
        assert await _wait_for(lambda: "maily_daily_snapshot" in sink.names())
        snapshot = next(e for e in sink.events if e.event_name == "maily_daily_snapshot")
        assert snapshot.properties["snapshot_day"] == str(clock.today_utc() - timedelta(days=1))
        assert snapshot.properties["period_start"]
        assert "$geoip_disable" in snapshot.properties
        await service.stop()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_failed_send_is_retried_then_marked_failed(tmp_path: Path):
    """Retryable failures stay pending, non-retryable ones are marked failed."""
    engine, factory = await _engine(tmp_path)
    try:
        settings = _settings(tmp_path, telemetry_max_attempts=1)
        sink = FakeSink(SinkResult(success=False, retryable=False, status_code=400, error="bad"))
        service = build_telemetry_service(
            factory, ProviderRegistry(), settings, sink=sink, clock=FakeClock()
        )
        await service.start()
        await service.track_once("maily_first_api_key_created")
        assert await _wait_for_event_rows(factory, "maily_first_api_key_created")
        await service.flush()
        assert await _wait_for_status(factory, "maily_first_api_key_created", "failed")
        rows = await _event_rows(factory, "maily_first_api_key_created")
        assert len(rows) == 1
        assert rows[0].status == "failed"
        await service.stop()
    finally:
        await engine.dispose()


def test_normalize_host():
    assert normalize_host("https://us.i.posthog.com") == "https://us.i.posthog.com/batch/"
    assert normalize_host("https://us.i.posthog.com/") == "https://us.i.posthog.com/batch/"
    assert normalize_host("https://us.i.posthog.com/batch") == "https://us.i.posthog.com/batch/"
    assert normalize_host("") == ""


def _event(name: str = "maily_test") -> TelemetryEvent:
    return TelemetryEvent(
        event_uuid="11111111-1111-5111-8111-111111111111",
        event_name=name,
        distinct_id="install-1",
        properties={"version": "0.8.0"},
        occurred_at=NOW,
    )


@pytest.mark.asyncio
async def test_sink_posts_expected_payload():
    """The batch body matches the PostHog capture API contract."""
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["body"] = request.read().decode()
        return httpx.Response(200, json={"status": 1})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    sink = PostHogSink(
        api_key="phc_test_token",
        host="https://us.i.posthog.com",
        client=client,
    )
    try:
        result = await sink.send([_event()])
        assert result.success
        assert seen["url"] == "https://us.i.posthog.com/batch/"
        body = str(seen["body"])
        assert '"api_key":"phc_test_token"' in body.replace(" ", "")
        assert "maily_test" in body
        assert "11111111-1111-5111-8111-111111111111" in body
        assert '"$lib":"maily-telemetry"' in body.replace(" ", "")
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_sink_error_classification():
    """5xx retries, 400 does not, 429 honours Retry-After."""

    async def _run(status: int, headers: dict[str, str] | None = None):
        async def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(status, text="err", headers=headers or {})

        client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
        sink = PostHogSink(
            api_key="phc_test_token",
            host="https://us.i.posthog.com",
            client=client,
        )
        try:
            return await sink.send([_event()])
        finally:
            await client.aclose()

    server_error = await _run(500)
    assert server_error.retryable and not server_error.success

    client_error = await _run(400)
    assert not client_error.retryable and not client_error.success

    throttled = await _run(429, {"Retry-After": "3"})
    assert throttled.retryable and throttled.retry_after == 3.0

    forbidden = await _run(401)
    assert forbidden.retryable and forbidden.retry_after and forbidden.retry_after > 3600


@pytest.mark.asyncio
async def test_sink_reports_network_failure_as_retryable():
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    sink = PostHogSink(
        api_key="phc_test_token",
        host="https://us.i.posthog.com",
        client=client,
    )
    try:
        result = await sink.send([_event()])
        assert result.retryable and not result.success
        assert result.error
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_end_to_end_event_reaches_posthog(tmp_path: Path):
    """track() -> outbox -> HTTP batch -> row marked as sent."""
    engine, factory = await _engine(tmp_path)
    received: list[dict] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        received.append(json.loads(request.read().decode()))
        return httpx.Response(200, json={"status": 1})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        sink = PostHogSink(
            api_key="phc_test_token",
            host="https://us.i.posthog.com",
            client=client,
        )
        settings = _settings(tmp_path)
        service = build_telemetry_service(
            factory, ProviderRegistry(), settings, sink=sink, clock=FakeClock()
        )
        await service.start()
        await service.track_once("maily_first_mailbox_created", provider="mailtm")

        async def _delivered() -> bool:
            return any(
                item["event"] == "maily_first_mailbox_created"
                for batch in received
                for item in batch["batch"]
            )

        assert await _wait_for(_delivered)
        batch = next(
            batch
            for batch in received
            if any(item["event"] == "maily_first_mailbox_created" for item in batch["batch"])
        )
        assert batch["api_key"] == "phc_test_token"
        payload = next(
            item for item in batch["batch"] if item["event"] == "maily_first_mailbox_created"
        )
        assert payload["distinct_id"]
        assert payload["uuid"]
        assert payload["timestamp"].endswith("Z")
        assert payload["properties"]["provider"] == "mailtm"

        assert await _wait_for_status(factory, "maily_first_mailbox_created", "sent")
        await service.stop()
    finally:
        await client.aclose()
        await engine.dispose()
