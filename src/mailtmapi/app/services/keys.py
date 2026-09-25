"""Issued API key lifecycle: encrypted secret, scope parse, and delete safety."""

from __future__ import annotations

import hashlib
import json
import secrets as _secrets
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...crypto import decrypt, encrypt
from ...db.models import ApiKey, GmailAccount, KeyRetention, Mailbox
from ...settings import Settings

ALLOWED_ACTIONS: Final[frozenset[str]] = frozenset(
    {
        "mailboxes:read",
        "mailboxes:write",
        "messages:read",
        "messages:write",
        "stats:read",
        "retention:read",
        "retention:write",
        "parents:add",
        "parents:read",
    }
)
_PREFIX_LEN: Final = 7
_SCOPE_KEYS: Final[frozenset[str]] = frozenset({"providers", "parent_ids", "actions"})


class KeyScope(BaseModel):
    """Parsed scope. Empty providers means all; empty parent_ids means none."""

    model_config = ConfigDict(frozen=True)

    providers: tuple[str, ...]
    parent_ids: tuple[int, ...]
    actions: tuple[str, ...]


class KeyCreate(BaseModel):
    """Create inputs. root_key is the env secret that must not be stored."""

    model_config = ConfigDict(frozen=True)

    name: str
    expires_at: datetime | None
    scope: Mapping[str, object]
    root_key: str


class KeyUpdate(BaseModel):
    """Fields rotate must not change. expires_at null means never expires."""

    model_config = ConfigDict(frozen=True)

    name: str
    expires_at: datetime | None
    scope: Mapping[str, object]


class KeyView(BaseModel):
    """Public key row. Never includes secret or secret_enc."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    prefix: str
    scope_json: str
    expires_at: datetime | None
    created_at: datetime | None
    updated_at: datetime | None


class CreatedKey(KeyView):
    """Create or rotate result. secret is returned once by the caller."""

    secret: str


class RevealedSecret(BaseModel):
    """Decrypted secret. Safe to call more than once."""

    model_config = ConfigDict(frozen=True)

    secret: str


@dataclass(frozen=True, slots=True)
class InvalidKeyScope(Exception):
    """Scope JSON failed the write contract."""

    detail: str

    def __str__(self) -> str:
        return self.detail


def parse_scope(raw: Mapping[str, object]) -> KeyScope:
    """Parse a write-time scope. Unknown parent ids are not checked."""
    if set(raw) != _SCOPE_KEYS:
        raise InvalidKeyScope(detail="scope requires providers, parent_ids, and actions")
    providers = raw["providers"]
    parent_ids = raw["parent_ids"]
    actions = raw["actions"]
    if not isinstance(providers, list) or not isinstance(parent_ids, list) or not isinstance(actions, list):
        raise InvalidKeyScope(detail="providers, parent_ids, and actions must be lists")
    if any(not isinstance(item, str) for item in providers):
        raise InvalidKeyScope(detail="providers must be strings")
    if any(type(item) is not int for item in parent_ids):
        raise InvalidKeyScope(detail="parent_ids must be ints")
    if any(not isinstance(item, str) for item in actions):
        raise InvalidKeyScope(detail="actions must be strings")
    unknown = [item for item in actions if item not in ALLOWED_ACTIONS]
    if unknown:
        raise InvalidKeyScope(detail="unknown action")
    return KeyScope(
        providers=tuple(providers),
        parent_ids=tuple(parent_ids),
        actions=tuple(actions),
    )


def _scope_json(raw: Mapping[str, object]) -> str:
    try:
        scope = parse_scope(raw)
    except InvalidKeyScope as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return json.dumps(
        {
            "providers": list(scope.providers),
            "parent_ids": list(scope.parent_ids),
            "actions": list(scope.actions),
        },
        separators=(",", ":"),
    )


def _sha256_hex(secret: str) -> str:
    return hashlib.sha256(secret.encode()).hexdigest()


def _mint_secret(root_key: str) -> str:
    while True:
        secret = "mk_" + _secrets.token_urlsafe(32)
        if secret != root_key:
            return secret


def _view(row: ApiKey) -> KeyView:
    return KeyView(
        id=row.id,
        name=row.name,
        prefix=row.prefix,
        scope_json=row.scope_json,
        expires_at=row.expires_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


async def _load(session: AsyncSession, key_id: int) -> ApiKey:
    """Load scalar columns only. Relationship refresh would lazy-load in async."""
    row = (
        await session.execute(select(ApiKey).where(ApiKey.id == key_id).execution_options(populate_existing=True))
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="api key not found")
    return row


def _store_secret(row: ApiKey, secret: str, fernet_key: str) -> None:
    row.prefix = secret[:_PREFIX_LEN]
    row.secret_enc = encrypt(fernet_key, secret)
    row.secret_sha256 = _sha256_hex(secret)


async def create_key(session: AsyncSession, settings: Settings, body: KeyCreate) -> CreatedKey:
    """Insert a key. Plaintext is returned once; the row stores ciphertext and SHA-256."""
    scope_json = _scope_json(body.scope)
    secret = _mint_secret(body.root_key)
    row = ApiKey(
        name=body.name,
        prefix=secret[:_PREFIX_LEN],
        secret_enc="",
        secret_sha256="",
        scope_json=scope_json,
        expires_at=body.expires_at,
    )
    _store_secret(row, secret, settings.resolved_secret_key())
    session.add(row)
    await session.flush()
    return CreatedKey(secret=secret, **_view(row).model_dump())


async def list_keys(session: AsyncSession) -> list[KeyView]:
    """Return every key without secret material."""
    rows = (await session.execute(select(ApiKey).order_by(ApiKey.id))).scalars().all()
    return [_view(row) for row in rows]


async def get_key(session: AsyncSession, key_id: int) -> KeyView:
    """Return one key without secret material."""
    row = await _load(session, key_id)
    return _view(row)


async def update_key(session: AsyncSession, key_id: int, body: KeyUpdate) -> KeyView:
    """Change name, expiry, and scope. Does not touch the secret."""
    row = await _load(session, key_id)
    row.name = body.name
    row.expires_at = body.expires_at
    row.scope_json = _scope_json(body.scope)
    await session.flush()
    stored = await _load(session, key_id)
    return _view(stored)


async def reveal_key(session: AsyncSession, settings: Settings, key_id: int) -> RevealedSecret:
    """Decrypt the stored secret. Repeat calls return the same plaintext."""
    row = await _load(session, key_id)
    return RevealedSecret(secret=decrypt(settings.resolved_secret_key(), row.secret_enc))


async def rotate_key(
    session: AsyncSession,
    settings: Settings,
    key_id: int,
    *,
    root_key: str,
) -> CreatedKey:
    """Replace the secret. Id, name, scope, and retention stay."""
    row = await _load(session, key_id)
    secret = _mint_secret(root_key)
    _store_secret(row, secret, settings.resolved_secret_key())
    await session.flush()
    stored = await _load(session, key_id)
    return CreatedKey(secret=secret, **_view(stored).model_dump())


async def delete_key(session: AsyncSession, key_id: int) -> None:
    """Delete the key. 409 while a live mailbox or any gmail account references it."""
    row = await _load(session, key_id)
    live_mailboxes = await session.scalar(
        select(func.count())
        .select_from(Mailbox)
        .where(Mailbox.owner_key_id == key_id, Mailbox.is_deleted.is_(False))
    )
    gmail_accounts = await session.scalar(
        select(func.count()).select_from(GmailAccount).where(GmailAccount.owner_key_id == key_id)
    )
    if live_mailboxes or gmail_accounts:
        raise HTTPException(status_code=409, detail="key still owns live mailboxes or gmail accounts")
    retention = (
        await session.execute(select(KeyRetention).where(KeyRetention.key_id == key_id))
    ).scalars().all()
    for item in retention:
        await session.delete(item)
    await session.delete(row)
    await session.flush()
