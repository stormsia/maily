from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import KeyRetention
from ..authz import PrincipalDep, require_root
from ..deps import SessionDep, SettingsDep
from ..schemas import (
    CreatedKeyOut,
    IssuedMeOut,
    KeyCreateIn,
    KeyOut,
    KeyRetentionIn,
    KeyRetentionOut,
    KeyScopeIn,
    KeyUpdateIn,
    RootMeOut,
    SecretOut,
)
from ..services.keys import KeyCreate, KeyUpdate, KeyView
from ..services.keys import create_key as create_key_row
from ..services.keys import delete_key as delete_key_row
from ..services.keys import get_key as get_key_row
from ..services.keys import list_keys as list_key_rows
from ..services.keys import reveal_key as reveal_key_row
from ..services.keys import rotate_key as rotate_key_row
from ..services.keys import update_key as update_key_row

_TAG = "Keys"


def _scope_payload(scope: KeyScopeIn) -> dict[str, list[str] | list[int]]:
    """The three lists the keys service stores. Unknown parent ids stay in the list."""
    return {
        "providers": list(scope.providers),
        "parent_ids": list(scope.parent_ids),
        "actions": list(scope.actions),
    }


def _scope(scope_json: str) -> KeyScopeIn:
    """Stored scope_json is written by the keys service, so it is already the three lists."""
    return KeyScopeIn.model_validate(json.loads(scope_json))


def _retention_out(rows: list[KeyRetention]) -> list[KeyRetentionOut]:
    return [
        KeyRetentionOut(
            provider=row.provider,
            mailbox_ttl_hours=row.mailbox_ttl_hours,
            message_ttl_hours=row.message_ttl_hours,
        )
        for row in rows
    ]


async def _retention_for(session: AsyncSession, key_id: int) -> list[KeyRetentionOut]:
    rows = (
        (
            await session.execute(
                select(KeyRetention)
                .where(KeyRetention.key_id == key_id)
                .order_by(KeyRetention.provider)
            )
        )
        .scalars()
        .all()
    )
    return _retention_out(list(rows))


async def _replace_retention(
    session: AsyncSession,
    key_id: int,
    rows: list[KeyRetentionIn],
) -> list[KeyRetentionOut]:
    """Delete this key's key_retention rows, then insert the replacement list."""
    existing = (
        (await session.execute(select(KeyRetention).where(KeyRetention.key_id == key_id)))
        .scalars()
        .all()
    )
    for item in existing:
        await session.delete(item)
    await session.flush()
    for row_in in rows:
        session.add(
            KeyRetention(
                key_id=key_id,
                provider=row_in.provider,
                mailbox_ttl_hours=row_in.mailbox_ttl_hours,
                message_ttl_hours=row_in.message_ttl_hours,
            )
        )
    await session.flush()
    return await _retention_for(session, key_id)


async def _public(session: AsyncSession, view: KeyView) -> KeyOut:
    """Key row plus its retention. Never copies secret or secret_enc."""
    return KeyOut(
        id=view.id,
        name=view.name,
        prefix=view.prefix,
        scope=_scope(view.scope_json),
        expires_at=view.expires_at,
        created_at=view.created_at,
        updated_at=view.updated_at,
        key_retention=await _retention_for(session, view.id),
    )


def _with_secret(row: KeyOut, secret: str) -> CreatedKeyOut:
    return CreatedKeyOut(secret=secret, **row.model_dump())


me_router = APIRouter(prefix="/v1/admin/keys", tags=[_TAG])
router = APIRouter(
    prefix="/v1/admin/keys",
    dependencies=[Depends(require_root)],
    tags=[_TAG],
)


@me_router.get(
    "/me",
    response_model=RootMeOut | IssuedMeOut,
    summary="Current principal",
    description="Any authenticated principal. Root is {is_root: true}; an issued key gets its own row without a secret.",
)
async def me(principal: PrincipalDep, session: SessionDep) -> RootMeOut | IssuedMeOut:
    """Root sees only the root flag. An issued key sees name, expiry, scope, and retention."""
    if principal.is_root or principal.key is None:
        return RootMeOut()
    key = principal.key
    return IssuedMeOut(
        name=key.name,
        expires_at=key.expires_at,
        scope=_scope(key.scope_json),
        key_retention=await _retention_for(session, key.id),
    )


@router.post(
    "",
    response_model=CreatedKeyOut,
    summary="Create key",
    description="Root only. Returns the new row plus the secret once.",
)
async def create_key(
    request: Request, body: KeyCreateIn, session: SessionDep, settings: SettingsDep
) -> CreatedKeyOut:
    """Mint a key, store optional retention, and return the plaintext secret once."""
    created = await create_key_row(
        session,
        settings,
        KeyCreate(
            name=body.name,
            expires_at=body.expires_at,
            scope=_scope_payload(body.scope),
            root_key=settings.api_key,
        ),
    )
    public = await _public(session, created)
    stored = public.model_copy(
        update={"key_retention": await _replace_retention(session, created.id, body.retention)}
    )
    await session.commit()
    telemetry = getattr(request.app.state, "telemetry", None)
    if telemetry is not None:
        await telemetry.track_once(
            "maily_first_api_key_created",
            actions_count=len(body.scope.actions),
            providers_count=len(body.scope.providers),
            parent_ids_count=len(body.scope.parent_ids),
        )
    return _with_secret(stored, created.secret)


@router.get(
    "",
    response_model=list[KeyOut],
    summary="List keys",
    description="Root only. Lists every key without secret material.",
)
async def list_keys(session: SessionDep) -> list[KeyOut]:
    """Return every key row. Secrets stay off the payload."""
    views = await list_key_rows(session)
    return [await _public(session, view) for view in views]


@router.get(
    "/{key_id}",
    response_model=KeyOut,
    summary="Get key",
    description="Root only. Returns one key without secret material.",
)
async def get_key(key_id: int, session: SessionDep) -> KeyOut:
    """Return one key row. The secret is not included."""
    return await _public(session, await get_key_row(session, key_id))


@router.get(
    "/{key_id}/secret",
    response_model=SecretOut,
    summary="Reveal secret",
    description="Root only. Decrypts the stored secret. Repeat calls return the same plaintext.",
)
async def reveal_secret(key_id: int, session: SessionDep, settings: SettingsDep) -> SecretOut:
    """Decrypt the stored secret. Safe to call more than once."""
    revealed = await reveal_key_row(session, settings, key_id)
    return SecretOut(secret=revealed.secret)


@router.patch(
    "/{key_id}",
    response_model=KeyOut,
    summary="Update key",
    description="Root only. Updates name, expires_at, and scope. Does not change the secret.",
)
async def update_key(key_id: int, body: KeyUpdateIn, session: SessionDep) -> KeyOut:
    """Change name, expiry, and scope, then commit."""
    view = await update_key_row(
        session,
        key_id,
        KeyUpdate(name=body.name, expires_at=body.expires_at, scope=_scope_payload(body.scope)),
    )
    await session.commit()
    return await _public(session, view)


@router.put(
    "/{key_id}/retention",
    response_model=list[KeyRetentionOut],
    summary="Replace retention",
    description="Root only. Replaces that key's key_retention rows.",
)
async def replace_retention(
    key_id: int,
    body: list[KeyRetentionIn],
    session: SessionDep,
) -> list[KeyRetentionOut]:
    """Drop existing key_retention rows for this key and insert the new list."""
    await get_key_row(session, key_id)
    rows = await _replace_retention(session, key_id, body)
    await session.commit()
    return rows


@router.post(
    "/{key_id}/rotate",
    response_model=CreatedKeyOut,
    summary="Rotate secret",
    description="Root only. Returns a new secret once. The key id does not change.",
)
async def rotate_key(key_id: int, session: SessionDep, settings: SettingsDep) -> CreatedKeyOut:
    """Replace the secret. Id, name, scope, and retention stay."""
    created = await rotate_key_row(session, settings, key_id, root_key=settings.api_key)
    public = await _public(session, created)
    await session.commit()
    return _with_secret(public, created.secret)


@router.delete(
    "/{key_id}",
    status_code=204,
    summary="Delete key",
    description="Root only. 204, or 409 when the key still owns a live mailbox or gmail account.",
)
async def delete_key(key_id: int, session: SessionDep) -> Response:
    """Delete the key. A live mailbox or gmail account is 409 from the service."""
    await delete_key_row(session, key_id)
    await session.commit()
    return Response(status_code=204)
