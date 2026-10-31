from __future__ import annotations

import asyncio
import logging
import time
from contextlib import suppress
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)

from ..settings import Settings
from .models import AppSetting

logger = logging.getLogger("mailtmapi.db.maintenance")

SETTING_KEY_LAST_MAINTENANCE = "db_maintenance.last_run_at"

_last_maintenance_cache: dict[str, datetime] = {}
_maintenance_lock = asyncio.Lock()


def _db_identifier(engine: AsyncEngine) -> str:
    return str(engine.url)


def reset_maintenance_cache() -> None:
    """Clear in-memory throttle cache (primarily for tests)."""
    _last_maintenance_cache.clear()


async def get_last_maintenance_at(
    factory: async_sessionmaker[AsyncSession],
    engine: AsyncEngine,
) -> datetime | None:
    ident = _db_identifier(engine)
    if ident in _last_maintenance_cache:
        return _last_maintenance_cache[ident]

    try:
        async with factory() as session:
            row = await session.get(AppSetting, SETTING_KEY_LAST_MAINTENANCE)
            if row is not None and row.value:
                dt = datetime.fromisoformat(row.value)
                _last_maintenance_cache[ident] = dt
                return dt
    except Exception as exc:
        logger.debug("could not read %s from app_settings: %s", SETTING_KEY_LAST_MAINTENANCE, exc)

    return None


async def record_maintenance_at(
    factory: async_sessionmaker[AsyncSession],
    engine: AsyncEngine,
    at: datetime,
) -> None:
    ident = _db_identifier(engine)
    _last_maintenance_cache[ident] = at

    try:
        async with factory() as session:
            row = await session.get(AppSetting, SETTING_KEY_LAST_MAINTENANCE)
            if row is None:
                row = AppSetting(key=SETTING_KEY_LAST_MAINTENANCE, value=at.isoformat())
                session.add(row)
            else:
                row.value = at.isoformat()
            await session.commit()
    except Exception as exc:
        logger.debug("could not persist %s in app_settings: %s", SETTING_KEY_LAST_MAINTENANCE, exc)


async def is_maintenance_due(
    factory: async_sessionmaker[AsyncSession],
    engine: AsyncEngine,
    settings: Settings,
    *,
    now: datetime | None = None,
) -> bool:
    if not settings.db_maintenance_enabled:
        return False
    if settings.db_maintenance_interval_minutes <= 0:
        return False

    now = now or datetime.now(timezone.utc).replace(tzinfo=None)
    last_run = await get_last_maintenance_at(factory, engine)
    if last_run is None:
        # Initialize baseline timestamp on first encounter so maintenance runs
        # after the configured interval rather than causing heavy locks at boot t=0.
        await record_maintenance_at(factory, engine, now)
        return False

    elapsed_seconds = (now - last_run).total_seconds()
    required_seconds = settings.db_maintenance_interval_minutes * 60
    return elapsed_seconds >= required_seconds


async def maintain_database(
    engine: AsyncEngine,
    *,
    busy_timeout_ms: int = 60000,
    max_retries: int = 3,
    retry_delay: float = 1.0,
) -> dict[str, Any]:
    """Execute complete database maintenance (VACUUM, REINDEX, ANALYZE, WAL checkpoints, etc.).

    Guaranteed not to raise an unhandled exception: errors are caught, logged,
    and returned in the result dictionary so neither background workers nor
    incoming requests crash.
    """
    dialect = engine.dialect.name
    start_time = time.monotonic()
    logger.info("db maintenance: starting thorough database maintenance for %s...", dialect)

    for attempt in range(max_retries):
        try:
            async with engine.connect() as conn:
                await conn.execution_options(isolation_level="AUTOCOMMIT")

                if dialect == "sqlite":
                    # 1. Set busy_timeout for this maintenance connection so it waits for open transactions
                    await conn.execute(text(f"PRAGMA busy_timeout = {busy_timeout_ms}"))

                    # 2. Flush write-ahead log into main database and truncate WAL file
                    try:
                        await conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
                    except Exception as chk_exc:
                        logger.debug(
                            "db maintenance: initial checkpoint contention (%s), using PASSIVE",
                            chk_exc,
                        )
                        await conn.execute(text("PRAGMA wal_checkpoint(PASSIVE)"))

                    # 3. VACUUM: compact, defragment, reclaim space freed by retention deletes
                    await conn.execute(text("VACUUM"))

                    # 4. REINDEX: rebuild all table and index B-trees for optimal lookup speed
                    await conn.execute(text("REINDEX"))

                    # 5. ANALYZE: gather statistical distributions for the SQLite query planner
                    await conn.execute(text("ANALYZE"))

                    # 6. PRAGMA optimize: SQLite recommended optimization pass
                    await conn.execute(text("PRAGMA optimize"))

                    # 7. Post-reindex/analyze WAL checkpoint
                    try:
                        await conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
                    except Exception as chk_exc:
                        logger.debug("db maintenance: post-vacuum checkpoint: %s", chk_exc)

                    # 8. Integrity check
                    check_cursor = await conn.execute(text("PRAGMA quick_check"))
                    check_rows = [r[0] for r in check_cursor.fetchall()]
                    if check_rows != ["ok"]:
                        logger.warning(
                            "db maintenance: PRAGMA quick_check warnings: %s", check_rows
                        )

                elif dialect == "postgresql":
                    await conn.execute(text("VACUUM (ANALYZE)"))

                else:
                    with suppress(Exception):
                        await conn.execute(text("ANALYZE"))

            duration = time.monotonic() - start_time
            logger.info("db maintenance: completed successfully in %.3fs (%s)", duration, dialect)
            return {
                "status": "completed",
                "dialect": dialect,
                "duration_seconds": round(duration, 3),
            }

        except OperationalError as exc:
            err = str(exc).lower()
            is_lock = any(k in err for k in ("locked", "busy", "timeout"))
            if is_lock and attempt < max_retries - 1:
                logger.debug(
                    "db maintenance: transient lock on attempt %d/%d (%s), retrying in %.1fs...",
                    attempt + 1,
                    max_retries,
                    exc,
                    retry_delay * (attempt + 1),
                )
                await asyncio.sleep(retry_delay * (attempt + 1))
                continue
            logger.warning("db maintenance: postponed or skipped due to lock contention: %s", exc)
            return {
                "status": "skipped",
                "reason": "locked",
                "error": str(exc),
            }
        except Exception as exc:
            logger.warning("db maintenance: maintenance failed: %s", exc)
            return {
                "status": "failed",
                "error": str(exc),
            }

    return {"status": "skipped", "reason": "lock_retries_exhausted"}


async def maybe_run_maintenance(
    factory: async_sessionmaker[AsyncSession],
    settings: Settings,
    *,
    force: bool = False,
) -> dict[str, Any]:
    """Check if maintenance is due and run it if necessary.

    Returns the maintenance result or a skipped descriptor. Never raises.
    """
    engine = getattr(factory, "bind", None) or factory.kw.get("bind")
    if engine is None:
        async with factory() as session:
            engine = session.bind

    if not isinstance(engine, AsyncEngine):
        return {"status": "skipped", "reason": "no_engine"}

    if _maintenance_lock.locked():
        logger.debug("db maintenance: already running in another task, skipping")
        return {"status": "skipped", "reason": "already_running"}

    async with _maintenance_lock:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not force:
            due = await is_maintenance_due(factory, engine, settings, now=now)
            if not due:
                last_run = await get_last_maintenance_at(factory, engine)
                elapsed_min = (now - last_run).total_seconds() / 60.0 if last_run else 0.0
                logger.debug(
                    "db maintenance: skipped (last run was %.1f min ago, interval %d min)",
                    elapsed_min,
                    settings.db_maintenance_interval_minutes,
                )
                return {"status": "skipped", "reason": "throttled"}

        result = await maintain_database(
            engine,
            busy_timeout_ms=settings.sqlite_busy_timeout_ms,
        )
        if result.get("status") == "completed":
            await record_maintenance_at(factory, engine, now)

        return result
