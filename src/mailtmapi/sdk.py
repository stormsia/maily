"""Async httpx SDK for the mailtmapi service API."""
from __future__ import annotations

import asyncio
import time
from typing import Any, Callable
from urllib.parse import quote

import httpx

from .exceptions import MailAPIError, MailNotFoundError


class MailTMAPI:
    """Minimal async client for the mailtmapi HTTP API. Use as ``async with``."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8477",
        api_key: str = "",
        timeout: float = 30.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._client = client or httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout)
        self._owns_client = client is None
        self._headers = {"X-API-Key": api_key} if api_key else {}

    async def __aenter__(self) -> "MailTMAPI":
        return self

    async def __aexit__(self, *_exc: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        resp = await self._client.request(method, path, headers=self._headers, **kwargs)
        if resp.status_code >= 400:
            detail = ""
            try:
                body = resp.json()
                if isinstance(body, dict):
                    detail = str(body.get("detail") or body)
            except Exception:
                detail = resp.text
            raise MailAPIError(detail or f"HTTP {resp.status_code}", status_code=resp.status_code)
        return {} if resp.status_code == 204 else resp.json()

    # --- mailboxes ---

    async def create_mailbox(
        self,
        *,
        provider: str | None = None,
        domain: str | None = None,
        parent_id: int | None = None,
        address: str | None = None,
        password: str | None = None,
    ) -> dict:
        payload = {
            k: v
            for k, v in {
                "provider": provider,
                "domain": domain,
                "parent_id": parent_id,
                "address": address,
                "password": password,
            }.items()
            if v is not None
        }
        return await self._request("POST", "/v1/mailboxes", json=payload)

    async def list_mailboxes(self, provider: str | None = None, active: bool = True) -> list:
        params: dict[str, Any] = {"active": str(active).lower()}
        if provider:
            params["provider"] = provider
        return await self._request("GET", "/v1/mailboxes", params=params)

    async def mailbox(self, mailbox_id: int) -> dict:
        return await self._request("GET", f"/v1/mailboxes/{mailbox_id}")

    async def mailbox_by_address(self, email: str) -> dict:
        return await self._request("GET", f"/v1/mailboxes/by-address/{quote(email)}")

    async def delete_mailbox(self, mailbox_id: int) -> None:
        await self._request("DELETE", f"/v1/mailboxes/{mailbox_id}")

    # --- messages ---

    async def list_messages(self, mailbox_id: int, page: int = 1) -> list:
        return await self._request(
            "GET", f"/v1/mailboxes/{mailbox_id}/messages", params={"page": page}
        )

    async def get_message(self, mailbox_id: int, message_id: str) -> dict:
        return await self._request("GET", f"/v1/mailboxes/{mailbox_id}/messages/{message_id}")

    async def mark_read(self, mailbox_id: int, message_id: str) -> dict:
        return await self._request(
            "POST", f"/v1/mailboxes/{mailbox_id}/messages/{message_id}/read"
        )

    async def delete_message(self, mailbox_id: int, message_id: str) -> None:
        await self._request("DELETE", f"/v1/mailboxes/{mailbox_id}/messages/{message_id}")

    async def get_source(self, mailbox_id: int, message_id: str) -> dict:
        return await self._request(
            "GET", f"/v1/mailboxes/{mailbox_id}/messages/{message_id}/source"
        )

    # --- gmail accounts ---

    async def gmail_oauth_start(self) -> dict:
        return await self._request("POST", "/v1/gmail/oauth/start")

    async def gmail_import_account(
        self, *, refresh_token: str | None = None, token_json: Any = None
    ) -> dict:
        payload: dict[str, Any] = {}
        if refresh_token:
            payload["refresh_token"] = refresh_token
        if token_json is not None:
            payload["token_json"] = token_json
        return await self._request("POST", "/v1/gmail/accounts/import", json=payload)

    async def list_gmail_accounts(self) -> list:
        return await self._request("GET", "/v1/gmail/accounts")

    async def delete_gmail_account(self, parent_id: int) -> None:
        await self._request("DELETE", f"/v1/gmail/accounts/{parent_id}")

    async def sync_gmail_account(self, parent_id: int) -> dict:
        return await self._request("POST", f"/v1/gmail/accounts/{parent_id}/sync")

    # --- polling ---

    async def wait_for_message(
        self,
        mailbox_id: int,
        *,
        timeout: float = 120.0,
        interval: float = 2.0,
        predicate: Callable[[dict], bool] | None = None,
    ) -> dict:
        """Poll list_messages until a message matches; default: any message."""
        deadline = time.monotonic() + timeout
        while True:
            messages = await self.list_messages(mailbox_id)
            hit = next((m for m in messages if predicate(m)), None) if predicate else (messages[0] if messages else None)
            if hit is not None:
                return hit
            if time.monotonic() >= deadline:
                raise MailNotFoundError(f"no message arrived within {timeout}s")
            await asyncio.sleep(interval)