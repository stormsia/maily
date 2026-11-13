from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select

from ...db.models import GmailAccount, Mailbox
from ...exceptions import MailNotFoundError
from ..authz import (
    MailboxesRead,
    MailboxesWrite,
    Principal,
    PrincipalDep,
    action_allowed,
    owns_mailbox,
    parent_allowed,
    parse_scope,
    provider_allowed,
    require_principal,
)
from ..deps import RegistryDep, SessionDep, SettingsDep
from ..schemas import CreateMailboxIn, MailboxOut
from ..services import domain_cache as dc
from ..services import mailboxes as svc
from ..services.stats_history import EVENT_MAILBOX_DELETED, extract_domain, record

# The dashboard fetches mailbox lists in bounded pages (see static mailboxes.js).
# Omitting limit still caps the response so a full table can't be streamed out.
MAX_PAGE_SIZE = 500


def _like_pattern(q: str) -> str:
    """Escape LIKE wildcards so user input matches literally, then wrap in %…%."""
    escaped = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


def _parse_page(limit: int | None, offset: int | None) -> tuple[int, int]:
    if limit is None:
        limit = MAX_PAGE_SIZE
    return max(1, min(limit, MAX_PAGE_SIZE)), max(0, offset or 0)


router = APIRouter(
    prefix="/v1/mailboxes",
    dependencies=[Depends(require_principal)],
    tags=["Mailboxes"],
)


async def _parent_statuses(request: Request, rows: list[Mailbox]) -> dict[int, str]:
    """Gmail account status per parent_id ('' status = unknown / not a gmail parent)."""
    parents = {
        row.parent_id for row in rows if row.provider == "gmail" and row.parent_id is not None
    }
    if not parents:
        return {}
    try:
        store = request.app.state.gmail._store  # type: ignore[attr-defined]
    except AttributeError:
        return {}
    statuses: dict[int, str] = {}
    for parent in await store.list_all():
        if parent.id in parents:
            statuses[parent.id] = parent.status
    return statuses


def _with_status(row: Mailbox, statuses: dict[int, str]) -> MailboxOut:
    out = MailboxOut.model_validate(row)
    if row.provider == "gmail" and row.parent_id is not None:
        out.parent_status = statuses.get(row.parent_id)
    return out


def _require_owner(principal: Principal, row: Mailbox) -> None:
    """Existing row with a different owner is 403. Missing rows stay 404 upstream."""
    if owns_mailbox(principal, row):
        return
    raise HTTPException(status_code=403, detail="forbidden")


async def _owned_parent_ids(session: SessionDep, key_id: int) -> list[int]:
    rows = (
        (
            await session.execute(
                select(GmailAccount.id).where(
                    GmailAccount.owner_key_id == key_id,
                    GmailAccount.status == "active",
                )
            )
        )
        .scalars()
        .all()
    )
    return list(rows)


async def _gmail_parent_ok(session: SessionDep, principal: Principal, parent_id: int) -> bool:
    if parent_allowed(principal, parent_id):
        return True
    key = principal.key
    if key is None:
        return False
    row = await session.get(GmailAccount, parent_id)
    return row is not None and row.owner_key_id == key.id


@router.post("", response_model=MailboxOut)
async def create(
    request: Request,
    body: CreateMailboxIn,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
    principal: MailboxesWrite,
) -> Mailbox:
    """Create a disposable mailbox on a provider (optionally with a specific address/password)."""
    slug = body.provider
    if not slug and body.domain:
        slug = await dc.find_provider_for_domain(session, registry, settings, body.domain)
    if slug and not provider_allowed(principal, slug):
        raise HTTPException(status_code=403, detail="forbidden")
    owner_key_id = None if principal.is_root or principal.key is None else principal.key.id
    allowed_parent_ids: list[int] | None = None
    if slug == "gmail" and not principal.is_root and principal.key is not None:
        if body.parent_id is not None:
            if not await _gmail_parent_ok(session, principal, body.parent_id):
                raise HTTPException(status_code=403, detail="forbidden")
        else:
            granted = list(parse_scope(principal.key.scope_json).parent_ids)
            owned = await _owned_parent_ids(session, principal.key.id)
            allowed_parent_ids = list(dict.fromkeys([*granted, *owned]))
            if not allowed_parent_ids:
                raise HTTPException(status_code=403, detail="no gmail parent granted")
    row = await svc.create_mailbox(
        session,
        registry,
        settings,
        provider=slug,
        domain=body.domain,
        parent_id=body.parent_id,
        address=body.address,
        password=body.password,
        owner_key_id=owner_key_id,
        allowed_parent_ids=allowed_parent_ids,
    )
    await session.commit()
    await session.refresh(row)
    telemetry = getattr(request.app.state, "telemetry", None)
    if telemetry is not None:
        await telemetry.track_once(
            "maily_first_mailbox_created",
            provider=row.provider,
            domain=extract_domain(row.address),
            has_custom_address=bool(body.address),
            has_custom_password=bool(body.password),
            owner_is_root=principal.is_root,
        )
        await telemetry.mark_setup("first_mailbox", provider=row.provider)
    return row


@router.get("", response_model=list[MailboxOut])
async def list_mailboxes(
    request: Request,
    session: SessionDep,
    principal: PrincipalDep,
    provider: str | None = Query(None),
    active: bool = Query(True),
    q: str | None = Query(None, description="Substring filter on the full address"),
    limit: int | None = Query(
        None, ge=1, le=MAX_PAGE_SIZE, description=f"Max rows to return (default {MAX_PAGE_SIZE})"
    ),
    offset: int | None = Query(None, ge=0, description="Row offset"),
) -> list[MailboxOut]:
    """List mailboxes with optional provider/status filtering, address search and pagination."""
    if not action_allowed(principal, "mailboxes:read"):
        raise HTTPException(status_code=403, detail="forbidden")
    limit, offset = _parse_page(limit, offset)
    q = q.strip() if q else None
    qry = select(Mailbox)
    if not principal.is_root and principal.key is not None:
        qry = qry.where(Mailbox.owner_key_id == principal.key.id)
    if provider:
        qry = qry.where(Mailbox.provider == provider)
    if active:
        qry = qry.where(Mailbox.is_active.is_(True), Mailbox.is_deleted.is_(False))
    if q:
        qry = qry.where(Mailbox.address.ilike(_like_pattern(q), escape="\\"))
    qry = qry.order_by(Mailbox.id.desc()).limit(limit).offset(offset)
    rows = list((await session.execute(qry)).scalars().all())
    statuses = await _parent_statuses(request, rows)
    return [_with_status(r, statuses) for r in rows]


@router.get("/by-address/{email}", response_model=MailboxOut)
async def by_address(
    email: str,
    request: Request,
    session: SessionDep,
    principal: MailboxesRead,
) -> MailboxOut:
    """Look up a mailbox by its full email address."""
    row = await svc.get_mailbox_by_address(session, email)
    _require_owner(principal, row)
    statuses = await _parent_statuses(request, [row])
    return _with_status(row, statuses)


@router.get("/{mailbox_id}", response_model=MailboxOut)
async def get_one(
    mailbox_id: int,
    request: Request,
    session: SessionDep,
    principal: MailboxesRead,
) -> MailboxOut:
    """Fetch a single mailbox by id."""
    row = await svc.get_mailbox(session, mailbox_id)
    _require_owner(principal, row)
    statuses = await _parent_statuses(request, [row])
    return _with_status(row, statuses)


@router.delete("/{mailbox_id}", status_code=204)
async def delete_one(
    mailbox_id: int,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
    principal: MailboxesWrite,
) -> None:
    """Deactivate and mark a mailbox deleted (also deletes it upstream)."""
    row = await svc.get_mailbox(session, mailbox_id)
    _require_owner(principal, row)
    info = svc.to_mailbox_info(row, settings.resolved_secret_key())
    provider = row.provider
    domain = extract_domain(row.address)
    owner_key_id = row.owner_key_id
    # Soft-delete first. If the provider then fails, retention reaps the row
    # instead of leaving an active mailbox whose upstream account is gone.
    row.is_active = False
    row.is_deleted = True
    await record(
        session,
        provider=provider,
        domain=domain,
        owner_key_id=owner_key_id,
        event=EVENT_MAILBOX_DELETED,
    )
    await session.commit()
    try:
        prov = registry.get(provider)
        await prov.delete_mailbox(info)
    except KeyError as exc:
        raise MailNotFoundError(str(exc)) from exc
