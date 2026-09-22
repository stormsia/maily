from __future__ import annotations

import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from ...exceptions import MailValidationError
from ...providers.gmail.oauth import GmailOAuth
from ...providers.gmail.service import GmailProvider
from ...providers.gmail.store import GmailParent, GmailParentStore
from ...settings import Settings
from ..deps import SettingsDep, require_api_key
from ..schemas import GmailAccountOut, ImportGmailIn, OAuthStartOut

router = APIRouter(
    prefix="/v1/gmail",
    dependencies=[Depends(require_api_key)],
    tags=["Gmail"],
)
public = APIRouter(prefix="/v1/gmail", tags=["Gmail"])

_OAUTH_STATE_TTL = 10 * 60


def _purge_stale_oauth_states(states: dict, now: float) -> None:
    expired = [s for s, ts in states.items() if now - ts > _OAUTH_STATE_TTL]
    for s in expired:
        states.pop(s, None)


def _gmail(request: Request) -> GmailProvider:
    return request.app.state.gmail


def _oauth(request: Request) -> GmailOAuth:
    return request.app.state.oauth


async def _redirect_uri(request: Request, settings: Settings) -> str:
    from ..services import gmail_config as gcfg

    async with request.app.state.session_factory() as session:
        return await gcfg.get_redirect_uri(session, settings.default_gmail_redirect_uri())


async def _resolve_creds(request: Request, settings: Settings) -> tuple[str, str] | None:
    """Env creds win; otherwise fall back to dashboard-stored creds (configures oauth)."""
    from ..services import gmail_config as gcfg

    secret = settings.resolved_secret_key()
    async with request.app.state.session_factory() as session:
        found = await gcfg.resolved(settings, session, secret)
    if found is None:
        return None
    cid, csec, _ = found
    request.app.state.oauth.configure(cid, csec)
    return cid, csec


def _store(request: Request) -> GmailParentStore:
    return request.app.state.gmail._store


def _out(parent: GmailParent) -> GmailAccountOut:
    return GmailAccountOut(
        id=parent.id,
        email=parent.email,
        status=parent.status,
        send_as=list(parent.send_as),
    )


async def _upsert_parent(request: Request, tokens: dict) -> GmailParent:
    gmail = _gmail(request)
    store = _store(request)
    parent = GmailParent(
        id=0,
        email="",
        refresh_token=tokens["refresh_token"],
        access_token=tokens.get("access_token"),
        access_expires_at=tokens.get("expires_at"),
        scopes=tokens.get("scopes") or "",
    )
    parent = await gmail.sync_profile(parent)
    if not parent.email:
        raise MailValidationError("could not resolve gmail profile email")
    existing = await store.get_by_email(parent.email)
    if existing:
        existing.refresh_token = parent.refresh_token
        existing.access_token = parent.access_token
        existing.access_expires_at = parent.access_expires_at
        existing.send_as = parent.send_as
        existing.scopes = parent.scopes
        existing.status = "active"
        await store.update(existing)
        return existing
    return await store.add(parent)


@router.post("/oauth/start", response_model=OAuthStartOut)
async def oauth_start(request: Request, settings: SettingsDep) -> OAuthStartOut:
    if await _resolve_creds(request, settings) is None:
        raise HTTPException(400, "Gmail OAuth credentials are not configured yet — set them up on the dashboard.")
    states: dict = request.app.state.oauth_states
    _purge_stale_oauth_states(states, time.time())
    state = secrets.token_urlsafe(16)
    states[state] = time.time()
    url = _oauth(request).auth_url(await _redirect_uri(request, settings), state)
    return OAuthStartOut(auth_url=url, state=state)


@public.get("/oauth/callback")
async def oauth_callback(request: Request, settings: SettingsDep, code: str = "", state: str = ""):
    """OAuth redirect target (browser flow). Not for direct use."""
    states: dict = request.app.state.oauth_states
    _purge_stale_oauth_states(states, time.time())
    issued = states.get(state)
    if issued is None:
        return PlainTextResponse("invalid oauth state", status_code=400)
    if time.time() - issued > _OAUTH_STATE_TTL:
        states.pop(state, None)
        return PlainTextResponse("oauth state expired", status_code=400)
    states.pop(state, None)
    if not code:
        return PlainTextResponse("missing code", status_code=400)
    tokens = await _oauth(request).exchange_code(code, await _redirect_uri(request, settings))
    await _upsert_parent(request, tokens)
    return HTMLResponse("ok, you can close this tab")


@router.post("/accounts/import", response_model=GmailAccountOut)
async def import_account(request: Request, body: ImportGmailIn) -> GmailAccountOut:
    if body.token_json is not None:
        tokens = GmailOAuth.parse_import(body.token_json)
    elif body.refresh_token:
        tokens = GmailOAuth.parse_import(
            {
                "refresh_token": body.refresh_token,
                "access_token": body.access_token,
                "expires_at": body.expires_at,
            }
        )
    else:
        raise MailValidationError("refresh_token or token_json required")
    parent = await _upsert_parent(request, tokens)
    return _out(parent)


@router.get("/accounts", response_model=list[GmailAccountOut])
async def list_accounts(request: Request) -> list[GmailAccountOut]:
    """List connected Gmail accounts (expired ones included for reconnection)."""
    # list_all: show expired accounts too so reconnection is possible.
    return [_out(p) for p in await _store(request).list_all()]


@router.delete("/accounts/{parent_id}", status_code=204)
async def delete_account(request: Request, parent_id: int) -> None:
    """Disconnect a linked Gmail account."""
    await _store(request).delete(parent_id)


@router.post("/accounts/{parent_id}/sync", response_model=GmailAccountOut)
async def sync_account(request: Request, parent_id: int) -> GmailAccountOut:
    """Refresh profile/token state for a linked Gmail account."""
    parent = await _store(request).get(parent_id)
    parent = await _gmail(request).sync_profile(parent)
    return _out(parent)
