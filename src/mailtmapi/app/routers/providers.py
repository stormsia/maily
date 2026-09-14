from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..deps import RegistryDep, require_api_key
from ..schemas import ProviderOut, TargetOut

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])


@router.get("/providers", response_model=list[ProviderOut])
async def list_providers(registry: RegistryDep) -> list[ProviderOut]:
    return [ProviderOut(slug=p.slug, kind=p.kind) for p in registry.all()]


@router.get("/targets", response_model=list[TargetOut])
async def list_targets(
    registry: RegistryDep,
    provider: str | None = Query(None),
) -> list[TargetOut]:
    providers = [registry.get(provider)] if provider else registry.all()
    out: list[TargetOut] = []
    for p in providers:
        for t in await p.list_targets():
            out.append(TargetOut(id=t.id, kind=t.kind, provider=t.provider, label=t.label))
    return out
