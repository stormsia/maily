from __future__ import annotations

import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse

from ...exceptions import MailValidationError
from ...providers.gmail.oauth import GmailOAuth
from ...providers.gmail.service import GmailProvider
from ...providers.gmail.store import GmailParent, GmailParentStore
from ..deps import SettingsDep, require_api_key
from ..schemas import GmailAccountOut, ImportGmailIn, OAuthStartOut

router = APIRouter(prefix="/v1/gmail", dependencies=[Depends(require_api_key)])
public = APIRouter(prefix="/v1/gmail")


def _gmail(request: Request) -> GmailProvider:
    return request.app.state.gmail


def _oauth(request: Request) -> GmailOAuth:
    return request.app.state.oauth


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
    try:
        settings.gmail_client()
    except RuntimeError as exc:
        raise HTTPException(400, str(exc)) from exc
    state = secrets.token_urlsafe(16)
    request.app.state.oauth_states[state] = time.time()
    url = _oauth(request).auth_url(settings.gmail_redirect_uri(), state)
    return OAuthStartOut(auth_url=url, state=state)


@public.get("/oauth/callback")
async def oauth_callback(request: Request, settings: SettingsDep, code: str = "", state: str = ""):
    states: dict = request.app.state.oauth_states
    if not state or state not in states:
        return PlainTextResponse("invalid oauth state", status_code=400)
    states.pop(state, None)
    if not code:
        return PlainTextResponse("missing code", status_code=400)
    tokens = await _oauth(request).exchange_code(code, settings.gmail_redirect_uri())
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
    return [_out(p) for p in await _store(request).list_active()]


@router.delete("/accounts/{parent_id}", status_code=204)
async def delete_account(request: Request, parent_id: int) -> None:
    await _store(request).delete(parent_id)


@router.post("/accounts/{parent_id}/sync", response_model=GmailAccountOut)
async def sync_account(request: Request, parent_id: int) -> GmailAccountOut:
    parent = await _store(request).get(parent_id)
    parent = await _gmail(request).sync_profile(parent)
    return _out(parent)
