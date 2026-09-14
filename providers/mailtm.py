"""
mail.tm provider implementation.

API docs: https://docs.mail.tm/

Features:
  - Connection-pooled aiohttp via AsyncHTTPSession
  - In-memory domain cache with configurable TTL (avoids redundant calls)
  - All mutating / fetching methods decorated with @async_retry
  - Full async context manager support
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ..core.base_provider import MailProvider
from ..core.http import AsyncHTTPSession
from ..schemas.account import Account, Token
from ..schemas.domains import Domain, Domains
from ..schemas.message import Messages, OneMessage, MessageSource
from ..utils.retry import async_retry

logger = logging.getLogger(__name__)

# Seconds before the cached domain list is considered stale
_DOMAIN_CACHE_TTL: float = 300.0


class MailTMProvider(MailProvider):
    """
    Concrete ``MailProvider`` implementation for https://api.mail.tm.

    All network calls go through ``AsyncHTTPSession`` which handles
    connection pooling, timeouts, and error-code mapping.
    """

    API_URL: str = "https://api.mail.tm"

    def __init__(
        self,
        *,
        session: AsyncHTTPSession | None = None,
        proxy: str | None = None,
        ssl: bool = False,
        domain_cache_ttl: float = _DOMAIN_CACHE_TTL,
    ) -> None:
        self._http = session or AsyncHTTPSession(proxy=proxy, ssl=ssl)
        self._domain_cache_ttl = domain_cache_ttl

        # Domain cache — guarded by an asyncio.Lock to prevent stampedes
        self._domain_cache: list[Domain] = []
        self._domain_cache_at: float = 0.0
        self._domain_lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Provider identity
    # ------------------------------------------------------------------

    @property
    def provider_name(self) -> str:
        return "mail.tm"

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def close(self) -> None:
        await self._http.close()

    # ------------------------------------------------------------------
    # Domains (with in-memory TTL cache)
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3)
    async def get_domains(self) -> list[Domain]:
        """Return active domains, using a local cache to reduce API calls."""
        from ..db.models import DomainRecord
        import datetime
        now = datetime.datetime.utcnow()
        async with self._domain_lock:
            latest = DomainRecord.select().where(DomainRecord.provider == self.provider_name).order_by(DomainRecord.cached_at.desc()).first()
            if latest and (now - latest.cached_at).total_seconds() < self._domain_cache_ttl:
                records = list(DomainRecord.select().where(DomainRecord.provider == self.provider_name))
                if records:
                    logger.debug(
                        "Domain cache hit from DB (%d domains)",
                        len(records),
                    )
                    return [
                        Domain(id=r.api_id or r.domain, domain=r.domain, isActive=r.is_active, isPrivate=r.is_private)
                        for r in records
                    ]

            response = await self._http.get(f"{self.API_URL}/domains")
            data = await response.json()
            parsed = Domains(**data)
            
            DomainRecord.delete().where(DomainRecord.provider == self.provider_name).execute()
            for d in parsed.hydra_member:
                DomainRecord.create(
                    provider=self.provider_name,
                    api_id=d.id,
                    domain=d.domain,
                    is_active=d.isActive,
                    is_private=d.isPrivate,
                    cached_at=now
                )
            logger.debug("Domain cache refreshed in DB: %d domains", len(parsed.hydra_member))
            return parsed.hydra_member

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3)
    async def get_account_token(self, address: str, password: str) -> Token:
        response = await self._http.post(
            f"{self.API_URL}/token",
            json={"address": address, "password": password},
        )
        return Token(**(await response.json()))

    # ------------------------------------------------------------------
    # Account CRUD
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3)
    async def create_account(self, address: str, password: str) -> Account:
        response = await self._http.post(
            f"{self.API_URL}/accounts",
            json={"address": address, "password": password},
        )
        data: dict[str, Any] = await response.json()
        # Fetch token in the same method to return a fully populated Account
        token = await self.get_account_token(address=address, password=password)
        data["token"] = token
        data["password"] = password
        return Account(**data)

    @async_retry(max_attempts=3)
    async def get_account_by_id(self, account_id: str, token: str) -> Account:
        response = await self._http.get(
            f"{self.API_URL}/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        data: dict[str, Any] = await response.json()
        if "token" not in data:
            data["token"] = Token(id=account_id, token=token)
        return Account(**data)

    @async_retry(max_attempts=3)
    async def delete_account(self, account_id: str, token: str) -> bool:
        response = await self._http.delete(
            f"{self.API_URL}/accounts/{account_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.status == 204

    @async_retry(max_attempts=3)
    async def get_me(self, token: str) -> Account:
        response = await self._http.get(
            f"{self.API_URL}/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        data: dict[str, Any] = await response.json()
        if "token" not in data:
            data["token"] = Token(id=data["id"], token=token)
        return Account(**data)

    # ------------------------------------------------------------------
    # Messages
    # ------------------------------------------------------------------

    @async_retry(max_attempts=3)
    async def get_messages(self, token: str, page: int = 1) -> Messages:
        response = await self._http.get(
            f"{self.API_URL}/messages",
            params={"page": page},
            headers={"Authorization": f"Bearer {token}"},
        )
        return Messages(**(await response.json()))

    @async_retry(max_attempts=3)
    async def get_message_by_id(self, message_id: str, token: str) -> OneMessage:
        response = await self._http.get(
            f"{self.API_URL}/messages/{message_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        return OneMessage(**(await response.json()))

    @async_retry(max_attempts=3)
    async def delete_message(self, message_id: str, token: str) -> bool:
        response = await self._http.delete(
            f"{self.API_URL}/messages/{message_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        return response.status == 204

    @async_retry(max_attempts=3)
    async def mark_message_read(self, message_id: str, token: str) -> bool:
        """
        Mark a message as seen using PATCH.
        """
        response = await self._http.patch(
            f"{self.API_URL}/messages/{message_id}",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/merge-patch+json"},
            json={"seen": True},
        )
        data = await response.json()
        return data.get("seen") is True

    @async_retry(max_attempts=3)
    async def get_message_source(self, message_id: str, token: str) -> MessageSource:
        response = await self._http.get(
            f"{self.API_URL}/sources/{message_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        html_content = await response.text()
        return MessageSource(
            id=message_id,
            downloadUrl=f"{self.API_URL}/sources/{message_id}",
            data=html_content,
        )
