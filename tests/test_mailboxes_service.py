from __future__ import annotations

import pytest

from mailtmapi.app.services import mailboxes as svc
from mailtmapi.exceptions import MailValidationError
from mailtmapi.providers.base import (
    MailboxInfo,
    MailboxSpec,
    MessageDetail,
    MessageSource,
    MessageSummary,
    Target,
)
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.settings import Settings

SECRET = "test-secret"


class StubProvider:
    slug = "stub"
    kind = "domain"

    def __init__(self, address: str) -> None:
        self._address = address

    async def close(self) -> None: ...

    async def list_targets(self) -> list[Target]:
        return []

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        return MailboxInfo(provider=self.slug, address=self._address, token="tok")

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        return []

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        return MessageDetail(id=message_id)

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        return MessageSource(id=message_id, data="")


class FakeSession:
    def __init__(self) -> None:
        self.added: list = []

    def add(self, obj) -> None:
        self.added.append(obj)

    async def flush(self) -> None: ...


async def _create(address: str, session: FakeSession | None = None) -> svc.Mailbox:
    session = session or FakeSession()
    registry = ProviderRegistry([StubProvider(address)])
    settings = Settings(
        secret_key=SECRET,
        database_url="sqlite+aiosqlite:///:memory:",
        _env_file=None,
    )
    return await svc.create_mailbox(
        session,
        registry,
        settings,
        provider="stub",
        domain=None,
        parent_id=None,
        address=None,
        password=None,
    )


@pytest.mark.asyncio
async def test_valid_address_is_saved():
    session = FakeSession()
    row = await _create("user@dom.com", session)
    assert row.address == "user@dom.com"
    assert session.added == [row]


@pytest.mark.asyncio
async def test_garbage_address_from_provider_is_rejected():
    session = FakeSession()
    with pytest.raises(MailValidationError):
        await _create("no-at-sign", session)
    assert session.added == []
