from __future__ import annotations

import json
import time
import urllib.parse
from typing import Any

from maily.exceptions import MailAPIError, MailAuthError, MailValidationError
from maily.http import HttpClient

SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.settings.basic",
]
TOKEN_URI = "https://oauth2.googleapis.com/token"
AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"

_FORM = {"Content-Type": "application/x-www-form-urlencoded"}
_AUTH_TOKEN_ERRORS = frozenset({"invalid_grant", "invalid_client", "unauthorized_client"})


def _raise_token_auth(body: dict[str, Any]) -> None:
    error = body.get("error")
    if not isinstance(error, str) or error not in _AUTH_TOKEN_ERRORS:
        return
    description = body.get("error_description")
    message = description if isinstance(description, str) and description else error
    raise MailAuthError(message, response_data=body)


class GmailOAuth:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        http: HttpClient,
        token_uri: str = TOKEN_URI,
        auth_uri: str = AUTH_URI,
        scopes: list[str] = SCOPES,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._http = http
        self._token_uri = token_uri
        self._auth_uri = auth_uri
        self._scopes = list(scopes)

    def configure(self, client_id: str, client_secret: str) -> None:
        """Swap credentials in place (used when creds are set from the admin UI)."""
        self._client_id = client_id
        self._client_secret = client_secret

    def auth_url(self, redirect_uri: str, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(self._scopes),
            "state": state,
            "access_type": "offline",
            "prompt": "consent",
        }
        return f"{self._auth_uri}?{urllib.parse.urlencode(params)}"

    async def exchange_code(self, code: str, redirect_uri: str) -> dict:
        return await self._token_post(
            {
                "code": code,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            }
        )

    async def refresh(self, refresh_token: str) -> dict:
        data = await self._token_post(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": self._client_id,
                "client_secret": self._client_secret,
            }
        )
        if not data.get("refresh_token"):
            data["refresh_token"] = refresh_token
        return data

    @staticmethod
    def parse_import(payload: dict | str) -> dict:
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise MailValidationError("invalid token JSON") from exc
        if not isinstance(payload, dict):
            raise MailValidationError("invalid token payload")
        data = {k: v for k, v in payload.items() if k not in ("installed", "web")}
        refresh = data.get("refresh_token")
        if not refresh:
            raise MailValidationError("missing refresh_token")
        return {
            "access_token": data.get("access_token"),
            "refresh_token": refresh,
            "expires_at": data.get("expires_at"),
            "scopes": data.get("scope") or data.get("scopes") or "",
        }

    async def _token_post(self, payload: dict[str, str]) -> dict:
        try:
            resp = await self._http.post(
                self._token_uri,
                content=urllib.parse.urlencode(payload).encode(),
                headers=_FORM,
            )
        except MailAuthError:
            raise
        except MailAPIError as exc:
            _raise_token_auth(exc.response_data)
            raise
        data: dict[str, Any] = resp.json()
        _raise_token_auth(data)
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
            "expires_at": time.time() + int(data.get("expires_in", 0)),
            "scopes": data.get("scope", ""),
        }
