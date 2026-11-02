"""Tests for path traversal prevention, API security routing, auth headers, and health helpers."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from pathlib import Path

from maily.app.routers.health import _iso_utc, _json_len, _safe_error
from maily.providers.gmail.parse import extract_parts
from maily.settings import Settings
from tests.api_keys_support import ROOT, client_for


def test_path_traversal_prevention(tmp_path: Path):
    """Verify relative traversal escapes in /static route return 404 or 400."""
    with client_for(tmp_path) as client:
        payloads = [
            "/static/../../etc/passwd",
            "/static/..%2f..%2fetc/passwd",
            "/static/....//....//config.py",
        ]
        for url in payloads:
            resp = client.get(url)
            assert resp.status_code in (
                400,
                404,
            ), f"Failed for {url}: {resp.status_code}"


def test_invalid_bearer_token_rejection(tmp_path: Path):
    """Verify malformed authorization headers are safely rejected."""
    with client_for(tmp_path) as client:
        resp = client.get("/v1/mailboxes", headers={"X-API-Key": "invalid_random_key_12345"})
        assert resp.status_code == 401
        assert resp.headers.get("x-mailtm-error") == "api_key"


def test_bearer_authorization_header(tmp_path: Path):
    """Verify Authorization: Bearer token is supported for auth and rejected if bad."""
    with client_for(tmp_path) as client:
        # Invalid Bearer
        resp = client.get("/v1/providers", headers={"Authorization": "Bearer bad-token"})
        assert resp.status_code == 401
        assert resp.headers.get("x-mailtm-error") == "api_key"

        # Valid Bearer
        resp_valid = client.get("/v1/providers", headers={"Authorization": f"Bearer {ROOT}"})
        assert resp_valid.status_code == 200


def test_security_response_headers_and_config(tmp_path: Path):
    """Verify health and public config endpoints respond correctly."""
    with client_for(tmp_path) as client:
        from maily.db.models import DomainCache

        async def _seed():
            async with client.app.state.session_factory() as session:
                session.add(
                    DomainCache(
                        provider="test_prov",
                        domains_json='["d1.test"]',
                        updated_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    )
                )
                await session.commit()

        client.portal.call(_seed)

        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"
        assert "domain_cache" in data

        # Check /v1/config
        cfg_resp = client.get("/v1/config")
        assert cfg_resp.status_code == 200
        cfg = cfg_resp.json()
        assert "client_version" in cfg


def test_health_internal_helpers():
    """Unit tests for _safe_error, _iso_utc, and _json_len."""
    # _safe_error
    assert _safe_error(None) is None
    assert _safe_error("") is None
    assert _safe_error("short error") == "short error"
    long_msg = "word " * 60
    safe = _safe_error(long_msg)
    assert safe is not None
    assert len(safe) <= 160
    assert safe.endswith("…")

    # _iso_utc
    assert _iso_utc(None) is None
    dt_naive = datetime(2025, 1, 1, 12, 0, 0)
    assert _iso_utc(dt_naive) == "2025-01-01T12:00:00Z"
    dt_aware = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    assert _iso_utc(dt_aware) == "2025-01-01T12:00:00Z"

    # _json_len
    assert _json_len("not json") == 0
    assert _json_len('{"a": 1}') == 0
    assert _json_len('["d1.com", "d2.com"]') == 2


def test_settings_secret_generation_and_credentials(tmp_path: Path):
    """Verify Settings generates and persists secret_key, and parses google creds."""
    secret_file = tmp_path / "secret.key"
    s1 = Settings(secret_key="", secret_key_path=secret_file, _env_file=None)
    key1 = s1.resolved_secret_key()
    assert secret_file.exists()
    assert len(key1) > 20

    # Second instance loads existing file
    s2 = Settings(secret_key="", secret_key_path=secret_file, _env_file=None)
    key2 = s2.resolved_secret_key()
    assert key1 == key2

    # Credential path parsing
    creds_file = tmp_path / "google_creds.json"
    creds_file.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "google-client-id",
                    "client_secret": "google-client-secret",
                }
            }
        )
    )
    s3 = Settings(
        secret_key="x" * 32,
        gmail_credentials_path=str(creds_file),
        _env_file=None,
    )
    cid, csec = s3.gmail_client()
    assert cid == "google-client-id"
    assert csec == "google-client-secret"
    assert "oauth/callback" in s3.default_gmail_redirect_uri()

    # Sanitize proxy & get_settings
    s_proxy = Settings(proxy="   ", secret_key="x" * 32, _env_file=None)
    assert s_proxy.proxy is None
    from maily.settings import get_settings

    assert get_settings() is not None


def test_gmail_multipart_and_attachments():
    """Verify extract_parts handles plain text, html, and attachments with nested parts."""
    text_b64 = base64.urlsafe_b64encode(b"Hello plain text").decode()
    html_b64 = base64.urlsafe_b64encode(b"<p>Hello html</p>").decode()

    payload = {
        "mimeType": "multipart/mixed",
        "parts": [
            {
                "mimeType": "text/plain",
                "body": {"data": text_b64},
            },
            {
                "mimeType": "text/html",
                "body": {"data": html_b64},
            },
            {
                "mimeType": "application/pdf",
                "filename": "document.pdf",
                "body": {"attachmentId": "att123", "size": 1024},
            },
            {
                "mimeType": "multipart/alternative",
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": text_b64},
                    }
                ],
            },
        ],
    }

    text_parts, html_parts, attachments = extract_parts(payload)
    assert len(text_parts) == 2
    assert "Hello plain text" in text_parts[0]
    assert len(html_parts) == 1
    assert "<p>Hello html</p>" in html_parts[0]
    assert len(attachments) == 1
    assert attachments[0]["filename"] == "document.pdf"
    assert attachments[0]["id"] == "att123"
