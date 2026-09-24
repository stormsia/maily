from __future__ import annotations

import pytest

from mailtmapi.app.services import mailboxes as svc
from mailtmapi.exceptions import MailValidationError
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.settings import Settings
from tests.helpers import StubProvider

SECRET = "test-secret"


class FakeSession:
    def __init__(self) -> None:
        self.added: list = []

    class _EmptyResult:
        def scalar_one_or_none(self):
            return None

    def add(self, obj) -> None:
        self.added.append(obj)

    async def execute(self, stmt) -> _EmptyResult:
        return self._EmptyResult()

    async def flush(self) -> None: ...

    async def commit(self) -> None: ...


async def _create(address: str, session: FakeSession | None = None) -> svc.Mailbox:
    session = session or FakeSession()
    registry = ProviderRegistry([StubProvider(address=address)])
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
    # ledger is an upsert (execute), not session.add
    assert [type(o).__name__ for o in session.added] == ["Mailbox"]


@pytest.mark.asyncio
async def test_garbage_address_from_provider_is_rejected():
    session = FakeSession()
    with pytest.raises(MailValidationError):
        await _create("no-at-sign", session)
    assert session.added == []
