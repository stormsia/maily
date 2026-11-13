"""Plain data structures shared by the telemetry package."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum
from typing import Any


class Priority(StrEnum):
    """How soon an event should leave the outbox."""

    IMMEDIATE = "immediate"
    DAILY = "daily"


class EventStatus(StrEnum):
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class TelemetryEvent:
    """One PostHog event waiting to be sent."""

    event_uuid: str
    event_name: str
    distinct_id: str
    properties: dict[str, Any]
    occurred_at: datetime
    row_id: int | None = None
    report_id: int | None = None
    status: str = "pending"
    attempts: int = 0
    next_attempt_at: datetime | None = None
    created_at: datetime | None = None
    sent_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TelemetryState:
    """Installation identity and counters (telemetry_state row)."""

    id: int
    installation_id: str
    created_at: datetime | None
    app_start_count: int
    first_version: str
    last_version: str
    last_start_at: datetime | None
    last_flush_at: datetime | None
    last_snapshot_day: date | None
    setup_completed_at: datetime | None
    geo_json: str
    geo_updated_at: datetime | None
    last_error: str | None
    updated_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class TelemetryReport:
    """Daily report row plus its queued events."""

    id: int
    report_day: date
    status: str
    attempts: int
    next_attempt_at: datetime | None
    last_error: str | None
    created_at: datetime | None
    sent_at: datetime | None
    events: list[TelemetryEvent] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class OutboxCounts:
    pending_events: int = 0
    failed_events: int = 0
    sent_events: int = 0
    pending_reports: int = 0
    failed_reports: int = 0


@dataclass(frozen=True, slots=True)
class TelemetryStatus:
    active: bool
    configured: bool
    installation_id: str | None
    last_flush_at: datetime | None
    last_snapshot_day: date | None
    pending_events: int
    failed_events: int
    sent_events: int
    pending_reports: int
    failed_reports: int
    dropped: int
    last_error: str | None


@dataclass(frozen=True, slots=True)
class FlushResult:
    sent: int = 0
    failed: int = 0
    pending: int = 0


@dataclass(frozen=True, slots=True)
class GeoInfo:
    """Public egress IP and geolocation resolved from ipwho.is."""

    ip: str
    country: str = ""
    country_code: str = ""
    region: str = ""
    city: str = ""
    timezone: str = ""
    asn: int | None = None
    isp: str = ""
    latitude: float | None = None
    longitude: float | None = None

    def to_json(self) -> str:
        return json.dumps(
            {
                "ip": self.ip,
                "country": self.country,
                "country_code": self.country_code,
                "region": self.region,
                "city": self.city,
                "timezone": self.timezone,
                "asn": self.asn,
                "isp": self.isp,
                "latitude": self.latitude,
                "longitude": self.longitude,
            },
            separators=(",", ":"),
        )

    @classmethod
    def from_json(cls, raw: str | None) -> GeoInfo | None:
        if not raw:
            return None
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            return None
        if not isinstance(data, dict) or not data.get("ip"):
            return None
        asn = data.get("asn")
        try:
            asn = int(asn) if asn is not None else None
        except (TypeError, ValueError):
            asn = None
        try:
            latitude = float(data["latitude"]) if data.get("latitude") is not None else None
        except (TypeError, ValueError):
            latitude = None
        try:
            longitude = float(data["longitude"]) if data.get("longitude") is not None else None
        except (TypeError, ValueError):
            longitude = None
        return cls(
            ip=str(data["ip"]),
            country=str(data.get("country") or ""),
            country_code=str(data.get("country_code") or ""),
            region=str(data.get("region") or ""),
            city=str(data.get("city") or ""),
            timezone=str(data.get("timezone") or ""),
            asn=asn,
            isp=str(data.get("isp") or ""),
            latitude=latitude,
            longitude=longitude,
        )
