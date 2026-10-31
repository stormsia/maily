"""Tests for retention service lifecycle, validation, and sweep edge cases."""

from __future__ import annotations

import asyncio
import contextlib
from datetime import timedelta
from pathlib import Path

import pytest

from mailtmapi.app.services.retention import (
    _check_ttls,
    _is_already_gone,
    delete_key_retention,
    delete_retention,
    get_key_retention,
    get_retention,
    retention_worker,
    run_sweep,
    set_key_retention,
    set_retention,
    utcnow_naive,
)
from mailtmapi.crypto import encrypt
from mailtmapi.db.engine import SessionFactory, make_engine
from mailtmapi.db.models import ApiKey, Base, Mailbox, Message, Retention
from mailtmapi.exceptions import MailNotFoundError, MailValidationError
from mailtmapi.providers.base import MailboxInfo
from mailtmapi.providers.registry import ProviderRegistry
from mailtmapi.settings import Settings
from tests.helpers import StubProvider


def test_check_ttls_validations():
    """Verify TTL constraints and validations."""
    with pytest.raises(MailValidationError, match="mailbox_ttl_hours must be >= 1"):
        _check_ttls(0, 10)

    with pytest.raises(MailValidationError, match="message_ttl_hours must be >= 1"):
        _check_ttls(10, -1)

    with pytest.raises(MailValidationError, match="at least one ttl required"):
        _check_ttls(None, None)

    # Valid values should not raise
    _check_ttls(1, None)
    _check_ttls(None, 24)
    _check_ttls(2, 48)


def test_is_already_gone_matching():
    """Verify _is_already_gone properly identifies not-found exceptions."""
    assert _is_already_gone(MailNotFoundError("mailbox not found"))
    assert _is_already_gone(RuntimeError("account does not exist"))
    assert _is_already_gone(ValueError("unknown account in provider"))
    assert _is_already_gone(Exception("No such email registered"))
    assert not _is_already_gone(RuntimeError("connection timed out"))
    assert not _is_already_gone(ValueError("internal server 500 error"))


@pytest.mark.asyncio
async def test_retention_worker_lifecycle():
    """Verify retention worker handles zero interval and error recovery."""
    calls = []

    async def fake_sweep():
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("simulated transient failure")

    # Zero interval exits immediately
    await retention_worker(fake_sweep, interval_seconds=0)
    assert len(calls) == 0

    # Negative interval exits immediately
    await retention_worker(fake_sweep, interval_seconds=-5)
    assert len(calls) == 0

    # Run worker for a brief moment and cancel
    task = asyncio.create_task(retention_worker(fake_sweep, interval_seconds=0.01))
    await asyncio.sleep(0.035)
    task.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await task

    assert len(calls) >= 1


@pytest.mark.asyncio
async def test_retention_crud_and_nonexistent_deletes(tmp_path: Path):
    """Test get, set, and delete operations on global and key retention."""
    db_file = tmp_path / "retention_crud.db"
    engine = make_engine(f"sqlite+aiosqlite:///{db_file}")
    factory = SessionFactory(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        async with factory() as session:
            # Seed an ApiKey so foreign key constraint passes
            api_key = ApiKey(
                name="test-key",
                prefix="test",
                secret_enc="dummy_enc",
                secret_sha256="dummy_hash_12345",
                scope_json="{}",
            )
            session.add(api_key)
            await session.flush()

            # Set retention
            r = await set_retention(session, "testprov", 24, 48)
            assert r.provider == "testprov"
            assert r.mailbox_ttl_hours == 24
            assert r.message_ttl_hours == 48

            all_r = await get_retention(session)
            assert len(all_r) == 1
            assert all_r[0].provider == "testprov"

            # Set key retention
            kr = await set_key_retention(session, api_key.id, "testprov", 12, None)
            assert kr.key_id == api_key.id
            assert kr.mailbox_ttl_hours == 12

            all_kr = await get_key_retention(session, api_key.id)
            assert len(all_kr) == 1
            assert all_kr[0].key_id == api_key.id

            # Delete existing
            deleted = await delete_retention(session, "testprov")
            assert deleted is True

            deleted_kr = await delete_key_retention(session, api_key.id, "testprov")
            assert deleted_kr is True

            # Delete non-existent
            deleted_again = await delete_retention(session, "nonexistent")
            assert deleted_again is False

            deleted_kr_again = await delete_key_retention(session, api_key.id, "nonexistent")
            assert deleted_kr_again is False

            await session.commit()
    finally:
        await engine.dispose()


class FlakySweepProvider(StubProvider):
    """Stub provider with configurable deletion behaviors."""

    def __init__(
        self, name: str, return_val: bool = True, raise_gone: bool = False, raise_err: bool = False
    ):
        super().__init__(name)
        self.return_val = return_val
        self.raise_gone = raise_gone
        self.raise_err = raise_err

    async def delete_mailbox(self, info: MailboxInfo) -> bool:
        if self.raise_gone:
            raise MailNotFoundError("upstream mailbox gone")
        if self.raise_err:
            raise RuntimeError("upstream server failure")
        return self.return_val

    async def delete_message(self, info: MailboxInfo, message_id: str) -> None:
        if self.raise_gone:
            raise MailNotFoundError("upstream message gone")
        if self.raise_err:
            raise RuntimeError("upstream network glitch")


@pytest.mark.asyncio
async def test_run_sweep_handling_upstream_states(tmp_path: Path):
    """Test sweep handles soft delete on False, already gone, and lock synchronization."""
    db_file = tmp_path / "retention_sweep.db"
    secret = "a" * 32
    settings = Settings(
        database_url=f"sqlite+aiosqlite:///{db_file}",
        secret_key=secret,
        api_key="root",
        _env_file=None,
    )
    engine = make_engine(settings.database_url)
    factory = SessionFactory(engine)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        # Seed global retention rule
        async with factory() as session:
            session.add(Retention(provider="p_false", mailbox_ttl_hours=1, message_ttl_hours=1))
            session.add(Retention(provider="p_gone", mailbox_ttl_hours=1, message_ttl_hours=1))
            session.add(Retention(provider="p_err", mailbox_ttl_hours=1, message_ttl_hours=1))

            old_time = utcnow_naive() - timedelta(hours=5)

            # Mailbox 1: delete returns False -> soft delete
            box1 = Mailbox(
                address="user1@example.com",
                provider="p_false",
                mailbox_token_enc=encrypt(secret, "token1"),
                created_at=old_time,
                is_deleted=False,
                is_active=True,
            )
            # Mailbox 2: delete raises MailNotFoundError -> cleans up
            box2 = Mailbox(
                address="user2@example.com",
                provider="p_gone",
                mailbox_token_enc=encrypt(secret, "token2"),
                created_at=old_time,
                is_deleted=False,
                is_active=True,
            )
            session.add_all([box1, box2])
            await session.commit()
            await session.refresh(box1)
            await session.refresh(box2)

            # Messages for p_err
            msg_err = Message(
                mailbox_id=box1.id,
                message_api_id="msg_fail",
                provider="p_err",
                subject="Err Msg",
                received_at=old_time,
                is_deleted=False,
            )
            session.add(msg_err)
            await session.commit()

        registry = ProviderRegistry()
        registry.register(FlakySweepProvider("p_false", return_val=False))
        registry.register(FlakySweepProvider("p_gone", raise_gone=True))
        registry.register(FlakySweepProvider("p_err", raise_err=True))

        lock = asyncio.Lock()
        res = await run_sweep(factory, registry, settings, lock=lock, force_maintenance=True)
        assert res["mailboxes_deleted"] == 2

        # Verify box1 was soft-deleted (is_deleted=True)
        async with factory() as session:
            b1 = await session.get(Mailbox, box1.id)
            assert b1 is not None
            assert b1.is_deleted is True
            assert b1.is_active is False

            # Verify box2 was hard-deleted
            b2 = await session.get(Mailbox, box2.id)
            assert b2 is None

    finally:
        await engine.dispose()
