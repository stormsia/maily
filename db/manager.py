"""
DatabaseManager: peewee + SQLite with production-grade PRAGMA settings.

Optimization rationale
----------------------
journal_mode = WAL
    Write-Ahead Logging: readers never block writers and writers never block
    readers.  Critical for concurrent async workloads.

synchronous = NORMAL
    Sync at WAL checkpoints only (not after every commit).  Safe against
    OS crashes (data is in the WAL) while being ~3× faster than FULL.

cache_size = -64000
    64 MB in-memory page cache (negative value = kilobytes).
    Keeps hot pages in RAM instead of re-reading from disk.

temp_store = MEMORY
    Temporary tables and sort buffers are kept in RAM.

mmap_size = 268435456
    Allow up to 256 MB of memory-mapped I/O.  The OS virtual-memory
    subsystem handles read-ahead; no copy between kernel ↔ user space.

busy_timeout = 5000
    Wait up to 5 seconds for a write lock before raising OperationalError.
    Eliminates most "database is locked" errors under light contention.

wal_autocheckpoint = 200
    Checkpoint (merge WAL → main DB) every 200 pages automatically.
    Prevents the WAL from growing unbounded.

foreign_keys = 1
    Enforce referential integrity at the DB level.
"""
from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

import peewee

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Production PRAGMA map
# ---------------------------------------------------------------------------
_PRAGMAS: dict[str, Any] = {
    "journal_mode": "WAL",
    "synchronous": "NORMAL",
    "cache_size": -64_000,      # 64 MB (negative = KB)
    "temp_store": "MEMORY",
    "mmap_size": 268_435_456,   # 256 MB
    "busy_timeout": 5_000,      # 5 s (milliseconds)
    "wal_autocheckpoint": 200,
    "foreign_keys": 1,
}

# ---------------------------------------------------------------------------
# DatabaseProxy — allows models to be defined before the DB is initialised
# ---------------------------------------------------------------------------
#: Shared proxy used by all ORM models.  Bound to a real database in
#: :meth:`DatabaseManager.initialize`.
db_proxy: peewee.DatabaseProxy = peewee.DatabaseProxy()


class DatabaseManager:
    """
    Manages a single SQLite database with optimised PRAGMA settings.

    Usage::

        from mailtmapi.db.manager import db_manager

        db_manager.initialize("data/mailtm.db")
        db_manager.create_tables([AccountRecord, MessageRecord, DomainRecord])

    The manager is a thin wrapper around ``peewee.SqliteDatabase``.
    All models reference the module-level ``db_proxy`` which is bound to
    the real database in :meth:`initialize`.

    Thread-safety:
        ``initialize()`` is protected by a ``threading.Lock`` and is
        idempotent — safe to call from multiple threads/startup hooks.
    """

    def __init__(self) -> None:
        self._db: peewee.SqliteDatabase | None = None
        self._lock = threading.Lock()
        self._initialized = False

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def db(self) -> peewee.SqliteDatabase:
        """Return the underlying database or raise if not yet initialised."""
        if self._db is None:
            raise RuntimeError(
                "DatabaseManager not initialised. Call initialize() first."
            )
        return self._db

    def initialize(
        self,
        path: str | Path = "mailtm.db",
    ) -> peewee.SqliteDatabase:
        """
        Initialise (or re-use) the database at *path*.

        Creates parent directories automatically. Subsequent calls are
        no-ops and return the existing database instance.

        Args:
            path: Filesystem path for the SQLite file.
                  Use ``:memory:`` for ephemeral in-process databases
                  (useful in tests).

        Returns:
            The initialised ``peewee.SqliteDatabase`` instance.
        """
        with self._lock:
            if self._initialized:
                return self._db  # type: ignore[return-value]

            path = Path(path)
            if path.name != ":memory:":
                path.parent.mkdir(parents=True, exist_ok=True)

            self._db = peewee.SqliteDatabase(
                str(path),
                pragmas=_PRAGMAS,
                timeout=10,   # connection-level timeout in seconds
            )

            # Bind the proxy so all models become live
            db_proxy.initialize(self._db)

            self._initialized = True
            logger.info("Database initialised at %s (WAL mode, 64 MB cache)", path)
            return self._db

    def create_tables(
        self,
        models: list[type[peewee.Model]],
        *,
        safe: bool = True,
    ) -> None:
        """
        Create tables for *models*.

        Args:
            models: List of peewee Model subclasses.
            safe:   Use ``CREATE TABLE IF NOT EXISTS`` (default True).
        """
        self.db.create_tables(models, safe=safe)
        logger.debug("Tables ensured: %s", [m.__name__ for m in models])

    def optimize(self) -> None:
        """
        Run ``PRAGMA optimize`` + ``ANALYZE``.

        Updates SQLite's internal query-planner statistics so that complex
        queries pick the right index.  Cheap to run on every startup.
        Does **not** rebuild the file (use :meth:`vacuum` for that).
        """
        self.db.execute_sql("PRAGMA optimize;")
        self.db.execute_sql("ANALYZE;")
        logger.info("Database PRAGMA optimize + ANALYZE complete")

    def vacuum(self) -> None:
        """
        Rebuild the database to reclaim fragmented space.

        Warning: This operation acquires an exclusive lock and rewrites the
        entire file.  Schedule during low-traffic windows.
        """
        logger.info("Starting VACUUM…")
        self.db.execute_sql("VACUUM;")
        logger.info("VACUUM complete")

    def checkpoint(self, mode: str = "PASSIVE") -> dict[str, int]:
        """
        Manually trigger a WAL checkpoint.

        Args:
            mode: One of ``PASSIVE``, ``FULL``, ``RESTART``, or ``TRUNCATE``.

        Returns:
            Dict with keys ``busy``, ``log``, ``checkpointed``.
        """
        cursor = self.db.execute_sql(f"PRAGMA wal_checkpoint({mode});")
        busy, log, checkpointed = cursor.fetchone()
        result = {"busy": busy, "log": log, "checkpointed": checkpointed}
        logger.debug("WAL checkpoint (%s): %s", mode, result)
        return result

    def page_count(self) -> int:
        """Return the total number of pages in the database (proxy for size)."""
        cursor = self.db.execute_sql("PRAGMA page_count;")
        return cursor.fetchone()[0]

    def close(self) -> None:
        """Close the underlying database connection."""
        if self._db and not self._db.is_closed():
            self._db.close()
            logger.debug("Database connection closed")


# ---------------------------------------------------------------------------
# Module-level singleton — import and use directly
# ---------------------------------------------------------------------------
#: Application-wide DatabaseManager instance.
db_manager: DatabaseManager = DatabaseManager()
