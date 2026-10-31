from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_DEFAULT_SQLITE_BUSY_TIMEOUT_MS = 60000

_SQLITE_PRAGMAS = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA foreign_keys=ON",
    f"PRAGMA busy_timeout={_DEFAULT_SQLITE_BUSY_TIMEOUT_MS}",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA wal_autocheckpoint=200",
)


def make_engine(url: str, *, busy_timeout_ms: int = _DEFAULT_SQLITE_BUSY_TIMEOUT_MS) -> AsyncEngine:
    engine = create_async_engine(url, echo=False)
    if url.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def _on_connect(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
            cur = dbapi_conn.cursor()
            pragmas = (
                "PRAGMA journal_mode=WAL",
                "PRAGMA synchronous=NORMAL",
                "PRAGMA foreign_keys=ON",
                f"PRAGMA busy_timeout={busy_timeout_ms}",
                "PRAGMA temp_store=MEMORY",
                "PRAGMA wal_autocheckpoint=200",
            )
            for pragma in pragmas:
                cur.execute(pragma)
            cur.close()

    return engine


def SessionFactory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope(
    factory: async_sessionmaker[AsyncSession],
) -> AsyncIterator[AsyncSession]:
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def retry_on_lock(
    operation: Callable[[], Awaitable[None]],
    *,
    attempts: int = 5,
    delay: float = 0.3,
) -> None:
    """Run a short write transaction, retrying on transient SQLite locks.

    ``SQLITE_BUSY`` (database is locked) is expected under concurrent Asyncio
    writers (API handlers + background workers). WAL + busy_timeout handles
    *waiting* for the writer lock, but a read->write snapshot upgrade after a
    foreign commit fails instantly — hence the retry loop.
    """
    for attempt in range(attempts):
        try:
            await operation()
            return
        except OperationalError as exc:
            err = str(exc).lower()
            is_lock_error = any(phrase in err for phrase in ("locked", "busy", "timeout"))
            if attempt == attempts - 1 or not is_lock_error:
                raise
            await asyncio.sleep(delay * (attempt + 1))
