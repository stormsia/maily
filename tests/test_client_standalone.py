"""Standalone client/maily_client.py: self-contained, versioned, auto-updatable."""

from __future__ import annotations

import ast
import importlib.util
import inspect
import json
import sys
from pathlib import Path
from typing import Any

import httpx
import pytest

import maily
import maily.client as pkg_client
from maily import standalone_client
from maily.standalone_client import ClientError, _main

CLIENT_FILE = Path(__file__).resolve().parents[1] / "client" / "maily_client.py"
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
    # no server package (fastapi/sqlalchemy/uvicorn/maily itself), only
    # light client deps beyond the stdlib
    unexpected = {
        name
        for name in imported
        if name not in ALLOWED_TOP_LEVEL_IMPORTS
        and name not in __import__("sys").stdlib_module_names
    }
    assert not unexpected, f"{CLIENT_FILE.name} imports unexpected modules: {unexpected}"
    assert "maily" not in imported


def test_versions_stay_in_sync():
    mod = _load_standalone()
    assert mod.__version__ == maily.__version__
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    client_pyproject = (CLIENT_FILE.parent / "pyproject.toml").read_text(encoding="utf-8")
    assert f'version = "{maily.__version__}"' in pyproject
    assert f'version = "{maily.__version__}"' in client_pyproject


def test_standalone_mirror_is_current():
    """client/client.py are generated from src/maily/standalone_client.py.

    Editing the canonical file without regenerating fails this test (and CI).
    """
    build = importlib.util.spec_from_file_location(
        "_build_client",
        Path(__file__).resolve().parents[1] / "scripts" / "build_client.py",
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
    # packaged `maily.client` may expose extra back-compat aliases
    # (AdminAPI etc.), but every public name of the canonical file must exist
    missing = set(mod.__all__) - set(pkg_client.__all__)
    assert not missing, f"packaged client missing: {sorted(missing)}"


def test_import_maily_client_as_module():
    spec = importlib.util.spec_from_file_location("maily_client", CLIENT_FILE)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert hasattr(mod, "Maily")
    assert hasattr(mod, "SyncMaily")
    assert mod.__version__ == maily.__version__
    assert set(mod.__all__) == set(_load_standalone().__all__)


class _Resp:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:  # pragma: no cover
        pass


def test_parse_version_and_check_update(monkeypatch: pytest.MonkeyPatch) -> None:
    assert standalone_client._parse_version('x = 1\n__version__ = "1.2.3"\n') == "1.2.3"
    assert standalone_client._parse_version("no version here") is None

    # remote equals local -> no update
    monkeypatch.setattr(
        standalone_client.httpx,
        "get",
        lambda *a, **k: _Resp(f'__version__ = "{standalone_client.__version__}"'),
    )
    assert standalone_client.check_update("https://example.invalid/client.py") is None

    # remote is newer -> tuple of versions
    monkeypatch.setattr(
        standalone_client.httpx, "get", lambda *a, **k: _Resp('__version__ = "9.9.9"')
    )
    assert standalone_client.check_update("https://example.invalid/client.py") == (
        standalone_client.__version__,
        "9.9.9",
    )

    # remote has no version -> raises ClientError
    monkeypatch.setattr(standalone_client.httpx, "get", lambda *a, **k: _Resp("no version here"))
    with pytest.raises(ClientError, match="could not read __version__"):
        standalone_client.check_update("https://example.invalid/client.py")


def test_self_update_replaces_target_file(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    target = tmp_path / "client.py"
    target.write_text(f'__version__ = "{standalone_client.__version__}"\n', encoding="utf-8")

    monkeypatch.setattr(inspect, "getsourcefile", lambda *_a, **_k: str(target))

    # same version -> nothing to do
    monkeypatch.setattr(
        standalone_client.httpx,
        "get",
        lambda *a, **k: _Resp(f'__version__ = "{standalone_client.__version__}"'),
    )
    assert standalone_client.self_update("https://example.invalid/client.py") is False

    # invalid remote version -> raises ClientError
    monkeypatch.setattr(standalone_client.httpx, "get", lambda *a, **k: _Resp("no version here"))
    with pytest.raises(ClientError, match="could not read __version__"):
        standalone_client.self_update("https://example.invalid/client.py")

    # newer version -> file replaced atomically, after callback executed
    after_called = False

    def on_after() -> None:
        nonlocal after_called
        after_called = True

    monkeypatch.setattr(
        standalone_client.httpx,
        "get",
        lambda *a, **k: _Resp('__version__ = "9.9.9"\nprint("hi")'),
    )
    assert (
        standalone_client.self_update("https://example.invalid/client.py", after=on_after) is True
    )
    assert after_called is True
    assert '__version__ = "9.9.9"' in target.read_text(encoding="utf-8")
    assert not (tmp_path / "client.py.tmp").exists()

    # newer version without after callback
    target.write_text(f'__version__ = "{standalone_client.__version__}"\n', encoding="utf-8")
    assert standalone_client.self_update("https://example.invalid/client.py") is True


@pytest.mark.asyncio
async def test_key_me_requests_current_key():
    """Given a mocked server, key_me hits GET /v1/admin/keys/me and returns its JSON."""
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"is_root": True})

    transport_client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    api = standalone_client.Maily(client=transport_client)
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
    seen: list[httpx.Request] = []
    scope: dict[str, Any] = {
        "providers": [],
        "parent_ids": [],
        "actions": ["mailboxes:read"],
    }
    retention: list[dict[str, Any]] = []
    body: dict[str, Any] = {
        "name": "reader",
        "expires_at": None,
        "scope": scope,
        "retention": retention,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json={"id": 1, "secret": "mk_once", "scope": scope})

    transport_client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    api = standalone_client.Maily(client=transport_client)
    try:
        created = await api.admin.key_create(
            name="reader",
            expires_at=None,
            scope=scope,
            retention=retention,
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
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/config"
        return httpx.Response(200, json={"client_version": "9.9.9"})

    transport_client = httpx.AsyncClient(
        base_url="http://test", transport=httpx.MockTransport(handler)
    )
    api = standalone_client.Maily(client=transport_client)
    try:
        assert await api.check_client_version() == "9.9.9"
        assert await api.config.get() == {"client_version": "9.9.9"}
    finally:
        await api.close()


# =========================================================================== #
# CLI _main(argv) Test Suite
# =========================================================================== #
def test_cli_help_no_args(capsys: pytest.CaptureFixture[str]) -> None:
    """_main([]) returns 0 and prints usage doc to stderr."""
    code = _main([])
    assert code == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.err
    assert "maily-client version" in captured.err
    assert captured.out == ""


@pytest.mark.parametrize("flag", ["--help", "-h", "help"])
def test_cli_help_flags(capsys: pytest.CaptureFixture[str], flag: str) -> None:
    """_main([flag]) returns 0 and prints usage doc to stderr."""
    code = _main([flag])
    assert code == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.err
    assert captured.out == ""


def test_cli_default_argv_sys_argv(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """_main(None) falls back to sys.argv[1:]."""
    monkeypatch.setattr(sys, "argv", ["client.py", "--help"])
    code = _main()
    assert code == 0
    captured = capsys.readouterr()
    assert "usage:" in captured.err


def test_cli_version(capsys: pytest.CaptureFixture[str]) -> None:
    """_main(['version']) prints __version__ to stdout and returns 0."""
    code = _main(["version"])
    assert code == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == standalone_client.__version__
    assert captured.err == ""


def test_cli_check_up_to_date(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """_main(['check']) when client is up to date returns 0."""
    monkeypatch.setattr(
        "maily.standalone_client.check_update",
        lambda source_url=None: None,
    )
    code = _main(["check"])
    assert code == 0
    captured = capsys.readouterr()
    assert f"client is up to date ({standalone_client.__version__})" in captured.out


def test_cli_check_update_available(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """_main(['check']) when update is available returns 2 and prints version delta."""
    monkeypatch.setattr(
        "maily.standalone_client.check_update",
        lambda source_url=None: ("0.2.0", "0.3.0"),
    )
    code = _main(["check"])
    assert code == 2
    captured = capsys.readouterr()
    assert "update available: 0.2.0 -> 0.3.0" in captured.out


def test_cli_check_forwards_custom_source_url(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """_main(['check', url]) forwards custom URL to check_update."""
    recorded_url: list[str | None] = []

    def fake_check(url: str | None = None) -> tuple[str, str] | None:
        recorded_url.append(url)
        return None

    monkeypatch.setattr("maily.standalone_client.check_update", fake_check)
    code = _main(["check", "https://custom.host/client.py"])
    assert code == 0
    assert recorded_url == ["https://custom.host/client.py"]


def test_cli_check_failure_network_or_parse_error(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """_main(['check']) when check_update raises returns 1 and prints error to stderr."""

    def fake_check(url: str | None = None) -> tuple[str, str] | None:
        raise httpx.ConnectError("Connection refused")

    monkeypatch.setattr("maily.standalone_client.check_update", fake_check)
    code = _main(["check"])
    assert code == 1
    captured = capsys.readouterr()
    assert "check failed: Connection refused" in captured.err


def test_cli_update_already_current(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """_main(['update']) when already current returns 0."""
    monkeypatch.setattr(
        "maily.standalone_client.self_update",
        lambda source_url=None: False,
    )
    code = _main(["update"])
    assert code == 0
    captured = capsys.readouterr()
    assert f"client is up to date ({standalone_client.__version__})" in captured.out


def test_cli_update_success(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """_main(['update']) when update succeeds returns 0 and prints restart notice."""
    monkeypatch.setattr(
        "maily.standalone_client.self_update",
        lambda source_url=None: True,
    )
    code = _main(["update"])
    assert code == 0
    captured = capsys.readouterr()
    assert "updated. Restart your scripts." in captured.out


def test_cli_update_forwards_custom_source_url(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """_main(['update', url]) forwards custom URL to self_update."""
    recorded_url: list[str | None] = []

    def fake_update(url: str | None = None) -> bool:
        recorded_url.append(url)
        return True

    monkeypatch.setattr("maily.standalone_client.self_update", fake_update)
    code = _main(["update", "https://custom.host/client.py"])
    assert code == 0
    assert recorded_url == ["https://custom.host/client.py"]


def test_cli_update_failure(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """_main(['update']) when self_update raises returns 1 and prints error to stderr."""

    def fake_update(url: str | None = None) -> bool:
        raise PermissionError("Access denied writing file")

    monkeypatch.setattr("maily.standalone_client.self_update", fake_update)
    code = _main(["update"])
    assert code == 1
    captured = capsys.readouterr()
    assert "update failed: Access denied writing file" in captured.err


def test_cli_unknown_command(capsys: pytest.CaptureFixture[str]) -> None:
    """_main(['foo']) prints unknown command to stderr and returns 2."""
    code = _main(["foo"])
    assert code == 2
    captured = capsys.readouterr()
    assert "unknown command: foo" in captured.err


def test_cli_system_exit_entrypoint() -> None:
    """Verifies entrypoint SystemExit handling."""
    with pytest.raises(SystemExit) as exc:
        raise SystemExit(_main(["version"]))
    assert exc.value.code == 0
