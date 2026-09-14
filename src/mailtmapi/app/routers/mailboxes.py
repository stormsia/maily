from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from ...db.models import Mailbox
from ...exceptions import MailNotFoundError
from ..deps import RegistryDep, SessionDep, SettingsDep, require_api_key
from ..schemas import CreateMailboxIn, MailboxOut
from ..services import mailboxes as svc

router = APIRouter(prefix="/v1/mailboxes", dependencies=[Depends(require_api_key)])


@router.post("", response_model=MailboxOut)
async def create(
    body: CreateMailboxIn,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> Mailbox:
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
    session: SessionDep,
    provider: str | None = Query(None),
    active: bool = Query(True),
) -> list[Mailbox]:
    q = select(Mailbox)
    if provider:
        q = q.where(Mailbox.provider == provider)
    if active:
        q = q.where(Mailbox.is_active.is_(True), Mailbox.is_deleted.is_(False))
    return list((await session.execute(q.order_by(Mailbox.id.desc()))).scalars().all())


@router.get("/by-address/{email}", response_model=MailboxOut)
async def by_address(email: str, session: SessionDep) -> Mailbox:
    return await svc.get_mailbox_by_address(session, email)


@router.get("/{mailbox_id}", response_model=MailboxOut)
async def get_one(mailbox_id: int, session: SessionDep) -> Mailbox:
    return await svc.get_mailbox(session, mailbox_id)


@router.delete("/{mailbox_id}", status_code=204)
async def delete_one(
    mailbox_id: int,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> None:
    row = await svc.get_mailbox(session, mailbox_id)
    try:
        prov = registry.get(row.provider)
        await prov.delete_mailbox(svc.to_mailbox_info(row, settings.resolved_secret_key()))
    except KeyError as exc:
        raise MailNotFoundError(str(exc)) from exc
    row.is_active = False
    row.is_deleted = True
    await session.commit()
