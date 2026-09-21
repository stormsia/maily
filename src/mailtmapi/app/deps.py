from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from ..providers.registry import ProviderRegistry
from ..settings import Settings


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_registry(request: Request) -> ProviderRegistry:
    return request.app.state.registry


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    factory = request.app.state.session_factory
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def require_api_key(
    request: Request,
    x_api_key: Annotated[str | None, Header()] = None,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    expected: str = request.app.state.settings.api_key
    if not expected:
        return
    provided = x_api_key
    if not provided and authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()
    if not provided or not secrets.compare_digest(provided, expected):
        raise HTTPException(status_code=401, detail="invalid api key")


SettingsDep = Annotated[Settings, Depends(get_settings)]
RegistryDep = Annotated[ProviderRegistry, Depends(get_registry)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]  # type: ignore[assignment]
