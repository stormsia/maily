from __future__ import annotations

import secrets
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from ..providers.registry import ProviderRegistry
from ..settings import Settings

api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API key (required only when the server runs with MAILTM_API_KEY set).",
)


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
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Security(api_key_header)] = None,
) -> None:
    expected: str = request.app.state.settings.api_key
    if not expected:
        return
    provided = x_api_key
    if not provided and authorization and authorization.lower().startswith("bearer "):
        provided = authorization[7:].strip()
    if not provided or not secrets.compare_digest(provided, expected):
        # Header lets the UI distinguish this 401 from a provider-auth 401
        # (Gmail token expired → MailAuthError) which must NOT trigger the
        # API-key prompt.
        raise HTTPException(
            status_code=401,
            detail="invalid api key",
            headers={"X-MailTM-Error": "api_key"},
        )


SettingsDep = Annotated[Settings, Depends(get_settings)]
RegistryDep = Annotated[ProviderRegistry, Depends(get_registry)]
SessionDep = Annotated[AsyncSession, Depends(get_session)]  # type: ignore[assignment]
