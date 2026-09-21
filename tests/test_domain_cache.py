from __future__ import annotations

import json
import sqlite3

from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.providers.base import (
    MailboxInfo,
    MailboxSpec,
    MessageDetail,
    MessageSource,
    MessageSummary,
    Target,
)
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.settings import Settings

SECRET = "test-secret"


def _targets(slug: str, *labels: str) -> list[Target]:
    return [Target(id=label, kind="domain", provider=slug, label=label) for label in labels]


class StubProvider:
    kind = "domain"

    def __init__(self, slug: str, targets: list[Target], fail: bool = False) -> None:
        self.slug = slug
        self._targets = targets
        self.fail = fail
        self.list_targets_calls = 0

    async def close(self) -> None: ...

    async def list_targets(self) -> list[Target]:
        self.list_targets_calls += 1
        if self.fail:
            raise RuntimeError("boom")
        return list(self._targets)

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        return MailboxInfo(provider=self.slug, address=f"user@{spec.domain or 'x.com'}", token="tok")

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        return []

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        return MessageDetail(id=message_id)

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        return MessageSource(id=message_id, data="")


def _app(tmp_path) -> TestClient:
    db = tmp_path / "test.db"
    app = create_app(Settings(database_url=f"sqlite+aiosqlite:///{db}", secret_key=SECRET))
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
        good = StubProvider("good", _targets("good", "a.com"))
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
        good = StubProvider("good", _targets("good", "a.com", "b.com"))
        bad = StubProvider("bad", _targets("bad", "x.com"), fail=True)
        client.app.state.registry = ProviderRegistry([good, bad])

        r = client.post("/v1/admin/domain-cache/run")
        assert r.status_code == 200
        assert r.json() == {"refreshed": ["good"], "failed": ["bad"]}

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
        good = StubProvider("good", _targets("good", "a.com"))
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


def test_mailbox_create_domain_resolution(tmp_path):
    with _app(tmp_path) as client:
        good = StubProvider("good", _targets("good", "a.com"))
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
        good._targets = _targets("good", "a.com", "c.com")
        r = client.post("/v1/mailboxes", json={"domain": "c.com"})
        assert r.status_code == 200
        assert r.json()["provider"] == "good"
        assert r.json()["address"] == "user@c.com"
        assert good.list_targets_calls == 2


def test_cache_disabled_serves_live(tmp_path):
    with _app(tmp_path) as client:
        good = StubProvider("good", _targets("good", "a.com"))
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
