import json

from fastapi import APIRouter, Request
from sqlalchemy import select

from ...db.models import DomainCache
from ..deps import RegistryDep, SessionDep

router = APIRouter()


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
            "last_refresh": row.updated_at.isoformat() if row.updated_at else None,
            "domains": _json_len(row.domains_json),
            "error": row.error,
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
async def config(request: Request) -> dict[str, bool]:
    """Non-secret server facts for the dashboard (this router is auth-free)."""
    return {"api_key_required": bool(request.app.state.settings.api_key)}
