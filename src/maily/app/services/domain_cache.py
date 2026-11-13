from __future__ import annotations

import asyncio
import json
import time
from contextlib import suppress
from datetime import datetime, timedelta, timezone

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker as AsyncSessionFactory

from ...db.engine import retry_on_lock
from ...db.models import AppSetting, DomainCache
from ...exceptions import MailValidationError
from ...providers.base import Target
from ...providers.registry import ProviderRegistry
from ...settings import Settings

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


def _utcnow_naive() -> datetime:
    """UTC now without tzinfo, matching what func.now() (CURRENT_TIMESTAMP) stores."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _as_naive_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(timezone.utc).replace(tzinfo=None)


def _fresh_domains(row: DomainCache | None, interval_seconds: int) -> list[str]:
    """Domains from a row still young enough to serve.

    A failed refresh keeps the previous list and stamps ``updated_at``, so age
    is the only signal that a stored list has gone stale. Rows older than
    ``2 * interval_seconds`` stay in the table but are not served.
    """
    domains = _parse_domains(row)
    if not domains or row is None or row.updated_at is None:
        return []
    age = _utcnow_naive() - _as_naive_utc(row.updated_at)
    if age > timedelta(seconds=2 * interval_seconds):
        return []
    return domains


def _labels(targets: list[Target]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for t in targets:
        label = (t.label or "").strip().lower()
        if label and label not in seen:
            seen.add(label)
            out.append(label)
    return out


async def _store(session, slug: str, targets: list[Target]) -> None:
    row = await session.get(DomainCache, slug)
    if row is None:
        row = DomainCache(provider=slug, domains_json="")
        session.add(row)
    # Full replace: domains the provider no longer returns are dropped.
    row.domains_json = json.dumps(_labels(targets))
    row.error = None
    # Force a timestamp bump even when the domain list didn't change — the
    # column's onupdate only fires on an actual UPDATE, and identical data
    # would otherwise keep a stale "last refresh" forever.
    row.updated_at = _utcnow_naive()


async def _store_committed(
    factory: AsyncSessionFactory[AsyncSession], slug: str, targets: list[Target]
) -> None:
    """Persist one provider's domains in a short transaction (no long-running
    write lock across other providers / HTTP fetches)."""

    async def _do() -> None:
        async with factory() as session:
            await _store(session, slug, targets)
            await session.commit()

    await retry_on_lock(_do)


async def _record_failure_committed(
    factory: AsyncSessionFactory[AsyncSession], slug: str, error: str
) -> None:
    async def _do() -> None:
        async with factory() as session:
            row = await session.get(DomainCache, slug)
            if row is None:
                row = DomainCache(provider=slug, domains_json="")
                session.add(row)
            row.error = error
            # Record the failed attempt so monitoring sees a recent date.
            row.updated_at = _utcnow_naive()
            await session.commit()

    await retry_on_lock(_do)


async def list_domain_targets(
    session,
    registry: ProviderRegistry,
    settings: Settings,
    provider: str | None = None,
) -> list[Target]:
    providers = [registry.get(provider)] if provider else registry.all()
    cfg = await get_settings(session, settings)
    # Read the cache, then drop the transaction before any provider HTTP.
    cached: dict[str, list[str]] = {}
    misses: list = []
    out: list[Target] = []
    for p in providers:
        if p.kind != "domain":
            misses.append(p)
            continue
        row = await session.get(DomainCache, p.slug) if cfg["enabled"] else None
        stored = _parse_domains(row)
        domains = _fresh_domains(row, cfg["interval_seconds"])
        if domains:
            cached[p.slug] = domains
        elif stored:
            # Stale lists stay stored and are not served or replaced here.
            continue
        else:
            misses.append(p)
    await session.commit()
    for slug, domains in cached.items():
        for d in domains:
            out.append(Target(id=d, kind="domain", provider=slug, label=d))
    for p in misses:
        targets = await p.list_targets()
        if p.kind == "domain" and cfg["enabled"]:
            await _store(session, p.slug, targets)
        out.extend(targets)
    return out


async def refresh_cache(
    factory: AsyncSessionFactory[AsyncSession],
    registry: ProviderRegistry,
    skip: set[str] | None = None,
) -> dict:
    """Refresh every domain provider into its own short transaction.

    Each provider's row is committed separately and its HTTP fetch happens with
    no DB transaction open — so the worker never holds the SQLite write lock
    across network I/O, which is what kept failing other writers with
    "database is locked".
    """
    refreshed: list[str] = []
    failed: list[str] = []
    for p in registry.all():
        if p.kind != "domain":
            continue
        if skip and p.slug in skip:
            continue
        try:
            # Bypass the adapter's in-memory TTL: a refresh must hit the provider.
            targets = await p.list_targets(fresh=True)
            await _store_committed(factory, p.slug, targets)
            refreshed.append(p.slug)
        except Exception as exc:  # noqa: BLE001 - keep old domains, report error
            failed.append(p.slug)
            logger.warning(f"domain cache: refresh failed for {p.slug}: {exc}")
            try:
                await _record_failure_committed(factory, p.slug, str(exc))
            except Exception:  # noqa: BLE001
                logger.exception(f"domain cache: could not record failure for {p.slug}")
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
    # session.get autoflushes, which would persist the caller's pending writes
    # before this lookup has decided anything. Reads here don't depend on them.
    with session.no_autoflush:
        cfg = await get_settings(session, settings)
        wanted = domain.lower()
        domain_providers = [p for p in registry.all() if p.kind == "domain"]
        if cfg["enabled"]:
            for p in domain_providers:
                row = await session.get(DomainCache, p.slug)
                if wanted in {d.lower() for d in _fresh_domains(row, cfg["interval_seconds"])}:
                    return p.slug
    # Do not commit or roll back the caller's session. create_mailbox commits
    # before provider I/O; a rollback here would drop unrelated pending writes.
    # Fresh cache misses the domain, so scan live once. A hit already returned.
    for p in domain_providers:
        for t in await p.list_targets():
            if t.label.lower() == wanted:
                return p.slug
    return None


async def domain_cache_worker(
    factory: AsyncSessionFactory[AsyncSession],
    registry: ProviderRegistry,
    settings: Settings,
) -> None:
    # Back off providers that keep failing (e.g. SSL issues): skip re-touching
    # them for an hour so the worker doesn't hammer a dead endpoint every run.
    backoff_until: dict[str, float] = {}
    while True:
        interval = settings.domain_cache_interval_seconds
        try:
            async with factory() as session:
                cfg = await get_settings(session, settings)
            interval = cfg["interval_seconds"]
            if cfg["enabled"]:
                now = time.time()
                backoff_until = {slug: ts for slug, ts in backoff_until.items() if ts > now}
                result = await refresh_cache(factory, registry, skip=set(backoff_until))
                for slug in result["failed"]:
                    backoff_until[slug] = now + 3600
        except Exception:  # noqa: BLE001 - worker must never die
            logger.exception("domain cache refresh failed")
        await asyncio.sleep(interval)
