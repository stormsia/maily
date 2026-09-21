from __future__ import annotations

import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from mailtmapi.crypto import decrypt, encrypt
from mailtmapi.db.models import GmailAccount
from mailtmapi.exceptions import MailNotFoundError

from .store import GmailParent


def _to_dt(ts: float | None) -> datetime | None:
    if ts is None:
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc).replace(tzinfo=None)


def _to_ts(dt: datetime | None) -> float | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.timestamp()


class DbGmailStore:
    def __init__(self, factory: async_sessionmaker[AsyncSession], secret: str) -> None:
        self._factory = factory
        self._secret = secret

    def _row_to_parent(self, row: GmailAccount) -> GmailParent:
        access = None
        if row.access_token_enc:
            access = decrypt(self._secret, row.access_token_enc)
        try:
            send_as = json.loads(row.send_as_json or "[]")
        except json.JSONDecodeError:
            send_as = []
        return GmailParent(
            id=row.id,
            email=row.email,
            refresh_token=decrypt(self._secret, row.refresh_token_enc),
            access_token=access,
            access_expires_at=_to_ts(row.access_expires_at),
            send_as=list(send_as),
            scopes=row.scopes or "",
            status=row.status,
        )

    def _apply(self, row: GmailAccount, parent: GmailParent) -> None:
        row.email = parent.email
        row.refresh_token_enc = encrypt(self._secret, parent.refresh_token)
        row.access_token_enc = (
            encrypt(self._secret, parent.access_token) if parent.access_token else None
        )
        row.access_expires_at = _to_dt(parent.access_expires_at)
        row.scopes = parent.scopes or ""
        row.send_as_json = json.dumps(parent.send_as)
        row.status = parent.status

    async def list_active(self) -> list[GmailParent]:
        async with self._factory() as s:
            rows = (
                await s.execute(select(GmailAccount).where(GmailAccount.status == "active"))
            ).scalars().all()
            return [self._row_to_parent(r) for r in rows]

    async def list_all(self) -> list[GmailParent]:
        async with self._factory() as s:
            rows = (await s.execute(select(GmailAccount))).scalars().all()
            return [self._row_to_parent(r) for r in rows]

    async def get(self, parent_id: int) -> GmailParent:
        async with self._factory() as s:
            row = await s.get(GmailAccount, parent_id)
            if row is None:
                raise MailNotFoundError(f"gmail parent {parent_id} not found")
            return self._row_to_parent(row)

    async def get_by_email(self, email: str) -> GmailParent | None:
        async with self._factory() as s:
            row = (
                await s.execute(select(GmailAccount).where(GmailAccount.email == email))
            ).scalar_one_or_none()
            if row is None:
                wanted = email.casefold()
                rows = (await s.execute(select(GmailAccount))).scalars().all()
                for r in rows:
                    if r.email.casefold() == wanted:
                        return self._row_to_parent(r)
                return None
            return self._row_to_parent(row)

    async def add(self, parent: GmailParent) -> GmailParent:
        async with self._factory() as s:
            row = GmailAccount(email=parent.email or f"pending-{id(parent)}@pending.local")
            self._apply(row, parent)
            s.add(row)
            await s.commit()
            await s.refresh(row)
            parent.id = row.id
            return parent

    async def update(self, parent: GmailParent) -> None:
        async with self._factory() as s:
            row = await s.get(GmailAccount, parent.id)
            if row is None:
                raise MailNotFoundError(f"gmail parent {parent.id} not found")
            self._apply(row, parent)
            await s.commit()

    async def delete(self, parent_id: int) -> None:
        async with self._factory() as s:
            row = await s.get(GmailAccount, parent_id)
            if row is None:
                raise MailNotFoundError(f"gmail parent {parent_id} not found")
            await s.delete(row)
            await s.commit()
