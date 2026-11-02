from __future__ import annotations

from contextlib import suppress

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select

from ...db.models import Mailbox, Message
from ...exceptions import MailNotFoundError
from ..authz import Principal, PrincipalDep, action_allowed, owns_mailbox, require_principal
from ..deps import RegistryDep, SessionDep, SettingsDep
from ..schemas import MessageDetailOut, MessageOut, SourceOut
from ..services import mailboxes as svc
from ..services.stats_history import EVENT_MESSAGE_DELETED, extract_domain, record

router = APIRouter(
    prefix="/v1/mailboxes/{mailbox_id}/messages",
    dependencies=[Depends(require_principal)],
    tags=["Messages"],
)


def _summary_out(row: Message) -> MessageOut:
    return MessageOut.model_validate(row)


async def _owned_mailbox(
    session: SessionDep, principal: Principal, mailbox_id: int, action: str
) -> Mailbox:
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

    if row.provider == "anonymmail.net":
        stmt = (
            select(Message)
            .where(Message.mailbox_id == row.id, Message.is_deleted.is_(False))
            .order_by(Message.received_at.desc().nulls_last(), Message.id.desc())
        )
        all_messages = (await session.execute(stmt)).scalars().all()
        return [_summary_out(m) for m in all_messages]

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

    cached = (
        await session.execute(
            select(Message).where(Message.mailbox_id == row.id, Message.message_api_id == msg_id)
        )
    ).scalar_one_or_none()
    if cached is not None and cached.is_deleted:
        raise MailNotFoundError(f"message {msg_id} not found")

    if cached is not None and (cached.body_text is not None or cached.body_html is not None):
        html_list = [cached.body_html] if cached.body_html is not None else []
        return MessageDetailOut(
            **_summary_out(cached).model_dump(),
            text=cached.body_text or "",
            html=html_list,
        )

    try:
        detail = await prov.get_message(info, msg_id)
    except MailNotFoundError:
        if cached is not None:
            html_list = [cached.body_html] if cached.body_html is not None else []
            return MessageDetailOut(
                **_summary_out(cached).model_dump(),
                text=cached.body_text or "",
                html=html_list,
            )
        raise

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
    with suppress(Exception):
        await prov.mark_read(info, msg_id)
    cached = (
        await session.execute(
            select(Message).where(Message.mailbox_id == row.id, Message.message_api_id == msg_id)
        )
    ).scalar_one_or_none()
    if cached is None or cached.is_deleted:
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
    try:
        await prov.delete_message(info, msg_id)
    except MailNotFoundError:
        raise
    except Exception:
        pass
    cached = (
        await session.execute(
            select(Message).where(Message.mailbox_id == row.id, Message.message_api_id == msg_id)
        )
    ).scalar_one_or_none()
    if cached is not None and not cached.is_deleted:
        cached.is_deleted = True
        domain = extract_domain(row.address)
        await record(
            session,
            provider=cached.provider,
            domain=domain,
            owner_key_id=row.owner_key_id,
            event=EVENT_MESSAGE_DELETED,
        )
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
    cached = (
        await session.execute(
            select(Message).where(Message.mailbox_id == row.id, Message.message_api_id == msg_id)
        )
    ).scalar_one_or_none()

    try:
        src = await prov.get_source(info, msg_id)
        return SourceOut(id=src.id, data=src.data, download_url=src.download_url or "")
    except Exception:
        if cached is not None and (cached.body_html or cached.body_text):
            return SourceOut(
                id=msg_id, data=cached.body_html or cached.body_text or "", download_url=""
            )
        raise
