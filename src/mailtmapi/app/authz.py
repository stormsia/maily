from __future__ import annotations

import hashlib
import json
import secrets
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated, Final

from fastapi import Depends, Header, HTTPException, Request, Security
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.models import ApiKey, Mailbox
from .deps import SessionDep, api_key_header

_API_KEY_HEADER: Final[dict[str, str]] = {"X-MailTM-Error": "api_key"}
_INVALID_DETAIL: Final[str] = "invalid api key"
_FORBIDDEN_DETAIL: Final[str] = "forbidden"


def utcnow_naive() -> datetime:
    """UTC now without tzinfo, matching stored naive expiry timestamps."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


@dataclass(frozen=True, slots=True)
class Principal:
    """Caller resolved from the env root key or an issued api_keys row."""

    is_root: bool
    key: ApiKey | None


@dataclass(frozen=True, slots=True)
class Scope:
    """Parsed scope_json. Invalid JSON is the deny scope, not an exception.

    ``providers_open`` is true only for a parsed empty ``providers`` list,
    which means every provider. A deny scope leaves it false so bad JSON
    cannot be confused with "all providers".
    """

    providers: tuple[str, ...]
    parent_ids: tuple[int, ...]
    actions: frozenset[str]
    providers_open: bool


def _invalid_api_key() -> HTTPException:
    return HTTPException(status_code=401, detail=_INVALID_DETAIL, headers=_API_KEY_HEADER)


def _forbidden() -> HTTPException:
    return HTTPException(status_code=403, detail=_FORBIDDEN_DETAIL)


def presented_secret(
    x_api_key: str | None,
    authorization: str | None,
) -> str | None:
    """X-API-Key wins; otherwise Authorization: Bearer, same as require_api_key."""
    if x_api_key:
        return x_api_key
    if authorization is None or not authorization.lower().startswith("bearer "):
        return None
    token = authorization[7:].strip()
    if not token:
        return None
    return token


def secret_sha256(secret: str) -> str:
    """Hex SHA-256 of the raw presented secret. Ciphertext is never touched."""
    return hashlib.sha256(secret.encode()).hexdigest()


def _is_root_secret(presented: str, expected: str) -> bool:
    if not expected or not presented:
        return False
    return secrets.compare_digest(presented, expected)


def _deny_scope() -> Scope:
    return Scope(providers=(), parent_ids=(), actions=frozenset(), providers_open=False)


def parse_scope(scope_json: str) -> Scope:
    """Parse scope_json. Any malformed payload denies every check."""
    try:
        raw = json.loads(scope_json)
    except json.JSONDecodeError:
        return _deny_scope()
    if not isinstance(raw, dict):
        return _deny_scope()
    return _scope_from_payload(raw)


def _scope_from_payload(payload: dict[str, object]) -> Scope:
    providers = payload.get("providers")
    parent_ids = payload.get("parent_ids")
    actions = payload.get("actions")
    if not isinstance(providers, list) or not isinstance(parent_ids, list):
        return _deny_scope()
    if not isinstance(actions, list):
        return _deny_scope()
    return _scope_from_lists(providers, parent_ids, actions)


def _scope_from_lists(
    providers: list[object],
    parent_ids: list[object],
    actions: list[object],
) -> Scope:
    provider_names = _strings(providers)
    parent_id_values = _parent_ids(parent_ids)
    action_names = _strings(actions)
    if provider_names is None or parent_id_values is None or action_names is None:
        return _deny_scope()
    return Scope(
        providers=provider_names,
        parent_ids=parent_id_values,
        actions=frozenset(action_names),
        providers_open=len(provider_names) == 0,
    )


def _strings(items: list[object]) -> tuple[str, ...] | None:
    names: list[str] = []
    for item in items:
        if not isinstance(item, str):
            return None
        names.append(item)
    return tuple(names)


def _parent_ids(items: list[object]) -> tuple[int, ...] | None:
    ids: list[int] = []
    for item in items:
        if isinstance(item, bool) or not isinstance(item, int):
            return None
        ids.append(item)
    return tuple(ids)


def _expired(key: ApiKey, now: datetime) -> bool:
    expires_at = key.expires_at
    if expires_at is None:
        return False
    return expires_at <= now


async def _lookup_key(session: AsyncSession, digest: str) -> ApiKey | None:
    result = await session.execute(select(ApiKey).where(ApiKey.secret_sha256 == digest))
    return result.scalar_one_or_none()


async def require_principal(
    request: Request,
    session: SessionDep,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Security(api_key_header)] = None,
) -> Principal:
    """Resolve the caller. Empty env key is root. Env match is root before any lookup."""
    expected: str = request.app.state.settings.api_key
    if not expected:
        return Principal(is_root=True, key=None)
    presented = presented_secret(x_api_key, authorization)
    if presented is None:
        raise _invalid_api_key()
    if _is_root_secret(presented, expected):
        return Principal(is_root=True, key=None)
    key = await _lookup_key(session, secret_sha256(presented))
    if key is None or _expired(key, utcnow_naive()):
        raise _invalid_api_key()
    return Principal(is_root=False, key=key)


PrincipalDep = Annotated[Principal, Depends(require_principal)]


def action_allowed(principal: Principal, *names: str) -> bool:
    """True when root, or when every named action is in the issued key's scope."""
    if principal.is_root:
        return True
    key = principal.key
    if key is None:
        return False
    scope = parse_scope(key.scope_json)
    return all(name in scope.actions for name in names)


def require_action(*names: str) -> Callable[..., Awaitable[Principal]]:
    """Dependency factory. Every named action must be present. Root bypasses."""

    async def _require(principal: PrincipalDep) -> Principal:
        if not action_allowed(principal, *names):
            raise _forbidden()
        return principal

    return _require


async def require_root(principal: PrincipalDep) -> Principal:
    """Issued keys are 403. Root (including open mode) passes."""
    if not principal.is_root:
        raise _forbidden()
    return principal


RootDep = Annotated[Principal, Depends(require_root)]
StatsRead = Annotated[Principal, Depends(require_action("stats:read"))]
RetentionRead = Annotated[Principal, Depends(require_action("retention:read"))]
RetentionWrite = Annotated[Principal, Depends(require_action("retention:write"))]
ParentsAdd = Annotated[Principal, Depends(require_action("parents:add"))]
ParentsRead = Annotated[Principal, Depends(require_action("parents:read"))]
MailboxesWrite = Annotated[Principal, Depends(require_action("mailboxes:write"))]
MailboxesRead = Annotated[Principal, Depends(require_action("mailboxes:read"))]


def owns_mailbox(principal: Principal, mailbox: Mailbox) -> bool:
    """Root owns every mailbox. An issued key owns only rows stamped with its id."""
    if principal.is_root:
        return True
    key = principal.key
    if key is None:
        return False
    return mailbox.owner_key_id == key.id


def provider_allowed(principal: Principal, slug: str) -> bool:
    """Empty providers means every slug. Invalid scope denies. Root always allowed."""
    if principal.is_root:
        return True
    key = principal.key
    if key is None:
        return False
    scope = parse_scope(key.scope_json)
    if scope.providers_open:
        return True
    return slug in scope.providers


def parent_allowed(principal: Principal, parent_id: int) -> bool:
    """Empty parent_ids means none. Root always allowed. Invalid scope denies."""
    if principal.is_root:
        return True
    key = principal.key
    if key is None:
        return False
    scope = parse_scope(key.scope_json)
    return parent_id in scope.parent_ids
