"""HTTP keys router: secret visibility, auth, and delete conflicts.

Given: a TestClient built by create_app with Settings(_env_file=None)
When: root or an issued key calls /v1/admin/keys
Then: secrets appear only on create, rotate, and reveal; issued keys are 403
      on the collection and 200 on /me; a live mailbox blocks delete with 409
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.settings import Settings

ROOT = "root-secret"
FERNET = "x" * 32
SCOPE = {
    "providers": ["mail.tm"],
    "parent_ids": [999_999],
    "actions": ["mailboxes:read"],
}
CREATE_BODY = {
    "name": "ops",
    "expires_at": None,
    "scope": SCOPE,
    "retention": [{"provider": "mail.tm", "mailbox_ttl_hours": 24, "message_ttl_hours": 12}],
}


def _client(tmp_path: Path) -> TestClient:
    db = tmp_path / "keys.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            api_key=ROOT,
            secret_key=FERNET,
            _env_file=None,
        )
    )
    return TestClient(app)


def _root() -> dict[str, str]:
    return {"X-API-Key": ROOT}


def _issued(secret: str) -> dict[str, str]:
    return {"X-API-Key": secret}


def test_create_returns_secret_and_list_omits_it(tmp_path: Path) -> None:
    """Given a root create, the list response has neither the secret field nor its value."""
    with _client(tmp_path) as client:
        created = client.post("/v1/admin/keys", json=CREATE_BODY, headers=_root())
        assert created.status_code == 200
        body = created.json()
        secret = body["secret"]
        assert secret.startswith("mk_")
        assert secret != ROOT
        assert body["scope"]["parent_ids"] == [999_999]
        listed = client.get("/v1/admin/keys", headers=_root())
        assert listed.status_code == 200
        rows = listed.json()
        dumped = str(rows)
        assert "secret" not in dumped
        assert secret not in dumped
        assert rows[0]["id"] == body["id"]
        assert rows[0]["name"] == "ops"


def test_reveal_returns_the_same_secret_twice(tmp_path: Path) -> None:
    """Given a created key, two secret GETs return the create-time plaintext."""
    with _client(tmp_path) as client:
        created = client.post("/v1/admin/keys", json=CREATE_BODY, headers=_root()).json()
        first = client.get(f"/v1/admin/keys/{created['id']}/secret", headers=_root())
        second = client.get(f"/v1/admin/keys/{created['id']}/secret", headers=_root())
        assert first.status_code == 200
        assert second.status_code == 200
        assert first.json() == {"secret": created["secret"]}
        assert second.json() == {"secret": created["secret"]}


def test_rotate_invalidates_old_secret_and_keeps_id(tmp_path: Path) -> None:
    """Given a rotated key, the old secret is 401 and the new secret authenticates."""
    with _client(tmp_path) as client:
        created = client.post("/v1/admin/keys", json=CREATE_BODY, headers=_root()).json()
        rotated = client.post(f"/v1/admin/keys/{created['id']}/rotate", headers=_root())
        assert rotated.status_code == 200
        body = rotated.json()
        assert body["id"] == created["id"]
        assert body["secret"] != created["secret"]
        old = client.get("/v1/admin/keys/me", headers=_issued(created["secret"]))
        new = client.get("/v1/admin/keys/me", headers=_issued(body["secret"]))
        assert old.status_code == 401
        assert new.status_code == 200
        assert "secret" not in new.json()


def test_issued_key_collection_is_403_without_error_header(tmp_path: Path) -> None:
    """Given an issued key, GET /v1/admin/keys is 403 forbidden with no X-MailTM-Error."""
    with _client(tmp_path) as client:
        created = client.post("/v1/admin/keys", json=CREATE_BODY, headers=_root()).json()
        res = client.get("/v1/admin/keys", headers=_issued(created["secret"]))
        assert res.status_code == 403
        assert res.json()["detail"] == "forbidden"
        assert res.headers.get("x-mailtm-error") is None


def test_issued_key_me_returns_row_without_secret(tmp_path: Path) -> None:
    """Given an issued key, GET /me returns name, expiry, parsed scope, and retention."""
    with _client(tmp_path) as client:
        created = client.post("/v1/admin/keys", json=CREATE_BODY, headers=_root()).json()
        res = client.get("/v1/admin/keys/me", headers=_issued(created["secret"]))
        assert res.status_code == 200
        body = res.json()
        assert body["name"] == "ops"
        assert body["expires_at"] is None
        assert body["scope"] == SCOPE
        assert body["key_retention"] == [
            {"provider": "mail.tm", "mailbox_ttl_hours": 24, "message_ttl_hours": 12}
        ]
        dumped = str(body)
        assert "secret" not in dumped
        assert "secret_enc" not in dumped
        assert created["secret"] not in dumped


def test_root_me_is_root_flag(tmp_path: Path) -> None:
    """Given the env root key, GET /me is exactly {is_root: true}."""
    with _client(tmp_path) as client:
        res = client.get("/v1/admin/keys/me", headers=_root())
        assert res.status_code == 200
        assert res.json() == {"is_root": True}


def test_delete_of_key_with_live_mailbox_is_409(tmp_path: Path) -> None:
    """Given a live mailbox owned by the key, DELETE is 409 and the key remains."""
    with _client(tmp_path) as client:
        created = client.post("/v1/admin/keys", json=CREATE_BODY, headers=_root()).json()
    _seed_live_mailbox(tmp_path, created["id"])
    with _client(tmp_path) as client:
        res = client.delete(f"/v1/admin/keys/{created['id']}", headers=_root())
        assert res.status_code == 409
        still = client.get(f"/v1/admin/keys/{created['id']}", headers=_root())
        assert still.status_code == 200
        assert still.json()["id"] == created["id"]
        assert "secret" not in still.json()


def _seed_live_mailbox(tmp_path: Path, key_id: int) -> None:
    """Insert a live mailbox owned by key_id. Mailbox create does not stamp ownership yet."""
    db = tmp_path / "keys.db"
    conn = sqlite3.connect(db)
    try:
        conn.execute(
            """
            INSERT INTO mailboxes (
                provider, address, mailbox_token_enc, is_active, is_deleted, owner_key_id
            ) VALUES ('mail.tm', 'live@example.com', 'enc', 1, 0, ?)
            """,
            (key_id,),
        )
        conn.commit()
    finally:
        conn.close()
