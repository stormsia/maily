from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from ...providers.base import MailProvider, Target
from ..authz import PrincipalDep, parent_allowed, provider_allowed, require_principal
from ..deps import RegistryDep, SessionDep, SettingsDep
from ..schemas import ProviderOut, TargetOut
from ..services import domain_cache as dc

router = APIRouter(prefix="/v1", dependencies=[Depends(require_principal)], tags=["Providers"])


@router.get("/providers", response_model=list[ProviderOut])
async def list_providers(registry: RegistryDep, principal: PrincipalDep) -> list[ProviderOut]:
    """List enabled providers and their kind (api/token or domain-based)."""
    return [
        ProviderOut(slug=p.slug, kind=p.kind)
        for p in registry.all()
        if provider_allowed(principal, p.slug)
    ]


def _visible_providers(registry: RegistryDep, principal: PrincipalDep, slug: str | None) -> list[MailProvider]:
    if slug is not None:
        return [registry.get(slug)] if provider_allowed(principal, slug) else []
    return [provider for provider in registry.all() if provider_allowed(principal, provider.slug)]


def _parent_visible(principal: PrincipalDep, target: Target) -> bool:
    if principal.is_root or target.kind != "parent":
        return True
    parent_id = int(target.id)
    if parent_allowed(principal, parent_id):
        return True
    key = principal.key
    return key is not None and target.owner_key_id == key.id


@router.get("/targets", response_model=list[TargetOut])
async def list_targets(
    session: SessionDep,
    settings: SettingsDep,
    registry: RegistryDep,
    principal: PrincipalDep,
    provider: str | None = Query(None),
) -> list[TargetOut]:
    """List usable posting targets, optionally filtered by provider slug."""
    out: list[TargetOut] = []
    for p in _visible_providers(registry, principal, provider):
        if p.kind == "domain":
            targets = await dc.list_domain_targets(session, registry, settings, provider=p.slug)
        else:
            targets = await p.list_targets()
        for t in targets:
            if _parent_visible(principal, t):
                out.append(TargetOut(id=t.id, kind=t.kind, provider=t.provider, label=t.label))
    await session.commit()
    return out
