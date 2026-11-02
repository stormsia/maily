"""Mailbox ownership: a key sees and mutates only rows it created.

Given: two issued keys and a root key against the real app
When: one key reads, lists, deletes, or messages the other's mailbox
Then: the other owner's row is 403 forbidden with no X-MailTM-Error header,
      a missing row stays 404, and create stamps owner_key_id
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from sqlalchemy import select

from maily.app.main import create_app
from maily.app.services import keys as key_svc
from maily.crypto import encrypt
from maily.db.models import GmailAccount, Mailbox
from maily.providers.registry import ProviderRegistry
from maily.settings import Settings
from tests.helpers import StubProvider

ROOT_KEY = "root-secret"
FERNET = Fernet.generate_key().decode()


def _scope(
    *,
    providers: list[str] | None = None,
    parent_ids: list[int] | None = None,
    actions: list[str] | None = None,
) -> dict[str, object]:
    return {
        "providers": ["stub"] if providers is None else providers,
        "parent_ids": [] if parent_ids is None else parent_ids,
        "actions": (
            ["mailboxes:read", "mailboxes:write", "messages:read", "messages:write"]
            if actions is None
            else actions
        ),
    }


def _app(tmp_path: Path) -> TestClient:
    db = tmp_path / "ownership.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            secret_key=FERNET,
            api_key=ROOT_KEY,
            _env_file=None,
        )
    )
    return TestClient(app)


def _key(client: TestClient, name: str, scope: dict[str, object]) -> str:
    session_factory = client.app.state.session_factory

    async def _create() -> str:
        async with session_factory() as session:
            created = await key_svc.create_key(
                session,
                client.app.state.settings,
                key_svc.KeyCreate(
                    name=name, expires_at=None, scope=scope, root_key=ROOT_KEY
                ),
            )
            await session.commit()
            return created.secret

    return client.portal.call(_create)


def _auth(secret: str) -> dict[str, str]:
    return {"X-API-Key": secret}


def _create_mailbox(client: TestClient, secret: str, address: str) -> int:
    client.app.state.registry = ProviderRegistry([StubProvider(address=address)])
    response = client.post(
        "/v1/mailboxes",
        json={"provider": "stub"},
        headers=_auth(secret),
    )
    assert response.status_code == 200, response.text
    mailbox_id = response.json()["id"]
    assert isinstance(mailbox_id, int)
    return mailbox_id


def _owner_of(client: TestClient, mailbox_id: int) -> int | None:
    session_factory = client.app.state.session_factory

    async def _load() -> int | None:
        async with session_factory() as session:
            row = await session.get(Mailbox, mailbox_id)
            assert row is not None
            return row.owner_key_id

    return client.portal.call(_load)


@pytest.fixture
def client(tmp_path: Path) -> Iterator[TestClient]:
    with _app(tmp_path) as app:
        yield app


def test_get_other_owners_mailbox_is_forbidden_when_row_exists(
    client: TestClient,
) -> None:
    """Given key B owns a mailbox, key A GET is 403 and does not set X-MailTM-Error."""
    key_a = _key(client, "a", _scope())
    key_b = _key(client, "b", _scope())
    mailbox_id = _create_mailbox(client, key_b, "b@x.com")
    response = client.get(f"/v1/mailboxes/{mailbox_id}", headers=_auth(key_a))
    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
    assert "x-mailtm-error" not in response.headers


def test_list_hides_other_owners_mailbox_when_both_keys_created(
    client: TestClient,
) -> None:
    """Given mailboxes owned by A and B, A's list contains only A's address."""
    key_a = _key(client, "a", _scope())
    key_b = _key(client, "b", _scope())
    _create_mailbox(client, key_a, "a@x.com")
    _create_mailbox(client, key_b, "b@x.com")
    listed = client.get("/v1/mailboxes", headers=_auth(key_a))
    assert listed.status_code == 200
    assert [row["address"] for row in listed.json()] == ["a@x.com"]


def test_get_missing_mailbox_is_not_found_when_id_does_not_exist(
    client: TestClient,
) -> None:
    """Given no row for the id, GET stays 404 even for an issued key."""
    key_a = _key(client, "a", _scope())
    response = client.get("/v1/mailboxes/999999", headers=_auth(key_a))
    assert response.status_code == 404


def test_root_lists_both_owners_when_two_keys_created(client: TestClient) -> None:
    """Given mailboxes owned by two keys, root list returns both addresses."""
    key_a = _key(client, "a", _scope())
    key_b = _key(client, "b", _scope())
    _create_mailbox(client, key_a, "a@x.com")
    _create_mailbox(client, key_b, "b@x.com")
    listed = client.get("/v1/mailboxes", headers=_auth(ROOT_KEY))
    assert listed.status_code == 200
    assert {row["address"] for row in listed.json()} == {"a@x.com", "b@x.com"}


def test_create_stamps_owner_key_id_and_root_stamps_null(client: TestClient) -> None:
    """Given an issued key and root, create stores that key id or NULL."""
    key_a = _key(client, "a", _scope())
    owned = _create_mailbox(client, key_a, "owned@x.com")
    client.app.state.registry = ProviderRegistry([StubProvider(address="root@x.com")])
    root_row = client.post(
        "/v1/mailboxes", json={"provider": "stub"}, headers=_auth(ROOT_KEY)
    )
    assert root_row.status_code == 200, root_row.text
    session_factory = client.app.state.session_factory

    async def _key_id() -> int:
        async with session_factory() as session:
            digest = __import__("hashlib").sha256(key_a.encode()).hexdigest()
            from maily.db.models import ApiKey

            row = (
                await session.execute(
                    select(ApiKey).where(ApiKey.secret_sha256 == digest)
                )
            ).scalar_one()
            return row.id

    assert _owner_of(client, owned) == client.portal.call(_key_id)
    assert _owner_of(client, root_row.json()["id"]) is None


def test_create_provider_outside_scope_is_forbidden(client: TestClient) -> None:
    """Given a key allowed only stub, creating on other is 403 forbidden."""
    key_a = _key(client, "a", _scope(providers=["stub"]))
    client.app.state.registry = ProviderRegistry(
        [StubProvider(slug="other", address="o@x.com")]
    )
    response = client.post(
        "/v1/mailboxes",
        json={"provider": "other"},
        headers=_auth(key_a),
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"
    assert "x-mailtm-error" not in response.headers


def test_by_address_and_delete_of_other_owner_are_forbidden(client: TestClient) -> None:
    """Given key B's mailbox, A's by-address and delete are 403 and the row stays."""
    key_a = _key(client, "a", _scope())
    key_b = _key(client, "b", _scope())
    mailbox_id = _create_mailbox(client, key_b, "b@x.com")
    looked = client.get("/v1/mailboxes/by-address/b@x.com", headers=_auth(key_a))
    assert looked.status_code == 403
    assert looked.json()["detail"] == "forbidden"
    deleted = client.delete(f"/v1/mailboxes/{mailbox_id}", headers=_auth(key_a))
    assert deleted.status_code == 403
    assert deleted.json()["detail"] == "forbidden"
    still = client.get(f"/v1/mailboxes/{mailbox_id}", headers=_auth(key_b))
    assert still.status_code == 200


def test_message_routes_require_owner_and_action(client: TestClient) -> None:
    """Given B's mailbox, A's read routes are 403 and a missing messages:write blocks mark-read."""
    key_b = _key(client, "b", _scope())
    mailbox_id = _create_mailbox(client, key_b, "b@x.com")
    reader = _key(client, "reader", _scope(actions=["mailboxes:read", "messages:read"]))
    listed = client.get(f"/v1/mailboxes/{mailbox_id}/messages", headers=_auth(reader))
    assert listed.status_code == 403
    assert listed.json()["detail"] == "forbidden"
    fetched = client.get(
        f"/v1/mailboxes/{mailbox_id}/messages/m1", headers=_auth(reader)
    )
    assert fetched.status_code == 403
    source = client.get(
        f"/v1/mailboxes/{mailbox_id}/messages/m1/source", headers=_auth(reader)
    )
    assert source.status_code == 403
    writer = _key(
        client,
        "writer",
        _scope(actions=["messages:read"]),
    )
    marked = client.post(
        f"/v1/mailboxes/{mailbox_id}/messages/m1/read", headers=_auth(writer)
    )
    assert marked.status_code == 403
    removed = client.delete(
        f"/v1/mailboxes/{mailbox_id}/messages/m1", headers=_auth(writer)
    )
    assert removed.status_code == 403
    owner_list = client.get(
        f"/v1/mailboxes/{mailbox_id}/messages", headers=_auth(key_b)
    )
    assert owner_list.status_code == 200


def test_create_without_mailboxes_write_is_forbidden(client: TestClient) -> None:
    """Given a key that can only read mailboxes, POST /v1/mailboxes is 403."""
    key_a = _key(client, "a", _scope(actions=["mailboxes:read"]))
    client.app.state.registry = ProviderRegistry([StubProvider(address="nope@x.com")])
    response = client.post(
        "/v1/mailboxes", json={"provider": "stub"}, headers=_auth(key_a)
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "forbidden"


def test_gmail_create_without_grant_does_not_pick_ungranted_parent(
    client: TestClient,
) -> None:
    """Given two active parents and an empty parent grant, gmail create is 403."""
    key_a = _key(client, "a", _scope(providers=["gmail"], parent_ids=[]))
    session_factory = client.app.state.session_factory

    async def _seed() -> None:
        async with session_factory() as session:
            session.add(
                GmailAccount(
                    email="one@gmail.com",
                    refresh_token_enc=encrypt(FERNET, "refresh-1"),
                    status="active",
                )
            )
            session.add(
                GmailAccount(
                    email="two@gmail.com",
                    refresh_token_enc=encrypt(FERNET, "refresh-2"),
                    status="active",
                )
            )
            await session.commit()

    client.portal.call(_seed)
    response = client.post(
        "/v1/mailboxes", json={"provider": "gmail"}, headers=_auth(key_a)
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "no gmail parent granted"
    assert "x-mailtm-error" not in response.headers

    async def _count() -> int:
        async with session_factory() as session:
            rows = (await session.execute(select(Mailbox))).scalars().all()
            return len(rows)

    assert client.portal.call(_count) == 0
