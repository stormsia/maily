from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ..deps import RegistryDep, SessionDep, SettingsDep, require_api_key
from ..schemas import ProviderOut, TargetOut
from ..services import domain_cache as dc

router = APIRouter(prefix="/v1", dependencies=[Depends(require_api_key)])


@router.get("/providers", response_model=list[ProviderOut])
async def list_providers(registry: RegistryDep) -> list[ProviderOut]:
    return [ProviderOut(slug=p.slug, kind=p.kind) for p in registry.all()]


@router.get("/targets", response_model=list[TargetOut])
async def list_targets(
    session: SessionDep,
    settings: SettingsDep,
    registry: RegistryDep,
    provider: str | None = Query(None),
) -> list[TargetOut]:
    providers = [registry.get(provider)] if provider else registry.all()
    out: list[TargetOut] = []
    for p in providers:
        if p.kind == "domain":
            targets = await dc.list_domain_targets(session, registry, settings, provider=p.slug)
        else:
            targets = await p.list_targets()
        for t in targets:
            out.append(TargetOut(id=t.id, kind=t.kind, provider=t.provider, label=t.label))
    await session.commit()
    return out
