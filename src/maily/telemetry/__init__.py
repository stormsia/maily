"""Asynchronous, PostHog-compatible installation telemetry."""

from __future__ import annotations

from .models import (
    EventStatus,
    FlushResult,
    GeoInfo,
    OutboxCounts,
    Priority,
    TelemetryEvent,
    TelemetryReport,
    TelemetryState,
    TelemetryStatus,
)
from .ports import Clock, GeoResolver, SinkResult, SystemClock, TelemetryRepository, TelemetrySink
from .posthog import PostHogSink
from .retention import prune_telemetry
from .service import TelemetryService, build_telemetry_service

__all__ = [
    "Clock",
    "EventStatus",
    "FlushResult",
    "GeoInfo",
    "GeoResolver",
    "OutboxCounts",
    "PostHogSink",
    "Priority",
    "SinkResult",
    "SystemClock",
    "TelemetryEvent",
    "TelemetryReport",
    "TelemetryRepository",
    "TelemetryService",
    "TelemetrySink",
    "TelemetryState",
    "TelemetryStatus",
    "build_telemetry_service",
    "prune_telemetry",
]
