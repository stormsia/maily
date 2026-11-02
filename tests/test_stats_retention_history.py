"""Tests verifying that mailboxes and messages deleted by retention sweeps
are transparently preserved in the 10-day history with provider and domain counters.
"""

from __future__ import annotations

import hashlib
import json
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
ROOT = "root-secret"


def _app(tmp_path: Path, *, api_key: str = ROOT) -> TestClient:
    db = tmp_path / "test.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            secret_key=SECRET,
            api_key=api_key,
            _env_file=None,
        )
    )
    return TestClient(app)


def _db(tmp_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(tmp_path / "test.db"))


def _sha256(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def _insert_key(
    conn: sqlite3.Connection,
    *,
    secret: str,
    actions: list[str],
    providers: list[str],
) -> int:
    scope = json.dumps({"providers": providers, "parent_ids": [], "actions": actions})
    conn.execute(
        "INSERT INTO api_keys (name, prefix, secret_enc, secret_sha256, scope_json)"
        " VALUES ('key-a', 'mk_aaaa', 'enc', ?, ?)",
        (_sha256(secret), scope),
    )
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def _insert_mailbox(
    conn: sqlite3.Connection,
    *,
    address: str,
    created_at: str,
    owner_key_id: int | None,
    provider: str = "stub",
) -> int:
    tok = encrypt(SECRET, "tok")
    conn.execute(
        "INSERT INTO mailboxes"
        " (provider, address, mailbox_token_enc, owner_key_id, created_at, updated_at)"
        " VALUES (?, ?, ?, ?, ?, ?)",
        (provider, address, tok, owner_key_id, created_at, created_at),
    )
    return int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])


def _insert_message(
    conn: sqlite3.Connection,
    *,
    mailbox_id: int,
    message_api_id: str,
    received_at: str,
    provider: str = "stub",
) -> None:
    conn.execute(
        "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at)"
        " VALUES (?, ?, ?, ?, ?)",
        (mailbox_id, provider, message_api_id, received_at, received_at),
    )


def test_retention_deletes_transparently_recorded_in_10_day_history_by_domain(
    tmp_path: Path,
) -> None:
    """When retention purges expired mailboxes and messages, their deletions
    are transparently recorded in the 10-day history with provider and domain breakdowns.
    """
    with _app(tmp_path) as client:
        stub = StubProvider(slug="stub")
        client.app.state.registry = ProviderRegistry([stub])

        now = utcnow_naive()
        old = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

        conn = _db(tmp_path)
        # Create 2 expired mailboxes under different domains
        mb1 = _insert_mailbox(
            conn, address="alice@domain-one.com", created_at=old, owner_key_id=None
        )
        mb2 = _insert_mailbox(conn, address="bob@domain-two.com", created_at=old, owner_key_id=None)

        # Create 2 expired messages
        _insert_message(conn, mailbox_id=mb1, message_api_id="msg-1", received_at=old)
        _insert_message(conn, mailbox_id=mb2, message_api_id="msg-2", received_at=old)

        # Set retention: mailbox TTL 1h, message TTL 1h
        conn.execute(
            "INSERT INTO retention (provider, mailbox_ttl_hours, message_ttl_hours) VALUES ('stub', 1, 1)"
        )
        conn.commit()
        conn.close()

        # Run retention sweep
        sweep_res = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})
        assert sweep_res.status_code == 200
        # Retention drops expired mailboxes first (or messages if message rules run)
        # Total deleted accounts and emails must be >= 1
        data = sweep_res.json()
        assert data["mailboxes_deleted"] == 2

        # Check that live rows are deleted from mailboxes table
        conn = _db(tmp_path)
        live_mbs = conn.execute("SELECT count(*) FROM mailboxes").fetchone()[0]
        conn.close()
        assert live_mbs == 0

        # Query stats
        stats = client.get("/v1/admin/stats", headers={"X-API-Key": ROOT}).json()
        history = stats["history"]

        # Totals in history
        assert history["totals"]["mailbox_deleted"] == 2
        assert history["window_days"] == 10

        # Breakdown by provider
        assert "stub" in history["by_provider"]
        assert history["by_provider"]["stub"]["mailbox_deleted"] == 2

        # Breakdown by domain
        assert "domain-one.com" in history["by_domain"]
        assert "domain-two.com" in history["by_domain"]
        assert history["by_domain"]["domain-one.com"]["mailbox_deleted"] == 1
        assert history["by_domain"]["domain-two.com"]["mailbox_deleted"] == 1


def test_retention_message_deletes_recorded_by_domain(tmp_path: Path) -> None:
    """When retention purges expired messages only (while mailboxes remain active),
    message_deleted counter is recorded per provider and domain."""
    with _app(tmp_path) as client:
        stub = StubProvider(slug="stub")
        client.app.state.registry = ProviderRegistry([stub])

        now = utcnow_naive()
        fresh = now.strftime("%Y-%m-%d %H:%M:%S")
        old = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

        conn = _db(tmp_path)
        mb = _insert_mailbox(conn, address="user@mycorp.org", created_at=fresh, owner_key_id=None)
        _insert_message(conn, mailbox_id=mb, message_api_id="old-msg-1", received_at=old)
        _insert_message(conn, mailbox_id=mb, message_api_id="old-msg-2", received_at=old)

        # Message retention rule: 1 hour (mailbox rule: None)
        conn.execute("INSERT INTO retention (provider, message_ttl_hours) VALUES ('stub', 1)")
        conn.commit()
        conn.close()

        sweep_res = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})
        assert sweep_res.status_code == 200
        assert sweep_res.json()["messages_deleted"] == 2

        stats = client.get("/v1/admin/stats", headers={"X-API-Key": ROOT}).json()
        history = stats["history"]

        assert history["totals"]["message_deleted"] == 2
        assert history["by_provider"]["stub"]["message_deleted"] == 2
        assert history["by_domain"]["mycorp.org"]["message_deleted"] == 2


def test_scoped_key_retention_history_preserves_deleted_accounts_and_messages(
    tmp_path: Path,
) -> None:
    """An issued API key reading /admin/stats sees its retention-deleted mailboxes and messages
    in its 10-day history with provider and domain counters."""
    secret = "mk_client_secret"
    with _app(tmp_path) as client:
        stub = StubProvider(slug="stub")
        client.app.state.registry = ProviderRegistry([stub])

        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret=secret,
            actions=[
                "mailboxes:read",
                "mailboxes:write",
                "messages:read",
                "messages:write",
                "stats:read",
                "retention:read",
                "retention:write",
            ],
            providers=["stub"],
        )

        now = utcnow_naive()
        old = (now - timedelta(days=2)).strftime("%Y-%m-%d %H:%M:%S")

        # Mailbox owned by key
        key_mb = _insert_mailbox(
            conn, address="service@customer.io", created_at=old, owner_key_id=key_id
        )
        # Mailbox owned by root
        root_mb = _insert_mailbox(
            conn, address="admin@rootcorp.com", created_at=old, owner_key_id=None
        )

        _insert_message(conn, mailbox_id=key_mb, message_api_id="key-msg", received_at=old)
        _insert_message(conn, mailbox_id=root_mb, message_api_id="root-msg", received_at=old)

        conn.execute(
            "INSERT INTO retention (provider, mailbox_ttl_hours, message_ttl_hours) VALUES ('stub', 1, 1)"
        )
        conn.commit()
        conn.close()

        # Run sweep
        sweep_res = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})
        assert sweep_res.status_code == 200
        assert sweep_res.json()["mailboxes_deleted"] == 2

        # Key reads scoped stats
        key_stats = client.get("/v1/admin/stats", headers={"X-API-Key": secret}).json()
        key_hist = key_stats["history"]

        # Key should see ONLY its own mailbox deletion (1) and its domain
        assert key_hist["totals"]["mailbox_deleted"] == 1
        assert "customer.io" in key_hist["by_domain"]
        assert key_hist["by_domain"]["customer.io"]["mailbox_deleted"] == 1
        assert "rootcorp.com" not in key_hist["by_domain"]

        # Root reads stats: sees BOTH mailboxes deleted and both domains
        root_stats = client.get("/v1/admin/stats", headers={"X-API-Key": ROOT}).json()
        root_hist = root_stats["history"]

        assert root_hist["totals"]["mailbox_deleted"] == 2
        assert "customer.io" in root_hist["by_domain"]
        assert "rootcorp.com" in root_hist["by_domain"]
        assert root_hist["by_domain"]["customer.io"]["mailbox_deleted"] == 1
        assert root_hist["by_domain"]["rootcorp.com"]["mailbox_deleted"] == 1


def test_api_mailbox_and_message_lifecycle_updates_counters_by_domain(
    tmp_path: Path,
) -> None:
    """Full API lifecycle: mailbox creation, message receive, message deletion, and mailbox deletion
    accurately increments provider and domain counters in 10-day history."""
    with _app(tmp_path) as client:
        stub = StubProvider(slug="stub", address="test@custom-domain.xyz")
        client.app.state.registry = ProviderRegistry([stub])

        # 1. Create mailbox
        create_res = client.post(
            "/v1/mailboxes", json={"provider": "stub"}, headers={"X-API-Key": ROOT}
        )
        assert create_res.status_code == 200
        mb_id = create_res.json()["id"]

        # Check history: created = 1
        s1 = client.get("/v1/admin/stats", headers={"X-API-Key": ROOT}).json()
        assert s1["history"]["totals"]["mailbox_created"] == 1
        assert s1["history"]["by_domain"]["custom-domain.xyz"]["mailbox_created"] == 1

        # 2. Sync messages (stub returns m1)
        client.get(f"/v1/mailboxes/{mb_id}/messages", headers={"X-API-Key": ROOT})

        s2 = client.get("/v1/admin/stats", headers={"X-API-Key": ROOT}).json()
        assert s2["history"]["totals"]["message_received"] == 1
        assert s2["history"]["by_domain"]["custom-domain.xyz"]["message_received"] == 1

        # 3. Delete message
        del_msg = client.delete(f"/v1/mailboxes/{mb_id}/messages/m1", headers={"X-API-Key": ROOT})
        assert del_msg.status_code == 204

        s3 = client.get("/v1/admin/stats", headers={"X-API-Key": ROOT}).json()
        assert s3["history"]["totals"]["message_deleted"] == 1
        assert s3["history"]["by_domain"]["custom-domain.xyz"]["message_deleted"] == 1

        # 4. Delete mailbox
        del_box = client.delete(f"/v1/mailboxes/{mb_id}", headers={"X-API-Key": ROOT})
        assert del_box.status_code == 204

        s4 = client.get("/v1/admin/stats", headers={"X-API-Key": ROOT}).json()
        assert s4["history"]["totals"] == {
            "mailbox_created": 1,
            "mailbox_deleted": 1,
            "message_received": 1,
            "message_deleted": 1,
        }
        assert s4["history"]["by_provider"]["stub"] == {
            "mailbox_created": 1,
            "mailbox_deleted": 1,
            "message_received": 1,
            "message_deleted": 1,
        }
        assert s4["history"]["by_domain"]["custom-domain.xyz"] == {
            "mailbox_created": 1,
            "mailbox_deleted": 1,
            "message_received": 1,
            "message_deleted": 1,
        }


def test_backfill_multiple_mailboxes_same_domain(tmp_path: Path) -> None:
    """When multiple mailboxes share the same domain and receive messages on the same day,
    startup backfill aggregates them properly without unique constraint errors."""
    with _app(tmp_path):
        pass  # Initialize database schema

    now = utcnow_naive()
    stamp = now.isoformat()
    conn = _db(tmp_path)
    # 3 mailboxes sharing the same domain
    mb1 = _insert_mailbox(
        conn, address="alice@shared-domain.com", created_at=stamp, owner_key_id=None
    )
    mb2 = _insert_mailbox(
        conn, address="bob@shared-domain.com", created_at=stamp, owner_key_id=None
    )
    mb3 = _insert_mailbox(
        conn, address="carol@shared-domain.com", created_at=stamp, owner_key_id=None
    )

    _insert_message(conn, mailbox_id=mb1, message_api_id="m1", received_at=stamp)
    _insert_message(conn, mailbox_id=mb2, message_api_id="m2", received_at=stamp)
    _insert_message(conn, mailbox_id=mb3, message_api_id="m3", received_at=stamp)
    conn.commit()
    conn.close()

    # Restart app to trigger backfill in lifespan
    with _app(tmp_path) as client:
        stats = client.get("/v1/admin/stats", headers={"X-API-Key": ROOT}).json()
        hist = stats["history"]
        assert hist["totals"]["message_received"] == 3
        assert "shared-domain.com" in hist["by_domain"]
        assert hist["by_domain"]["shared-domain.com"]["message_received"] == 3


def test_scoped_history_mathematical_consistency(tmp_path: Path) -> None:
    """Scoped key's totals, daily sums, provider sums, and domain sums must be 100% consistent."""
    secret = "mk_scoped_secret"
    with _app(tmp_path) as client:
        stub = StubProvider(slug="stub")
        client.app.state.registry = ProviderRegistry([stub])

        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret=secret,
            actions=[
                "mailboxes:read",
                "mailboxes:write",
                "messages:read",
                "stats:read",
            ],
            providers=["stub", "mailtm"],
        )
        now = utcnow_naive()
        stamp = now.isoformat()
        # Seed 1 mailbox in provider 'stub'
        _insert_mailbox(
            conn,
            address="user@corp-a.com",
            created_at=stamp,
            owner_key_id=key_id,
            provider="stub",
        )
        # Seed 1 mailbox in provider 'mailtm'
        _insert_mailbox(
            conn,
            address="user@corp-b.com",
            created_at=stamp,
            owner_key_id=key_id,
            provider="mailtm",
        )

        # Record ledger event for corp-a
        conn.execute(
            "INSERT INTO stats_events (day, provider, domain, owner_key_id, event, count)"
            " VALUES (?, 'stub', 'corp-a.com', ?, 'mailbox_created', 1)",
            (now.date().isoformat(), key_id),
        )
        conn.commit()
        conn.close()

        res = client.get("/v1/admin/stats", headers={"X-API-Key": secret})
        assert res.status_code == 200
        hist = res.json()["history"]

        totals = hist["totals"]
        prov_sum = sum(p["mailbox_created"] for p in hist["by_provider"].values())
        dom_sum = sum(d["mailbox_created"] for d in hist["by_domain"].values())
        day_sum = sum(d["mailbox_created"] for d in hist["days"])

        # Both mailboxes (corp-a from ledger, corp-b from live) must roll up consistently
        assert totals["mailbox_created"] == 2
        assert prov_sum == 2
        assert dom_sum == 2
        assert day_sum == 2
