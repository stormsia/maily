from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from mailtmapi.app.main import create_app
from mailtmapi.providers.base import (
    MailboxInfo,
    MailboxSpec,
    MessageDetail,
    MessageSource,
    MessageSummary,
    Party,
    Target,
)
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.settings import Settings

SECRET = "test-secret"

STAMP = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


class StubMailProvider:
    slug = "stub"
    kind = "domain"

    async def close(self) -> None: ...

    async def list_targets(self) -> list[Target]:
        return []

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        return MailboxInfo(provider=self.slug, address="stub@x", token="tok")

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        return [
            MessageSummary(
                id="m1",
                subject="Hello",
                from_=Party(address="a@b.c", name="Alice"),
                received_at=STAMP,
            )
        ]

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        return MessageDetail(
            id=message_id,
            subject="Hello",
            from_=Party(address="a@b.c", name="Alice"),
            text="body text",
            html=["<p>body text</p>"],
            received_at=STAMP,
        )

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        return MessageSource(id=message_id, data="From: a@b.c\nSubject: x\n")


def _client(tmp_path: Path) -> TestClient:
    db = tmp_path / "test.db"
    app = create_app(
        Settings(database_url=f"sqlite+aiosqlite:///{db}", secret_key=SECRET)
    )
    return TestClient(app)


def _create_mailbox(client: TestClient) -> int:
    client.app.state.registry = ProviderRegistry([StubMailProvider()])
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
