import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Request
from sqlalchemy import select

from ...db.models import DomainCache
from ..deps import RegistryDep, SessionDep

_ERROR_MAX = 160


def _safe_error(raw: str | None) -> str | None:
    """Short, single-line provider error for the public health payload.

    Refresh failures can echo an upstream URL or response body; the dashboard
    banner only needs to know that a refresh failed, not the raw text.
    """
    if not raw:
        return None
    text = " ".join(raw.split())
    if len(text) <= _ERROR_MAX:
        return text
    return text[: _ERROR_MAX - 1] + "…"


def _iso_utc(dt: datetime | None) -> str | None:
    """Naive-UTC datetime as ISO-8601 with an explicit Z (this is a plain dict
    response, so the schema-level serializer does not apply here)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


router = APIRouter(tags=["System"])


@router.get("/health")
async def health(session: SessionDep, registry: RegistryDep) -> dict:
    """Brief liveness + degradation view for monitoring.

    `status` mirrors the previous shape; `domain_cache` reports per-provider
    last refresh time, cached domain count and the latest refresh error.
    """
    cache: dict[str, dict] = {}
    rows = (await session.execute(select(DomainCache))).scalars().all()
    for row in rows:
        cache[row.provider] = {
            "last_refresh": _iso_utc(row.updated_at) if row.updated_at else None,
            "domains": _json_len(row.domains_json),
            "error": _safe_error(row.error),
        }
    providers: dict[str, dict] = {}
    for provider in registry.all():
        if provider.kind == "domain":
            providers[provider.slug] = cache.get(
                provider.slug,
                {"last_refresh": None, "domains": 0, "error": None},
            )
    return {"status": "ok", "domain_cache": providers}


def _json_len(raw: str) -> int:
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return 0
    return len(data) if isinstance(data, list) else 0


@router.get("/v1/config")
async def config(request: Request) -> dict[str, Any]:
    """Non-secret server facts for the dashboard and the standalone client.

    This router is auth-free: `client_version` lets a pip-installed client
    detect it should run `python -m client update`.
    """
    from ... import __version__

    return {
        "api_key_required": bool(request.app.state.settings.api_key),
        "client_version": __version__,
    }
