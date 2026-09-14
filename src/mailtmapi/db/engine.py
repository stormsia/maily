from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_SQLITE_PRAGMAS = (
    "PRAGMA journal_mode=WAL",
    "PRAGMA synchronous=NORMAL",
    "PRAGMA foreign_keys=ON",
    "PRAGMA busy_timeout=5000",
    "PRAGMA temp_store=MEMORY",
    "PRAGMA wal_autocheckpoint=200",
)


def make_engine(url: str) -> AsyncEngine:
    engine = create_async_engine(url, echo=False)
    if url.startswith("sqlite"):

        @event.listens_for(engine.sync_engine, "connect")
        def _on_connect(dbapi_conn, _connection_record) -> None:  # noqa: ANN001
            cur = dbapi_conn.cursor()
            for pragma in _SQLITE_PRAGMAS:
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
