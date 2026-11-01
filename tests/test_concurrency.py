"""Tests for concurrent SQLite database operations, scale, and WAL checkpointing."""

import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import func, select

from mailtmapi.db.engine import SessionFactory, make_engine
from mailtmapi.db.maintenance import maintain_database
from mailtmapi.db.models import Base, Mailbox, Message
from mailtmapi.settings import Settings


@pytest.mark.asyncio
async def test_concurrent_mailbox_and_message_writes(tmp_path):
    """Verify 20 concurrent tasks write to SQLite in WAL mode without database locked errors."""
    db_path = str(tmp_path / "test_concurrent.db")
    settings = Settings(database_url=f"sqlite+aiosqlite:///{db_path}")
    engine = make_engine(settings.database_url)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = SessionFactory(engine)

        async def worker(idx: int):
            async with session_factory() as session:
                box = Mailbox(
                    id=idx + 1,
                    provider="tempmail.plus",
                    address=f"user_{idx}@example.com",
                    mailbox_token_enc="enc_token",
                    is_active=True,
                    is_deleted=False,
                )
                session.add(box)
                await session.flush()

                msg = Message(
                    mailbox_id=box.id,
                    provider="tempmail.plus",
                    message_api_id=f"msg_api_{idx}",
                    subject=f"Subject {idx}",
                    from_address="sender@example.com",
                    received_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    is_deleted=False,
                )
                session.add(msg)
                await session.commit()

        # Run 20 concurrent coroutines
        await asyncio.gather(*(worker(i) for i in range(20)))

        # Verify all 20 mailboxes and 20 messages are written
        async with session_factory() as session:
            mb_count = (await session.execute(select(func.count(Mailbox.id)))).scalar()
            msg_count = (await session.execute(select(func.count(Message.id)))).scalar()
            assert mb_count == 20
            assert msg_count == 20

        # Run maintenance while DB is open
        report = await maintain_database(engine)
        assert report is not None
        assert report.get("status") == "completed"
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_100_workers_wal_mode(tmp_path):
    """Stress-test SQLite WAL mode under 100 concurrent workers."""
    db_path = str(tmp_path / "test_scale_100.db")
    settings = Settings(database_url=f"sqlite+aiosqlite:///{db_path}")
    engine = make_engine(settings.database_url)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = SessionFactory(engine)

        async def write_task(idx: int):
            async with session_factory() as session:
                box = Mailbox(
                    id=idx + 1,
                    provider="mail.tm",
                    address=f"scale_{idx}@example.com",
                    mailbox_token_enc="enc_token",
                    is_active=True,
                    is_deleted=False,
                )
                session.add(box)
                await session.flush()

                msg = Message(
                    mailbox_id=box.id,
                    provider="mail.tm",
                    message_api_id=f"msg_scale_{idx}",
                    subject=f"Scale Subject {idx}",
                    from_address="tester@service.example.com",
                    received_at=datetime.now(timezone.utc).replace(tzinfo=None),
                    is_deleted=False,
                )
                session.add(msg)
                await session.commit()

        # Launch 100 concurrent writers
        await asyncio.gather(*(write_task(i) for i in range(100)))

        async with session_factory() as session:
            total_boxes = (await session.execute(select(func.count(Mailbox.id)))).scalar()
            total_msgs = (await session.execute(select(func.count(Message.id)))).scalar()
            assert total_boxes == 100
            assert total_msgs == 100
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_concurrent_mixed_readers_and_writers(tmp_path):
    """Verify simultaneous 30 readers and 30 writers execute without lock errors."""
    db_path = str(tmp_path / "test_mixed_rw.db")
    settings = Settings(database_url=f"sqlite+aiosqlite:///{db_path}")
    engine = make_engine(settings.database_url)

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        session_factory = SessionFactory(engine)

        # Pre-seed 10 mailboxes
        async with session_factory() as session:
            for i in range(10):
                session.add(
                    Mailbox(
                        id=i + 1,
                        provider="mail.tm",
                        address=f"seed_{i}@example.com",
                        mailbox_token_enc="token",
                        is_active=True,
                    )
                )
            await session.commit()

        async def writer(idx: int):
            async with session_factory() as session:
                box = Mailbox(
                    id=idx + 100,
                    provider="tempmail.plus",
                    address=f"writer_{idx}@example.com",
                    mailbox_token_enc="token",
                    is_active=True,
                )
                session.add(box)
                await session.commit()

        async def reader(idx: int):
            async with session_factory() as session:
                rows = (await session.execute(select(Mailbox).limit(5))).scalars().all()
                assert len(rows) > 0

        # Run 30 writers and 30 readers concurrently
        tasks = [writer(i) for i in range(30)] + [reader(i) for i in range(30)]
        await asyncio.gather(*tasks)

        async with session_factory() as session:
            total = (await session.execute(select(func.count(Mailbox.id)))).scalar()
            assert total == 40  # 10 seeded + 30 written
    finally:
        await engine.dispose()
