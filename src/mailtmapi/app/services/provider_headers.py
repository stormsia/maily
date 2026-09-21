from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker as AsyncSessionFactory

from ...db.models import ProviderHeaders
from ...http import HttpClient
from ...providers.registry import ProviderRegistry
from ...providers.tempmail_io.headers import build_headers, fetch_cors_header
from ...settings import Settings

logger = logging.getLogger("mailtmapi.provider_headers")

SLUG = "temp-mail.io"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _parse_json(value: str) -> dict[str, str]:
    try:
        data = json.loads(value)
    except ValueError:
        return {}
    return {str(k): str(v) for k, v in data.items()} if isinstance(data, dict) else {}


async def _load(session: AsyncSession, provider: str) -> dict[str, str] | None:
    row = await session.get(ProviderHeaders, provider)
    if row is None or not row.headers_json:
        return None
    return _parse_json(row.headers_json)


async def _save(
    session: AsyncSession, provider: str, headers: dict[str, str], error: str | None = None
) -> None:
    row = await session.get(ProviderHeaders, provider)
    if row is None:
        row = ProviderHeaders(provider=provider, headers_json="")
        session.add(row)
    row.headers_json = json.dumps(headers)
    row.error = error


async def _token_from_override(settings: Settings) -> str | None:
    if settings.tempmail_io_cors_header:
        return settings.tempmail_io_cors_header
    return None


async def refresh(
    factory: AsyncSessionFactory[AsyncSession],
    http: HttpClient,
    provider: str,
    settings: Settings,
    *,
    force: bool = False,
) -> dict[str, str]:
    """Return fresh cached headers for provider, fetching from the site if stale."""
    if provider != SLUG:
        return {}
    override = await _token_from_override(settings)
    if override:
        return build_headers(override)

    ttl = timedelta(seconds=settings.provider_headers_ttl_seconds)
    async with factory() as session:
        row = await session.get(ProviderHeaders, provider)
        if (
            not force
            and row is not None
            and row.headers_json
            and row.updated_at
            and _utcnow() - row.updated_at < ttl
        ):
            return _parse_json(row.headers_json)

        stale = _parse_json(row.headers_json) if row and row.headers_json else {}
        try:
            token = await fetch_cors_header(http, settings.tempmail_io_origin)
        except Exception as exc:  # noqa: BLE001 - keep last-known headers on network failure
            logger.warning("provider_headers: fetch failed for %s: %s", provider, exc)
            await _save(session, provider, stale, str(exc))
            await session.commit()
            return stale
        headers = build_headers(token)
        await _save(session, provider, headers, None if token else "no cors token found")
        await session.commit()
        return headers


def apply_headers(registry: ProviderRegistry, provider: str, headers: dict[str, str]) -> None:
    try:
        prov = registry.get(provider)
    except KeyError:
        return
    setter = getattr(prov, "set_headers", None)
    if setter:
        setter(headers)


async def bootstrap(
    factory: AsyncSessionFactory[AsyncSession],
    http: HttpClient,
    registry: ProviderRegistry,
    settings: Settings,
) -> None:
    headers = await refresh(factory, http, SLUG, settings)
    apply_headers(registry, SLUG, headers)


async def provider_headers_worker(
    factory: AsyncSessionFactory[AsyncSession],
    http: HttpClient,
    registry: ProviderRegistry,
    settings: Settings,
) -> None:
    while True:
        try:
            headers = await refresh(factory, http, SLUG, settings, force=True)
            apply_headers(registry, SLUG, headers)
        except Exception:  # noqa: BLE001 - worker must never die
            logger.exception("provider headers refresh failed")
        await asyncio.sleep(settings.provider_headers_ttl_seconds)
