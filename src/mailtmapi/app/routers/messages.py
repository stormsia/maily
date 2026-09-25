from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from ...db.models import Mailbox, Message
from ...exceptions import MailNotFoundError
from ..authz import Principal, PrincipalDep, action_allowed, owns_mailbox, require_principal
from ..deps import RegistryDep, SessionDep, SettingsDep
from ..schemas import MessageDetailOut, MessageOut, SourceOut
from ..services import mailboxes as svc
from ..services.stats_history import EVENT_MESSAGE_DELETED, record

router = APIRouter(
    prefix="/v1/mailboxes/{mailbox_id}/messages",
    dependencies=[Depends(require_principal)],
    tags=["Messages"],
)


def _summary_out(row: Message) -> MessageOut:
    return MessageOut.model_validate(row)


async def _owned_mailbox(session: SessionDep, principal: Principal, mailbox_id: int, action: str) -> Mailbox:
    """Load the mailbox, then require the action and an owner match. Missing stays 404."""
    if not action_allowed(principal, action):
        raise HTTPException(status_code=403, detail="forbidden")
    row = await svc.get_mailbox(session, mailbox_id)
    if not owns_mailbox(principal, row):
        raise HTTPException(status_code=403, detail="forbidden")
    return row


@router.get("", response_model=list[MessageOut])
async def list_messages(
    mailbox_id: int,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
    principal: PrincipalDep,
    page: int = Query(1, ge=1),
) -> list[MessageOut]:
    """List a mailbox's messages (fetches one page from the provider and caches it)."""
    row = await _owned_mailbox(session, principal, mailbox_id, "messages:read")
    info = svc.to_mailbox_info(row, settings.resolved_secret_key())
    prov = registry.get(row.provider)
    # Release the read transaction before the provider round-trip.
    await session.commit()
    summaries = await prov.list_messages(info, page=page)
    cached = await svc.upsert_messages(session, row, summaries)
    await session.commit()
    for m in cached:
        await session.refresh(m)
    return [_summary_out(m) for m in cached if not m.is_deleted]


@router.get("/{msg_id}", response_model=MessageDetailOut)
async def get_message(
    mailbox_id: int,
    msg_id: str,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
    principal: PrincipalDep,
) -> MessageDetailOut:
    """Fetch a single message with its full text and HTML bodies."""
    row = await _owned_mailbox(session, principal, mailbox_id, "messages:read")
    info = svc.to_mailbox_info(row, settings.resolved_secret_key())
    prov = registry.get(row.provider)
    await session.commit()
    detail = await prov.get_message(info, msg_id)
    cached = (
        await session.execute(
            select(Message).where(Message.mailbox_id == row.id, Message.message_api_id == msg_id)
        )
    ).scalar_one_or_none()
    if cached is None:
        cached = Message(mailbox_id=row.id, provider=row.provider, message_api_id=msg_id)
        session.add(cached)
    cached.subject = detail.subject or ""
    cached.from_address = detail.from_.address or ""
    cached.from_name = detail.from_.name or ""
    if detail.seen:  # provider flag never downgrades a locally-marked read
        cached.seen = True
    cached.has_attachments = detail.has_attachments
    cached.size = detail.size
    cached.received_at = svc.as_naive_utc(detail.received_at)
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
    principal: PrincipalDep,
) -> MessageOut:
    """Mark a message as read (both upstream and locally)."""
    row = await _owned_mailbox(session, principal, mailbox_id, "messages:write")
    info = svc.to_mailbox_info(row, settings.resolved_secret_key())
    prov = registry.get(row.provider)
    await session.commit()
    await prov.mark_read(info, msg_id)
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
    principal: PrincipalDep,
) -> None:
    """Delete a message (upstream and local cache)."""
    row = await _owned_mailbox(session, principal, mailbox_id, "messages:write")
    info = svc.to_mailbox_info(row, settings.resolved_secret_key())
    prov = registry.get(row.provider)
    await session.commit()
    await prov.delete_message(info, msg_id)
    cached = (
        await session.execute(
            select(Message).where(Message.mailbox_id == row.id, Message.message_api_id == msg_id)
        )
    ).scalar_one_or_none()
    if cached is not None:
        cached.is_deleted = True
        await record(session, provider=cached.provider, event=EVENT_MESSAGE_DELETED)
        await session.commit()


@router.get("/{msg_id}/source", response_model=SourceOut)
async def get_source(
    mailbox_id: int,
    msg_id: str,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
    principal: PrincipalDep,
) -> SourceOut:
    """Download the raw message source (.eml payload)."""
    row = await _owned_mailbox(session, principal, mailbox_id, "messages:read")
    info = svc.to_mailbox_info(row, settings.resolved_secret_key())
    prov = registry.get(row.provider)
    await session.commit()
    src = await prov.get_source(info, msg_id)
    return SourceOut(id=src.id, data=src.data, download_url=src.download_url or "")
