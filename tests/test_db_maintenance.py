from __future__ import annotations

import asyncio
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import text

from mailtmapi.app.main import create_app
from mailtmapi.db.engine import SessionFactory, make_engine
from mailtmapi.db.maintenance import (
    SETTING_KEY_LAST_MAINTENANCE,
    is_maintenance_due,
    maintain_database,
    reset_maintenance_cache,
)
from mailtmapi.settings import Settings

ROOT_KEY = "root-test-key"


def _make_app(
    tmp_path: Path,
    *,
    maintenance_enabled: bool = True,
    interval_minutes: int = 60,
    busy_timeout_ms: int = 60000,
) -> tuple[TestClient, Path]:
    reset_maintenance_cache()
    db_file = tmp_path / "test_maint.db"
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_file}",
        api_key=ROOT_KEY,
        secret_key="test-secret",
        db_maintenance_enabled=maintenance_enabled,
        db_maintenance_interval_minutes=interval_minutes,
        sqlite_busy_timeout_ms=busy_timeout_ms,
        _env_file=None,
    )
    app = create_app(settings)
    return TestClient(app), db_file


def test_maintain_database_direct_sqlite(tmp_path: Path) -> None:
    db_file = tmp_path / "direct.db"
    engine = make_engine(f"sqlite+aiosqlite:///{db_file}")

    async def _run():
        async with engine.connect() as conn:
            await conn.execute(text("CREATE TABLE test_tab (id INTEGER PRIMARY KEY, val TEXT)"))
            await conn.commit()
        result = await maintain_database(engine, busy_timeout_ms=10000)
        assert result["status"] == "completed"
        assert result["dialect"] == "sqlite"
        assert "duration_seconds" in result
        await engine.dispose()

    asyncio.run(_run())


def test_retention_sweep_runs_maintenance_and_records_setting(tmp_path: Path) -> None:
    client, db_file = _make_app(tmp_path, interval_minutes=60)
    with client:
        # Run sweep
        res = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT_KEY})
        assert res.status_code == 200
        assert res.json() == {"mailboxes_deleted": 0, "messages_deleted": 0}

        # Verify app_settings has the maintenance timestamp
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (SETTING_KEY_LAST_MAINTENANCE,))
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        last_dt = datetime.fromisoformat(row[0])
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        assert abs((now - last_dt).total_seconds()) < 60


def test_retention_sweep_throttling_skips_subsequent_runs(tmp_path: Path) -> None:
    client, db_file = _make_app(tmp_path, interval_minutes=60)
    with client:
        # First sweep runs maintenance
        res1 = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT_KEY})
        assert res1.status_code == 200

        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (SETTING_KEY_LAST_MAINTENANCE,))
        first_recorded = cursor.fetchone()[0]
        conn.close()

        # Second sweep immediately afterwards: should skip maintenance because 60 mins haven't elapsed
        with patch("mailtmapi.db.maintenance.maintain_database") as mock_maint:
            res2 = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT_KEY})
            assert res2.status_code == 200
            # maintain_database was not called because it was throttled
            mock_maint.assert_not_called()

        # Verify setting did not change
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM app_settings WHERE key = ?", (SETTING_KEY_LAST_MAINTENANCE,))
        second_recorded = cursor.fetchone()[0]
        conn.close()
        assert first_recorded == second_recorded


def test_force_maintenance_bypasses_throttle(tmp_path: Path) -> None:
    client, _ = _make_app(tmp_path, interval_minutes=60)
    with client:
        # First run
        client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT_KEY})

        # Second run with force_maintenance=true
        with patch("mailtmapi.db.maintenance.maintain_database", wraps=maintain_database) as mock_maint:
            res = client.post(
                "/v1/admin/retention/run?force_maintenance=true",
                headers={"X-API-Key": ROOT_KEY},
            )
            assert res.status_code == 200
            mock_maint.assert_called_once()


def test_maintenance_disabled_via_settings(tmp_path: Path) -> None:
    client, _ = _make_app(tmp_path, maintenance_enabled=False)
    with client, patch("mailtmapi.db.maintenance.maintain_database") as mock_maint:
        res = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT_KEY})
        assert res.status_code == 200
        mock_maint.assert_not_called()


def test_scoped_sweep_does_not_trigger_maintenance(tmp_path: Path) -> None:
    client, db_file = _make_app(tmp_path, interval_minutes=60)
    with client:
        # Create an issued key with retention:write action
        key_res = client.post(
            "/v1/admin/keys",
            headers={"X-API-Key": ROOT_KEY},
            json={
                "name": "sub-key",
                "scope": {
                    "providers": ["mailtm"],
                    "parent_ids": [],
                    "actions": ["retention:write", "retention:read"],
                },
            },
        )
        assert key_res.status_code == 200
        issued_key = key_res.json()["secret"]

        # Run sweep with issued key
        with patch("mailtmapi.db.maintenance.maybe_run_maintenance") as mock_maybe_maint:
            res = client.post("/v1/admin/retention/run", headers={"X-API-Key": issued_key})
            assert res.status_code == 200
            mock_maybe_maint.assert_not_called()


def test_maintenance_lock_error_handled_gracefully(tmp_path: Path) -> None:
    """When maintenance hits a lock error, it logs and skips without crashing retention."""
    client, _ = _make_app(tmp_path)
    with client:

        async def _fake_failing_maint(*args, **kwargs):
            return {"status": "skipped", "reason": "locked", "error": "database is locked"}

        with patch("mailtmapi.db.maintenance.maintain_database", side_effect=_fake_failing_maint):
            res = client.post("/v1/admin/retention/run?force_maintenance=true", headers={"X-API-Key": ROOT_KEY})
            # Sweep completes successfully without 500 error!
            assert res.status_code == 200
            assert res.json() == {"mailboxes_deleted": 0, "messages_deleted": 0}


def test_is_maintenance_due_calculation(tmp_path: Path) -> None:
    db_file = tmp_path / "due.db"
    engine = make_engine(f"sqlite+aiosqlite:///{db_file}")
    factory = SessionFactory(engine)
    settings = Settings(
        db_maintenance_enabled=True,
        db_maintenance_interval_minutes=30,
        _env_file=None,
    )

    async def _test():
        now = datetime(2026, 1, 1, 12, 0, 0)
        # 1. Never run before -> initializes baseline timestamp and returns False
        reset_maintenance_cache()
        assert await is_maintenance_due(factory, engine, settings, now=now) is False

        # 2. Just ran at 12:00:00 -> not due at 12:15:00 (15 min elapsed, 30 min required)
        from mailtmapi.db.maintenance import record_maintenance_at
        await record_maintenance_at(factory, engine, now)

        not_due_time = now + timedelta(minutes=15)
        assert await is_maintenance_due(factory, engine, settings, now=not_due_time) is False

        # 3. Due at 12:30:00 (30 min elapsed)
        due_time = now + timedelta(minutes=30)
        assert await is_maintenance_due(factory, engine, settings, now=due_time) is True

        # 4. Due at 12:45:00 (45 min elapsed)
        overdue_time = now + timedelta(minutes=45)
        assert await is_maintenance_due(factory, engine, settings, now=overdue_time) is True

        await engine.dispose()

    asyncio.run(_test())
