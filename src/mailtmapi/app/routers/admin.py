from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Depends, Request
from sqlalchemy import case, func, select

from ...db.models import AppSetting, GmailAccount, Mailbox, Message
from ...exceptions import MailNotFoundError
from ..deps import RegistryDep, SessionDep, SettingsDep, require_api_key
from ..schemas import DomainCacheIn, DomainCacheOut, GmailCredsIn, GmailCredsOut, RetentionIn, RetentionOut
from ..services import domain_cache as dc
from ..services import gmail_config as gcfg
from ..services import retention as svc

router = APIRouter(prefix="/v1/admin", dependencies=[Depends(require_api_key)])


def _sum_or_zero(value: int | None) -> int:
    return value or 0


@router.get("/stats")
async def stats(session: SessionDep) -> dict:
    now = svc.utcnow_naive()
    cutoff = now - timedelta(days=6)

    mb_total, mb_active, mb_deleted = (
        await session.execute(
            select(
                func.count(),
                func.sum(case((Mailbox.is_active.is_(True), 1), else_=0)),
                func.sum(case((Mailbox.is_deleted.is_(True), 1), else_=0)),
            )
        )
    ).one()
    msg_total, msg_deleted = (
        await session.execute(
            select(
                func.count(),
                func.sum(case((Message.is_deleted.is_(True), 1), else_=0)),
            )
        )
    ).one()

    by_provider: dict[str, dict] = {}
    for provider, total, active, deleted in (
        await session.execute(
            select(
                Mailbox.provider,
                func.count(),
                func.sum(case((Mailbox.is_active.is_(True), 1), else_=0)),
                func.sum(case((Mailbox.is_deleted.is_(True), 1), else_=0)),
            ).group_by(Mailbox.provider)
        )
    ).all():
        by_provider[provider] = {
            "mailboxes_total": _sum_or_zero(total),
            "mailboxes_active": _sum_or_zero(active),
            "mailboxes_deleted": _sum_or_zero(deleted),
            "messages_total": 0,
        }
    for provider, msg_count in (
        await session.execute(select(Message.provider, func.count()).group_by(Message.provider))
    ).all():
        by_provider.setdefault(provider, {"mailboxes_total": 0, "mailboxes_active": 0, "mailboxes_deleted": 0, "messages_total": 0})[
            "messages_total"
        ] = _sum_or_zero(msg_count)

    gmail_total, gmail_active = (
        await session.execute(
            select(
                func.count(),
                func.sum(case((GmailAccount.status == "active", 1), else_=0)),
            )
        )
    ).one()

    trend = [
        {"date": d, "count": _sum_or_zero(c)}
        for d, c in (
            await session.execute(
                select(func.date(Message.received_at).label("d"), func.count())
                .where(Message.received_at >= cutoff)
                .group_by("d")
                .order_by("d")
            )
        ).all()
    ] or [{"date": "no-data", "count": 0}]

    return {
        "mailboxes": {
            "total": _sum_or_zero(mb_total),
            "active": _sum_or_zero(mb_active),
            "deleted": _sum_or_zero(mb_deleted),
        },
        "messages": {"total": _sum_or_zero(msg_total), "deleted": _sum_or_zero(msg_deleted)},
        "by_provider": by_provider,
        "gmail_accounts": {
            "total": _sum_or_zero(gmail_total),
            "active": _sum_or_zero(gmail_active),
        },
        "messages_last_7_days": trend,
    }


@router.get("/retention", response_model=list[RetentionOut])
async def list_retention(session: SessionDep) -> list:
    return await svc.get_retention(session)


@router.put("/retention/{provider}", response_model=RetentionOut)
async def set_retention(provider: str, body: RetentionIn, session: SessionDep):
    row = await svc.set_retention(session, provider, body.mailbox_ttl_hours, body.message_ttl_hours)
    await session.commit()
    await session.refresh(row)
    return row


@router.delete("/retention/{provider}", status_code=204)
async def remove_retention(provider: str, session: SessionDep) -> None:
    if not await svc.delete_retention(session, provider):
        raise MailNotFoundError(f"retention for {provider} not found")
    await session.commit()


@router.post("/retention/run")
async def run_retention_sweep(
    request: Request,
    registry: RegistryDep,
    settings: SettingsDep,
) -> dict:
    return await svc.run_sweep(request.app.state.session_factory, registry, settings)


@router.get("/domain-cache", response_model=DomainCacheOut)
async def get_domain_cache(
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> DomainCacheOut:
    cfg = await dc.get_settings(session, settings)
    return DomainCacheOut(
        enabled=cfg["enabled"],
        interval_seconds=cfg["interval_seconds"],
        providers=await dc.cache_status(session, registry, settings),
    )


@router.put("/domain-cache", response_model=DomainCacheOut)
async def set_domain_cache(
    body: DomainCacheIn,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
) -> DomainCacheOut:
    cfg = await dc.set_settings(
        session, settings, enabled=body.enabled, interval_seconds=body.interval_seconds
    )
    await session.commit()
    return DomainCacheOut(
        enabled=cfg["enabled"],
        interval_seconds=cfg["interval_seconds"],
        providers=await dc.cache_status(session, registry, settings),
    )


@router.post("/domain-cache/run")
async def run_domain_cache(request: Request, registry: RegistryDep) -> dict:
    return await dc.refresh_cache(request.app.state.session_factory, registry)


@router.get("/gmail/creds", response_model=GmailCredsOut)
async def get_gmail_creds(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> GmailCredsOut:
    secret = settings.resolved_secret_key()
    found = await gcfg.resolved(settings, session, secret)
    if found is None:
        return GmailCredsOut(configured=False, source="none", redirect_uri=settings.gmail_redirect_uri())
    cid, _, source = found
    return GmailCredsOut(
        configured=True,
        source=source,
        client_id=cid,
        redirect_uri=await gcfg.get_redirect_uri(session, settings.gmail_redirect_uri()),
    )


@router.put("/gmail/creds", response_model=GmailCredsOut)
async def save_gmail_creds(
    request: Request,
    body: GmailCredsIn,
    session: SessionDep,
    settings: SettingsDep,
) -> GmailCredsOut:
    from fastapi import HTTPException

    secret = settings.resolved_secret_key()
    env = await gcfg.resolved(settings, session, secret)
    if env and env[2] == "env":
        raise HTTPException(
            409, "Gmail OAuth credentials are managed by environment variables (MAILTM_GMAIL_CLIENT_ID/SECRET)."
        )
    cid, csec = body.client_id.strip(), body.client_secret.strip()
    if not cid or not csec:
        raise HTTPException(400, "client_id and client_secret are required.")
    await gcfg.save_creds(session, secret, cid, csec, body.redirect_uri)
    await session.commit()
    request.app.state.oauth.configure(cid, csec)
    return GmailCredsOut(
        configured=True,
        source="db",
        client_id=cid,
        redirect_uri=await gcfg.get_redirect_uri(session, settings.gmail_redirect_uri()),
    )


@router.delete("/gmail/creds", status_code=204)
async def clear_gmail_creds(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> None:
    from fastapi import HTTPException

    secret = settings.resolved_secret_key()
    env = await gcfg.resolved(settings, session, secret)
    if env and env[2] == "env":
        raise HTTPException(
            409, "Gmail OAuth credentials are managed by environment variables and cannot be removed here."
        )
    await gcfg.clear_creds(session)
    await session.commit()
    request.app.state.oauth.configure("", "")