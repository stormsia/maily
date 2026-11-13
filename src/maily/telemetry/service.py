"""Telemetry orchestration: lifecycle, event tracking, daily reports, sending."""

from __future__ import annotations

import asyncio
import logging
import random
import uuid
from collections.abc import Mapping, Sequence
from datetime import date, datetime, timedelta
from typing import Any

from .. import __version__
from ..providers.registry import ProviderRegistry
from ..settings import POSTHOG_PLACEHOLDER_TOKEN, Settings
from .geo import IpWhoIsGeoResolver
from .models import (
    FlushResult,
    OutboxCounts,
    TelemetryEvent,
    TelemetryReport,
    TelemetryState,
    TelemetryStatus,
)
from .ports import Clock, GeoResolver, SinkResult, SystemClock, TelemetryRepository, TelemetrySink
from .posthog import PostHogSink
from .privacy import (
    installation_properties,
    runtime_properties,
    sanitize_properties,
    truncate_error,
)
from .repository import SqlTelemetryRepository
from .snapshot import SnapshotBuilder
from .worker import TelemetryWorker

logger = logging.getLogger("maily.telemetry")

_GEO_TTL = timedelta(hours=24)
_CATCH_UP_DAYS = 7


def _token_configured(token: str) -> bool:
    if not token:
        return False
    if token == POSTHOG_PLACEHOLDER_TOKEN:
        return False
    return not token.startswith("phc_REPLACE")


def _backoff_seconds(attempts: int) -> float:
    base = min(3600.0, 5.0 * (2 ** min(max(attempts, 0), 6)))
    return base + random.uniform(0.0, 1.0)


class TelemetryService:
    def __init__(
        self,
        *,
        repository: TelemetryRepository,
        sink: TelemetrySink | None,
        snapshot_builder: SnapshotBuilder,
        geo_resolver: GeoResolver | None,
        settings: Settings,
        registry: ProviderRegistry | None,
        clock: Clock,
        version: str,
    ) -> None:
        self._repository = repository
        self._sink = sink
        self._snapshot_builder = snapshot_builder
        self._geo = geo_resolver
        self._settings = settings
        self._registry = registry
        self._clock = clock
        self._version = version
        self._active = bool(getattr(settings, "telemetry_enabled", True)) and sink is not None
        self._lock = asyncio.Lock()
        self._worker: TelemetryWorker | None = None
        self._state: TelemetryState | None = None
        self._installation_id: str | None = None

    @property
    def active(self) -> bool:
        return self._active and self._sink is not None

    @property
    def installation_id(self) -> str | None:
        return self._installation_id

    async def start(self) -> None:
        if not self.active:
            logger.info("telemetry: disabled")
            return
        async with self._lock:
            state = await self._repository.ensure_state()
            now = self._clock.now_utc()
            state = await self._refresh_geo(state, now)
            today = now.date()

            if state.app_start_count == 0:
                await self._repository.update_state(
                    first_version=self._version,
                    last_version=self._version,
                    app_start_count=1,
                    last_start_at=now,
                    last_snapshot_day=today - timedelta(days=1),
                )
                refreshed = await self._repository.load_state()
                if refreshed is None:
                    logger.error("telemetry: state disappeared during startup")
                    return
                state = refreshed
                self._state = state
                self._installation_id = state.installation_id
                await self._start_worker()
                baseline = await self._baseline_properties(state, today)
                await self._track("maily_install_created", baseline, dedupe_key="install")
                logger.info(
                    "telemetry: install %s started (version %s)",
                    state.installation_id,
                    self._version,
                )
                return

            previous_version = state.last_version
            last_start = state.last_start_at
            updates: dict[str, Any] = {
                "app_start_count": state.app_start_count + 1,
                "last_start_at": now,
            }
            if previous_version != self._version:
                updates["last_version"] = self._version
            await self._repository.update_state(**updates)
            refreshed = await self._repository.load_state()
            if refreshed is None:
                logger.error("telemetry: state disappeared during startup")
                return
            state = refreshed
            self._state = state
            self._installation_id = state.installation_id
            await self._start_worker()

            if previous_version != self._version:
                await self._track(
                    "maily_version_upgraded",
                    {"from_version": previous_version, "to_version": self._version},
                )
            if last_start is None or (now - last_start) >= timedelta(
                seconds=self._settings.telemetry_app_start_debounce_seconds
            ):
                await self._track(
                    "maily_app_started",
                    {
                        "version": self._version,
                        "previous_version": previous_version,
                        "app_start_count": state.app_start_count,
                    },
                )
            logger.info(
                "telemetry: started host=%s install=%s",
                self._settings.telemetry_posthog_host,
                state.installation_id,
            )

    async def stop(self) -> None:
        # After a stop the worker is gone: further events would be lost, so the
        # service becomes inactive.
        self._active = False
        if self._worker is not None:
            await self._worker.stop()
            self._worker = None
        if self._sink is not None:
            await self._sink.close()

    async def deactivate(self) -> None:
        await self.stop()

    async def track(
        self,
        event_name: str,
        properties: Mapping[str, Any] | None = None,
        *,
        dedupe_key: str | None = None,
        occurred_at: datetime | None = None,
    ) -> bool:
        return await self._track(
            event_name,
            dict(properties or {}),
            dedupe_key=dedupe_key,
            occurred_at=occurred_at,
        )

    async def track_once(self, event_name: str, **properties: Any) -> bool:
        return await self._track(event_name, dict(properties), dedupe_key=event_name)

    async def mark_setup(self, trigger: str, **properties: Any) -> None:
        if not self.active:
            return
        try:
            created = await self._repository.mark_setup_completed()
        except Exception:  # noqa: BLE001 - telemetry must never break a request
            logger.exception("telemetry: could not record setup completion")
            return
        if created:
            await self.track_once("maily_setup_completed", trigger=trigger, **properties)

    async def flush(self) -> FlushResult:
        if not self.active:
            return FlushResult()
        async with self._lock:
            return await self._tick_impl()

    async def status(self) -> TelemetryStatus:
        state = await self._ensure_state()
        counts = await self._repository.counts() if state is not None else OutboxCounts()
        dropped = self._worker.dropped if self._worker is not None else 0
        return TelemetryStatus(
            active=self.active,
            configured=self._sink is not None,
            installation_id=state.installation_id if state else None,
            last_flush_at=state.last_flush_at if state else None,
            last_snapshot_day=state.last_snapshot_day if state else None,
            pending_events=counts.pending_events,
            failed_events=counts.failed_events,
            sent_events=counts.sent_events,
            pending_reports=counts.pending_reports,
            failed_reports=counts.failed_reports,
            dropped=dropped,
            last_error=state.last_error if state else None,
        )

    async def _start_worker(self) -> None:
        worker = TelemetryWorker(
            repository=self._repository,
            settings=self._settings,
            clock=self._clock,
            on_tick=self._tick,
        )
        await worker.start()
        self._worker = worker

    async def _track(
        self,
        event_name: str,
        properties: Mapping[str, Any] | None,
        *,
        dedupe_key: str | None = None,
        occurred_at: datetime | None = None,
    ) -> bool:
        if not self.active or self._worker is None:
            return False
        state = await self._ensure_state()
        if state is None:
            return False

        props = runtime_properties(self._settings, self._version)
        props.update(installation_properties(state, self._clock.today_utc()))
        if not self._settings.telemetry_include_ip:
            props["$geoip_disable"] = True
        if properties:
            props.update(properties)

        event_uuid = (
            str(
                uuid.uuid5(uuid.NAMESPACE_URL, f"{state.installation_id}:{event_name}:{dedupe_key}")
            )
            if dedupe_key
            else str(uuid.uuid4())
        )
        event = TelemetryEvent(
            event_uuid=event_uuid,
            event_name=event_name,
            distinct_id=state.installation_id,
            properties=sanitize_properties(props),
            occurred_at=occurred_at or self._clock.now_utc(),
        )
        return self._worker.enqueue(event)

    async def _ensure_state(self) -> TelemetryState | None:
        if self._state is None:
            self._state = await self._repository.load_state()
        return self._state

    async def _refresh_geo(self, state: TelemetryState, now: datetime) -> TelemetryState:
        if not self._settings.telemetry_include_ip or self._geo is None:
            return state
        if state.geo_updated_at is not None and (now - state.geo_updated_at) < _GEO_TTL:
            return state
        geo = await self._geo.resolve()
        if geo is None:
            return state
        await self._repository.update_state(geo_json=geo.to_json(), geo_updated_at=now)
        return (await self._repository.load_state()) or state

    async def _baseline_properties(self, state: TelemetryState, today: date) -> dict[str, Any]:
        try:
            events = await self._snapshot_builder.build(today, state, is_backfill=False)
        except Exception:  # noqa: BLE001 - baseline is best-effort
            logger.exception("telemetry: baseline snapshot failed")
            return {}
        if not events:
            return {}
        properties = dict(events[0].properties)
        properties["baseline"] = True
        return properties

    async def _tick(self) -> None:
        if not self.active:
            return
        async with self._lock:
            await self._tick_impl()

    async def _tick_impl(self) -> FlushResult:
        try:
            await self._maybe_daily()
        except Exception:  # noqa: BLE001 - keep the worker alive
            logger.exception("telemetry: daily report generation failed")
        result = FlushResult()
        try:
            result = await self._send_due()
        except Exception:  # noqa: BLE001 - keep the worker alive
            logger.exception("telemetry: sending failed")
        try:
            await self._repository.reset_stale_sending(0)
        except Exception:  # noqa: BLE001 - cleanup is best-effort
            logger.exception("telemetry: stale send cleanup failed")
        return result

    def _daily_window_open(self, now: datetime) -> bool:
        """True once the configured UTC hour (plus jitter) has passed."""
        hour = self._settings.telemetry_daily_hour_utc
        jitter_minutes = max(0, int(self._settings.telemetry_daily_jitter_seconds) // 60)
        if now.hour > hour:
            return True
        return now.hour == hour and now.minute >= jitter_minutes

    async def _maybe_daily(self) -> None:
        state = await self._repository.load_state()
        if state is None:
            return
        now = self._clock.now_utc()
        state = await self._refresh_geo(state, now)
        today = now.date()
        install_day = state.created_at.date() if state.created_at else today
        last_day = state.last_snapshot_day or (install_day - timedelta(days=1))

        due_days: list[date] = []
        day = last_day + timedelta(days=1)
        while day < today:
            due_days.append(day)
            day += timedelta(days=1)
        due_days = [candidate for candidate in due_days if candidate >= install_day]
        if not due_days:
            return
        only_yesterday_missing = len(due_days) == 1 and due_days[0] == today - timedelta(days=1)
        if only_yesterday_missing and not self._daily_window_open(now):
            # The scheduled hour has not arrived yet — wait instead of reporting early.
            return
        due_days = due_days[-_CATCH_UP_DAYS:]

        for candidate in due_days:
            try:
                events = await self._snapshot_builder.build(
                    candidate,
                    state,
                    is_backfill=(candidate < today - timedelta(days=1)),
                )
            except Exception:  # noqa: BLE001 - skip a bad day, keep the rest
                logger.exception("telemetry: snapshot build failed for %s", candidate)
                continue
            try:
                await self._repository.create_report(candidate, events)
            except Exception:  # noqa: BLE001 - skip a bad day, keep the rest
                logger.exception("telemetry: create_report failed for %s", candidate)

        await self._repository.update_state(last_snapshot_day=due_days[-1])

    async def _send_due(self) -> FlushResult:
        sent = 0
        failed = 0
        reports = await self._repository.claim_due_reports(limit=10)
        for report in reports:
            try:
                report_sent, report_failed = await self._send_report(report)
            except Exception:  # noqa: BLE001 - keep sending other reports
                logger.exception("telemetry: report %s send failed", report.id)
                continue
            sent += report_sent
            failed += report_failed

        events = await self._repository.claim_due_events(
            limit=self._settings.telemetry_max_batch_events
        )
        if events:
            try:
                events_sent, events_failed = await self._send_events(events)
            except Exception:  # noqa: BLE001 - keep the worker alive
                logger.exception("telemetry: immediate events send failed")
            else:
                sent += events_sent
                failed += events_failed
        return FlushResult(sent=sent, failed=failed)

    async def _send_report(self, report: TelemetryReport) -> tuple[int, int]:
        if not report.events:
            await self._repository.mark_report_failed(report.id, [], "empty report")
            return (0, 1)
        result = await self._sink.send(report.events)  # type: ignore[union-attr]
        if result.success:
            await self._repository.mark_report_sent(
                report.id, [event.row_id for event in report.events if event.row_id]
            )
            await self._repository.update_state(last_flush_at=self._clock.now_utc())
            return (len(report.events), 0)
        if result.too_large and len(report.events) > 1:
            middle = len(report.events) // 2
            left = await self._send_report_chunk(report, report.events[:middle])
            right = await self._send_report_chunk(report, report.events[middle:])
            return (left[0] + right[0], left[1] + right[1])
        await self._handle_report_failure(report, result)
        return (0, len(report.events))

    async def _send_report_chunk(
        self, report: TelemetryReport, events: Sequence[TelemetryEvent]
    ) -> tuple[int, int]:
        result = await self._sink.send(events)  # type: ignore[union-attr]
        if result.success:
            return (len(events), 0)
        if result.too_large and len(events) > 1:
            middle = len(events) // 2
            left = await self._send_report_chunk(report, events[:middle])
            right = await self._send_report_chunk(report, events[middle:])
            return (left[0] + right[0], left[1] + right[1])
        await self._handle_report_failure(report, result)
        return (0, len(events))

    async def _handle_report_failure(self, report: TelemetryReport, result: SinkResult) -> None:
        attempts = max((event.attempts for event in report.events), default=0)
        error = truncate_error(result.error or f"HTTP {result.status_code}")
        event_ids = [event.row_id for event in report.events if event.row_id]
        if result.retryable and attempts < self._settings.telemetry_max_attempts:
            delay = result.retry_after or _backoff_seconds(attempts)
            next_attempt = self._clock.now_utc() + timedelta(seconds=delay)
            await self._repository.mark_report_retry(report.id, event_ids, error, next_attempt)
        else:
            await self._repository.mark_report_failed(report.id, event_ids, error)
        await self._repository.update_state(last_error=error)

    async def _send_events(self, events: Sequence[TelemetryEvent]) -> tuple[int, int]:
        if not events:
            return (0, 0)
        result = await self._sink.send(events)  # type: ignore[union-attr]
        if result.success:
            await self._repository.mark_events_sent(
                [event.row_id for event in events if event.row_id]
            )
            await self._repository.update_state(last_flush_at=self._clock.now_utc())
            return (len(events), 0)
        if result.too_large and len(events) > 1:
            middle = len(events) // 2
            left = await self._send_events(events[:middle])
            right = await self._send_events(events[middle:])
            return (left[0] + right[0], left[1] + right[1])
        await self._handle_events_failure(events, result)
        return (0, len(events))

    async def _handle_events_failure(
        self, events: Sequence[TelemetryEvent], result: SinkResult
    ) -> None:
        attempts = max((event.attempts for event in events), default=0)
        error = truncate_error(result.error or f"HTTP {result.status_code}")
        ids = [event.row_id for event in events if event.row_id]
        if result.retryable and attempts < self._settings.telemetry_max_attempts:
            delay = result.retry_after or _backoff_seconds(attempts)
            next_attempt = self._clock.now_utc() + timedelta(seconds=delay)
            await self._repository.mark_events_retry(ids, error, next_attempt)
        else:
            await self._repository.mark_events_failed(ids, error)
        await self._repository.update_state(last_error=error)


def build_telemetry_service(
    factory: Any,
    registry: ProviderRegistry | None,
    settings: Settings,
    *,
    clock: Clock | None = None,
    sink: TelemetrySink | None = None,
    repository: TelemetryRepository | None = None,
    snapshot_builder: SnapshotBuilder | None = None,
    geo_resolver: GeoResolver | None = None,
    force_disabled: bool = False,
) -> TelemetryService:
    """Wire the telemetry service from settings. Never raises for a missing token."""
    resolved_clock = clock or SystemClock()
    resolved_repo = repository or SqlTelemetryRepository(factory, resolved_clock)
    resolved_snapshot = snapshot_builder or SnapshotBuilder(
        factory, registry, settings, resolved_clock
    )
    if (
        geo_resolver is None
        and settings.telemetry_include_ip
        and settings.telemetry_geo_lookup_enabled
    ):
        geo_resolver = IpWhoIsGeoResolver(
            settings.telemetry_geo_lookup_url,
            timeout=min(5.0, settings.telemetry_http_timeout_seconds),
        )

    token = settings.telemetry_posthog_api_key
    if (
        sink is None
        and not force_disabled
        and settings.telemetry_enabled
        and _token_configured(token)
    ):
        sink = PostHogSink(
            api_key=token,
            host=settings.telemetry_posthog_host,
            proxy=settings.telemetry_proxy,
            timeout=settings.telemetry_http_timeout_seconds,
            max_batch_events=settings.telemetry_max_batch_events,
            max_event_bytes=settings.telemetry_max_event_bytes,
            person_profiles=settings.telemetry_person_profiles,
        )

    return TelemetryService(
        repository=resolved_repo,
        sink=sink,
        snapshot_builder=resolved_snapshot,
        geo_resolver=geo_resolver,
        settings=settings,
        registry=registry,
        clock=resolved_clock,
        version=__version__,
    )
