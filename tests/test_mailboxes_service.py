from __future__ import annotations

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from mailtmapi.app.services import mailboxes as svc
from mailtmapi.db.models import Base, Mailbox
from mailtmapi.exceptions import (
    MailAPIError,
    MailConflictError,
    MailNotFoundError,
    MailValidationError,
)
from mailtmapi.providers.base import MailboxInfo
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

    async def rollback(self) -> None: ...


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


@pytest.mark.asyncio
async def test_none_or_missing_address_from_provider_is_rejected():
    class MissingAddressProvider(StubProvider):
        async def create_mailbox(self, spec):
            return MailboxInfo(provider=self.slug, address="", token="tok")

    session = FakeSession()
    registry = ProviderRegistry([MissingAddressProvider()])
    settings = Settings(
        secret_key=SECRET,
        database_url="sqlite+aiosqlite:///:memory:",
        _env_file=None,
    )
    with pytest.raises(MailValidationError):
        await svc.create_mailbox(
            session,
            registry,
            settings,
            provider="stub",
            domain=None,
            parent_id=None,
            address=None,
            password=None,
        )
    assert session.added == []


@pytest.mark.asyncio
async def test_provider_failure_does_not_save_to_db():
    class FailingProvider(StubProvider):
        async def create_mailbox(self, spec):
            raise MailAPIError("provider upstream failed to confirm")

    session = FakeSession()
    registry = ProviderRegistry([FailingProvider()])
    settings = Settings(
        secret_key=SECRET,
        database_url="sqlite+aiosqlite:///:memory:",
        _env_file=None,
    )
    with pytest.raises(MailAPIError):
        await svc.create_mailbox(
            session,
            registry,
            settings,
            provider="stub",
            domain=None,
            parent_id=None,
            address=None,
            password=None,
        )
    assert session.added == []


@pytest.mark.asyncio
async def test_none_token_from_provider_is_saved_safely():
    class NoneTokenProvider(StubProvider):
        async def create_mailbox(self, spec):
            return MailboxInfo(provider=self.slug, address="notoken@dom.com", token=None)  # type: ignore[arg-type]

    session = FakeSession()
    registry = ProviderRegistry([NoneTokenProvider()])
    settings = Settings(
        secret_key=SECRET,
        database_url="sqlite+aiosqlite:///:memory:",
        _env_file=None,
    )
    row = await svc.create_mailbox(
        session,
        registry,
        settings,
        provider="stub",
        domain=None,
        parent_id=None,
        address=None,
        password=None,
    )
    assert row.address == "notoken@dom.com"
    assert row.mailbox_token_enc is not None



def _settings() -> Settings:
    return Settings(
        secret_key=SECRET,
        database_url="sqlite+aiosqlite:///:memory:",
        _env_file=None,
    )


async def _db(tmp_path: Path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'mb.db'}")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    return engine, factory


class _DeletingStub(StubProvider):
    def __init__(self, address: str) -> None:
        super().__init__(address=address)
        self.deleted: list[str] = []

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        self.deleted.append(mailbox.address)
        return True


@pytest.mark.asyncio
async def test_create_duplicate_live_address_is_conflict(tmp_path: Path):
    engine, factory = await _db(tmp_path)
    stub = _DeletingStub("dup@x.com")
    registry = ProviderRegistry([stub])
    try:
        async with factory() as session:
            await svc.create_mailbox(
                session,
                registry,
                _settings(),
                provider="stub",
                domain=None,
                parent_id=None,
                address=None,
                password=None,
            )
            await session.commit()
        async with factory() as session:
            with pytest.raises(MailConflictError):
                await svc.create_mailbox(
                    session,
                    registry,
                    _settings(),
                    provider="stub",
                    domain=None,
                    parent_id=None,
                    address=None,
                    password=None,
                )
        assert stub.deleted == ["dup@x.com"]
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_create_after_soft_delete_reuses_address(tmp_path: Path):
    engine, factory = await _db(tmp_path)
    registry = ProviderRegistry([StubProvider(address="again@x.com")])
    try:
        async with factory() as session:
            first = await svc.create_mailbox(
                session,
                registry,
                _settings(),
                provider="stub",
                domain=None,
                parent_id=None,
                address=None,
                password=None,
            )
            first.is_active = False
            first.is_deleted = True
            await session.commit()
            first_id = first.id
        async with factory() as session:
            second = await svc.create_mailbox(
                session,
                registry,
                _settings(),
                provider="stub",
                domain=None,
                parent_id=None,
                address=None,
                password=None,
            )
            await session.commit()
            assert second.address == "again@x.com"
            assert second.id != first_id
        async with factory() as session:
            with pytest.raises(MailNotFoundError):
                await svc.get_mailbox_by_address(session, "gone@nope")
            live = await svc.get_mailbox_by_address(session, "again@x.com")
            assert live.id == second.id
            assert live.is_deleted is False
    finally:
        await engine.dispose()


class _FlushFails(FakeSession):
    async def flush(self) -> None:
        raise RuntimeError("disk full")


@pytest.mark.asyncio
async def test_create_deletes_provider_mailbox_when_flush_fails():
    stub = _DeletingStub("orphan@x.com")
    session = _FlushFails()
    with pytest.raises(RuntimeError, match="disk full"):
        await svc.create_mailbox(
            session,
            ProviderRegistry([stub]),
            _settings(),
            provider="stub",
            domain=None,
            parent_id=None,
            address=None,
            password=None,
        )
    assert stub.deleted == ["orphan@x.com"]


@pytest.mark.asyncio
async def test_get_mailbox_by_address_ignores_deleted(tmp_path: Path):
    engine, factory = await _db(tmp_path)
    try:
        async with factory() as session:
            session.add(
                Mailbox(
                    provider="stub",
                    address="dead@x.com",
                    mailbox_token_enc="enc",
                    is_active=False,
                    is_deleted=True,
                )
            )
            await session.commit()
        async with factory() as session:
            with pytest.raises(MailNotFoundError):
                await svc.get_mailbox_by_address(session, "dead@x.com")
    finally:
        await engine.dispose()
