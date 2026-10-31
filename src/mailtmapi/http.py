from __future__ import annotations

from contextlib import suppress
from typing import Any

import httpx

from .exceptions import (
    MailAPIError,
    MailAuthError,
    MailConflictError,
    MailNotFoundError,
    MailRateLimitError,
    MailServerError,
    MailTimeoutError,
    MailValidationError,
)


def _raise_for_status(response: httpx.Response) -> None:
    if response.status_code < 400:
        return
    try:
        body = response.json()
        if not isinstance(body, dict):
            body = {"detail": str(body)}
    except Exception:
        body = {"detail": response.text[:300]}
    detail = (
        body.get("detail")
        or body.get("message")
        or body.get("hydra:description")
        or f"HTTP {response.status_code}"
    )
    code = response.status_code
    if code in (401, 403):
        raise MailAuthError(detail, status_code=code, response_data=body)
    if code == 404:
        raise MailNotFoundError(detail, status_code=code, response_data=body)
    if code == 429:
        retry_after = None
        raw = response.headers.get("Retry-After")
        if raw:
            with suppress(ValueError):
                retry_after = float(raw)
        raise MailRateLimitError(
            detail, retry_after=retry_after, status_code=code, response_data=body
        )
    if code == 409:
        raise MailConflictError(detail, status_code=code, response_data=body)
    if code == 422:
        raise MailValidationError(detail, status_code=code, response_data=body)
    if code >= 500:
        raise MailServerError(detail, status_code=code, response_data=body)
    raise MailAPIError(detail, status_code=code, response_data=body)


class HttpClient:
    def __init__(self, *, proxy: str | None = None, headers: dict[str, str] | None = None) -> None:
        self._client = httpx.AsyncClient(
            proxy=proxy or None,
            headers=headers,
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=False,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        try:
            response = await self._client.request(method, url, **kwargs)
        except httpx.TimeoutException as exc:
            raise MailTimeoutError(f"Request timed out: {method} {url}") from exc
        except httpx.ConnectError as exc:
            raise MailAPIError(f"Connection error for {method} {url}: {exc}") from exc
        _raise_for_status(response)
        return response

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("POST", url, **kwargs)

    async def patch(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("PATCH", url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self.request("DELETE", url, **kwargs)
