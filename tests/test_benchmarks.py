from __future__ import annotations

import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.crypto import decrypt, encrypt
from mailtmapi.settings import Settings
from mailtmapi.standalone_client import MailTMAPI
from mailtmapi.utils.misc import random_password, random_string

SECRET = "test-secret-benchmark-key-32bytes!!"


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
def benchmark_app(tmp_path_factory) -> TestClient:
    db = tmp_path_factory.mktemp("bench_db") / "bench.db"
    app = create_app(
        Settings(database_url=f"sqlite+aiosqlite:///{db}", secret_key=SECRET, _env_file=None)
    )
    with TestClient(app) as client:
        yield client


@pytest.mark.benchmark(group="crypto")
def test_benchmark_crypto_encrypt_1kb(benchmark, fernet_key: str, sample_payload_1kb: str):
    res = benchmark(encrypt, fernet_key, sample_payload_1kb)
    assert res is not None


@pytest.mark.benchmark(group="crypto")
def test_benchmark_crypto_decrypt_1kb(benchmark, fernet_key: str, sample_encrypted_1kb: str):
    res = benchmark(decrypt, fernet_key, sample_encrypted_1kb)
    assert len(res) == 1024


@pytest.mark.benchmark(group="utils")
def test_benchmark_random_string(benchmark):
    res = benchmark(random_string, 16)
    assert len(res) == 16


@pytest.mark.benchmark(group="utils")
def test_benchmark_random_password(benchmark):
    res = benchmark(random_password, 24)
    assert len(res) == 24


@pytest.mark.benchmark(group="api")
def test_benchmark_health_endpoint(benchmark, benchmark_app: TestClient):
    response = benchmark(benchmark_app.get, "/health")
    assert response.status_code == 200


@pytest.mark.benchmark(group="api")
def test_benchmark_domain_cache_settings(benchmark, benchmark_app: TestClient):
    response = benchmark(benchmark_app.get, "/v1/admin/domain-cache")
    assert response.status_code == 200


@pytest.mark.benchmark(group="client")
def test_benchmark_client_init(benchmark):
    client = benchmark(MailTMAPI, base_url="http://localhost:8477", api_key="bench-key")
    assert str(client._transport._client.base_url).rstrip("/") == "http://localhost:8477"
