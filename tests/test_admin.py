from __future__ import annotations

import sqlite3
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from maily.app.main import create_app
from maily.app.services.retention import utcnow_naive
from maily.crypto import encrypt
from maily.providers.registry import ProviderRegistry
from maily.settings import Settings
from tests.helpers import StubProvider

SECRET = "test-secret"


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
        assert r.json() == [{"provider": "stub", "mailbox_ttl_hours": 24, "message_ttl_hours": 12}]

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

        # TTL deletes stay visible in the ledger after their rows are gone
        totals = client.get("/v1/admin/stats").json()["history"]["totals"]
        assert totals["mailbox_deleted"] == 1
        assert totals["message_deleted"] == 1


def test_retention_marks_mailbox_deleted_when_provider_delete_fails(tmp_path: Path):
    from maily.exceptions import MailAPIError

    class Boom(StubProvider):
        async def delete_mailbox(self, mailbox) -> bool:
            raise MailAPIError("upstream exploded")

    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([Boom()])
        now = utcnow_naive()
        old = now - timedelta(days=10)
        conn = _db(tmp_path)
        tok = encrypt(SECRET, "tok")
        conn.execute(
            "INSERT INTO mailboxes (provider, address, mailbox_token_enc, created_at, updated_at)"
            " VALUES ('stub', 'stuck@x', ?, ?, ?)",
            (tok, old.isoformat(), old.isoformat()),
        )
        box_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at)"
            " VALUES (?, 'stub', 'child', ?, ?)",
            (box_id, old.isoformat(), now.isoformat()),
        )
        conn.execute("INSERT INTO retention (provider, mailbox_ttl_hours) VALUES ('stub', 24)")
        conn.commit()
        conn.close()

        r = client.post("/v1/admin/retention/run")
        assert r.status_code == 200
        assert r.json()["mailboxes_deleted"] == 1

        conn = _db(tmp_path)
        row = conn.execute(
            "SELECT address, is_deleted, is_active FROM mailboxes WHERE id = ?",
            (box_id,),
        ).fetchone()
        msg = conn.execute(
            "SELECT message_api_id FROM messages WHERE mailbox_id = ?", (box_id,)
        ).fetchone()
        conn.close()
        assert row == ("stuck@x", 1, 0)
        assert msg == ("child",)


def test_retention_keeps_message_when_provider_delete_fails(tmp_path: Path):
    from maily.exceptions import MailAPIError

    class Boom(StubProvider):
        async def delete_message(self, mailbox, message_id: str) -> bool:
            raise MailAPIError("upstream exploded")

    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([Boom()])
        now = utcnow_naive()
        old = now - timedelta(days=10)
        conn = _db(tmp_path)
        tok = encrypt(SECRET, "tok")
        conn.execute(
            "INSERT INTO mailboxes (provider, address, mailbox_token_enc, created_at, updated_at)"
            " VALUES ('stub', 'live@x', ?, ?, ?)",
            (tok, now.isoformat(), now.isoformat()),
        )
        box_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at)"
            " VALUES (?, 'stub', 'stuck-msg', ?, ?)",
            (box_id, old.isoformat(), now.isoformat()),
        )
        conn.execute("INSERT INTO retention (provider, message_ttl_hours) VALUES ('stub', 24)")
        conn.commit()
        conn.close()

        r = client.post("/v1/admin/retention/run")
        assert r.status_code == 200
        assert r.json()["messages_deleted"] == 0

        conn = _db(tmp_path)
        msg = conn.execute(
            "SELECT message_api_id FROM messages WHERE mailbox_id = ?", (box_id,)
        ).fetchone()
        conn.close()
        assert msg == ("stuck-msg",)


def test_retention_deletes_mailbox_that_has_messages(tmp_path: Path):
    with _app(tmp_path) as client:
        stub = StubProvider()
        client.app.state.registry = ProviderRegistry([stub])
        now = utcnow_naive()
        old = now - timedelta(days=10)
        conn = _db(tmp_path)
        tok = encrypt(SECRET, "tok")
        conn.execute(
            "INSERT INTO mailboxes (provider, address, mailbox_token_enc, created_at, updated_at)"
            " VALUES ('stub', 'parent@x', ?, ?, ?)",
            (tok, old.isoformat(), old.isoformat()),
        )
        box_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.execute(
            "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at)"
            " VALUES (?, 'stub', 'kid', ?, ?)",
            (box_id, old.isoformat(), now.isoformat()),
        )
        conn.execute("INSERT INTO retention (provider, mailbox_ttl_hours) VALUES ('stub', 24)")
        conn.commit()
        conn.close()

        r = client.post("/v1/admin/retention/run")
        assert r.status_code == 200
        assert r.json()["mailboxes_deleted"] == 1
        assert stub.delete_mailbox_calls == ["parent@x"]

        conn = _db(tmp_path)
        left = conn.execute("SELECT id FROM mailboxes").fetchall()
        msgs = conn.execute("SELECT id FROM messages").fetchall()
        conn.close()
        assert left == []
        assert msgs == []


def test_stats_history_records_api_events(tmp_path: Path):
    with _app(tmp_path) as client:
        stub = StubProvider(address="hist@x")
        client.app.state.registry = ProviderRegistry([stub])

        mb = client.post("/v1/mailboxes", json={"provider": "stub"}).json()
        client.get(f"/v1/mailboxes/{mb['id']}/messages")
        client.delete(f"/v1/mailboxes/{mb['id']}/messages/m1")
        client.delete(f"/v1/mailboxes/{mb['id']}")

        stats = client.get("/v1/admin/stats").json()
        assert stats["history"]["totals"] == {
            "mailbox_created": 1,
            "mailbox_deleted": 1,
            "message_received": 1,
            "message_deleted": 1,
        }
        # by_provider bucket rolls the events up per provider
        assert stats["history"]["by_provider"]["stub"]["mailbox_deleted"] == 1
        # the 7-day trend switches to the ledger once it has receive-events
        assert stats["messages_last_7_days"][-1]["count"] == 1


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
        # message inserted after boot is not backfilled — shown via live fallback
        assert stats["messages_last_7_days"][-1]["count"] == 1
        # ledger exists even when nothing was recorded through the API yet
        assert stats["history"]["window_days"] == 10
        assert len(stats["history"]["days"]) == 10
        assert stats["history"]["totals"] == {
            "mailbox_created": 0,
            "mailbox_deleted": 0,
            "message_received": 0,
            "message_deleted": 0,
        }


def test_stats_backfill_is_idempotent_across_restarts(tmp_path: Path):
    # first boot creates the schema (alembic) so the raw INSERTs below work
    with _app(tmp_path):
        pass

    now = utcnow_naive()
    conn = _db(tmp_path)
    conn.execute(
        "INSERT INTO mailboxes (provider, address, mailbox_token_enc) VALUES ('stub', 'bf@x', ?)",
        (encrypt(SECRET, "tok"),),
    )
    mb_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    # two messages received on different days — both must appear in the chart
    for i, minutes in enumerate((0, 60 * 24)):
        conn.execute(
            "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at)"
            " VALUES (?, 'stub', ?, ?, ?)",
            (
                mb_id,
                f"m{i}",
                (now - timedelta(minutes=minutes)).isoformat(),
                now.isoformat(),
            ),
        )
    conn.commit()
    conn.close()

    with _app(tmp_path) as client:
        days = client.get("/v1/admin/stats").json()["history"]["days"]
        counts = [d["message_received"] for d in days]
        assert counts[-1] == 1 and counts[-2] == 1

    # second boot on the same DB must not double-count (per-day idempotency)
    with _app(tmp_path) as client:
        totals = client.get("/v1/admin/stats").json()["history"]["totals"]
        assert totals["message_received"] == 2


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
            json={
                "client_id": "cid-123.apps.googleusercontent.com",
                "client_secret": "topsecret",
            },
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
