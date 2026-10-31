"""Tests for concurrent SQLite database operations and WAL checkpointing."""

import asyncio
from datetime import datetime, timezone

import pytest

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
            from sqlalchemy import func, select

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
