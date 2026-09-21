from __future__ import annotations

import asyncio
import json
import logging
from contextlib import suppress

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker as AsyncSessionFactory

from ...db.models import AppSetting, DomainCache
from ...exceptions import MailValidationError
from ...providers.base import Target
from ...providers.registry import ProviderRegistry
from ...settings import Settings

logger = logging.getLogger("mailtmapi.domain_cache")

_KEY_ENABLED = "domain_cache.enabled"
_KEY_INTERVAL = "domain_cache.interval_seconds"


def _parse_domains(row: DomainCache | None) -> list[str]:
    if row is None or not row.domains_json:
        return []
    try:
        domains = json.loads(row.domains_json)
    except ValueError:
        return []
    return [d for d in domains if isinstance(d, str)]


async def get_settings(session, settings: Settings) -> dict:
    enabled = settings.domain_cache_enabled
    interval_seconds = settings.domain_cache_interval_seconds
    row = await session.get(AppSetting, _KEY_ENABLED)
    if row is not None:
        enabled = row.value == "1"
    row = await session.get(AppSetting, _KEY_INTERVAL)
    if row is not None:
        with suppress(ValueError):
            interval_seconds = int(row.value)
    return {"enabled": enabled, "interval_seconds": interval_seconds}


async def set_settings(
    session,
    settings: Settings,
    *,
    enabled: bool | None,
    interval_seconds: int | None,
) -> dict:
    if interval_seconds is not None and interval_seconds < 60:
        raise MailValidationError("interval_seconds must be >= 60")
    if enabled is None and interval_seconds is None:
        raise MailValidationError("at least one of enabled/interval_seconds is required")
    if enabled is not None:
        row = await session.get(AppSetting, _KEY_ENABLED)
        if row is None:
            row = AppSetting(key=_KEY_ENABLED)
            session.add(row)
        row.value = "1" if enabled else "0"
    if interval_seconds is not None:
        row = await session.get(AppSetting, _KEY_INTERVAL)
        if row is None:
            row = AppSetting(key=_KEY_INTERVAL)
            session.add(row)
        row.value = str(interval_seconds)
    await session.flush()
    return await get_settings(session, settings)


async def _store(session, slug: str, targets: list[Target]) -> None:
    row = await session.get(DomainCache, slug)
    if row is None:
        row = DomainCache(provider=slug, domains_json="")
        session.add(row)
    row.domains_json = json.dumps([t.label for t in targets])
    row.error = None


async def list_domain_targets(
    session,
    registry: ProviderRegistry,
    settings: Settings,
    provider: str | None = None,
) -> list[Target]:
    providers = [registry.get(provider)] if provider else registry.all()
    cfg = await get_settings(session, settings)
    out: list[Target] = []
    for p in providers:
        if p.kind != "domain":
            out.extend(await p.list_targets())
            continue
        row = None
        if cfg["enabled"]:
            row = await session.get(DomainCache, p.slug)
        if row and row.domains_json:
            for d in _parse_domains(row):
                out.append(Target(id=d, kind="domain", provider=p.slug, label=d))
        else:
            targets = await p.list_targets()
            if cfg["enabled"]:
                await _store(session, p.slug, targets)
            out.extend(targets)
    return out


async def refresh_cache(factory: AsyncSessionFactory[AsyncSession], registry: ProviderRegistry) -> dict:
    refreshed: list[str] = []
    failed: list[str] = []
    async with factory() as session:
        for p in registry.all():
            if p.kind != "domain":
                continue
            try:
                targets = await p.list_targets()
                await _store(session, p.slug, targets)
                refreshed.append(p.slug)
            except Exception as exc:  # noqa: BLE001 - keep old domains, report error
                failed.append(p.slug)
                logger.warning("domain cache: refresh failed for %s: %s", p.slug, exc)
                row = await session.get(DomainCache, p.slug)
                if row is None:
                    row = DomainCache(provider=p.slug, domains_json="")
                    session.add(row)
                row.error = str(exc)
        await session.commit()
    return {"refreshed": refreshed, "failed": failed}


async def cache_status(session, registry: ProviderRegistry, settings: Settings) -> list[dict]:
    rows = {r.provider: r for r in (await session.execute(select(DomainCache))).scalars()}
    by_provider: dict[str, dict] = {}
    for p in registry.all():
        if p.kind != "domain":
            continue
        row = rows.get(p.slug)
        by_provider[p.slug] = {
            "provider": p.slug,
            "kind": p.kind,
            "domains_count": len(_parse_domains(row)),
            "updated_at": row.updated_at if row else None,
            "error": row.error if row else None,
        }
    for slug, row in rows.items():
        if slug in by_provider:
            continue
        by_provider[slug] = {
            "provider": slug,
            "kind": "domain",
            "domains_count": len(_parse_domains(row)),
            "updated_at": row.updated_at,
            "error": row.error,
        }
    return [by_provider[slug] for slug in sorted(by_provider)]


async def find_provider_for_domain(
    session,
    registry: ProviderRegistry,
    settings: Settings,
    domain: str,
) -> str | None:
    cfg = await get_settings(session, settings)
    if cfg["enabled"]:
        for p in registry.all():
            if p.kind != "domain":
                continue
            row = await session.get(DomainCache, p.slug)
            if row and row.domains_json and domain.lower() in {d.lower() for d in _parse_domains(row)}:
                return p.slug
    for p in registry.all():
        for t in await p.list_targets():
            if t.label.lower() == domain.lower():
                return p.slug
    return None


async def domain_cache_worker(
    factory: AsyncSessionFactory[AsyncSession],
    registry: ProviderRegistry,
    settings: Settings,
) -> None:
    while True:
        interval = settings.domain_cache_interval_seconds
        try:
            async with factory() as session:
                cfg = await get_settings(session, settings)
            interval = cfg["interval_seconds"]
            if cfg["enabled"]:
                await refresh_cache(factory, registry)
        except Exception:  # noqa: BLE001 - worker must never die
            logger.exception("domain cache refresh failed")
        await asyncio.sleep(interval)
