"""Shared provider stub and small factories used across the API/service tests."""

from __future__ import annotations

from datetime import datetime, timezone

from mailtmapi.providers.base import (
    MailboxInfo,
    MailboxSpec,
    MessageDetail,
    MessageSource,
    MessageSummary,
    Party,
    Target,
)

STAMP = datetime(2026, 1, 2, 3, 4, 5, tzinfo=timezone.utc)


def make_targets(slug: str, *labels: str) -> list[Target]:
    return [Target(id=label, kind="domain", provider=slug, label=label) for label in labels]


class StubProvider:
    """Flexible fake MailProvider.

    - `targets`/`fail` control list_targets (used by admin/domain-cache tests).
    - `address` overrides the address returned by create_mailbox; otherwise it
      derives from the requested spec domain (or the slug).
    - `messages` overrides list_messages; otherwise a canned "m1" is returned.
    """

    kind = "domain"

    def __init__(
        self,
        slug: str = "stub",
        targets: list[Target] | None = None,
        fail: bool = False,
        address: str | None = None,
        messages: list[MessageSummary] | None = None,
    ) -> None:
        self.slug = slug
        self._targets = targets or []
        self.fail = fail
        self._address = address
        self._messages = messages
        self.list_targets_calls = 0
        self.delete_mailbox_calls: list[str] = []
        self.delete_message_calls: list[str] = []

    async def close(self) -> None: ...

    async def list_targets(self) -> list[Target]:
        self.list_targets_calls += 1
        if self.fail:
            raise RuntimeError("boom")
        return list(self._targets)

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo:
        return MailboxInfo(
            provider=self.slug,
            address=self._address or f"user@{spec.domain or 'x.com'}",
            token="tok",
        )

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool:
        self.delete_mailbox_calls.append(mailbox.address)
        return True

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]:
        if self._messages is not None:
            return list(self._messages)
        return [
            MessageSummary(
                id="m1",
                subject="Hello",
                from_=Party(address="a@b.c", name="Alice"),
                received_at=STAMP,
            )
        ]

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail:
        return MessageDetail(
            id=message_id,
            subject="Hello",
            from_=Party(address="a@b.c", name="Alice"),
            text="body text",
            html=["<p>body text</p>"],
            received_at=STAMP,
        )

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool:
        self.delete_message_calls.append(message_id)
        return True

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool:
        return True

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource:
        return MessageSource(id=message_id, data="From: a@b.c\nSubject: x\n")
