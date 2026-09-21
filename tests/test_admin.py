from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.app.services.retention import utcnow_naive
from mailtmapi.crypto import encrypt
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


class StubProvider:
    slug = "stub"
    kind = "domain"

    def __init__(self) -> None:
        self.delete_mailbox_calls: list[str] = []
        self.delete_message_calls: list[str] = []

    async def close(self) -> None: ...

    async def list_targets(self) -> list[Target]:
        return []

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        return MailboxInfo(provider=self.slug, address="stub@x", token="tok")

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        self.delete_mailbox_calls.append(mailbox.address)
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        return []

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        return MessageDetail(id=message_id)

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        self.delete_message_calls.append(message_id)
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        return MessageSource(id=message_id, data="")


def _app(tmp_path) -> TestClient:
    db = tmp_path / "test.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            secret_key=SECRET,
            _env_file=None,
        )
    )
    return TestClient(app)


def _db(tmp_path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(tmp_path / "test.db"))
    return conn


def test_retention_crud(tmp_path):
    with _app(tmp_path) as client:
        r = client.put(
            "/v1/admin/retention/stub",
            json={"mailbox_ttl_hours": 24, "message_ttl_hours": 12},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["provider"] == "stub"
        assert body["mailbox_ttl_hours"] == 24
        assert body["message_ttl_hours"] == 12

        r = client.put("/v1/admin/retention/stub", json={"mailbox_ttl_hours": 0})
        assert r.status_code == 400

        r = client.put("/v1/admin/retention/stub", json={})
        assert r.status_code == 400

        r = client.get("/v1/admin/retention")
        assert r.status_code == 200
        assert r.json() == [
            {"provider": "stub", "mailbox_ttl_hours": 24, "message_ttl_hours": 12}
        ]

        r = client.delete("/v1/admin/retention/stub")
        assert r.status_code == 204

        r = client.delete("/v1/admin/retention/stub")
        assert r.status_code == 404

        r = client.get("/v1/admin/retention")
        assert r.json() == []


def test_retention_sweep(tmp_path: Path):
    with _app(tmp_path) as client:
        stub = StubProvider()
        client.app.state.registry = ProviderRegistry([stub])

        now = utcnow_naive()
        old = now - timedelta(days=10)
        conn = _db(tmp_path)
        tok = encrypt(SECRET, "tok")
        conn.execute(
            "INSERT INTO mailboxes (provider, address, mailbox_token_enc, created_at, updated_at)"
            " VALUES ('stub', 'old@x', ?, ?, ?)",
            (tok, old.isoformat(), old.isoformat()),
        )
        old_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO mailboxes (provider, address, mailbox_token_enc, created_at, updated_at)"
            " VALUES ('stub', 'fresh@x', ?, ?, ?)",
            (tok, now.isoformat(), now.isoformat()),
        )
        fresh_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at)"
            " VALUES (?, 'stub', 'old-msg', ?, ?)",
            (old_id, old.isoformat(), now.isoformat()),
        )
        conn.execute(
            "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at)"
            " VALUES (?, 'stub', 'fresh-msg', ?, ?)",
            (fresh_id, old.isoformat(), now.isoformat()),
        )
        conn.execute(
            "INSERT INTO retention (provider, mailbox_ttl_hours, message_ttl_hours)"
            " VALUES ('stub', 24, 24)"
        )
        conn.commit()
        conn.close()

        r = client.post("/v1/admin/retention/run")
        assert r.status_code == 200
        assert r.json() == {"mailboxes_deleted": 1, "messages_deleted": 1}
        assert stub.delete_mailbox_calls == ["old@x"]
        assert stub.delete_message_calls == ["fresh-msg"]

        conn = _db(tmp_path)
        mbs = {r[0] for r in conn.execute("SELECT address FROM mailboxes")}
        msgs = {r[0] for r in conn.execute("SELECT message_api_id FROM messages")}
        conn.close()
        assert mbs == {"fresh@x"}
        assert msgs == set()


def test_admin_stats(tmp_path: Path):
    with _app(tmp_path) as client:
        now = utcnow_naive()
        conn = _db(tmp_path)
        conn.execute(
            "INSERT INTO mailboxes (provider, address, mailbox_token_enc)"
            " VALUES ('stub', 'stats@x', ?)",
            (encrypt(SECRET, "tok"),),
        )
        mb_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at)"
            " VALUES (?, 'stub', 'm1', ?, ?)",
            (mb_id, now.isoformat(), now.isoformat()),
        )
        conn.commit()
        conn.close()

        stats = client.get("/v1/admin/stats").json()
        assert stats["mailboxes"] == {"total": 1, "active": 1, "deleted": 0}
        assert stats["messages"] == {"total": 1, "deleted": 0}
        assert stats["by_provider"]["stub"]["mailboxes_total"] == 1
        assert stats["by_provider"]["stub"]["mailboxes_active"] == 1
        assert stats["by_provider"]["stub"]["messages_total"] == 1
        assert stats["gmail_accounts"] == {"total": 0, "active": 0}
        assert len(stats["messages_last_7_days"]) >= 1


def test_gmail_creds_crud(tmp_path):
    with _app(tmp_path) as client:
        # not configured
        r = client.get("/v1/admin/gmail/creds")
        assert r.status_code == 200
        body = r.json()
        assert body == {
            "configured": False,
            "source": "none",
            "client_id": None,
            "redirect_uri": "http://127.0.0.1:8477/v1/gmail/oauth/callback",
        }

        # oauth/start fails friendly
        r = client.post("/v1/gmail/oauth/start")
        assert r.status_code == 400
        assert "not configured" in r.json()["detail"]

        # save via dashboard
        r = client.put(
            "/v1/admin/gmail/creds",
            json={"client_id": "cid-123.apps.googleusercontent.com", "client_secret": "topsecret"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["configured"] is True
        assert body["source"] == "db"
        assert body["client_id"] == "cid-123.apps.googleusercontent.com"

        # secret stored encrypted
        conn = _db(tmp_path)
        enc = conn.execute(
            "SELECT value FROM app_settings WHERE key = 'gmail.client_secret'"
        ).fetchone()[0]
        conn.close()
        assert enc != "topsecret"

        # oauth/start now works and carries the stored client id
        r = client.post("/v1/gmail/oauth/start")
        assert r.status_code == 200
        url = r.json()["auth_url"]
        assert "client_id=cid-123.apps.googleusercontent.com" in url
        assert "redirect_uri=" in url

        # clear
        r = client.delete("/v1/admin/gmail/creds")
        assert r.status_code == 204
        r = client.get("/v1/admin/gmail/creds")
        assert r.json()["configured"] is False
        r = client.post("/v1/gmail/oauth/start")
        assert r.status_code == 400


def test_gmail_creds_env_wins(tmp_path):
    db = tmp_path / "test.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            secret_key=SECRET,
            gmail_client_id="env-cid",
            gmail_client_secret="env-csec",
            _env_file=None,
        )
    )
    with TestClient(app) as client:
        r = client.get("/v1/admin/gmail/creds")
        assert r.json()["source"] == "env"
        assert r.json()["client_id"] == "env-cid"

        # env-managed creds cannot be overwritten or cleared via the dashboard
        r = client.put(
            "/v1/admin/gmail/creds",
            json={"client_id": "other", "client_secret": "other"},
        )
        assert r.status_code == 409
        r = client.delete("/v1/admin/gmail/creds")
        assert r.status_code == 409

        r = client.post("/v1/gmail/oauth/start")
        assert r.status_code == 200
        assert "client_id=env-cid" in r.json()["auth_url"]
