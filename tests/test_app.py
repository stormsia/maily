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
        res = client.get("/health")
        assert res.status_code == 200
        body = res.json()
        assert body["status"] == "ok"
        # brief provider/domain-cache degradation view for monitoring
        assert isinstance(body["domain_cache"], dict)


def test_health_includes_domain_cache_status(tmp_path):
    with _app(tmp_path) as client:
        body = client.get("/health").json()
        # every domain-provider is present, values are shaped
        for _slug, meta in body["domain_cache"].items():
            assert set(meta) == {"last_refresh", "domains", "error"}
            assert isinstance(meta["domains"], int)


def test_config_exposes_client_version(tmp_path):
    import mailtmapi

    with _app(tmp_path, api_key="sekret") as client:
        # /v1/config is auth-free: it powers the dashboard banner and the
        # standalone client's auto-update check
        body = client.get("/v1/config").json()
        assert body["api_key_required"] is True
        assert body["client_version"] == mailtmapi.__version__


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
        # structured code in the body (not only the header)
        assert res.json().get("code") == "api_key"


def test_validation_error_has_code(tmp_path):
    with _app(tmp_path, api_key="sekret") as client:
        res = client.put(
            "/v1/admin/retention/stub",
            json={"mailbox_ttl_hours": "not-an-int"},
            headers={"X-API-Key": "sekret"},
        )
        assert res.status_code == 422
        assert res.json().get("code") == "validation_error"


def test_cross_origin_api_is_rejected(tmp_path):
    with _app(tmp_path) as client:
        # no Origin (curl, tests, server-to-server) or same-origin → allowed
        assert client.get("/v1/providers").status_code == 200
        assert (
            client.get(
                "/v1/providers", headers={"Origin": "http://testserver"}
            ).status_code
            == 200
        )
        # foreign origin is refused outright, even though /v1 is key-protected
        res = client.get("/v1/providers", headers={"Origin": "http://evil.example"})
        assert res.status_code == 403
        assert res.json().get("code") == "cross_origin"
        # sandboxed/opaque origins ("null") are not trusted
        assert (
            client.get(
                "/v1/providers", headers={"Origin": "null"}
            ).status_code
            == 403
        )


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
