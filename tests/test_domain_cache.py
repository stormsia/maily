from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime

from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.settings import Settings
from tests.helpers import StubProvider, make_targets

SECRET = "test-secret"


def _app(tmp_path) -> TestClient:
    db = tmp_path / "test.db"
    app = create_app(
        Settings(database_url=f"sqlite+aiosqlite:///{db}", secret_key=SECRET, _env_file=None)
    )
    return TestClient(app)


def _db(tmp_path) -> sqlite3.Connection:
    return sqlite3.connect(str(tmp_path / "test.db"))


def test_put_settings_validation(tmp_path):
    with _app(tmp_path) as client:
        r = client.put("/v1/admin/domain-cache", json={"interval_seconds": 30})
        assert r.status_code == 400

        r = client.put("/v1/admin/domain-cache", json={})
        assert r.status_code == 400


def test_get_default_settings(tmp_path):
    with _app(tmp_path) as client:
        good = StubProvider("good", make_targets("good", "a.com"))
        client.app.state.registry = ProviderRegistry([good])

        body = client.get("/v1/admin/domain-cache").json()
        assert body["enabled"] is True
        assert body["interval_seconds"] == 1800
        assert {p["provider"] for p in body["providers"]} >= {"good"}
        by_provider = {p["provider"]: p for p in body["providers"]}
        assert by_provider["good"]["domains_count"] == 0

        # PUT persists settings and they show up on GET
        r = client.put("/v1/admin/domain-cache", json={"enabled": False, "interval_seconds": 120})
        assert r.status_code == 200
        assert r.json()["enabled"] is False
        assert r.json()["interval_seconds"] == 120
        assert client.get("/v1/admin/domain-cache").json()["enabled"] is False


def test_run_populates_cache_and_reports_failures(tmp_path):
    with _app(tmp_path) as client:
        good = StubProvider("good", make_targets("good", "a.com", "b.com"))
        bad = StubProvider("bad", make_targets("bad", "x.com"), fail=True)
        client.app.state.registry = ProviderRegistry([good, bad])

        r = client.post("/v1/admin/domain-cache/run")
        assert r.status_code == 502
        body = r.json()
        assert body["refreshed"] == ["good"]
        assert body["failed"] == ["bad"]
        assert good.list_targets_fresh is True
        assert bad.list_targets_fresh is True
        assert isinstance(body["detail"], str) and body["detail"]

        body = client.get("/v1/admin/domain-cache").json()
        by_provider = {p["provider"]: p for p in body["providers"]}
        assert by_provider["good"]["domains_count"] == 2
        assert by_provider["good"]["error"] is None
        assert by_provider["bad"]["domains_count"] == 0
        assert by_provider["bad"]["error"] == "boom"

        conn = _db(tmp_path)
        row = conn.execute(
            "SELECT domains_json, error FROM domain_cache WHERE provider = 'good'"
        ).fetchone()
        conn.close()
        assert json.loads(row[0]) == ["a.com", "b.com"]
        assert row[1] is None


def test_targets_served_from_cache(tmp_path):
    with _app(tmp_path) as client:
        good = StubProvider("good", make_targets("good", "a.com"))
        client.app.state.registry = ProviderRegistry([good])

        r = client.post("/v1/admin/domain-cache/run")
        assert r.json() == {"refreshed": ["good"], "failed": []}
        assert good.list_targets_calls == 1

        r = client.get("/v1/targets")
        assert r.status_code == 200
        assert r.json() == [
            {"id": "a.com", "kind": "domain", "provider": "good", "label": "a.com"}
        ]
        # served from DB cache, provider not called again
        assert good.list_targets_calls == 1


def test_run_stores_and_bumps_last_refresh(tmp_path):
    # domain_cache_enabled=False: the background worker does nothing, so the
    # controlled POST /run calls below are the only writer on the sqlite file
    # (otherwise the worker's first refresh can race the test's writes).
    db = tmp_path / "test.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            secret_key=SECRET,
            _env_file=None,
            domain_cache_enabled=False,
        )
    )
    with TestClient(app) as client:
        good = StubProvider("good", make_targets("good", "a.com"))
        client.app.state.registry = ProviderRegistry([good])

        client.post("/v1/admin/domain-cache/run")
        first = client.get("/v1/admin/domain-cache").json()
        t1 = {p["provider"]: p["updated_at"] for p in first["providers"]}["good"]
        assert t1 is not None  # the refresh timestamp is persisted

        # Refresh again with identical data: updated_at must still move forward
        # (a naive onupdate-only column would stay stale when nothing changes).
        time.sleep(1.1)
        client.post("/v1/admin/domain-cache/run")
        t2 = {p["provider"]: p["updated_at"] for p in client.get("/v1/admin/domain-cache").json()["providers"]}["good"]

        assert datetime.fromisoformat(t2) > datetime.fromisoformat(t1)


def test_mailbox_create_domain_resolution(tmp_path):
    with _app(tmp_path) as client:
        good = StubProvider("good", make_targets("good", "a.com"))
        client.app.state.registry = ProviderRegistry([good])
        client.post("/v1/admin/domain-cache/run")
        assert good.list_targets_calls == 1

        # cached hit: resolved without hitting the provider again
        r = client.post("/v1/mailboxes", json={"domain": "a.com"})
        assert r.status_code == 200
        assert r.json()["provider"] == "good"
        assert r.json()["address"] == "user@a.com"
        assert good.list_targets_calls == 1

        # cache miss: falls back to live scan of the provider
        good._targets = make_targets("good", "a.com", "c.com")
        r = client.post("/v1/mailboxes", json={"domain": "c.com"})
        assert r.status_code == 200
        assert r.json()["provider"] == "good"
        assert r.json()["address"] == "user@c.com"
        assert good.list_targets_calls == 2


def test_cache_disabled_serves_live(tmp_path):
    with _app(tmp_path) as client:
        good = StubProvider("good", make_targets("good", "a.com"))
        client.app.state.registry = ProviderRegistry([good])

        r = client.put("/v1/admin/domain-cache", json={"enabled": False})
        assert r.status_code == 200

        r = client.post("/v1/admin/domain-cache/run")
        assert r.json() == {"refreshed": ["good"], "failed": []}
        assert good.list_targets_calls == 1

        # cache disabled -> /v1/targets goes live and does not store
        r = client.get("/v1/targets", params={"provider": "good"})
        assert r.status_code == 200
        assert r.json() == [
            {"id": "a.com", "kind": "domain", "provider": "good", "label": "a.com"}
        ]
        assert good.list_targets_calls == 2

        conn = _db(tmp_path)
        row = conn.execute("SELECT error FROM domain_cache WHERE provider = 'good'").fetchone()
        conn.close()
        # run stored the row, but the live /v1/targets call did not touch it
        assert row is not None
