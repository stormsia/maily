"""Cross-cutting API-key scope suite against the real app. # noqa: SIZE_OK

Given: Settings(api_key="root", _env_file=None) and create_app
When: root, an unknown secret, or an issued key hits the scoped routes
Then: each case asserts the status (and, for a recipient miss, that trash was not called)

One module is the suite the plan names. Splitting it would hide cases from
`pytest tests/test_api_keys.py`.
"""

from __future__ import annotations

import base64
import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from maily.app.services.retention import utcnow_naive
from maily.crypto import encrypt
from maily.db.models import ApiKey, KeyRetention, Mailbox
from maily.providers.registry import ProviderRegistry
from tests.api_keys_support import (
    FERNET,
    PLUS_DETAIL,
    ROOT,
    KeySpec,
    RecordingGmail,
    auth,
    client_for,
    forbid,
    issue,
    mailbox_parent,
    seed_parent,
    stored_refresh,
    stub_gmail,
)
from tests.helpers import StubProvider

_ALIAS = "user+tag@gmail.com"
_BARE = "user@gmail.com"
_WRITE: KeySpec = {
    "providers": ["gmail"],
    "actions": ["mailboxes:read", "mailboxes:write", "messages:read", "messages:write"],
}


def _past() -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()


def _message(headers: list[tuple[str, str]]) -> dict[str, object]:
    return {
        "id": "m1",
        "threadId": "t1",
        "labelIds": ["INBOX"],
        "snippet": "hello",
        "sizeEstimate": 12,
        "internalDate": "1700000000000",
        "payload": {
            "mimeType": "text/plain",
            "headers": [{"name": name, "value": value} for name, value in headers],
            "body": {"data": base64.urlsafe_b64encode(b"hello").decode().rstrip("=")},
        },
    }


def test_unknown_key_is_401_with_api_key_header(tmp_path: Path) -> None:
    """Given a set root key, an unknown secret is 401 and x-mailtm-error is api_key."""
    with client_for(tmp_path) as client:
        response = client.get("/v1/providers", headers=auth("not-a-key"))
    assert response.status_code == 401
    assert response.headers.get("x-mailtm-error") == "api_key"


def test_expired_key_is_401(tmp_path: Path) -> None:
    """Given a key whose expires_at is in the past, that secret is 401."""
    with client_for(tmp_path) as client:
        _key_id, secret = issue(client, {"expires_at": _past()})
        response = client.get("/v1/providers", headers=auth(secret))
    assert response.status_code == 401
    assert response.headers.get("x-mailtm-error") == "api_key"


def test_root_lists_keys_200(tmp_path: Path) -> None:
    """Given the env root key, GET /v1/admin/keys is 200."""
    with client_for(tmp_path) as client:
        response = client.get("/v1/admin/keys", headers=auth(ROOT))
    assert response.status_code == 200


def test_issued_key_list_keys_is_403(tmp_path: Path) -> None:
    """Given an issued key, GET /v1/admin/keys is 403 with no x-mailtm-error."""
    with client_for(tmp_path) as client:
        _key_id, secret = issue(client)
        forbid(client.get("/v1/admin/keys", headers=auth(secret)))


def test_issued_key_gmail_creds_is_403(tmp_path: Path) -> None:
    """Given an issued key, GET /v1/admin/gmail/creds is 403 with no x-mailtm-error."""
    with client_for(tmp_path) as client:
        _key_id, secret = issue(client)
        forbid(client.get("/v1/admin/gmail/creds", headers=auth(secret)))


def test_issued_key_domain_cache_is_403(tmp_path: Path) -> None:
    """Given an issued key, GET /v1/admin/domain-cache is 403 with no x-mailtm-error."""
    with client_for(tmp_path) as client:
        _key_id, secret = issue(client)
        forbid(client.get("/v1/admin/domain-cache", headers=auth(secret)))


def test_key_a_cannot_get_or_list_key_b_mailbox(tmp_path: Path) -> None:
    """Given B's mailbox, A's GET is 403 and A's list does not contain it."""
    with client_for(tmp_path) as client:
        _a_id, key_a = issue(client, {"name": "a"})
        _b_id, key_b = issue(client, {"name": "b"})
        client.app.state.registry = ProviderRegistry([StubProvider(address="b@x.com")])
        created = client.post("/v1/mailboxes", json={"provider": "stub"}, headers=auth(key_b))
        assert created.status_code == 200, created.text
        mailbox_id = created.json()["id"]
        forbid(client.get(f"/v1/mailboxes/{mailbox_id}", headers=auth(key_a)))
        listed = client.get("/v1/mailboxes", headers=auth(key_a))
    assert listed.status_code == 200
    assert listed.json() == []


def test_key_a_create_outside_providers_is_403(tmp_path: Path) -> None:
    """Given providers is [stub], creating on other is 403 with no x-mailtm-error."""
    with client_for(tmp_path) as client:
        _key_id, secret = issue(client, {"providers": ["stub"]})
        client.app.state.registry = ProviderRegistry(
            [StubProvider(slug="other", address="o@x.com")]
        )
        forbid(client.post("/v1/mailboxes", json={"provider": "other"}, headers=auth(secret)))


def test_key_a_create_on_ungranted_root_parent_is_403(tmp_path: Path) -> None:
    """Given a root parent absent from parent_ids, gmail create with that parent_id is 403."""
    with client_for(tmp_path) as client:
        _key_id, secret = issue(client, _WRITE)
        parent_id = seed_parent(
            client, email="root@gmail.com", refresh_token="kept", owner_key_id=None
        )
        response = client.post(
            "/v1/mailboxes",
            json={"provider": "gmail", "parent_id": parent_id, "address": _ALIAS},
            headers=auth(secret),
        )
    forbid(response)


def test_gmail_create_without_parent_id_uses_granted_parent(tmp_path: Path) -> None:
    """Given two active parents and one granted id, auto-pick stores that parent."""
    with client_for(tmp_path) as client:
        outside = seed_parent(
            client, email="outside@gmail.com", refresh_token="out", owner_key_id=None
        )
        granted = seed_parent(client, email=_BARE, refresh_token="in", owner_key_id=None)
        _key_id, secret = issue(
            client,
            {
                "providers": ["gmail"],
                "parent_ids": [granted],
                "actions": ["mailboxes:write"],
            },
        )
        created = client.post("/v1/mailboxes", json={"provider": "gmail"}, headers=auth(secret))
        assert created.status_code == 200, created.text
        parent_id = mailbox_parent(client, created.json()["id"])
    assert parent_id == granted
    assert parent_id != outside


def test_gmail_create_with_empty_grant_is_403(tmp_path: Path) -> None:
    """Given two active parents and an empty parent grant, gmail create is 403."""
    with client_for(tmp_path) as client:
        seed_parent(client, email="one@gmail.com", refresh_token="r1", owner_key_id=None)
        seed_parent(client, email="two@gmail.com", refresh_token="r2", owner_key_id=None)
        _key_id, secret = issue(client, {"providers": ["gmail"], "parent_ids": []})
        response = client.post("/v1/mailboxes", json={"provider": "gmail"}, headers=auth(secret))
    assert response.status_code == 403
    assert response.json()["detail"] == "no gmail parent granted"
    assert response.headers.get("x-mailtm-error") is None


def test_key_with_parents_add_imports_and_deletes_only_its_parent(
    tmp_path: Path,
) -> None:
    """Given parents:add, import then delete of that parent is 200 and 204."""
    recorder = RecordingGmail(profile_email="mine@gmail.com")
    with client_for(tmp_path) as client:
        stub_gmail(client, recorder)
        _key_id, secret = issue(client, {"actions": ["parents:add"]})
        imported = client.post(
            "/v1/gmail/accounts/import",
            json={"refresh_token": "fresh", "access_token": "at"},
            headers=auth(secret),
        )
        assert imported.status_code == 200, imported.text
        deleted = client.delete(f"/v1/gmail/accounts/{imported.json()['id']}", headers=auth(secret))
    assert deleted.status_code == 204


def test_key_delete_of_root_parent_is_403(tmp_path: Path) -> None:
    """Given a root-owned parent, the issued key's DELETE is 403 with no x-mailtm-error."""
    with client_for(tmp_path) as client:
        parent_id = seed_parent(
            client, email="root@gmail.com", refresh_token="kept", owner_key_id=None
        )
        _key_id, secret = issue(client, {"actions": ["parents:add"]})
        forbid(client.delete(f"/v1/gmail/accounts/{parent_id}", headers=auth(secret)))


def test_import_of_root_email_is_403_and_token_unchanged(tmp_path: Path) -> None:
    """Given a root-owned email, import is 403 and the stored refresh token stays."""
    recorder = RecordingGmail(profile_email="root@gmail.com")
    with client_for(tmp_path) as client:
        stub_gmail(client, recorder)
        seed_parent(client, email="root@gmail.com", refresh_token="kept", owner_key_id=None)
        _key_id, secret = issue(client, {"actions": ["parents:add"]})
        response = client.post(
            "/v1/gmail/accounts/import",
            json={"refresh_token": "stolen", "access_token": "at"},
            headers=auth(secret),
        )
        forbid(response)
        assert stored_refresh(client, "root@gmail.com") == "kept"


def test_bare_gmail_address_is_400(tmp_path: Path) -> None:
    """Given user@gmail.com, POST /v1/mailboxes is 400 and names the plus-alias rule."""
    with client_for(tmp_path) as client:
        parent_id = seed_parent(client, email=_BARE, refresh_token="r", owner_key_id=None)
        response = client.post(
            "/v1/mailboxes",
            json={"provider": "gmail", "parent_id": parent_id, "address": _BARE},
            headers=auth(ROOT),
        )
    assert response.status_code == 400
    assert response.json()["detail"] == PLUS_DETAIL


def test_plus_alias_reaches_provider_boundary(tmp_path: Path) -> None:
    """Given user+tag@gmail.com and a stubbed parent, create is not rejected as non-plus."""
    with client_for(tmp_path) as client:
        parent_id = seed_parent(client, email=_BARE, refresh_token="r", owner_key_id=None)
        response = client.post(
            "/v1/mailboxes",
            json={"provider": "gmail", "parent_id": parent_id, "address": _ALIAS},
            headers=auth(ROOT),
        )
    assert response.status_code == 200, response.text
    assert PLUS_DETAIL not in response.text
    assert response.json()["address"] == _ALIAS


def test_recipient_miss_does_not_call_trash(tmp_path: Path) -> None:
    """Given a message addressed only to the bare base, get and delete are 404 and skip trash."""
    recorder = RecordingGmail(profile_email=_BARE, message=_message([("To", _BARE)]))
    with client_for(tmp_path) as client:
        stub_gmail(client, recorder)
        parent_id = seed_parent(client, email=_BARE, refresh_token="r", owner_key_id=None)
        granted: KeySpec = {**_WRITE, "parent_ids": [parent_id]}
        _key_id, secret = issue(client, granted)
        created = client.post(
            "/v1/mailboxes",
            json={"provider": "gmail", "parent_id": parent_id, "address": _ALIAS},
            headers=auth(secret),
        )
        assert created.status_code == 200, created.text
        mailbox_id = created.json()["id"]
        fetched = client.get(f"/v1/mailboxes/{mailbox_id}/messages/m1", headers=auth(secret))
        deleted = client.delete(f"/v1/mailboxes/{mailbox_id}/messages/m1", headers=auth(secret))
    assert fetched.status_code == 404
    assert deleted.status_code == 404
    assert recorder.trash_calls() == []


def test_key_sweep_does_not_delete_root_mailbox(tmp_path: Path) -> None:
    """Given an old root mailbox and a short key TTL, the key sweep leaves the root box."""
    with client_for(tmp_path) as client:
        client.app.state.registry = ProviderRegistry([StubProvider()])
        _key_id, issued = issue(
            client,
            {"name": "sweep", "actions": ["retention:write"], "providers": ["stub"]},
        )
        _seed_root_mailbox(client, utcnow_naive() - timedelta(days=10))
        _seed_key_ttl(client, secret=issued)
        response = client.post("/v1/admin/retention/run", headers=auth(issued))
        left = _addresses(client)
    assert response.status_code == 200
    assert response.json()["mailboxes_deleted"] == 0
    assert left == ["root@x"]


def _seed_root_mailbox(client: TestClient, created_at: datetime) -> None:
    async def _insert() -> None:
        async with client.app.state.session_factory() as session:
            session.add(
                Mailbox(
                    provider="stub",
                    address="root@x",
                    mailbox_token_enc=encrypt(FERNET, "tok"),
                    is_active=True,
                    is_deleted=False,
                    owner_key_id=None,
                    created_at=created_at,
                    updated_at=created_at,
                )
            )
            await session.commit()

    client.portal.call(_insert)


def _seed_key_ttl(client: TestClient, *, secret: str) -> None:
    digest = hashlib.sha256(secret.encode()).hexdigest()

    async def _insert() -> None:
        async with client.app.state.session_factory() as session:
            key = (
                await session.execute(select(ApiKey).where(ApiKey.secret_sha256 == digest))
            ).scalar_one()
            session.add(KeyRetention(key_id=key.id, provider="stub", mailbox_ttl_hours=1))
            await session.commit()

    client.portal.call(_insert)


def _addresses(client: TestClient) -> list[str]:
    async def _load() -> list[str]:
        async with client.app.state.session_factory() as session:
            rows = (await session.execute(select(Mailbox.address))).scalars().all()
            return list(rows)

    found = client.portal.call(_load)
    assert isinstance(found, list)
    return found


def test_rotate_returns_new_secret_and_old_secret_401s(tmp_path: Path) -> None:
    """Given a rotated key, the body has a new secret and the old secret is 401."""
    with client_for(tmp_path) as client:
        key_id, old = issue(client)
        rotated = client.post(f"/v1/admin/keys/{key_id}/rotate", headers=auth(ROOT))
        assert rotated.status_code == 200
        new = rotated.json()["secret"]
        denied = client.get("/v1/providers", headers=auth(old))
    assert new != old
    assert new.startswith("mk_")
    assert denied.status_code == 401


def test_reveal_returns_the_same_secret_on_second_get(tmp_path: Path) -> None:
    """Given a created key, two secret GETs both return that secret and status 200."""
    with client_for(tmp_path) as client:
        key_id, secret = issue(client)
        first = client.get(f"/v1/admin/keys/{key_id}/secret", headers=auth(ROOT))
        second = client.get(f"/v1/admin/keys/{key_id}/secret", headers=auth(ROOT))
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == {"secret": secret}
    assert second.json() == {"secret": secret}


def test_delete_of_key_with_live_mailbox_is_409(tmp_path: Path) -> None:
    """Given a live mailbox owned by the key, DELETE is 409."""
    with client_for(tmp_path) as client:
        key_id, secret = issue(client)
        client.app.state.registry = ProviderRegistry([StubProvider(address="live@x.com")])
        created = client.post("/v1/mailboxes", json={"provider": "stub"}, headers=auth(secret))
        assert created.status_code == 200, created.text
        deleted = client.delete(f"/v1/admin/keys/{key_id}", headers=auth(ROOT))
    assert deleted.status_code == 409


def test_empty_api_key_allows_providers(tmp_path: Path) -> None:
    """Given Settings(api_key=""), GET /v1/providers on the test client is 200."""
    with client_for(tmp_path, api_key="") as client:
        response = client.get("/v1/providers")
    assert response.status_code == 200
