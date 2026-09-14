from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal, Protocol, runtime_checkable

TargetKind = Literal["domain", "parent"]


@dataclass
class Target:
    id: str
    kind: TargetKind
    provider: str
    label: str  # domain hostname or parent email


@dataclass
class MailboxSpec:
    address: str | None = None
    domain: str | None = None
    parent_id: int | None = None
    password: str | None = None


@dataclass
class MailboxInfo:
    provider: str
    address: str
    token: str
    provider_account_id: str | None = None
    password: str | None = None
    parent_id: int | None = None


@dataclass
class Party:
    name: str = ""
    address: str = ""


@dataclass
class Attachment:
    id: str = ""
    filename: str = ""
    content_type: str = ""
    size: int = 0
    download_url: str = ""


@dataclass
class MessageSummary:
    id: str
    subject: str = ""
    from_: Party = field(default_factory=Party)
    to: list[Party] = field(default_factory=list)
    intro: str = ""
    seen: bool = False
    has_attachments: bool = False
    size: int = 0
    received_at: datetime | None = None


@dataclass
class MessageDetail(MessageSummary):
    text: str = ""
    html: list[str] = field(default_factory=list)
    attachments: list[Attachment] = field(default_factory=list)


@dataclass
class MessageSource:
    id: str
    data: str
    download_url: str = ""


@runtime_checkable
class MailProvider(Protocol):
    slug: str
    kind: TargetKind

    async def close(self) -> None: ...

    async def list_targets(self) -> list[Target]: ...

    async def create_mailbox(self, spec: MailboxSpec) -> MailboxInfo: ...

    async def delete_mailbox(self, mailbox: MailboxInfo) -> bool: ...

    async def list_messages(self, mailbox: MailboxInfo, page: int = 1) -> list[MessageSummary]: ...

    async def get_message(self, mailbox: MailboxInfo, message_id: str) -> MessageDetail: ...

    async def delete_message(self, mailbox: MailboxInfo, message_id: str) -> bool: ...

    async def mark_read(self, mailbox: MailboxInfo, message_id: str) -> bool: ...

    async def get_source(self, mailbox: MailboxInfo, message_id: str) -> MessageSource: ...
