"""Issued keys see only their providers, granted Gmail parents, and own stats."""

from __future__ import annotations

import hashlib
import json
from datetime import timedelta
from pathlib import Path

from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.app.services.retention import utcnow_naive
from mailtmapi.crypto import encrypt
from mailtmapi.providers.gmail.service import GmailProvider
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.settings import Settings
from tests.helpers import StubProvider, make_targets

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


def _sha256(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def _insert_key(
    client: TestClient,
    *,
    secret: str,
    providers: list[str],
    parent_ids: list[int],
    actions: list[str],
) -> int:
    import sqlite3

    scope = json.dumps({"providers": providers, "parent_ids": parent_ids, "actions": actions})
    conn = sqlite3.connect(str(client.app.state.settings.database_url.split("///", 1)[1]))
    conn.execute(
        "INSERT INTO api_keys (name, prefix, secret_enc, secret_sha256, scope_json)"
        " VALUES ('key-a', 'mk_aaaa', 'enc', ?, ?)",
        (_sha256(secret), scope),
    )
    key_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    conn.commit()
    conn.close()
    return key_id


def _use_stubs(client: TestClient) -> GmailProvider:
    gmail = client.app.state.gmail
    client.app.state.registry = ProviderRegistry(
        [
            gmail,
            StubProvider("mail.tm", targets=make_targets("mail.tm", "tm.test")),
            StubProvider("tempmail.plus", targets=make_targets("tempmail.plus", "plus.test")),
        ]
    )
    return gmail


def test_providers_returns_only_allowed_slugs(tmp_path: Path) -> None:
    """Given a key limited to mail.tm, when it lists providers, other slugs are absent."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        _use_stubs(client)
        _insert_key(client, secret=secret, providers=["mail.tm"], parent_ids=[], actions=[])

        response = client.get("/v1/providers", headers={"X-API-Key": secret})

        assert response.status_code == 200
        assert [row["slug"] for row in response.json()] == ["mail.tm"]


def test_providers_empty_allow_list_returns_every_slug(tmp_path: Path) -> None:
    """Given an empty providers list, when a key lists providers, every slug is present."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        _use_stubs(client)
        _insert_key(client, secret=secret, providers=[], parent_ids=[], actions=[])

        issued = client.get("/v1/providers", headers={"X-API-Key": secret})
        root = client.get("/v1/providers", headers={"X-API-Key": ROOT})

        assert issued.status_code == 200
        assert {row["slug"] for row in issued.json()} == {row["slug"] for row in root.json()}
        assert "gmail" in {row["slug"] for row in issued.json()}


def test_targets_drops_disallowed_providers_and_ungranted_parents(tmp_path: Path) -> None:
    """Given a mail.tm-only key, when it lists targets, Gmail and other providers are absent."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        _use_stubs(client)
        key_id = _insert_key(
            client, secret=secret, providers=["mail.tm"], parent_ids=[], actions=[]
        )
        _seed_parents(client, key_id)

        response = client.get("/v1/targets", headers={"X-API-Key": secret})

        assert response.status_code == 200
        assert {row["provider"] for row in response.json()} == {"mail.tm"}


def test_targets_keeps_owned_and_listed_gmail_parents(tmp_path: Path) -> None:
    """Given an owned parent and one listed root parent, both stay and the other root is dropped."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        _use_stubs(client)
        key_id = _insert_key(client, secret=secret, providers=["gmail"], parent_ids=[1], actions=[])
        _seed_parents(client, key_id)

        response = client.get("/v1/targets", headers={"X-API-Key": secret})

        assert response.status_code == 200
        labels = {row["label"] for row in response.json() if row["provider"] == "gmail"}
        assert labels == {"owned@gmail.com", "granted@gmail.com"}


def test_targets_empty_parent_ids_keeps_owned_gmail_parent(tmp_path: Path) -> None:
    """Given no root parents granted, when a key lists Gmail targets, its own parent stays."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        _use_stubs(client)
        key_id = _insert_key(client, secret=secret, providers=["gmail"], parent_ids=[], actions=[])
        _seed_parents(client, key_id)

        response = client.get("/v1/targets", headers={"X-API-Key": secret})

        assert response.status_code == 200
        labels = {row["label"] for row in response.json()}
        assert labels == {"owned@gmail.com"}


def test_stats_without_action_is_forbidden(tmp_path: Path) -> None:
    """Given a key without stats:read, when it reads stats, the response is 403 with no error header."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        _insert_key(client, secret=secret, providers=[], parent_ids=[], actions=["mailboxes:read"])

        response = client.get("/v1/admin/stats", headers={"X-API-Key": secret})

        assert response.status_code == 403
        assert response.json()["detail"] == "forbidden"
        assert response.headers.get("x-mailtm-error") is None


def test_stats_counts_only_the_callers_rows(tmp_path: Path) -> None:
    """Given mixed owners, when a key reads stats, only its mailboxes, messages, and granted parents count."""
    secret = "mk_key-a-secret"
    with _app(tmp_path) as client:
        key_id = _insert_key(
            client,
            secret=secret,
            providers=["stub"],
            parent_ids=[1],
            actions=["stats:read"],
        )
        own_id, other_id = _seed_stats(client, key_id)
        _seed_ledger(client)

        response = client.get("/v1/admin/stats", headers={"X-API-Key": secret})

        assert response.status_code == 200
        body = response.json()
        assert body["mailboxes"] == {"total": 1, "active": 1, "deleted": 0}
        assert body["messages"] == {"total": 1, "deleted": 0}
        assert body["by_provider"]["stub"]["mailboxes_total"] == 1
        assert body["by_provider"]["stub"]["messages_total"] == 1
        assert body["gmail_accounts"] == {"total": 2, "active": 2}
        received = [day for day in body["history"]["days"] if day["message_received"]]
        assert len(received) == 1
        assert received[0]["message_received"] == 1
        assert body["history"]["totals"]["message_received"] == 1
        assert body["history"]["totals"]["mailbox_created"] == 1
        assert body["messages_last_7_days"] == [{"date": received[0]["date"], "count": 1}]
        assert own_id != other_id


def test_root_stats_still_uses_the_global_ledger(tmp_path: Path) -> None:
    """Given a ledger row and no live mail, when root reads stats, the ledger total is returned."""
    with _app(tmp_path) as client:
        _seed_ledger(client)

        response = client.get("/v1/admin/stats", headers={"X-API-Key": ROOT})

        assert response.status_code == 200
        assert response.json()["history"]["totals"]["message_received"] == 9
        assert response.json()["mailboxes"]["total"] == 0


def _seed_parents(client: TestClient, key_id: int) -> None:
    import sqlite3

    conn = sqlite3.connect(str(client.app.state.settings.database_url.split("///", 1)[1]))
    token = encrypt(SECRET, "refresh")
    conn.execute(
        "INSERT INTO gmail_accounts (email, refresh_token_enc, status, owner_key_id)"
        " VALUES ('granted@gmail.com', ?, 'active', NULL)",
        (token,),
    )
    conn.execute(
        "INSERT INTO gmail_accounts (email, refresh_token_enc, status, owner_key_id)"
        " VALUES ('other@gmail.com', ?, 'active', NULL)",
        (token,),
    )
    conn.execute(
        "INSERT INTO gmail_accounts (email, refresh_token_enc, status, owner_key_id)"
        " VALUES ('owned@gmail.com', ?, 'active', ?)",
        (token, key_id),
    )
    conn.commit()
    conn.close()


def _seed_stats(client: TestClient, key_id: int) -> tuple[int, int]:
    import sqlite3

    now = utcnow_naive()
    stamp = now.isoformat()
    conn = sqlite3.connect(str(client.app.state.settings.database_url.split("///", 1)[1]))
    tok = encrypt(SECRET, "tok")
    conn.execute(
        "INSERT INTO mailboxes (provider, address, mailbox_token_enc, owner_key_id, created_at, updated_at)"
        " VALUES ('stub', 'own@x', ?, ?, ?, ?)",
        (tok, key_id, stamp, stamp),
    )
    own_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    conn.execute(
        "INSERT INTO mailboxes (provider, address, mailbox_token_enc, owner_key_id, created_at, updated_at)"
        " VALUES ('stub', 'root@x', ?, NULL, ?, ?)",
        (tok, stamp, stamp),
    )
    other_id = int(conn.execute("SELECT last_insert_rowid()").fetchone()[0])
    conn.execute(
        "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at, is_deleted)"
        " VALUES (?, 'stub', 'own-msg', ?, ?, 0)",
        (own_id, stamp, stamp),
    )
    conn.execute(
        "INSERT INTO messages (mailbox_id, provider, message_api_id, received_at, cached_at, is_deleted)"
        " VALUES (?, 'stub', 'root-msg', ?, ?, 0)",
        (other_id, stamp, stamp),
    )
    token = encrypt(SECRET, "refresh")
    conn.execute(
        "INSERT INTO gmail_accounts (email, refresh_token_enc, status, owner_key_id)"
        " VALUES ('granted@gmail.com', ?, 'active', NULL)",
        (token,),
    )
    conn.execute(
        "INSERT INTO gmail_accounts (email, refresh_token_enc, status, owner_key_id)"
        " VALUES ('other@gmail.com', ?, 'active', NULL)",
        (token,),
    )
    conn.execute(
        "INSERT INTO gmail_accounts (email, refresh_token_enc, status, owner_key_id)"
        " VALUES ('owned@gmail.com', ?, 'active', ?)",
        (token, key_id),
    )
    conn.commit()
    conn.close()
    return own_id, other_id


def _seed_ledger(client: TestClient) -> None:
    import sqlite3

    day = (utcnow_naive() - timedelta(days=1)).date().isoformat()
    conn = sqlite3.connect(str(client.app.state.settings.database_url.split("///", 1)[1]))
    conn.execute(
        "INSERT INTO stats_events (day, provider, event, count) VALUES (?, 'stub', 'message_received', 9)",
        (day,),
    )
    conn.commit()
    conn.close()
