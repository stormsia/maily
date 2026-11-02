from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from maily.app.services.mailboxes import upsert_messages
from maily.db.models import Base, Mailbox, Message
from maily.providers.base import MessageSummary, Party


@pytest.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s
    await engine.dispose()


def _summary(seen: bool) -> MessageSummary:
    return MessageSummary(
        id="m1",
        subject="s",
        from_=Party(name=None, address="a@b.c"),
        to=[Party(name=None, address="u@t.io")],
        intro="",
        seen=seen,
        has_attachments=False,
        size=0,
        received_at=None,
    )


async def _seed(session, seen: bool) -> tuple[Mailbox, Message]:
    mbox = Mailbox(
        provider="temp-mail.io",
        address="u@t.io",
        mailbox_token_enc="tok",
        is_active=True,
        is_deleted=False,
    )
    session.add(mbox)
    await session.flush()
    msg = Message(
        mailbox_id=mbox.id,
        provider=mbox.provider,
        message_api_id="m1",
        seen=seen,
    )
    session.add(msg)
    await session.flush()
    return mbox, msg


@pytest.mark.asyncio
async def test_upsert_never_downgrades_locally_marked_read(session):
    mbox, msg = await _seed(session, seen=True)
    await upsert_messages(session, mbox, [_summary(seen=False)])
    assert msg.seen is True


@pytest.mark.asyncio
async def test_upsert_inserts_new_message_as_unseen(session):
    mbox, _ = await _seed(session, seen=True)  # existing m1 seen=True
    fresh = MessageSummary(
        id="m2",
        subject="new",
        from_=Party(name=None, address="a@b.c"),
        to=[Party(name=None, address="u@t.io")],
        intro="",
        seen=False,
        has_attachments=False,
        size=0,
        received_at=None,
    )
    await upsert_messages(session, mbox, [_summary(seen=False), fresh])
    rows = {
        m.message_api_id: m.seen for m in (await session.scalars(select(Message))).all()
    }
    assert rows == {"m1": True, "m2": False}
