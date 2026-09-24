from __future__ import annotations

import httpx
import pytest

from mailtmapi.exceptions import MailConflictError, MailServerError, MailValidationError
from mailtmapi.http import HttpClient


def _client(handler) -> HttpClient:
    http = HttpClient.__new__(HttpClient)
    http._client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return http


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("status", "exc_type"),
    [(422, MailValidationError), (409, MailConflictError)],
)
async def test_request_maps_422_and_409(status, exc_type):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"detail": "nope"})

    http = _client(handler)
    try:
        with pytest.raises(exc_type) as raised:
            await http.request("GET", "https://api.example/x")
        assert raised.value.status_code == status
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_non_json_error_detail_is_capped():
    page = "<html>" + ("x" * 500) + "</html>"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text=page)

    http = _client(handler)
    try:
        with pytest.raises(MailServerError) as raised:
            await http.request("GET", "https://api.example/x")
        assert len(str(raised.value)) == 300
    finally:
        await http.close()


@pytest.mark.asyncio
async def test_client_does_not_follow_redirects():
    http = HttpClient()
    try:
        assert http._client.follow_redirects is False
    finally:
        await http.close()
