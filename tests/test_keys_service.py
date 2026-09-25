"""Issued API key service: secret storage, scope parse, and delete safety.

Given: an in-memory SQLite session built from ORM metadata
When: create, list, get, update, reveal, rotate, or delete runs
Then: ciphertext and SHA-256 are stored, list/get hide the secret, and
      delete is 409 while live mailboxes or any gmail account remain
"""

from __future__ import annotations

import hashlib
from collections.abc import AsyncIterator
from datetime import datetime

import pytest
from cryptography.fernet import Fernet
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from mailtmapi.app.services import keys as key_svc
from mailtmapi.crypto import decrypt
from mailtmapi.db.models import ApiKey, Base, GmailAccount, KeyRetention, Mailbox, Message
from mailtmapi.settings import Settings

SECRET = Fernet.generate_key().decode()
ROOT_KEY = "root-api-key-not-stored"
READ_SCOPE = {
    "providers": ["mail.tm"],
    "parent_ids": [7],
    "actions": ["mailboxes:read", "messages:read"],
}


def _settings() -> Settings:
    return Settings(
        secret_key=SECRET,
        api_key=ROOT_KEY,
        database_url="sqlite+aiosqlite:///:memory:",
        _env_file=None,
    )


@pytest.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        yield db
    await engine.dispose()


def _sha256(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


@pytest.mark.asyncio
async def test_create_stores_ciphertext_and_returns_plaintext_once_when_scope_is_valid(
    session: AsyncSession,
) -> None:
    """Given a valid scope and a root key, create stores Fernet ciphertext and the SHA-256 hex."""
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ops", expires_at=None, scope=READ_SCOPE, root_key=ROOT_KEY),
    )
    assert created.secret.startswith("mk_")
    assert created.secret != ROOT_KEY
    assert created.prefix == created.secret[:7]
    row = await session.get(ApiKey, created.id)
    assert row is not None
    assert row.secret_enc != created.secret
    assert decrypt(SECRET, row.secret_enc) == created.secret
    assert row.secret_sha256 == _sha256(created.secret)
    assert row.prefix == created.prefix
    assert row.name == "ops"
    assert row.expires_at is None


@pytest.mark.asyncio
async def test_list_and_get_omit_secret_when_key_exists(session: AsyncSession) -> None:
    """Given a stored key, list and get expose metadata only."""
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ops", expires_at=None, scope=READ_SCOPE, root_key=ROOT_KEY),
    )
    listed = await key_svc.list_keys(session)
    fetched = await key_svc.get_key(session, created.id)
    for view in (listed[0], fetched):
        dumped = view.model_dump()
        assert "secret" not in dumped
        assert "secret_enc" not in dumped
        assert view.id == created.id
        assert view.prefix == created.prefix
        assert view.name == "ops"


@pytest.mark.asyncio
async def test_reveal_returns_same_secret_when_called_twice(session: AsyncSession) -> None:
    """Given a stored key, two reveals decrypt to the create-time secret."""
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ops", expires_at=None, scope=READ_SCOPE, root_key=ROOT_KEY),
    )
    first = await key_svc.reveal_key(session, _settings(), created.id)
    second = await key_svc.reveal_key(session, _settings(), created.id)
    assert first.secret == created.secret
    assert second.secret == created.secret


@pytest.mark.asyncio
async def test_rotate_keeps_id_and_replaces_secret_when_root_key_is_provided(
    session: AsyncSession,
) -> None:
    """Given an existing key, rotate keeps the id and stores a new SHA-256."""
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ops", expires_at=None, scope=READ_SCOPE, root_key=ROOT_KEY),
    )
    old_sha = _sha256(created.secret)
    rotated = await key_svc.rotate_key(session, _settings(), created.id, root_key=ROOT_KEY)
    row = await session.get(ApiKey, created.id)
    assert row is not None
    assert rotated.id == created.id
    assert rotated.secret != created.secret
    assert rotated.secret != ROOT_KEY
    assert row.secret_sha256 != old_sha
    assert row.secret_sha256 == _sha256(rotated.secret)
    assert row.name == "ops"
    assert row.scope_json == created.scope_json


@pytest.mark.asyncio
async def test_delete_raises_409_when_live_mailbox_references_key(session: AsyncSession) -> None:
    """Given a mailbox with is_deleted=0, delete refuses with 409 and keeps the key."""
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ops", expires_at=None, scope=READ_SCOPE, root_key=ROOT_KEY),
    )
    session.add(
        Mailbox(
            provider="mail.tm",
            address="live@x.test",
            mailbox_token_enc="tok",
            owner_key_id=created.id,
            is_deleted=False,
        )
    )
    await session.flush()
    with pytest.raises(HTTPException) as raised:
        await key_svc.delete_key(session, created.id)
    assert raised.value.status_code == 409
    assert await session.get(ApiKey, created.id) is not None


@pytest.mark.asyncio
async def test_delete_succeeds_when_only_soft_deleted_mailbox_references_key(
    session: AsyncSession,
) -> None:
    """Given only is_deleted=1 mail, delete removes the key and leaves the mailbox."""
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ops", expires_at=None, scope=READ_SCOPE, root_key=ROOT_KEY),
    )
    mailbox = Mailbox(
        provider="mail.tm",
        address="gone@x.test",
        mailbox_token_enc="tok",
        owner_key_id=created.id,
        is_deleted=True,
    )
    session.add(mailbox)
    await session.flush()
    mailbox_id = mailbox.id
    message = Message(
        mailbox_id=mailbox_id,
        provider="mail.tm",
        message_api_id="m1",
    )
    session.add(message)
    await session.flush()
    await key_svc.delete_key(session, created.id)
    assert await session.get(ApiKey, created.id) is None
    kept = await session.get(Mailbox, mailbox_id)
    assert kept is not None
    assert await session.get(Message, message.id) is not None


@pytest.mark.asyncio
async def test_delete_raises_409_when_gmail_account_references_key(session: AsyncSession) -> None:
    """Given any gmail_accounts row for the key, delete refuses with 409."""
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ops", expires_at=None, scope=READ_SCOPE, root_key=ROOT_KEY),
    )
    session.add(
        GmailAccount(
            email="parent@gmail.com",
            refresh_token_enc="enc",
            owner_key_id=created.id,
        )
    )
    await session.flush()
    with pytest.raises(HTTPException) as raised:
        await key_svc.delete_key(session, created.id)
    assert raised.value.status_code == 409
    assert await session.get(ApiKey, created.id) is not None


@pytest.mark.asyncio
async def test_delete_removes_key_retention_and_keeps_mail_when_unreferenced(
    session: AsyncSession,
) -> None:
    """Given no live owner rows, delete removes the key and its key_retention rows."""
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ops", expires_at=None, scope=READ_SCOPE, root_key=ROOT_KEY),
    )
    session.add(KeyRetention(key_id=created.id, provider="mail.tm", mailbox_ttl_hours=24))
    await session.flush()
    await key_svc.delete_key(session, created.id)
    remaining = (
        await session.execute(select(KeyRetention).where(KeyRetention.key_id == created.id))
    ).scalars().all()
    assert remaining == []
    assert await session.get(ApiKey, created.id) is None


@pytest.mark.asyncio
async def test_update_changes_name_expiry_and_scope_when_patch_is_valid(
    session: AsyncSession,
) -> None:
    """Given a stored key, update writes name, expires_at, and scope_json only."""
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ops", expires_at=None, scope=READ_SCOPE, root_key=ROOT_KEY),
    )
    expires = datetime(2030, 1, 2, 3, 4, 5)
    next_scope = {
        "providers": [],
        "parent_ids": [9],
        "actions": ["stats:read"],
    }
    updated = await key_svc.update_key(
        session,
        created.id,
        key_svc.KeyUpdate(name="renamed", expires_at=expires, scope=next_scope),
    )
    row = await session.get(ApiKey, created.id)
    assert row is not None
    assert updated.name == "renamed"
    assert row.name == "renamed"
    assert row.expires_at == expires
    assert row.secret_sha256 == _sha256(created.secret)
    assert '"stats:read"' in row.scope_json


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "scope",
    [
        {"providers": [], "parent_ids": [], "actions": ["keys:write"]},
        {"providers": "mail.tm", "parent_ids": [], "actions": ["mailboxes:read"]},
        {"providers": [], "parent_ids": ["7"], "actions": ["mailboxes:read"]},
        {"providers": [1], "parent_ids": [], "actions": ["mailboxes:read"]},
        {"providers": [], "parent_ids": [1.5], "actions": ["mailboxes:read"]},
        {"providers": [], "parent_ids": [], "actions": ["nope"]},
    ],
)
async def test_scope_rejected_when_shape_or_action_is_illegal(
    session: AsyncSession,
    scope: dict[str, object],
) -> None:
    """Given an unknown action or a non-list field, create raises HTTP 422."""
    with pytest.raises(HTTPException) as raised:
        await key_svc.create_key(
            session,
            _settings(),
            key_svc.KeyCreate(name="bad", expires_at=None, scope=scope, root_key=ROOT_KEY),
        )
    assert raised.value.status_code == 422


@pytest.mark.asyncio
async def test_scope_accepts_empty_lists_and_unknown_parent_ids_when_types_match(
    session: AsyncSession,
) -> None:
    """Given int parent ids and string providers, unknown parent ids are stored."""
    scope = {"providers": [], "parent_ids": [999_999], "actions": ["parents:read"]}
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(name="ok", expires_at=None, scope=scope, root_key=ROOT_KEY),
    )
    row = await session.get(ApiKey, created.id)
    assert row is not None
    assert "999999" in row.scope_json
    assert row.scope_json.startswith("{")


@pytest.mark.asyncio
async def test_create_regenerates_secret_when_generator_returns_root_key(
    session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given a generator whose first full secret equals the root key, create stores the next one."""
    tokens = iter(["COLLIDE", "second-secret-value"])

    def _fake_token(_nbytes: int = 32) -> str:
        return next(tokens)

    monkeypatch.setattr(key_svc._secrets, "token_urlsafe", _fake_token)
    created = await key_svc.create_key(
        session,
        _settings(),
        key_svc.KeyCreate(
            name="ops",
            expires_at=None,
            scope=READ_SCOPE,
            root_key="mk_COLLIDE",
        ),
    )
    assert created.secret == "mk_second-secret-value"
    row = await session.get(ApiKey, created.id)
    assert row is not None
    assert row.secret_sha256 == _sha256("mk_second-secret-value")
    assert row.secret_sha256 != _sha256("mk_COLLIDE")
