"""UI-managed server config stored in app_settings (key/value).

Gmail OAuth credentials can be provided via env (MAILTM_GMAIL_CLIENT_ID/SECRET
or credentials file) or, alternatively, saved from the admin dashboard. When
env credentials exist they win; the dashboard reports them as read-only
(source="env"). The client secret is stored encrypted with the server secret.
"""
from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...crypto import decrypt, encrypt
from ...db.models import AppSetting

KEY_CLIENT_ID = "gmail.client_id"
KEY_CLIENT_SECRET = "gmail.client_secret"
KEY_REDIRECT_URI = "gmail.redirect_uri"


async def get_creds(session: AsyncSession, secret: str) -> tuple[str, str] | None:
    rows = {
        r.key: r.value
        for r in (
            await session.execute(select(AppSetting).where(AppSetting.key.in_([KEY_CLIENT_ID, KEY_CLIENT_SECRET])))
        ).scalars()
    }
    cid, csec_enc = rows.get(KEY_CLIENT_ID) or "", rows.get(KEY_CLIENT_SECRET) or ""
    if not cid or not csec_enc:
        return None
    try:
        csec = decrypt(secret, csec_enc)
    except ValueError:
        return None
    return cid, csec


async def save_creds(
    session: AsyncSession, secret: str, client_id: str, client_secret: str, redirect_uri: str | None = None
) -> None:
    for key, value in (
        (KEY_CLIENT_ID, client_id),
        (KEY_CLIENT_SECRET, encrypt(secret, client_secret)),
        (KEY_REDIRECT_URI, redirect_uri or ""),
    ):
        row = await session.get(AppSetting, key)
        if row is None:
            session.add(AppSetting(key=key, value=value))
        else:
            row.value = value


async def clear_creds(session: AsyncSession) -> None:
    await session.execute(delete(AppSetting).where(AppSetting.key.in_([KEY_CLIENT_ID, KEY_CLIENT_SECRET, KEY_REDIRECT_URI])))


async def get_redirect_uri(session: AsyncSession, default: str) -> str:
    row = await session.get(AppSetting, KEY_REDIRECT_URI)
    return (row.value if row and row.value else default) or default


async def resolved(settings, session: AsyncSession, secret: str) -> tuple[str, str, str] | None:
    """(client_id, client_secret, source) — env wins over dashboard-stored creds."""
    try:
        cid, csec = settings.gmail_client()
        return cid, csec, "env"
    except RuntimeError:
        creds = await get_creds(session, secret)
        if creds:
            return creds[0], creds[1], "db"
    return None
