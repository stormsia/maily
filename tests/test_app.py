from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.settings import Settings


def _app(tmp_path: Path, **kwargs) -> TestClient:
    db = tmp_path / "test.db"
    app = create_app(
        Settings(database_url=f"sqlite+aiosqlite:///{db}", secret_key="test-secret", **kwargs)
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