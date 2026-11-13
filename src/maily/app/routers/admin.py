from __future__ import annotations

from contextlib import suppress
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy import case, func, select

from ...db.models import GmailAccount, KeyRetention, Mailbox, Message, Retention
from ...exceptions import MailNotFoundError
from ..authz import (
    Principal,
    RetentionRead,
    RetentionWrite,
    RootDep,
    StatsRead,
    parse_scope,
    provider_allowed,
    require_principal,
    require_root,
)
from ..deps import RegistryDep, SessionDep, SettingsDep
from ..schemas import (
    DomainCacheIn,
    DomainCacheOut,
    DomainCacheProviderOut,
    GmailCredsIn,
    GmailCredsOut,
    RetentionIn,
    RetentionOut,
)
from ..services import domain_cache as dc
from ..services import gmail_config as gcfg
from ..services import retention as svc
from ..services import scoped_stats, stats_history
from ..services.stats_history import EVENT_MESSAGE_RECEIVED

router = APIRouter(
    prefix="/v1/admin",
    dependencies=[Depends(require_principal)],
    tags=["Admin"],
)


def _sum_or_zero(value: int | None) -> int:
    return value or 0


@router.get("/stats")
async def stats(
    session: SessionDep,
    principal: StatsRead,
) -> dict | scoped_stats.ScopedStats:
    """Dashboard stats: mailbox/message totals, provider split, 7-day trend,
    and a 10-day activity history that also covers retention-deleted items."""
    if not principal.is_root:
        return await _owned_stats(session, principal)
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
        await session.execute(
            select(Message.provider, func.count())
            .where(Message.is_deleted.is_(False))
            .group_by(Message.provider)
        )
    ).all():
        by_provider.setdefault(
            provider,
            {
                "mailboxes_total": 0,
                "mailboxes_active": 0,
                "mailboxes_deleted": 0,
                "messages_total": 0,
            },
        )["messages_total"] = _sum_or_zero(msg_count)

    gmail_total, gmail_active = (
        await session.execute(
            select(
                func.count(),
                func.sum(case((GmailAccount.status == "active", 1), else_=0)),
            )
        )
    ).one()

    history = await stats_history.report(session)

    ledger_received = history["totals"][EVENT_MESSAGE_RECEIVED]
    if ledger_received:
        trend = [
            {"date": day["date"], "count": day[EVENT_MESSAGE_RECEIVED]}
            for day in history["days"][-7:]
        ]
    else:
        # first boot / pre-ledger data: fall back to the live table
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
        "history": history,
    }


async def _owned_stats(session: SessionDep, principal: Principal) -> scoped_stats.ScopedStats:
    key = principal.key
    if key is None:
        raise HTTPException(status_code=403, detail="forbidden")
    scope = parse_scope(key.scope_json)
    return await scoped_stats.owned_report(session, key_id=key.id, parent_ids=scope.parent_ids)


def _issued_key_id(principal: Principal) -> int:
    key = principal.key
    if key is None:
        raise HTTPException(status_code=403, detail="forbidden")
    return key.id


def _require_key_provider(principal: Principal, provider: str) -> None:
    if provider_allowed(principal, provider):
        return
    raise HTTPException(status_code=403, detail="forbidden")


@router.get("/retention", response_model=list[RetentionOut])
async def list_retention(
    session: SessionDep,
    principal: RetentionRead,
) -> list:
    """List active TTL retention rules. Root reads the global table."""
    if principal.is_root:
        return await svc.get_retention(session)
    return await svc.get_key_retention(session, _issued_key_id(principal))


@router.put("/retention/{provider}", response_model=RetentionOut)
async def set_retention(
    provider: str,
    body: RetentionIn,
    session: SessionDep,
    principal: RetentionWrite,
):
    """Create or update TTL retention for a provider (at least one TTL required)."""
    row: Retention | KeyRetention
    if principal.is_root:
        row = await svc.set_retention(
            session, provider, body.mailbox_ttl_hours, body.message_ttl_hours
        )
    else:
        _require_key_provider(principal, provider)
        row = await svc.set_key_retention(
            session,
            _issued_key_id(principal),
            provider,
            body.mailbox_ttl_hours,
            body.message_ttl_hours,
        )
    await session.commit()
    await session.refresh(row)
    return row


@router.delete("/retention/{provider}", status_code=204)
async def remove_retention(
    provider: str,
    session: SessionDep,
    principal: RetentionWrite,
) -> None:
    """Disable retention rules for a provider."""
    if principal.is_root:
        removed = await svc.delete_retention(session, provider)
    else:
        _require_key_provider(principal, provider)
        removed = await svc.delete_key_retention(session, _issued_key_id(principal), provider)
    if not removed:
        raise MailNotFoundError(f"retention for {provider} not found")
    await session.commit()


@router.post("/retention/run")
async def run_retention_sweep(
    request: Request,
    registry: RegistryDep,
    settings: SettingsDep,
    principal: RetentionWrite,
    force_maintenance: bool = False,
) -> dict:
    """Run the retention cleanup sweep right now. A key sweeps only its mailboxes.

    Pass `force_maintenance=true` to force full database maintenance (VACUUM,
    REINDEX, ANALYZE, WAL checkpoints, quick_check) immediately regardless of the
    configured throttling interval.
    """
    only_key_id = None if principal.is_root else _issued_key_id(principal)
    return await svc.run_sweep(
        request.app.state.session_factory,
        registry,
        settings,
        only_key_id=only_key_id,
        lock=getattr(request.app.state, "sweep_lock", None),
        force_maintenance=force_maintenance,
    )


@router.get("/domain-cache", response_model=DomainCacheOut)
async def get_domain_cache(
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
    _: RootDep,
) -> DomainCacheOut:
    """Domain cache settings and per-provider state."""
    cfg = await dc.get_settings(session, settings)
    return DomainCacheOut(
        enabled=cfg["enabled"],
        interval_seconds=cfg["interval_seconds"],
        providers=[
            DomainCacheProviderOut.model_validate(p)
            for p in await dc.cache_status(session, registry, settings)
        ],
    )


@router.put("/domain-cache", response_model=DomainCacheOut)
async def set_domain_cache(
    body: DomainCacheIn,
    session: SessionDep,
    registry: RegistryDep,
    settings: SettingsDep,
    _: RootDep,
) -> DomainCacheOut:
    """Update domain cache settings (enabled / interval)."""
    cfg = await dc.set_settings(
        session, settings, enabled=body.enabled, interval_seconds=body.interval_seconds
    )
    await session.commit()
    return DomainCacheOut(
        enabled=cfg["enabled"],
        interval_seconds=cfg["interval_seconds"],
        providers=[
            DomainCacheProviderOut.model_validate(p)
            for p in await dc.cache_status(session, registry, settings)
        ],
    )


@router.post("/domain-cache/run", response_model=None)
async def run_domain_cache(
    request: Request,
    registry: RegistryDep,
    _: RootDep,
) -> dict | JSONResponse:
    """Force a domain cache refresh; 502 with a failed list when a provider errors."""
    result = await dc.refresh_cache(request.app.state.session_factory, registry)
    if result["failed"]:
        # A partial refresh is still a failed run — signal it, don't claim 200.
        return JSONResponse(
            status_code=502,
            content={
                "detail": "Domain cache refresh failed for: " + ", ".join(result["failed"]),
                "code": "upstream",
                "refreshed": result["refreshed"],
                "failed": result["failed"],
            },
        )
    return result


@router.get("/gmail/creds", response_model=GmailCredsOut, dependencies=[Depends(require_root)])
async def get_gmail_creds(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> GmailCredsOut:
    """Current Gmail OAuth credentials (env or the encrypted store)."""
    secret = settings.resolved_secret_key()
    found = await gcfg.resolved(settings, session, secret)
    if found is None:
        return GmailCredsOut(
            configured=False, source="none", redirect_uri=settings.default_gmail_redirect_uri()
        )
    cid, _, source = found
    return GmailCredsOut(
        configured=True,
        source=source,
        client_id=cid,
        redirect_uri=await gcfg.get_redirect_uri(session, settings.default_gmail_redirect_uri()),
    )


@router.put("/gmail/creds", response_model=GmailCredsOut, dependencies=[Depends(require_root)])
async def save_gmail_creds(
    request: Request,
    body: GmailCredsIn,
    session: SessionDep,
    settings: SettingsDep,
) -> GmailCredsOut:
    """Save Gmail OAuth credentials to the encrypted store."""
    from fastapi import HTTPException

    secret = settings.resolved_secret_key()
    env = await gcfg.resolved(settings, session, secret)
    if env and env[2] == "env":
        raise HTTPException(
            409,
            "Gmail OAuth credentials are managed by environment variables (MAILY_GMAIL_CLIENT_ID/SECRET).",
        )
    cid, csec = body.client_id.strip(), body.client_secret.strip()
    if not cid or not csec:
        raise HTTPException(400, "client_id and client_secret are required.")
    await gcfg.save_creds(session, secret, cid, csec, body.redirect_uri)
    await session.commit()
    request.app.state.oauth.configure(cid, csec)
    telemetry = getattr(request.app.state, "telemetry", None)
    if telemetry is not None:
        with suppress(Exception):
            await telemetry.track_once("maily_gmail_connected", source="admin")
    return GmailCredsOut(
        configured=True,
        source="db",
        client_id=cid,
        redirect_uri=await gcfg.get_redirect_uri(session, settings.default_gmail_redirect_uri()),
    )


@router.delete("/gmail/creds", status_code=204, dependencies=[Depends(require_root)])
async def clear_gmail_creds(
    request: Request,
    session: SessionDep,
    settings: SettingsDep,
) -> None:
    """Clear stored Gmail OAuth credentials."""
    from fastapi import HTTPException

    secret = settings.resolved_secret_key()
    env = await gcfg.resolved(settings, session, secret)
    if env and env[2] == "env":
        raise HTTPException(
            409,
            "Gmail OAuth credentials are managed by environment variables and cannot be removed here.",
        )
    await gcfg.clear_creds(session)
    await session.commit()
    request.app.state.oauth.configure("", "")
