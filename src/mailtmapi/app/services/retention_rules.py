"""Which retention row may delete which mailbox owner."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import KeyRetention, Mailbox, Retention


@dataclass(frozen=True, slots=True)
class TtlRule:
    """One provider TTL plus the mailbox owner it may delete. None is root."""

    provider: str
    hours: int
    owner_key_id: int | None


def owner_clause(owner_key_id: int | None) -> ColumnElement[bool]:
    """Root TTL matches NULL owners. A key TTL matches only that key id."""
    if owner_key_id is None:
        return Mailbox.owner_key_id.is_(None)
    return Mailbox.owner_key_id == owner_key_id


def _rules(
    rows: list[Retention] | list[KeyRetention],
    owner_key_id: int | None,
    field: str,
) -> list[TtlRule]:
    rules: list[TtlRule] = []
    for row in rows:
        hours = row.mailbox_ttl_hours if field == "mailbox" else row.message_ttl_hours
        if not hours:
            continue
        rules.append(TtlRule(provider=row.provider, hours=hours, owner_key_id=owner_key_id))
    return rules


async def load_sweep_rules(
    session: AsyncSession, only_key_id: int | None
) -> tuple[list[TtlRule], list[TtlRule]]:
    """Global TTL is root mail only. Each key TTL is that key's mail only.

    ``only_key_id`` limits the pass to one issued key and skips the global table.
    An expired key is not a caller, but its rows still load on a full sweep.
    """
    mailbox_rules: list[TtlRule] = []
    message_rules: list[TtlRule] = []
    if only_key_id is None:
        global_rows = list((await session.execute(select(Retention))).scalars())
        mailbox_rules.extend(_rules(global_rows, None, "mailbox"))
        message_rules.extend(_rules(global_rows, None, "message"))
        key_rows = list((await session.execute(select(KeyRetention))).scalars())
    else:
        key_rows = list(
            (
                await session.execute(
                    select(KeyRetention).where(KeyRetention.key_id == only_key_id)
                )
            ).scalars()
        )
    for row in key_rows:
        mailbox_rules.extend(_rules([row], row.key_id, "mailbox"))
        message_rules.extend(_rules([row], row.key_id, "message"))
    return mailbox_rules, message_rules
