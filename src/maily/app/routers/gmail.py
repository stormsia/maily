from __future__ import annotations

import secrets
import time
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from typing_extensions import TypedDict

from ...exceptions import MailValidationError
from ...providers.gmail.oauth import GmailOAuth
from ...providers.gmail.service import GmailProvider
from ...providers.gmail.store import GmailParent, GmailParentStore
from ...settings import Settings
from ..authz import (
    ParentsAdd,
    ParentsRead,
    Principal,
    PrincipalDep,
    parent_allowed,
    require_principal,
)
from ..deps import SettingsDep
from ..schemas import GmailAccountOut, ImportGmailIn, OAuthCallbackIn, OAuthStartOut

router = APIRouter(
    prefix="/v1/gmail",
    dependencies=[Depends(require_principal)],
    tags=["Gmail"],
)
public = APIRouter(prefix="/v1/gmail", tags=["Gmail"])

_OAUTH_STATE_TTL = 10 * 60


class _OAuthState(TypedDict):
    """Server-side OAuth state. The query param stays the random token."""

    ts: float
    owner_key_id: int | None


def _purge_stale_oauth_states(states: dict[str, _OAuthState], now: float) -> None:
    expired = [s for s, entry in states.items() if now - entry["ts"] > _OAUTH_STATE_TTL]
    for s in expired:
        states.pop(s, None)


def _caller_key_id(principal: Principal) -> int | None:
    """Root (and open mode) own new parents as NULL. Issued keys own them by id."""
    if principal.is_root or principal.key is None:
        return None
    return principal.key.id


def _may_mutate_parent(principal: Principal, parent: GmailParent) -> bool:
    """Delete and sync only when the caller owns the parent. Root bypasses. NULL is root."""
    if principal.is_root:
        return True
    caller_id = _caller_key_id(principal)
    if parent.owner_key_id == caller_id:
        return True
    raise HTTPException(status_code=403, detail="forbidden")


def _visible_parents(principal: Principal, parents: list[GmailParent]) -> list[GmailParent]:
    """Own parents plus root-owned parents listed in parent_ids. Root sees every parent."""
    if principal.is_root:
        return list(parents)
    caller_id = _caller_key_id(principal)
    return [
        parent
        for parent in parents
        if parent.owner_key_id == caller_id
        or (parent.owner_key_id is None and parent_allowed(principal, parent.id))
    ]


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


async def _track_gmail_connected(request: Request, source: str) -> None:
    """Best-effort telemetry for the first connected Gmail account."""
    telemetry = getattr(request.app.state, "telemetry", None)
    if telemetry is None:
        return
    try:
        await telemetry.track_once("maily_gmail_connected", source=source)
    except Exception:  # noqa: BLE001 - telemetry must never break the request
        return


def _out(parent: GmailParent) -> GmailAccountOut:
    return GmailAccountOut(
        id=parent.id,
        email=parent.email,
        status=parent.status,
        send_as=list(parent.send_as),
    )


async def _upsert_parent(request: Request, tokens: dict, caller_key_id: int | None) -> GmailParent:
    """Insert a parent for this caller, or refresh tokens when the caller already owns it.

    An existing row whose owner_key_id differs (NULL equals only None) is 403.
    A matching caller may refresh tokens; owner_key_id stays as stored.
    """
    gmail = _gmail(request)
    store = _store(request)
    parent = GmailParent(
        id=0,
        email="",
        refresh_token=tokens["refresh_token"],
        access_token=tokens.get("access_token"),
        access_expires_at=tokens.get("expires_at"),
        scopes=tokens.get("scopes") or "",
        owner_key_id=caller_key_id,
    )
    parent = await gmail.sync_profile(parent)
    if not parent.email:
        raise MailValidationError("could not resolve gmail profile email")
    existing = await store.get_by_email(parent.email)
    if existing:
        if existing.owner_key_id != caller_key_id:
            raise HTTPException(status_code=403, detail="forbidden")
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
async def oauth_start(
    request: Request,
    settings: SettingsDep,
    principal: ParentsAdd,
) -> OAuthStartOut:
    if await _resolve_creds(request, settings) is None:
        raise HTTPException(
            400, "Gmail OAuth credentials are not configured yet — set them up on the dashboard."
        )
    states: dict[str, _OAuthState] = request.app.state.oauth_states
    _purge_stale_oauth_states(states, time.time())
    state = secrets.token_urlsafe(16)
    states[state] = {"ts": time.time(), "owner_key_id": _caller_key_id(principal)}
    url = _oauth(request).auth_url(await _redirect_uri(request, settings), state)
    return OAuthStartOut(auth_url=url, state=state)


def _extract_oauth_input(
    raw: str | None,
    code: str | None = None,
    state: str | None = None,
    redirect_uri: str | None = None,
) -> tuple[str, str | None, str | None]:
    raw_str = (raw or "").strip()
    c = (code or "").strip()
    s = (state or "").strip() or None
    r = (redirect_uri or "").strip() or None

    if raw_str:
        if "://" in raw_str or "?" in raw_str or "code=" in raw_str:
            try:
                target = raw_str if "://" in raw_str else f"http://dummy/{raw_str.lstrip('/')}"
                parsed = urlparse(target)
                qs = parse_qs(parsed.query)
                if "code" in qs and qs["code"]:
                    c = qs["code"][0]
                if "state" in qs and qs["state"]:
                    s = qs["state"][0]
                if (
                    not r
                    and parsed.scheme
                    and parsed.netloc
                    and (parsed.scheme != "http" or parsed.netloc != "dummy")
                ):
                    extracted = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                    extracted = extracted.replace("://0.0.0.0", "://127.0.0.1")
                    r = extracted
            except Exception:
                if not c:
                    c = raw_str
        elif not c:
            c = raw_str

    return c, s, r


@public.get("/oauth/callback")
async def oauth_callback(request: Request, settings: SettingsDep, code: str = "", state: str = ""):
    """OAuth redirect target (browser flow). Not for direct use."""
    wants_json = (
        request.headers.get("accept", "").startswith("application/json")
        or request.query_params.get("format") == "json"
    )

    def _err(msg: str, status_code: int = 400):
        if wants_json:
            return JSONResponse({"detail": msg}, status_code=status_code)
        return PlainTextResponse(msg, status_code=status_code)

    states: dict[str, _OAuthState] = request.app.state.oauth_states
    _purge_stale_oauth_states(states, time.time())
    entry = states.get(state)
    if entry is None:
        return _err("invalid oauth state", status_code=400)
    if time.time() - entry["ts"] > _OAUTH_STATE_TTL:
        states.pop(state, None)
        return _err("oauth state expired", status_code=400)
    owner_key_id = entry["owner_key_id"]
    states.pop(state, None)
    if not code:
        return _err("missing code", status_code=400)
    tokens = await _oauth(request).exchange_code(code, await _redirect_uri(request, settings))
    try:
        parent = await _upsert_parent(request, tokens, owner_key_id)
    except HTTPException as exc:
        return _err(str(exc.detail), status_code=exc.status_code)
    await _track_gmail_connected(request, "oauth_callback")
    if wants_json:
        return JSONResponse({"ok": True, "email": parent.email, "id": parent.id})
    return HTMLResponse("ok, you can close this tab")


@router.post("/oauth/callback", response_model=GmailAccountOut)
@router.post("/oauth/exchange", response_model=GmailAccountOut)
async def oauth_callback_post(
    request: Request,
    body: OAuthCallbackIn,
    settings: SettingsDep,
    principal: ParentsAdd,
) -> GmailAccountOut:
    """Manually complete OAuth when browser callback is unreachable (e.g. behind proxy)."""
    if await _resolve_creds(request, settings) is None:
        raise HTTPException(
            400, "Gmail OAuth credentials are not configured yet — set them up on the dashboard."
        )

    code, state, r_uri = _extract_oauth_input(
        body.url_or_code, body.code, body.state, body.redirect_uri
    )
    if not code:
        raise MailValidationError("Authorization code or redirect URL is required")

    states: dict[str, _OAuthState] = request.app.state.oauth_states
    _purge_stale_oauth_states(states, time.time())

    owner_key_id = _caller_key_id(principal)
    if state and state in states:
        entry = states.pop(state, None)
        if entry:
            owner_key_id = entry["owner_key_id"]

    configured_redirect_uri = await _redirect_uri(request, settings)
    target_uri = (r_uri or configured_redirect_uri).replace("://0.0.0.0", "://127.0.0.1")

    try:
        tokens = await _oauth(request).exchange_code(code, target_uri)
    except Exception as exc:
        if target_uri != configured_redirect_uri:
            try:
                tokens = await _oauth(request).exchange_code(code, configured_redirect_uri)
            except Exception:
                raise exc from None
        else:
            raise

    parent = await _upsert_parent(request, tokens, owner_key_id)
    await _track_gmail_connected(request, "oauth_exchange")
    return _out(parent)


@router.post("/accounts/import", response_model=GmailAccountOut)
async def import_account(
    request: Request,
    body: ImportGmailIn,
    principal: ParentsAdd,
) -> GmailAccountOut:
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
    parent = await _upsert_parent(request, tokens, _caller_key_id(principal))
    await _track_gmail_connected(request, "import")
    return _out(parent)


@router.get("/accounts", response_model=list[GmailAccountOut])
async def list_accounts(
    request: Request,
    principal: ParentsRead,
) -> list[GmailAccountOut]:
    """List connected Gmail accounts (expired ones included for reconnection)."""
    # list_all: show expired accounts too so reconnection is possible.
    visible = _visible_parents(principal, await _store(request).list_all())
    return [_out(p) for p in visible]


@router.delete("/accounts/{parent_id}", status_code=204)
async def delete_account(
    request: Request,
    parent_id: int,
    principal: PrincipalDep,
) -> None:
    """Disconnect a linked Gmail account the caller owns."""
    parent = await _store(request).get(parent_id)
    _may_mutate_parent(principal, parent)
    await _store(request).delete(parent_id)


@router.post("/accounts/{parent_id}/sync", response_model=GmailAccountOut)
async def sync_account(
    request: Request,
    parent_id: int,
    principal: PrincipalDep,
) -> GmailAccountOut:
    """Refresh profile/token state for a linked Gmail account the caller owns."""
    parent = await _store(request).get(parent_id)
    _may_mutate_parent(principal, parent)
    parent = await _gmail(request).sync_profile(parent)
    return _out(parent)
