"""Retention paths stay on the caller's table and sweep only that owner's mail."""

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
from maily.exceptions import MailAPIError
from maily.providers.base import MailboxInfo
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
    conn = sqlite3.connect(str(tmp_path / "test.db"), timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def _sha256(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def _insert_key(
    conn: sqlite3.Connection,
    *,
    secret: str,
    actions: list[str],
    providers: list[str],
    expires_at: str | None = None,
) -> int:
    scope = json.dumps({"providers": providers, "parent_ids": [], "actions": actions})
    conn.execute(
        "INSERT INTO api_keys (name, prefix, secret_enc, secret_sha256, scope_json, expires_at)"
        " VALUES ('key-a', 'mk_aaaa', 'enc', ?, ?, ?)",
        (_sha256(secret), scope, expires_at),
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


def test_key_sweep_does_not_delete_root_mailbox_when_key_ttl_is_short(
    tmp_path: Path,
) -> None:
    """Given an old root mailbox and a key TTL, when the key sweeps, the root box stays."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([StubProvider()])
        now = utcnow_naive()
        old = (now - timedelta(days=10)).isoformat()
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret=secret,
            actions=["retention:write"],
            providers=["stub"],
        )
        _insert_mailbox(conn, address="root@x", created_at=old, owner_key_id=None)
        conn.execute(
            "INSERT INTO key_retention (key_id, provider, mailbox_ttl_hours) VALUES (?, 'stub', 1)",
            (key_id,),
        )
        conn.commit()
        conn.close()

        response = client.post("/v1/admin/retention/run", headers={"X-API-Key": secret})

        assert response.status_code == 200
        assert response.json()["mailboxes_deleted"] == 0
        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT address FROM mailboxes")}
        conn.close()
        assert left == {"root@x"}


def test_root_sweep_does_not_apply_key_ttl_to_root_mailbox(tmp_path: Path) -> None:
    """Given only a key TTL, when root sweeps, a root mailbox older than that TTL stays."""
    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([StubProvider()])
        now = utcnow_naive()
        old = (now - timedelta(days=10)).isoformat()
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret="mk_unused",
            actions=["retention:write"],
            providers=["stub"],
        )
        _insert_mailbox(conn, address="root@x", created_at=old, owner_key_id=None)
        conn.execute(
            "INSERT INTO key_retention (key_id, provider, mailbox_ttl_hours) VALUES (?, 'stub', 1)",
            (key_id,),
        )
        conn.commit()
        conn.close()

        response = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})

        assert response.status_code == 200
        assert response.json()["mailboxes_deleted"] == 0
        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT address FROM mailboxes")}
        conn.close()
        assert left == {"root@x"}


def test_key_put_does_not_write_global_retention_row(tmp_path: Path) -> None:
    """Given retention:write, when a key PUTs, only key_retention changes."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret=secret,
            actions=["retention:write", "retention:read"],
            providers=["stub"],
        )
        conn.commit()
        conn.close()

        response = client.put(
            "/v1/admin/retention/stub",
            headers={"X-API-Key": secret},
            json={"mailbox_ttl_hours": 3, "message_ttl_hours": 5},
        )

        assert response.status_code == 200
        assert response.json()["provider"] == "stub"
        assert response.json()["mailbox_ttl_hours"] == 3
        conn = _db(tmp_path)
        global_rows = conn.execute("SELECT provider FROM retention").fetchall()
        key_rows = conn.execute(
            "SELECT key_id, mailbox_ttl_hours, message_ttl_hours FROM key_retention"
        ).fetchall()
        conn.close()
        assert global_rows == []
        assert key_rows == [(key_id, 3, 5)]


def test_domain_cache_is_forbidden_for_issued_key(tmp_path: Path) -> None:
    """Given an issued key, when it reads domain-cache, the response is 403 with no error header."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        conn = _db(tmp_path)
        _insert_key(
            conn,
            secret=secret,
            actions=["retention:read", "retention:write"],
            providers=[],
        )
        conn.commit()
        conn.close()

        response = client.get("/v1/admin/domain-cache", headers={"X-API-Key": secret})

        assert response.status_code == 403
        assert response.json()["detail"] == "forbidden"
        assert response.headers.get("x-mailtm-error") is None


def test_key_get_returns_only_key_retention_when_global_row_exists(
    tmp_path: Path,
) -> None:
    """Given both tables have a stub row, when the key GETs, only its hours come back."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret=secret,
            actions=["retention:read"],
            providers=["stub"],
        )
        conn.execute(
            "INSERT INTO retention (provider, mailbox_ttl_hours, message_ttl_hours)"
            " VALUES ('stub', 99, 88)"
        )
        conn.execute(
            "INSERT INTO key_retention (key_id, provider, mailbox_ttl_hours, message_ttl_hours)"
            " VALUES (?, 'stub', 3, 5)",
            (key_id,),
        )
        conn.commit()
        conn.close()

        response = client.get("/v1/admin/retention", headers={"X-API-Key": secret})

        assert response.status_code == 200
        assert response.json() == [
            {"provider": "stub", "mailbox_ttl_hours": 3, "message_ttl_hours": 5}
        ]


def test_key_put_outside_allow_list_is_forbidden(tmp_path: Path) -> None:
    """Given providers is [stub], when the key writes other, the response is 403."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        conn = _db(tmp_path)
        _insert_key(
            conn,
            secret=secret,
            actions=["retention:write"],
            providers=["stub"],
        )
        conn.commit()
        conn.close()

        response = client.put(
            "/v1/admin/retention/other",
            headers={"X-API-Key": secret},
            json={"mailbox_ttl_hours": 2},
        )

        assert response.status_code == 403
        assert response.json()["detail"] == "forbidden"
        assert response.headers.get("x-mailtm-error") is None


def test_key_put_any_provider_when_providers_empty(tmp_path: Path) -> None:
    """Given an empty providers list, when the key writes other, key_retention stores it."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret=secret,
            actions=["retention:write"],
            providers=[],
        )
        conn.commit()
        conn.close()

        response = client.put(
            "/v1/admin/retention/other",
            headers={"X-API-Key": secret},
            json={"mailbox_ttl_hours": 4},
        )

        assert response.status_code == 200
        conn = _db(tmp_path)
        row = conn.execute(
            "SELECT key_id, provider, mailbox_ttl_hours FROM key_retention"
        ).fetchone()
        conn.close()
        assert row == (key_id, "other", 4)


def test_key_without_retention_read_is_forbidden(tmp_path: Path) -> None:
    """Given no retention:read, when the key GETs retention, the response is 403."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        conn = _db(tmp_path)
        _insert_key(
            conn,
            secret=secret,
            actions=["retention:write"],
            providers=[],
        )
        conn.commit()
        conn.close()

        response = client.get("/v1/admin/retention", headers={"X-API-Key": secret})

        assert response.status_code == 403
        assert response.json()["detail"] == "forbidden"
        assert response.headers.get("x-mailtm-error") is None


def test_key_run_sweeps_only_its_mailboxes(tmp_path: Path) -> None:
    """Given both owners have expired mail, when the key runs, only its mailbox is deleted."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([StubProvider()])
        now = utcnow_naive()
        old = (now - timedelta(days=10)).isoformat()
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret=secret,
            actions=["retention:write"],
            providers=["stub"],
        )
        _insert_mailbox(conn, address="root@x", created_at=old, owner_key_id=None)
        _insert_mailbox(conn, address="key@x", created_at=old, owner_key_id=key_id)
        conn.execute("INSERT INTO retention (provider, mailbox_ttl_hours) VALUES ('stub', 1)")
        conn.execute(
            "INSERT INTO key_retention (key_id, provider, mailbox_ttl_hours) VALUES (?, 'stub', 1)",
            (key_id,),
        )
        conn.commit()
        conn.close()

        response = client.post("/v1/admin/retention/run", headers={"X-API-Key": secret})

        assert response.status_code == 200
        assert response.json()["mailboxes_deleted"] == 1
        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT address FROM mailboxes")}
        conn.close()
        assert left == {"root@x"}


def test_expired_key_ttl_still_applies_on_root_sweep(tmp_path: Path) -> None:
    """Given an expired key's TTL, when root sweeps, that key's mailbox is deleted and root's is not."""
    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([StubProvider()])
        now = utcnow_naive()
        old = (now - timedelta(days=10)).isoformat()
        expired = (now - timedelta(hours=1)).isoformat()
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret="mk_expired",
            actions=["retention:write"],
            providers=["stub"],
            expires_at=expired,
        )
        _insert_mailbox(conn, address="root@x", created_at=old, owner_key_id=None)
        _insert_mailbox(conn, address="owned@x", created_at=old, owner_key_id=key_id)
        conn.execute(
            "INSERT INTO key_retention (key_id, provider, mailbox_ttl_hours) VALUES (?, 'stub', 1)",
            (key_id,),
        )
        conn.commit()
        conn.close()

        denied = client.post("/v1/admin/retention/run", headers={"X-API-Key": "mk_expired"})
        response = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})

        assert denied.status_code == 401
        assert response.status_code == 200
        assert response.json()["mailboxes_deleted"] == 1
        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT address FROM mailboxes")}
        conn.close()
        assert left == {"root@x"}


def test_full_sweep_applies_root_ttl_when_key_has_no_retention_row(
    tmp_path: Path,
) -> None:
    """Given no key_retention, when root sweeps, both the key mailbox and the root mailbox go."""
    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([StubProvider()])
        now = utcnow_naive()
        old = (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret="mk_inherit",
            actions=["retention:write"],
            providers=["stub"],
        )
        _insert_mailbox(conn, address="root@x", created_at=old, owner_key_id=None)
        _insert_mailbox(conn, address="key@x", created_at=old, owner_key_id=key_id)
        conn.execute("INSERT INTO retention (provider, mailbox_ttl_hours) VALUES ('stub', 1)")
        conn.commit()
        conn.close()

        response = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})

        assert response.status_code == 200
        assert response.json()["mailboxes_deleted"] == 2
        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT address FROM mailboxes")}
        conn.close()
        assert left == set()


def test_key_sweep_inherits_root_ttl_without_deleting_root_mailbox(
    tmp_path: Path,
) -> None:
    """Given no key_retention, when the key sweeps, only its mailbox older than the root TTL goes."""
    secret = "mk_inherit"
    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([StubProvider()])
        now = utcnow_naive()
        old = (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret=secret,
            actions=["retention:write"],
            providers=["stub"],
        )
        _insert_mailbox(conn, address="root@x", created_at=old, owner_key_id=None)
        _insert_mailbox(conn, address="key@x", created_at=old, owner_key_id=key_id)
        conn.execute("INSERT INTO retention (provider, mailbox_ttl_hours) VALUES ('stub', 1)")
        conn.commit()
        conn.close()

        response = client.post("/v1/admin/retention/run", headers={"X-API-Key": secret})

        assert response.status_code == 200
        assert response.json()["mailboxes_deleted"] == 1
        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT address FROM mailboxes")}
        conn.close()
        assert left == {"root@x"}


def test_key_longer_ttl_keeps_key_mail_while_root_short_ttl_deletes_root(
    tmp_path: Path,
) -> None:
    """Given a key TTL longer than root, when root sweeps, only the root mailbox is deleted."""
    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([StubProvider()])
        now = utcnow_naive()
        old = (now - timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S")
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret="mk_longer",
            actions=["retention:write"],
            providers=["stub"],
        )
        _insert_mailbox(conn, address="root@x", created_at=old, owner_key_id=None)
        _insert_mailbox(conn, address="key@x", created_at=old, owner_key_id=key_id)
        conn.execute("INSERT INTO retention (provider, mailbox_ttl_hours) VALUES ('stub', 1)")
        conn.execute(
            "INSERT INTO key_retention (key_id, provider, mailbox_ttl_hours)"
            " VALUES (?, 'stub', 48)",
            (key_id,),
        )
        conn.commit()
        conn.close()

        response = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})

        assert response.status_code == 200
        assert response.json()["mailboxes_deleted"] == 1
        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT address FROM mailboxes")}
        conn.close()
        assert left == {"key@x"}


def test_root_sweep_message_ttl_follows_root_when_key_has_no_row(
    tmp_path: Path,
) -> None:
    """Given a global message TTL and no key row, when root sweeps, both owners' messages go."""
    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([StubProvider()])
        now = utcnow_naive()
        fresh = now.isoformat()
        old = (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        conn = _db(tmp_path)
        key_id = _insert_key(
            conn,
            secret="mk_unused",
            actions=["retention:write"],
            providers=["stub"],
        )
        root_id = _insert_mailbox(conn, address="root@x", created_at=fresh, owner_key_id=None)
        key_box = _insert_mailbox(conn, address="key@x", created_at=fresh, owner_key_id=key_id)
        _insert_message(conn, mailbox_id=root_id, message_api_id="root-msg", received_at=old)
        _insert_message(conn, mailbox_id=key_box, message_api_id="key-msg", received_at=old)
        conn.execute("INSERT INTO retention (provider, message_ttl_hours) VALUES ('stub', 1)")
        conn.commit()
        conn.close()

        response = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})

        assert response.status_code == 200
        assert response.json()["messages_deleted"] == 2
        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT message_api_id FROM messages")}
        conn.close()
        assert left == set()


def test_retention_purges_mailbox_when_provider_reports_not_exist(
    tmp_path: Path,
) -> None:
    """When upstream delete fails with 'email not exist', retention drops the local mailbox."""

    class NotFoundProvider(StubProvider):
        async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
            raise MailAPIError("tempmail: email not exist", status_code=400)

    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([NotFoundProvider()])
        now = utcnow_naive()
        old = (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        conn = _db(tmp_path)
        _insert_mailbox(conn, address="expired@x", created_at=old, owner_key_id=None)
        conn.execute("INSERT INTO retention (provider, mailbox_ttl_hours) VALUES ('stub', 1)")
        conn.commit()
        conn.close()

        response = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})
        assert response.status_code == 200
        assert response.json()["mailboxes_deleted"] == 1

        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT address FROM mailboxes")}
        conn.close()
        assert left == set()


def test_retention_marks_mailbox_deleted_when_provider_fails_and_subsequent_reap_purges_it(
    tmp_path: Path,
) -> None:
    """When upstream delete fails with an exception, retention marks mailbox deleted locally, and next sweep reaps it."""

    class ErrorProvider(StubProvider):
        async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
            raise MailAPIError("provider 500 error", status_code=500)

    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([ErrorProvider()])
        now = utcnow_naive()
        old = (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        conn = _db(tmp_path)
        _insert_mailbox(conn, address="upstream-fail@x", created_at=old, owner_key_id=None)
        conn.execute("INSERT INTO retention (provider, mailbox_ttl_hours) VALUES ('stub', 1)")
        conn.commit()
        conn.close()

        # First sweep: provider fails, account is marked deleted locally
        res1 = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})
        assert res1.status_code == 200
        assert res1.json()["mailboxes_deleted"] == 1

        conn = _db(tmp_path)
        row = conn.execute(
            "SELECT address, is_deleted, is_active FROM mailboxes WHERE address = 'upstream-fail@x'"
        ).fetchone()
        conn.close()
        assert row == ("upstream-fail@x", 1, 0)

        # Second sweep: reap cleans up soft-deleted mailboxes
        res2 = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})
        assert res2.status_code == 200

        conn = _db(tmp_path)
        left = {row[0] for row in conn.execute("SELECT address FROM mailboxes")}
        conn.close()
        assert left == set()


def test_retention_marks_mailbox_deleted_when_provider_returns_false(
    tmp_path: Path,
) -> None:
    """When upstream delete returns False, retention marks mailbox deleted locally."""

    class FalseProvider(StubProvider):
        async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
            return False

    with _app(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([FalseProvider()])
        now = utcnow_naive()
        old = (now - timedelta(days=10)).strftime("%Y-%m-%d %H:%M:%S")
        conn = _db(tmp_path)
        _insert_mailbox(conn, address="return-false@x", created_at=old, owner_key_id=None)
        conn.execute("INSERT INTO retention (provider, mailbox_ttl_hours) VALUES ('stub', 1)")
        conn.commit()
        conn.close()

        res = client.post("/v1/admin/retention/run", headers={"X-API-Key": ROOT})
        assert res.status_code == 200
        assert res.json()["mailboxes_deleted"] == 1

        conn = _db(tmp_path)
        row = conn.execute(
            "SELECT address, is_deleted, is_active FROM mailboxes WHERE address = 'return-false@x'"
        ).fetchone()
        conn.close()
        assert row == ("return-false@x", 1, 0)
