from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from ..exceptions import (
    MailAPIError,
    MailAuthError,
    MailConflictError,
    MailNotFoundError,
    MailRateLimitError,
    MailValidationError,
)


def _json(
    status: int,
    detail: str,
    headers: dict[str, str] | None = None,
    code: str | None = None,
) -> JSONResponse:
    body: dict[str, str] = {"detail": detail}
    if code:
        body["code"] = code
    return JSONResponse(body, status_code=status, headers=headers)


def register_errors(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def _http(_req: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Generic HTTPException (raise HTTPException(...) in routers / deps).
        # The API-key 401 (X-MailTM-Error: api_key) gets a machine-readable
        # `code` so the UI no longer depends on headers or detail strings only.
        headers = dict(exc.headers or {})
        body: dict[str, str] = {"detail": str(exc.detail)}
        if headers.get("X-MailTM-Error") == "api_key":
            body["code"] = "api_key"
        return JSONResponse(body, status_code=exc.status_code, headers=headers)

    @app.exception_handler(RequestValidationError)
    async def _validation(_req: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            {"detail": exc.errors(), "code": "validation_error"},
            status_code=422,
        )

    @app.exception_handler(MailNotFoundError)
    async def _not_found(_req: Request, exc: MailNotFoundError) -> JSONResponse:
        return _json(404, str(exc), code="not_found")

    @app.exception_handler(MailValidationError)
    async def _bad(_req: Request, exc: MailValidationError) -> JSONResponse:
        return _json(400, str(exc), code="validation_error")

    @app.exception_handler(MailAuthError)
    async def _auth(_req: Request, exc: MailAuthError) -> JSONResponse:
        # 401 collides with the API-key check; the header lets the UI tell
        # "Google rejected the account token" apart from "server needs a key".
        return _json(
            401,
            str(exc),
            headers={"X-MailTM-Error": "provider_auth"},
            code="provider_auth",
        )

    @app.exception_handler(MailConflictError)
    async def _conflict(_req: Request, exc: MailConflictError) -> JSONResponse:
        return _json(409, str(exc), code="conflict")

    @app.exception_handler(MailRateLimitError)
    async def _rate(_req: Request, exc: MailRateLimitError) -> JSONResponse:
        return _json(429, str(exc), code="rate_limit")

    @app.exception_handler(MailAPIError)
    async def _api(_req: Request, exc: MailAPIError) -> JSONResponse:
        return _json(502, str(exc), code="upstream")

    @app.exception_handler(KeyError)
    async def _key(_req: Request, exc: KeyError) -> JSONResponse:
        # registry.get raises KeyError for an unknown provider slug
        return _json(404, str(exc).strip("'\""), code="not_found")

    @app.exception_handler(Exception)
    async def _internal(req: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"unhandled error on {req.method} {req.url.path}")
        return _json(500, "Internal server error", code="internal")
