from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.settings import Settings


def _app(tmp_path: Path, **kwargs) -> TestClient:
    db = tmp_path / "test.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            secret_key="test-secret",
            _env_file=None,
            **kwargs,
        )
    )
    return TestClient(app)


def test_app_builds_and_health_ok(tmp_path):
    with _app(tmp_path) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/health").json() == {"status": "ok"}


def test_api_key_enforced_when_set(tmp_path):
    with _app(tmp_path, api_key="sekret") as client:
        # open endpoints
        assert client.get("/health").status_code == 200
        assert client.get("/v1/gmail/oauth/callback").status_code == 400
        # protected ones require key
        assert client.get("/v1/providers").status_code == 401
        assert client.get("/v1/providers", headers={"X-API-Key": "sekret"}).status_code == 200
        assert client.get("/v1/providers", headers={"X-API-Key": "wrong"}).status_code == 401


def test_api_key_401_is_tagged(tmp_path):
    with _app(tmp_path, api_key="sekret") as client:
        res = client.get("/v1/providers")
        assert res.status_code == 401
        assert res.headers.get("x-mailtm-error") == "api_key"


def test_provider_auth_401_is_tagged_distinctly():
    from fastapi import FastAPI

    from mailtmapi.app.errors import register_errors
    from mailtmapi.exceptions import MailAuthError

    app = FastAPI()
    register_errors(app)

    @app.get("/boom")
    async def boom() -> None:
        raise MailAuthError("Google rejected the token", status_code=401)

    with TestClient(app) as client:
        res = client.get("/boom")
        assert res.status_code == 401
        assert res.headers.get("x-mailtm-error") == "provider_auth"
