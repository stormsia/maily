from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from ..exceptions import (
    MailAPIError,
    MailAuthError,
    MailConflictError,
    MailNotFoundError,
    MailRateLimitError,
    MailValidationError,
)


def _json(status: int, detail: str, headers: dict[str, str] | None = None) -> JSONResponse:
    return JSONResponse({"detail": detail}, status_code=status, headers=headers)


def register_errors(app: FastAPI) -> None:
    @app.exception_handler(MailNotFoundError)
    async def _not_found(_req: Request, exc: MailNotFoundError) -> JSONResponse:
        return _json(404, str(exc))

    @app.exception_handler(MailValidationError)
    async def _bad(_req: Request, exc: MailValidationError) -> JSONResponse:
        return _json(400, str(exc))

    @app.exception_handler(MailAuthError)
    async def _auth(_req: Request, exc: MailAuthError) -> JSONResponse:
        # 401 collides with the API-key check; the header lets the UI tell
        # "Google rejected the account token" apart from "server needs a key".
        return _json(
            401,
            str(exc),
            headers={"X-MailTM-Error": "provider_auth"},
        )

    @app.exception_handler(MailConflictError)
    async def _conflict(_req: Request, exc: MailConflictError) -> JSONResponse:
        return _json(409, str(exc))

    @app.exception_handler(MailRateLimitError)
    async def _rate(_req: Request, exc: MailRateLimitError) -> JSONResponse:
        return _json(429, str(exc))

    @app.exception_handler(MailAPIError)
    async def _api(_req: Request, exc: MailAPIError) -> JSONResponse:
        return _json(502, str(exc))

    @app.exception_handler(KeyError)
    async def _key(_req: Request, exc: KeyError) -> JSONResponse:
        return _json(404, str(exc).strip("'\""))
