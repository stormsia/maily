from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select

from ...db.models import Mailbox
from ...exceptions import MailNotFoundError
from ..deps import RegistryDep, SessionDep, SettingsDep, require_api_key
from ..schemas import CreateMailboxIn, MailboxOut
from ..services import mailboxes as svc
from ..services.stats_history import EVENT_MAILBOX_DELETED, record

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
    dependencies=[Depends(require_api_key)],
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


@router.post("", response_model=MailboxOut)
async def create(
    body: CreateMailboxIn,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> Mailbox:
    """Create a disposable mailbox on a provider (optionally with a specific address/password)."""
    row = await svc.create_mailbox(
        session,
        registry,
        settings,
        provider=body.provider,
        domain=body.domain,
        parent_id=body.parent_id,
        address=body.address,
        password=body.password,
    )
    await session.commit()
    await session.refresh(row)
    return row


@router.get("", response_model=list[MailboxOut])
async def list_mailboxes(
    request: Request,
    session: SessionDep,
    provider: str | None = Query(None),
    active: bool = Query(True),
    q: str | None = Query(None, description="Substring filter on the full address"),
    limit: int | None = Query(
        None, ge=1, le=MAX_PAGE_SIZE, description=f"Max rows to return (default {MAX_PAGE_SIZE})"
    ),
    offset: int | None = Query(None, ge=0, description="Row offset"),
) -> list[MailboxOut]:
    """List mailboxes with optional provider/status filtering, address search and pagination."""
    limit, offset = _parse_page(limit, offset)
    q = q.strip() if q else None
    qry = select(Mailbox)
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
async def by_address(email: str, request: Request, session: SessionDep) -> MailboxOut:
    """Look up a mailbox by its full email address."""
    row = await svc.get_mailbox_by_address(session, email)
    statuses = await _parent_statuses(request, [row])
    return _with_status(row, statuses)


@router.get("/{mailbox_id}", response_model=MailboxOut)
async def get_one(mailbox_id: int, request: Request, session: SessionDep) -> MailboxOut:
    """Fetch a single mailbox by id."""
    row = await svc.get_mailbox(session, mailbox_id)
    statuses = await _parent_statuses(request, [row])
    return _with_status(row, statuses)


@router.delete("/{mailbox_id}", status_code=204)
async def delete_one(
    mailbox_id: int,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> None:
    """Deactivate and mark a mailbox deleted (also deletes it upstream)."""
    row = await svc.get_mailbox(session, mailbox_id)
    info = svc.to_mailbox_info(row, settings.resolved_secret_key())
    provider = row.provider
    # Soft-delete first. If the provider then fails, retention reaps the row
    # instead of leaving an active mailbox whose upstream account is gone.
    row.is_active = False
    row.is_deleted = True
    await record(session, provider=provider, event=EVENT_MAILBOX_DELETED)
    await session.commit()
    try:
        prov = registry.get(provider)
        await prov.delete_mailbox(info)
    except KeyError as exc:
        raise MailNotFoundError(str(exc)) from exc
