"""Unit tests for the telemetry helpers: geo, privacy, sink edges, repository, worker."""

from __future__ import annotations

import asyncio
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from maily.db.engine import SessionFactory, make_engine
from maily.db.models import Base
from maily.db.models import TelemetryEvent as TelemetryEventRow
from maily.telemetry.geo import IpWhoIsGeoResolver
from maily.telemetry.models import GeoInfo, TelemetryEvent, TelemetryState
from maily.telemetry.posthog import PostHogSink
from maily.telemetry.privacy import (
    deployment,
    geo_properties,
    installation_properties,
    json_bytes,
    runtime_properties,
    sanitize_properties,
    truncate_error,
)
from maily.telemetry.repository import SqlTelemetryRepository
from maily.telemetry.worker import TelemetryWorker

NOW = datetime(2026, 3, 5, 12, 0, 0)


class FakeClock:
    def now_utc(self) -> datetime:
        return NOW

    def today_utc(self) -> date:
        return NOW.date()


def _state() -> TelemetryState:
    return TelemetryState(
        id=1,
        installation_id="inst-1",
        created_at=datetime(2026, 3, 1, 8, 0, 0),
        app_start_count=2,
        first_version="0.8.0",
        last_version="0.8.0",
        last_start_at=None,
        last_flush_at=None,
        last_snapshot_day=date(2026, 3, 4),
        setup_completed_at=None,
        geo_json="{}",
        geo_updated_at=None,
        last_error=None,
        updated_at=None,
    )


def _event(name: str = "maily_test", uuid: str = "e1") -> TelemetryEvent:
    return TelemetryEvent(
        event_uuid=uuid,
        event_name=name,
        distinct_id="inst-1",
        properties={"version": "0.8.0"},
        occurred_at=NOW,
    )


async def _repo(tmp_path: Path):
    engine = make_engine(f"sqlite+aiosqlite:///{tmp_path / 'repo.db'}")
    factory = SessionFactory(engine)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, SqlTelemetryRepository(factory, FakeClock())


# --- geo ---------------------------------------------------------------------


@pytest.mark.asyncio
async def test_geo_resolver_parses_ipwho_payload():
    payload = {
        "success": True,
        "ip": "203.0.113.7",
        "country": "Germany",
        "country_code": "DE",
        "region": "Berlin",
        "city": "Berlin",
        "timezone": "Europe/Berlin",
        "latitude": 52.52,
        "longitude": 13.405,
        "connection": {"asn": 64496, "isp": "Example ISP"},
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=payload)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    resolver = IpWhoIsGeoResolver("https://ipwho.is/", client=client)
    try:
        geo = await resolver.resolve()
        assert geo is not None
        assert geo.ip == "203.0.113.7"
        assert geo.country_code == "DE"
        assert geo.asn == 64496
        assert geo.isp == "Example ISP"
        assert geo.latitude == 52.52
    finally:
        await client.aclose()


@pytest.mark.asyncio
async def test_geo_resolver_returns_none_on_failure():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"success": False, "message": "reserved range"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    resolver = IpWhoIsGeoResolver("https://ipwho.is/", client=client)
    try:
        assert await resolver.resolve() is None
    finally:
        await client.aclose()

    async def broken(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down", request=request)

    client2 = httpx.AsyncClient(transport=httpx.MockTransport(broken))
    resolver2 = IpWhoIsGeoResolver("https://ipwho.is/", client=client2)
    try:
        assert await resolver2.resolve() is None
    finally:
        await client2.aclose()


@pytest.mark.asyncio
async def test_geo_resolver_closes_owned_client():
    resolver = IpWhoIsGeoResolver("https://ipwho.is/")
    await resolver.close()


# --- privacy -----------------------------------------------------------------


def test_sanitize_properties_drops_sensitive_keys():
    cleaned = sanitize_properties(
        {
            "api_key": "phc_secret",
            "user_email": "a@b.c",
            "mailbox_token_enc": "x",
            "refresh_token": "y",
            "password": "z",
            "address": "a@b.c",
            "api_key_required": True,
            "provider": "mailtm",
            "version": "0.8.0",
        }
    )
    assert "api_key" not in cleaned
    assert "user_email" not in cleaned
    assert "mailbox_token_enc" not in cleaned
    assert "refresh_token" not in cleaned
    assert "password" not in cleaned
    assert "address" not in cleaned
    assert cleaned["api_key_required"] is True
    assert cleaned["provider"] == "mailtm"


def test_sanitize_properties_bounds_values():
    cleaned = sanitize_properties(
        {
            "long": "x" * 1000,
            "nested": {"a": {"b": {"c": {"d": {"e": "deep"}}}}},
            "items": list(range(500)),
            "number": 12,
            "flag": False,
            "empty": None,
        }
    )
    assert len(cleaned["long"]) == 512
    assert len(cleaned["items"]) == 100
    assert cleaned["number"] == 12
    assert cleaned["flag"] is False
    assert cleaned["empty"] is None
    assert json_bytes(cleaned) > 0


def test_truncate_error_and_json_bytes():
    assert truncate_error(None) == ""
    assert truncate_error("boom\n  boom") == "boom boom"
    assert len(truncate_error("x" * 1000)) == 300
    assert json_bytes({"a": 1}) > 0


def test_geo_properties_variants():
    assert geo_properties(None, include_ip=False) == {"$geoip_disable": True}
    assert geo_properties(None, include_ip=True) == {}
    geo = GeoInfo(
        ip="198.51.100.1",
        country="France",
        country_code="FR",
        asn=1234,
        latitude=48.85,
    )
    props = geo_properties(geo, include_ip=True)
    assert props["$ip"] == "198.51.100.1"
    assert props["country_code"] == "FR"
    assert props["asn"] == 1234
    assert "isp" not in props  # empty values are dropped


def test_installation_and_runtime_properties():
    props = installation_properties(_state(), date(2026, 3, 5))
    assert props["installation_id"] == "inst-1"
    assert props["install_age_days"] == 4
    assert props["days_since_last_snapshot"] == 1
    assert props["app_start_count"] == 2

    class _Settings:
        api_key = "root"
        proxy = None
        gmail_client_id = "id"
        gmail_client_secret = "secret"
        domain_cache_enabled = True
        db_maintenance_enabled = True
        retention_interval_seconds = 60

    runtime = runtime_properties(_Settings(), "0.8.0")
    assert runtime["version"] == "0.8.0"
    assert runtime["api_key_required"] is True
    assert runtime["gmail_configured"] is True
    assert runtime["deployment"] in {"docker", "kubernetes", "bare"}
    assert deployment() in {"docker", "kubernetes", "bare"}


def test_geo_info_json_roundtrip():
    geo = GeoInfo(ip="203.0.113.7", country="Germany", asn=42)
    restored = GeoInfo.from_json(geo.to_json())
    assert restored is not None
    assert restored.ip == "203.0.113.7"
    assert restored.asn == 42
    assert GeoInfo.from_json("not json") is None
    assert GeoInfo.from_json("{}") is None
    assert GeoInfo.from_json(None) is None


# --- sink --------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sink_edge_cases():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(413, text="too large")

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    sink = PostHogSink(
        api_key="phc_x",
        host="https://us.i.posthog.com",
        client=client,
        max_event_bytes=10_000,
    )
    try:
        assert (await sink.send([])).success
        big = TelemetryEvent(
            event_uuid="u",
            event_name="maily_big",
            distinct_id="inst-1",
            properties={"blob": "x" * 50},
            occurred_at=NOW,
        )
        oversized = PostHogSink(
            api_key="phc_x",
            host="https://us.i.posthog.com",
            client=client,
            max_event_bytes=10,
        )
        result = await oversized.send([big])
        assert not result.success
        assert not result.retryable

        too_large = await sink.send([_event()])
        assert too_large.too_large and not too_large.success
    finally:
        await client.aclose()

    unconfigured = PostHogSink(api_key="", host="")
    result = await unconfigured.send([_event()])
    assert not result.success
    await unconfigured.close()


@pytest.mark.asyncio
async def test_sink_splits_large_batches():
    calls: list[int] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read().decode())
        calls.append(len(body["batch"]))
        return httpx.Response(200, json={"status": 1})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    sink = PostHogSink(
        api_key="phc_x",
        host="https://us.i.posthog.com",
        client=client,
        max_batch_events=50,
    )
    try:
        events = [_event(f"e{i}", uuid=f"uuid-{i}") for i in range(120)]
        result = await sink.send(events)
        assert result.success
        assert calls == [50, 50, 20]
    finally:
        await client.aclose()


# --- repository --------------------------------------------------------------


@pytest.mark.asyncio
async def test_repository_lifecycle(tmp_path: Path):
    engine, repo = await _repo(tmp_path)
    try:
        state = await repo.ensure_state()
        again = await repo.ensure_state()
        assert state.installation_id == again.installation_id

        await repo.update_state(first_version="0.8.0", app_start_count=3)
        refreshed = await repo.load_state()
        assert refreshed is not None
        assert refreshed.first_version == "0.8.0"
        assert refreshed.app_start_count == 3

        assert await repo.mark_setup_completed() is True
        assert await repo.mark_setup_completed() is False

        inserted = await repo.enqueue_events([_event("a", "u1"), _event("a", "u1")])
        assert inserted == 1
        assert await repo.enqueue_events([_event("b", "u2")]) == 1

        claimed = await repo.claim_due_events(10)
        assert len(claimed) == 2
        assert all(item.status == "sending" for item in claimed)
        assert all(item.attempts == 1 for item in claimed)
        assert await repo.claim_due_events(10) == []

        await repo.mark_events_retry([claimed[0].row_id], "boom", NOW)
        await repo.mark_events_failed([claimed[1].row_id], "bad")
        counts = await repo.counts()
        assert counts.pending_events == 1
        assert counts.failed_events == 1

        await repo.mark_events_sent([claimed[0].row_id])
        counts = await repo.counts()
        assert counts.sent_events == 1

        report_id = await repo.create_report(date(2026, 3, 4), [_event("r", "u3")])
        assert report_id is not None
        assert await repo.create_report(date(2026, 3, 4), [_event("r", "u4")]) is None

        reports = await repo.claim_due_reports(5)
        assert len(reports) == 1
        assert len(reports[0].events) == 1
        await repo.mark_report_retry(reports[0].id, [], "later", NOW + timedelta(hours=1))
        await repo.mark_report_failed(reports[0].id, [], "fatal")
        counts = await repo.counts()
        assert counts.failed_reports == 1

        await repo.reset_stale_sending(0)
        assert (await repo.counts()).pending_reports == 0
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_repository_update_state_without_row(tmp_path: Path):
    engine, repo = await _repo(tmp_path)
    try:
        await repo.update_state(first_version="0.0.1")
        assert await repo.load_state() is None
    finally:
        await engine.dispose()


# --- worker ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_drains_queue_on_stop(tmp_path: Path):
    engine, repo = await _repo(tmp_path)
    try:
        ticks: list[int] = []

        async def _tick() -> None:
            ticks.append(1)

        worker = TelemetryWorker(
            repository=repo,
            settings=type(
                "S",
                (),
                {"telemetry_queue_maxsize": 1, "telemetry_immediate_debounce_seconds": 0.0},
            )(),
            clock=FakeClock(),
            on_tick=_tick,
        )
        assert worker.enqueue(_event("a", "w1")) is True
        # The queue holds a single item, so the next one is dropped.
        assert worker.enqueue(_event("b", "w2")) is False
        assert worker.dropped == 1

        await worker.start()
        await worker.stop()

        async with SessionFactory(engine)() as session:
            from sqlalchemy import select

            rows = (await session.execute(select(TelemetryEventRow))).scalars().all()
            assert len(rows) == 1
            assert rows[0].event_name == "a"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_worker_survives_repository_failure(tmp_path: Path):
    engine, repo = await _repo(tmp_path)
    try:

        class _BrokenRepo:
            async def enqueue_events(self, events):
                raise RuntimeError("db down")

        worker = TelemetryWorker(
            repository=_BrokenRepo(),
            settings=type(
                "S",
                (),
                {"telemetry_queue_maxsize": 8, "telemetry_immediate_debounce_seconds": 0.0},
            )(),
            clock=FakeClock(),
            on_tick=_tick_noop,
        )
        worker.enqueue(_event("a", "w3"))
        await worker.start()
        await asyncio.sleep(0.1)
        await worker.stop()
        assert worker.dropped == 1
    finally:
        await engine.dispose()


async def _tick_noop() -> None:
    return None
