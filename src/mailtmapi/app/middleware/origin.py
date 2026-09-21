from __future__ import annotations

from urllib.parse import urlsplit

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class OriginGuard:
    """Reject cross-origin calls to the JSON API.

    The dashboard is served same-origin by this app and the API is protected
    by the API-key header; a foreign page could not read responses anyway
    (no CORS headers are emitted). This middleware is defense-in-depth: the
    server refuses requests whose `Origin` does not match the Host instead of
    silently serving them. Server-to-server callers and local tooling that
    send no `Origin` header are unaffected.

    The scheme is compared loosely (host[:port] only) so setups behind an
    HTTP->HTTPS reverse proxy keep working.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = scope.get("headers", [])
        path = scope.get("path", "")
        origin = ""
        host_header = ""
        for name, value in headers:
            if name == b"origin":
                origin = value.decode("latin-1")
            elif name == b"host":
                host_header = value.decode("latin-1")

        if origin and path.startswith("/v1/") and not _same_netloc(origin, host_header):
            response = JSONResponse(
                {
                    "detail": "Cross-origin API access is not allowed",
                    "code": "cross_origin",
                },
                status_code=403,
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)


def _netloc(host_header: str) -> str:
    """'example.com:8477' -> 'example.com:8477'; also handles path noise."""
    return urlsplit(f"//{host_header}").netloc.lower()


def _same_netloc(origin: str, host_header: str) -> bool:
    try:
        origin_parts = urlsplit(origin)
    except ValueError:
        return False
    if origin_parts.scheme not in ("http", "https") or not origin_parts.hostname:
        return False
    if not host_header:
        return False
    return origin_parts.netloc.lower() == _netloc(host_header)
