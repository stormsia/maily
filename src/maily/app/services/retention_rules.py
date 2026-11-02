"""Which retention row may delete which mailbox owner."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ColumnElement, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...db.models import ApiKey, KeyRetention, Mailbox, Retention


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


def _hours(row: Retention | KeyRetention, field: str) -> int | None:
    """Mailbox and message TTLs are independent. Zero or null is off."""
    hours = row.mailbox_ttl_hours if field == "mailbox" else row.message_ttl_hours
    if not hours:
        return None
    return hours


def _append(
    rules: list[TtlRule], provider: str, hours: int | None, owner_key_id: int | None
) -> None:
    """One owner, one provider, one side: at most one rule."""
    if hours is None:
        return
    if any(rule.provider == provider and rule.owner_key_id == owner_key_id for rule in rules):
        return
    rules.append(TtlRule(provider=provider, hours=hours, owner_key_id=owner_key_id))


def _key_ids(only_key_id: int | None, issued: list[int]) -> list[int]:
    """A key sweep covers that key. A full sweep covers every issued key."""
    if only_key_id is None:
        return issued
    return [only_key_id]


async def load_sweep_rules(
    session: AsyncSession, only_key_id: int | None
) -> tuple[list[TtlRule], list[TtlRule]]:
    """Root TTL deletes root mail. A missing key row follows that TTL for the key's mail.

    A present key row replaces the root hours for that provider, including a null
    side (null means that side is off, not that it falls back). ``only_key_id``
    still inherits root hours the key did not override, and never deletes root mail.
    """
    global_rows = list((await session.execute(select(Retention))).scalars())
    issued = list((await session.execute(select(ApiKey.id))).scalars())
    key_rows = list((await session.execute(select(KeyRetention))).scalars())
    by_key: dict[int, dict[str, KeyRetention]] = {}
    for row in key_rows:
        by_key.setdefault(row.key_id, {})[row.provider] = row

    mailbox_rules: list[TtlRule] = []
    message_rules: list[TtlRule] = []
    if only_key_id is None:
        for root_row in global_rows:
            _append(mailbox_rules, root_row.provider, _hours(root_row, "mailbox"), None)
            _append(message_rules, root_row.provider, _hours(root_row, "message"), None)

    root_by_provider = {row.provider: row for row in global_rows}
    for key_id in _key_ids(only_key_id, issued):
        overrides = by_key.get(key_id, {})
        providers = set(root_by_provider) | set(overrides)
        for provider in providers:
            override = overrides.get(provider)
            root = root_by_provider.get(provider)
            if override is not None:
                mailbox_hours = _hours(override, "mailbox")
                message_hours = _hours(override, "message")
            elif root is not None:
                mailbox_hours = _hours(root, "mailbox")
                message_hours = _hours(root, "message")
            else:
                continue
            _append(mailbox_rules, provider, mailbox_hours, key_id)
            _append(message_rules, provider, message_hours, key_id)
    return mailbox_rules, message_rules
