"""Async PostHog batch ingestion client.

Only the public ``/batch/`` endpoint is used. The project token is a public
ingest token (``phc_...``), never a personal API key.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from typing import Any

import httpx

from .. import __version__
from .models import TelemetryEvent
from .ports import SinkResult, TelemetrySink
from .privacy import truncate_error, utc_timestamp

_MAX_BODY_BYTES = 20 * 1024 * 1024
_LONG_BACKOFF_SECONDS = 6 * 60 * 60


def normalize_host(host: str) -> str:
    """Accept both a bare host and one that already ends in /batch."""
    cleaned = (host or "").strip().rstrip("/")
    if not cleaned:
        return ""
    if cleaned.endswith("/batch"):
        return cleaned + "/"
    return cleaned + "/batch/"


class PostHogSink(TelemetrySink):
    def __init__(
        self,
        *,
        api_key: str,
        host: str,
        proxy: str | None = None,
        timeout: float = 10.0,
        max_batch_events: int = 50,
        max_event_bytes: int = 900_000,
        person_profiles: bool = True,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._api_key = api_key
        self._endpoint = normalize_host(host)
        self._max_batch_events = max(1, max_batch_events)
        self._max_event_bytes = max_event_bytes
        self._person_profiles = person_profiles
        self._owns_client = client is None
        if client is None:
            client = httpx.AsyncClient(
                proxy=proxy or None,
                timeout=httpx.Timeout(timeout, connect=min(10.0, timeout)),
                follow_redirects=False,
            )
        self._client = client

    async def send(self, events: Sequence[TelemetryEvent]) -> SinkResult:
        if not events:
            return SinkResult(success=True)
        if not self._endpoint or not self._api_key:
            return SinkResult(success=False, error="telemetry endpoint not configured")

        for event in events:
            size = len(json.dumps(event.properties, default=str).encode("utf-8"))
            if size > self._max_event_bytes:
                return SinkResult(
                    success=False,
                    error=f"event {event.event_name} exceeds {self._max_event_bytes} bytes",
                )

        sent_count = 0
        for chunk in self._chunks(events):
            payload = self._payload(chunk)
            try:
                body_size = len(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
            except (TypeError, ValueError) as exc:
                return SinkResult(success=False, error=truncate_error(exc), sent_count=sent_count)
            if body_size > _MAX_BODY_BYTES:
                return SinkResult(
                    success=False,
                    too_large=True,
                    error="batch body too large",
                    sent_count=sent_count,
                )

            try:
                response = await self._client.post(self._endpoint, json=payload)
            except httpx.TimeoutException as exc:
                return SinkResult(
                    success=False, retryable=True, error=truncate_error(exc), sent_count=sent_count
                )
            except httpx.TransportError as exc:
                return SinkResult(
                    success=False, retryable=True, error=truncate_error(exc), sent_count=sent_count
                )
            except Exception as exc:  # noqa: BLE001 - never break the sender loop
                return SinkResult(
                    success=False, retryable=True, error=truncate_error(exc), sent_count=sent_count
                )

            code = response.status_code
            if code < 300:
                sent_count += len(chunk)
                continue
            if code == 413:
                return SinkResult(
                    success=False, too_large=True, status_code=code, sent_count=sent_count
                )
            if code == 429:
                return SinkResult(
                    success=False,
                    retryable=True,
                    status_code=code,
                    retry_after=_retry_after(response),
                    error=truncate_error(response.text),
                    sent_count=sent_count,
                )
            if code in (401, 403):
                return SinkResult(
                    success=False,
                    retryable=True,
                    status_code=code,
                    retry_after=_LONG_BACKOFF_SECONDS,
                    error=truncate_error(response.text),
                    sent_count=sent_count,
                )
            if code == 408 or code >= 500:
                return SinkResult(
                    success=False,
                    retryable=True,
                    status_code=code,
                    error=truncate_error(response.text),
                    sent_count=sent_count,
                )
            return SinkResult(
                success=False,
                retryable=False,
                status_code=code,
                error=truncate_error(response.text),
                sent_count=sent_count,
            )

        return (
            SinkResult(success=True, sent_count=sent_count)
            if sent_count == len(events)
            else SinkResult(success=False, sent_count=sent_count)
        )

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    def _chunks(self, events: Sequence[TelemetryEvent]) -> list[list[TelemetryEvent]]:
        return [
            list(events[index : index + self._max_batch_events])
            for index in range(0, len(events), self._max_batch_events)
        ]

    def _payload(self, events: Sequence[TelemetryEvent]) -> dict[str, Any]:
        return {
            "api_key": self._api_key,
            "batch": [self._event_payload(event) for event in events],
        }

    def _event_payload(self, event: TelemetryEvent) -> dict[str, Any]:
        properties = dict(event.properties)
        properties.setdefault("$lib", "maily-telemetry")
        properties.setdefault("$lib_version", __version__)
        if self._person_profiles:
            properties.setdefault("$process_person_profile", True)
        return {
            "event": event.event_name,
            "distinct_id": event.distinct_id,
            "uuid": event.event_uuid,
            "timestamp": utc_timestamp(event.occurred_at),
            "properties": properties,
        }


def _retry_after(response: httpx.Response) -> float | None:
    raw = response.headers.get("Retry-After")
    if not raw:
        return None
    try:
        return max(0.0, float(raw))
    except ValueError:
        return None
