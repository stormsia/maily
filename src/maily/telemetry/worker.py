"""In-process dispatcher and scheduler for the telemetry outbox."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any

from loguru import logger

from .models import TelemetryEvent
from .ports import Clock, TelemetryRepository

_TICK_SECONDS = 30.0
_DISPATCH_BATCH = 50


class TelemetryWorker:
    def __init__(
        self,
        *,
        repository: TelemetryRepository,
        settings: Any,
        clock: Clock,
        on_tick: Callable[[], Awaitable[None]],
    ) -> None:
        self._repository = repository
        self._settings = settings
        self._clock = clock
        self._on_tick = on_tick
        self._queue: asyncio.Queue[TelemetryEvent] = asyncio.Queue(
            maxsize=getattr(settings, "telemetry_queue_maxsize", 512)
        )
        self._wake = asyncio.Event()
        self._stop = asyncio.Event()
        self._tasks: set[asyncio.Task[None]] = set()
        self.dropped = 0

    def enqueue(self, event: TelemetryEvent) -> bool:
        try:
            self._queue.put_nowait(event)
        except asyncio.QueueFull:
            self.dropped += 1
            logger.warning(
                "telemetry: queue full, dropping event %s (dropped=%d)",
                event.event_name,
                self.dropped,
            )
            return False
        return True

    async def start(self) -> None:
        self._tasks.add(asyncio.create_task(self._dispatch_loop()))
        self._tasks.add(asyncio.create_task(self._sender_loop()))

    async def stop(self) -> None:
        # Persist anything still in memory before shutting the loops down.
        pending: list[TelemetryEvent] = []
        while True:
            try:
                pending.append(self._queue.get_nowait())
            except asyncio.QueueEmpty:
                break
        if pending:
            try:
                await self._repository.enqueue_events(pending)
            except Exception:  # noqa: BLE001 - shutdown must not fail
                logger.exception(
                    "telemetry: could not persist %d queued event(s) during shutdown",
                    len(pending),
                )
                self.dropped += len(pending)

        self._stop.set()
        self._wake.set()
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            with suppress(asyncio.CancelledError):
                await task
        self._tasks.clear()

    async def _dispatch_loop(self) -> None:
        while not self._stop.is_set():
            try:
                first = await self._queue.get()
            except asyncio.CancelledError:
                break
            batch = [first]
            while len(batch) < _DISPATCH_BATCH:
                try:
                    batch.append(self._queue.get_nowait())
                except asyncio.QueueEmpty:
                    break
            try:
                inserted = await self._repository.enqueue_events(batch)
                if inserted < len(batch):
                    logger.debug("telemetry: %d duplicate event(s) skipped", len(batch) - inserted)
                self._wake.set()
            except Exception:  # noqa: BLE001 - never kill the dispatcher
                logger.exception("telemetry: failed to persist %d event(s)", len(batch))
                self.dropped += len(batch)
            finally:
                for _ in batch:
                    self._queue.task_done()

    async def _sender_loop(self) -> None:
        while not self._stop.is_set():
            with suppress(asyncio.TimeoutError):
                await asyncio.wait_for(self._wake.wait(), timeout=_TICK_SECONDS)
            self._wake.clear()
            if self._stop.is_set():
                break
            try:
                await asyncio.sleep(self._settings.telemetry_immediate_debounce_seconds)
                await self._on_tick()
            except asyncio.CancelledError:
                break
            except Exception:  # noqa: BLE001 - the worker must never die
                logger.exception("telemetry: tick failed")
