from __future__ import annotations

import re
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from mailtmapi.app.authz import parse_scope, secret_sha256
from mailtmapi.app.main import create_app
from mailtmapi.crypto import decrypt, encrypt
from mailtmapi.schemas import MessageDetailOut, MessageOut
from mailtmapi.settings import Settings
from mailtmapi.standalone_client import MailTMAPI
from mailtmapi.utils.misc import random_password, random_string

SECRET = "test-secret-benchmark-key-32bytes!!"
_URL_RE = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
_OTP_RE = re.compile(r"\b(\d{6})\b")
_CONFIRM_KEYWORDS = ("verify", "confirm", "activate", "token")

SAMPLE_EMAIL_HTML = """
<!DOCTYPE html>
<html>
<head><title>Verify your account</title></head>
<body>
  <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
    <h2>Welcome to MailTMAPI Services</h2>
    <p>Thank you for registering. To complete your account activation, please enter the following verification code:</p>
    <div style="font-size: 28px; font-weight: bold; background: #f4f4f4; padding: 12px; text-align: center; letter-spacing: 4px;">
      849201
    </div>
    <p>Or alternatively, click the confirmation button below:</p>
    <p style="text-align: center;">
      <a href="https://example.com/api/v1/auth/verify?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.t-ID"
         style="background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">Confirm Email</a>
    </p>
    <p>If you did not request this, you can safely ignore this email.</p>
    <p>Links for reference: <a href="https://example.com/help">Help</a> | <a href="https://example.com/privacy">Privacy Policy</a></p>
  </div>
</body>
</html>
"""

SAMPLE_MESSAGE_PAYLOAD = {
    "id": 101,
    "message_api_id": "msg_live_api_998877",
    "subject": "Complete your registration on MailTMAPI",
    "from_address": "support@service.example.com",
    "from_name": "Service Support",
    "seen": False,
    "has_attachments": True,
    "size": 4096,
    "received_at": datetime.now(timezone.utc),
    "text": "Your verification code is 849201. Confirm at https://example.com/verify?token=abc",
    "html": [SAMPLE_EMAIL_HTML],
}

SAMPLE_BATCH_MESSAGES = [
    MessageOut(
        id=i,
        message_api_id=f"msg_batch_{i}",
        subject=f"Incoming notification #{i}",
        from_address=f"sender_{i % 5}@example.com",
        from_name="System Sender",
        seen=(i % 2 == 0),
        has_attachments=False,
        size=1024 + i * 10,
        received_at=datetime.now(timezone.utc),
    )
    for i in range(50)
]

SAMPLE_SCOPE_JSON = (
    '{"providers":["mail.tm","tempmail.plus"],"parent_ids":[1,2],'
    '"actions":["messages:read","mailboxes:read"]}'
)


@pytest.fixture(scope="module")
def fernet_key() -> str:
    return Fernet.generate_key().decode()


@pytest.fixture(scope="module")
def sample_payload_1kb() -> str:
    return "A" * 1024


@pytest.fixture(scope="module")
def sample_encrypted_1kb(fernet_key: str, sample_payload_1kb: str) -> str:
    return encrypt(fernet_key, sample_payload_1kb)


@pytest.fixture(scope="module")
def benchmark_app(tmp_path_factory, fernet_key: str) -> Iterator[TestClient]:
    db = tmp_path_factory.mktemp("bench_db") / "bench.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            api_key=SECRET,
            secret_key=fernet_key,
            _env_file=None,  # type: ignore[call-arg]
        )
    )
    with TestClient(app) as client:
        # Seed an admin key to test authenticated operations against stored rows
        client.post(
            "/v1/admin/keys",
            json={
                "name": "bench-ops",
                "scope": {
                    "providers": ["mail.tm"],
                    "parent_ids": [],
                    "actions": ["mailboxes:read"],
                },
            },
            headers={"X-API-Key": SECRET},
        )
        yield client


# --- Crypto benchmarks ---


@pytest.mark.benchmark(group="crypto")
def test_benchmark_crypto_encrypt_1kb(benchmark, fernet_key: str, sample_payload_1kb: str):
    res = benchmark(encrypt, fernet_key, sample_payload_1kb)
    assert res is not None


@pytest.mark.benchmark(group="crypto")
def test_benchmark_crypto_decrypt_1kb(benchmark, fernet_key: str, sample_encrypted_1kb: str):
    res = benchmark(decrypt, fernet_key, sample_encrypted_1kb)
    assert len(res) == 1024


# --- Utility benchmarks ---


@pytest.mark.benchmark(group="utils")
def test_benchmark_random_string(benchmark):
    res = benchmark(random_string, 16)
    assert len(res) == 16


@pytest.mark.benchmark(group="utils")
def test_benchmark_random_password(benchmark):
    res = benchmark(random_password, 24)
    assert len(res) == 24


# --- Serialization & Schema benchmarks ---


@pytest.mark.benchmark(group="serialization")
def test_benchmark_pydantic_message_detail_parse(benchmark):
    model = benchmark(MessageDetailOut.model_validate, SAMPLE_MESSAGE_PAYLOAD)
    assert model.id == 101


@pytest.mark.benchmark(group="serialization")
def test_benchmark_pydantic_batch_messages_serialize(benchmark):
    def _dump_batch() -> list[dict]:
        return [m.model_dump(mode="json") for m in SAMPLE_BATCH_MESSAGES]

    dumped = benchmark(_dump_batch)
    assert len(dumped) == 50


# --- Pattern Extraction benchmarks ---


@pytest.mark.benchmark(group="pattern_extraction")
def test_benchmark_extract_verification_code(benchmark):
    def _find_otp() -> str | None:
        match = _OTP_RE.search(SAMPLE_EMAIL_HTML)
        return match.group(1) if match else None

    code = benchmark(_find_otp)
    assert code == "849201"


@pytest.mark.benchmark(group="pattern_extraction")
def test_benchmark_extract_confirmation_url(benchmark):
    def _find_link() -> str | None:
        urls = _URL_RE.findall(SAMPLE_EMAIL_HTML)
        return next((u for u in urls if any(kw in u.casefold() for kw in _CONFIRM_KEYWORDS)), None)

    link = benchmark(_find_link)
    assert link is not None
    assert "verify" in link


# --- Authz benchmarks ---


@pytest.mark.benchmark(group="authz")
def test_benchmark_authz_parse_scope(benchmark):
    scope = benchmark(parse_scope, SAMPLE_SCOPE_JSON)
    assert "mail.tm" in scope.providers
    assert "messages:read" in scope.actions


@pytest.mark.benchmark(group="authz")
def test_benchmark_authz_secret_sha256(benchmark):
    digest = benchmark(secret_sha256, "mk_live_api_key_secret_32bytes_value_benchmark")
    assert len(digest) == 64


# --- API Endpoint benchmarks ---


@pytest.mark.benchmark(group="api")
def test_benchmark_health_endpoint(benchmark, benchmark_app: TestClient):
    response = benchmark(benchmark_app.get, "/health")
    assert response.status_code == 200


@pytest.mark.benchmark(group="api")
def test_benchmark_domain_cache_settings(benchmark, benchmark_app: TestClient):
    response = benchmark(
        benchmark_app.get, "/v1/admin/domain-cache", headers={"X-API-Key": SECRET}
    )
    assert response.status_code == 200


@pytest.mark.benchmark(group="api")
def test_benchmark_mailboxes_list(benchmark, benchmark_app: TestClient):
    response = benchmark(benchmark_app.get, "/v1/mailboxes", headers={"X-API-Key": SECRET})
    assert response.status_code == 200


@pytest.mark.benchmark(group="api")
def test_benchmark_admin_keys_list(benchmark, benchmark_app: TestClient):
    response = benchmark(benchmark_app.get, "/v1/admin/keys", headers={"X-API-Key": SECRET})
    assert response.status_code == 200
    assert len(response.json()) >= 1


# --- Standalone Client benchmarks ---


@pytest.mark.benchmark(group="client")
def test_benchmark_client_init(benchmark):
    client = benchmark(MailTMAPI, base_url="http://localhost:8477", api_key="bench-key")
    assert str(client._transport._client.base_url).rstrip("/") == "http://localhost:8477"
