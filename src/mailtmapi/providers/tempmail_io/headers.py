from __future__ import annotations

import re
from urllib.parse import urljoin

from ...http import HttpClient

DEFAULT_ORIGIN = "https://temp-mail.io/"

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"
_SCRIPT_RE = re.compile(r'<script[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)
_TOKEN_RES = (
    re.compile(r'X-CORS-Header\s*[:=]\s*["\']([A-Za-z0-9+/=_-]{8,})["\']', re.IGNORECASE),
    re.compile(r"X-CORS[-_]?Header\s*[:=]\s*[\"'`]([A-Za-z0-9+/=_-]{8,})[\"'`]", re.IGNORECASE),
    re.compile(
        r"cors[_-]?header[\"'`]?\s*[,:]\s*[\"'`]([A-Za-z0-9+/=_-]{8,})[\"'`]", re.IGNORECASE
    ),
)


def _script_urls(html: str, base: str) -> list[str]:
    urls = [urljoin(base, src.strip()) for src in _SCRIPT_RE.findall(html)]
    return [u for u in urls if u.startswith("http")]


def find_cors_token(text: str) -> str | None:
    for pattern in _TOKEN_RES:
        m = pattern.search(text)
        if m:
            return m.group(1)
    return None


async def fetch_cors_header(
    http: HttpClient,
    origin: str = DEFAULT_ORIGIN,
    *,
    max_scripts: int = 6,
) -> str | None:
    headers = {"User-Agent": _UA}
    page = await http.get(origin, headers=headers)
    html = page.text

    inline = find_cors_token(html)
    if inline:
        return inline

    for url in _script_urls(html, origin)[:max_scripts]:
        resp = await http.get(url, headers=headers)
        token = find_cors_token(resp.text)
        if token:
            return token
    return None


def build_headers(token: str | None) -> dict[str, str]:
    if not token:
        return {}
    return {"X-CORS-Header": token}
