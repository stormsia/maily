"""Interfaces and small shared contracts for the telemetry package."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol

from .models import (
    OutboxCounts,
    TelemetryEvent,
    TelemetryReport,
    TelemetryState,
)


@dataclass(frozen=True, slots=True)
class SinkResult:
    """Outcome of one PostHog batch attempt."""

    success: bool
    status_code: int | None = None
    retryable: bool = False
    retry_after: float | None = None
    error: str | None = None
    too_large: bool = False
    sent_count: int = 0


class TelemetrySink(ABC):
    """Sends a batch of events to an ingestion endpoint."""

    @abstractmethod
    async def send(self, events: Sequence[TelemetryEvent]) -> SinkResult:
        """Send events. Implementations must not raise for network errors."""
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        """Release underlying HTTP resources."""
        raise NotImplementedError


class TelemetryRepository(ABC):
    """Persistence for installation state and the telemetry outbox."""

    @abstractmethod
    async def ensure_state(self) -> TelemetryState:
        raise NotImplementedError

    @abstractmethod
    async def load_state(self) -> TelemetryState | None:
        raise NotImplementedError

    @abstractmethod
    async def update_state(self, **fields: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_setup_completed(self) -> bool:
        """Set setup_completed_at once. Returns True when this call won."""
        raise NotImplementedError

    @abstractmethod
    async def enqueue_events(self, events: Sequence[TelemetryEvent]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def create_report(self, day: date, events: Sequence[TelemetryEvent]) -> int | None:
        """Persist a daily report and its events. None when the day exists."""
        raise NotImplementedError

    @abstractmethod
    async def claim_due_events(self, limit: int) -> list[TelemetryEvent]:
        raise NotImplementedError

    @abstractmethod
    async def claim_due_reports(self, limit: int) -> list[TelemetryReport]:
        raise NotImplementedError

    @abstractmethod
    async def mark_events_sent(self, ids: Sequence[int]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_events_retry(
        self, ids: Sequence[int], error: str, next_attempt_at: datetime
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_events_failed(self, ids: Sequence[int], error: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_report_sent(self, report_id: int, event_ids: Sequence[int]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_report_retry(
        self,
        report_id: int,
        event_ids: Sequence[int],
        error: str,
        next_attempt_at: datetime,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def mark_report_failed(
        self, report_id: int, event_ids: Sequence[int], error: str
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def counts(self) -> OutboxCounts:
        raise NotImplementedError

    @abstractmethod
    async def reset_stale_sending(self, older_than_seconds: int) -> None:
        raise NotImplementedError


class GeoResolver(ABC):
    """Resolves the installation's public IP and geolocation."""

    @abstractmethod
    async def resolve(self) -> Any | None:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError


class Clock(Protocol):
    def now_utc(self) -> datetime: ...

    def today_utc(self) -> date: ...


@dataclass(frozen=True, slots=True)
class SystemClock:
    def now_utc(self) -> datetime:
        from datetime import timezone

        return datetime.now(timezone.utc).replace(tzinfo=None)

    def today_utc(self) -> date:
        return self.now_utc().date()
