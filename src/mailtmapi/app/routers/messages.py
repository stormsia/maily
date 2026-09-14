from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select

from ...db.models import Message
from ...exceptions import MailNotFoundError
from ..deps import RegistryDep, SessionDep, SettingsDep, require_api_key
from ..schemas import MessageDetailOut, MessageOut, SourceOut
from ..services import mailboxes as svc

router = APIRouter(
    prefix="/v1/mailboxes/{mailbox_id}/messages", dependencies=[Depends(require_api_key)]
)


def _summary_out(row: Message) -> MessageOut:
    return MessageOut.model_validate(row)


@router.get("", response_model=list[MessageOut])
async def list_messages(
    mailbox_id: int,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
    page: int = Query(1, ge=1),
) -> list[MessageOut]:
    row = await svc.get_mailbox(session, mailbox_id)
    prov = registry.get(row.provider)
    summaries = await prov.list_messages(
        svc.to_mailbox_info(row, settings.resolved_secret_key()), page=page
    )
    cached = await svc.upsert_messages(session, row, summaries)
    await session.commit()
    for m in cached:
        await session.refresh(m)
    return [_summary_out(m) for m in cached]


@router.get("/{msg_id}", response_model=MessageDetailOut)
async def get_message(
    mailbox_id: int,
    msg_id: str,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> MessageDetailOut:
    row = await svc.get_mailbox(session, mailbox_id)
    prov = registry.get(row.provider)
    detail = await prov.get_message(svc.to_mailbox_info(row, settings.resolved_secret_key()), msg_id)
    cached = (
        await session.execute(
            select(Message).where(Message.mailbox_id == row.id, Message.message_api_id == msg_id)
        )
    ).scalar_one_or_none()
    if cached is None:
        cached = Message(mailbox_id=row.id, provider=row.provider, message_api_id=msg_id)
        session.add(cached)
    cached.subject = detail.subject
    cached.from_address = detail.from_.address
    cached.from_name = detail.from_.name
    cached.seen = detail.seen
    cached.has_attachments = detail.has_attachments
    cached.size = detail.size
    cached.received_at = detail.received_at
    cached.body_text = detail.text
    cached.body_html = "\n".join(detail.html) if detail.html else None
    await session.commit()
    await session.refresh(cached)
    return MessageDetailOut(
        **_summary_out(cached).model_dump(),
        text=detail.text,
        html=detail.html,
    )


@router.post("/{msg_id}/read", response_model=MessageOut)
async def mark_read(
    mailbox_id: int,
    msg_id: str,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> MessageOut:
    row = await svc.get_mailbox(session, mailbox_id)
    prov = registry.get(row.provider)
    await prov.mark_read(svc.to_mailbox_info(row, settings.resolved_secret_key()), msg_id)
    cached = (
        await session.execute(
            select(Message).where(Message.mailbox_id == row.id, Message.message_api_id == msg_id)
        )
    ).scalar_one_or_none()
    if cached is None:
        raise MailNotFoundError(f"message {msg_id} not found")
    cached.seen = True
    await session.commit()
    await session.refresh(cached)
    return _summary_out(cached)


@router.delete("/{msg_id}", status_code=204)
async def delete_message(
    mailbox_id: int,
    msg_id: str,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> None:
    row = await svc.get_mailbox(session, mailbox_id)
    prov = registry.get(row.provider)
    await prov.delete_message(svc.to_mailbox_info(row, settings.resolved_secret_key()), msg_id)
    cached = (
        await session.execute(
            select(Message).where(Message.mailbox_id == row.id, Message.message_api_id == msg_id)
        )
    ).scalar_one_or_none()
    if cached is not None:
        cached.is_deleted = True
        await session.commit()


@router.get("/{msg_id}/source", response_model=SourceOut)
async def get_source(
    mailbox_id: int,
    msg_id: str,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> SourceOut:
    row = await svc.get_mailbox(session, mailbox_id)
    prov = registry.get(row.provider)
    src = await prov.get_source(svc.to_mailbox_info(row, settings.resolved_secret_key()), msg_id)
    return SourceOut(id=src.id, data=src.data, download_url=src.download_url)
