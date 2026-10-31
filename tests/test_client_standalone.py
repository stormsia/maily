"""Standalone client/client.py: self-contained, versioned, auto-updatable."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
from pathlib import Path

import httpx
import pytest

import mailtmapi
import mailtmapi.client as pkg_client

CLIENT_FILE = Path(__file__).resolve().parents[1] / "client" / "client.py"
ALLOWED_TOP_LEVEL_IMPORTS = {"httpx", "loguru", "pydantic"}


def _load_standalone():
    spec = importlib.util.spec_from_file_location("_standalone_client", CLIENT_FILE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _imported_top_level(source: str) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.add(node.module.split(".")[0])
    return names


def test_client_file_is_self_contained():
    source = CLIENT_FILE.read_text(encoding="utf-8")
    imported = _imported_top_level(source)
    # no server package (fastapi/sqlalchemy/uvicorn/mailtmapi itself), only
    # light client deps beyond the stdlib
    unexpected = {
        name
        for name in imported
        if name not in ALLOWED_TOP_LEVEL_IMPORTS
        and name not in __import__("sys").stdlib_module_names
    }
    assert not unexpected, f"standalone client imports unexpected modules: {unexpected}"
    assert "mailtmapi" not in imported


def test_versions_stay_in_sync():
    mod = _load_standalone()
    assert mod.__version__ == mailtmapi.__version__
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    client_pyproject = (CLIENT_FILE.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{mailtmapi.__version__}"' in pyproject
    assert f'version = "{mailtmapi.__version__}"' in client_pyproject


def test_standalone_mirror_is_current():
    """client/client.py are generated from src/mailtmapi/standalone_client.py.

    Editing the canonical file without regenerating fails this test (and CI).
    """
    build = importlib.util.spec_from_file_location(
        "_build_client", Path(__file__).resolve().parents[1] / "scripts" / "build_client.py"
    )
    assert build and build.loader
    build_mod = importlib.util.module_from_spec(build)
    build.loader.exec_module(build_mod)

    expected = build_mod.render()
    assert CLIENT_FILE.read_text(encoding="utf-8") == expected, (
        f"{CLIENT_FILE.name} is stale — run `python scripts/build_client.py`"
    )


def test_api_surface_matches_packaged_client():
    mod = _load_standalone()
    # packaged `mailtmapi.client` may expose extra back-compat aliases
    # (AdminAPI etc.), but every public name of the canonical file must exist
    missing = set(mod.__all__) - set(pkg_client.__all__)
    assert not missing, f"packaged client missing: {sorted(missing)}"


class _Resp:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:  # pragma: no cover
        pass


def test_parse_version_and_check_update(monkeypatch):
    mod = _load_standalone()

    assert mod._parse_version('x = 1\n__version__ = "1.2.3"\n') == "1.2.3"
    assert mod._parse_version("no version here") is None

    # remote equals local -> no update
    monkeypatch.setattr(
        mod.httpx, "get", lambda *a, **k: _Resp(f'__version__ = "{mod.__version__}"')
    )
    assert mod.check_update("https://example.invalid/client.py") is None

    # remote is newer -> tuple of versions
    monkeypatch.setattr(mod.httpx, "get", lambda *a, **k: _Resp('__version__ = "9.9.9"'))
    assert mod.check_update("https://example.invalid/client.py") == (
        mod.__version__,
        "9.9.9",
    )


def test_self_update_replaces_target_file(monkeypatch, tmp_path):
    mod = _load_standalone()
    target = tmp_path / "client.py"
    target.write_text(f'__version__ = "{mod.__version__}"\n', encoding="utf-8")

    monkeypatch.setattr(inspect, "getsourcefile", lambda *_a, **_k: str(target))

    # same version -> nothing to do
    monkeypatch.setattr(
        mod.httpx, "get", lambda *a, **k: _Resp(f'__version__ = "{mod.__version__}"')
    )
    assert mod.self_update("https://example.invalid/client.py") is False

    # newer version -> file replaced atomically
    monkeypatch.setattr(
        mod.httpx, "get", lambda *a, **k: _Resp('__version__ = "9.9.9"\nprint("hi")')
    )
    assert mod.self_update("https://example.invalid/client.py") is True
    assert '__version__ = "9.9.9"' in target.read_text(encoding="utf-8")
    assert not (tmp_path / "client.py.tmp").exists()


@pytest.mark.asyncio
async def test_key_me_requests_current_key():
    """Given a mocked server, key_me hits GET /v1/admin/keys/me and returns its JSON."""
    mod = _load_standalone()
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"is_root": True})

    transport_client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    api = mod.MailTMAPI(client=transport_client)
    try:
        assert await api.admin.key_me() == {"is_root": True}
    finally:
        await api.close()

    assert len(seen) == 1
    assert seen[0].method == "GET"
    assert seen[0].url.path == "/v1/admin/keys/me"


@pytest.mark.asyncio
async def test_key_create_posts_scope_body_unchanged():
    """Given empty scope lists, key_create posts them as given and returns the secret JSON."""
    mod = _load_standalone()
    seen: list[httpx.Request] = []
    scope = {"providers": [], "parent_ids": [], "actions": ["mailboxes:read"]}
    body = {
        "name": "reader",
        "expires_at": None,
        "scope": scope,
        "retention": [],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": 1, "secret": "mk_once", "scope": scope})

    transport_client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    api = mod.MailTMAPI(client=transport_client)
    try:
        created = await api.admin.key_create(
            name=body["name"],
            expires_at=body["expires_at"],
            scope=scope,
            retention=body["retention"],
        )
    finally:
        await api.close()

    assert created == {"id": 1, "secret": "mk_once", "scope": scope}
    assert len(seen) == 1
    assert seen[0].method == "POST"
    assert seen[0].url.path == "/v1/admin/keys"
    assert json.loads(seen[0].content) == body


@pytest.mark.asyncio
async def test_check_client_version_reports_server_version():
    mod = _load_standalone()

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/config"
        return httpx.Response(200, json={"client_version": "9.9.9"})

    transport_client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    api = mod.MailTMAPI(client=transport_client)
    try:
        assert await api.check_client_version() == "9.9.9"
        assert await api.config.get() == {"client_version": "9.9.9"}
    finally:
        await api.close()
