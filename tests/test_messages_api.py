from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient
from tests.helpers import StubProvider

from mailtmapi.app.main import create_app
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.settings import Settings

SECRET = "test-secret"


def _client(tmp_path: Path) -> TestClient:
    db = tmp_path / "test.db"
    app = create_app(
        Settings(
            database_url=f"sqlite+aiosqlite:///{db}",
            secret_key=SECRET,
            _env_file=None,
        )
    )
    return TestClient(app)


def _create_mailbox(client: TestClient) -> int:
    client.app.state.registry = ProviderRegistry([StubProvider()])
    r = client.post("/v1/mailboxes", json={"provider": "stub"})
    assert r.status_code == 200
    return r.json()["id"]


def test_messages_list_caches_from_provider(tmp_path: Path):
    with _client(tmp_path) as client:
        mb_id = _create_mailbox(client)
        r = client.get(f"/v1/mailboxes/{mb_id}/messages")
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 1
        assert body[0]["message_api_id"] == "m1"
        assert body[0]["subject"] == "Hello"
        assert body[0]["from_address"] == "a@b.c"
        assert body[0]["from_name"] == "Alice"
        assert body[0]["seen"] is False

        # second read serves from the local cache
        r = client.get(f"/v1/mailboxes/{mb_id}/messages")
        assert r.json() == body


def test_messages_get_detail(tmp_path: Path):
    with _client(tmp_path) as client:
        mb_id = _create_mailbox(client)
        client.get(f"/v1/mailboxes/{mb_id}/messages")
        r = client.get(f"/v1/mailboxes/{mb_id}/messages/m1")
        assert r.status_code == 200
        body = r.json()
        assert body["text"] == "body text"
        assert body["html"] == ["<p>body text</p>"]
        assert body["subject"] == "Hello"


def test_messages_mark_read_persists(tmp_path: Path):
    with _client(tmp_path) as client:
        mb_id = _create_mailbox(client)
        client.get(f"/v1/mailboxes/{mb_id}/messages")
        r = client.post(f"/v1/mailboxes/{mb_id}/messages/m1/read")
        assert r.status_code == 200
        assert r.json()["seen"] is True
        r = client.get(f"/v1/mailboxes/{mb_id}/messages/m1")
        assert r.json()["seen"] is True


def test_messages_delete_and_source(tmp_path: Path):
    with _client(tmp_path) as client:
        mb_id = _create_mailbox(client)
        client.get(f"/v1/mailboxes/{mb_id}/messages")

        r = client.get(f"/v1/mailboxes/{mb_id}/messages/m1/source")
        assert r.status_code == 200
        assert r.json() == {
            "id": "m1",
            "data": "From: a@b.c\nSubject: x\n",
            "download_url": "",
        }

        r = client.delete(f"/v1/mailboxes/{mb_id}/messages/m1")
        assert r.status_code == 204
        # source still resolvable after deletion
        r = client.get(f"/v1/mailboxes/{mb_id}/messages/m1/source")
        assert r.status_code == 200


def test_messages_unknown_message_404(tmp_path: Path):
    with _client(tmp_path) as client:
        mb_id = _create_mailbox(client)
        r = client.post(f"/v1/mailboxes/{mb_id}/messages/nope/read")
        assert r.status_code == 404

        r = client.get(f"/v1/mailboxes/{mb_id}/messages/nope")
        assert r.status_code == 200  # get refetches detail, not governs by cache
