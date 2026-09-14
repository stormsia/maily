"""Message schemas (Pydantic v2)."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MessageFromTo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str = ""
    address: str = ""


class Message(BaseModel):
    """Message list item (summary view)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    accountId: str = ""
    msgid: str = ""
    from_: MessageFromTo = Field(alias="from", default_factory=MessageFromTo)
    to: list[MessageFromTo] = Field(default_factory=list)
    subject: str = ""
    intro: str = ""
    seen: bool = False
    isDeleted: bool = False
    hasAttachments: bool = False
    size: int = 0
    downloadUrl: str = ""
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class MessageView(BaseModel):
    """Hydra pagination view (all fields optional — API may omit some)."""

    model_config = ConfigDict(populate_by_name=True)

    first: Optional[str] = Field(None, alias="hydra:first")
    last: Optional[str] = Field(None, alias="hydra:last")
    previous: Optional[str] = Field(None, alias="hydra:previous")
    next: Optional[str] = Field(None, alias="hydra:next")


class Attachment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = ""
    filename: str = ""
    contentType: str = ""
    disposition: str = ""
    transferEncoding: str = ""
    related: bool = False
    size: int = 0
    downloadUrl: str = ""


class OneMessage(BaseModel):
    """Full message detail (includes body, attachments, headers)."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    accountId: str = ""
    msgid: str = ""
    from_: MessageFromTo = Field(alias="from", default_factory=MessageFromTo)
    to: list[MessageFromTo] = Field(default_factory=list)
    cc: list[str] = Field(default_factory=list)
    bcc: list[str] = Field(default_factory=list)
    subject: str = ""
    flagged: bool = False
    isDeleted: bool = False
    verifications: dict = Field(default_factory=dict)
    retention: bool = False
    retentionDate: Optional[str] = None
    text: str = ""
    html: list[str] = Field(default_factory=list)
    hasAttachments: bool = False
    attachments: Optional[list[Attachment]] = None
    size: int = 0
    downloadUrl: str = ""
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None


class Messages(BaseModel):
    """Paginated list of messages (hydra:member envelope)."""

    model_config = ConfigDict(populate_by_name=True)

    hydra_member: list[Message] = Field(alias="hydra:member", default_factory=list)
    hydra_totalItems: int = Field(0, alias="hydra:totalItems")
    hydra_view: Optional[MessageView] = Field(None, alias="hydra:view")


class MessageSource(BaseModel):
    """Raw MIME source of a message."""

    model_config = ConfigDict(populate_by_name=True)

    id: str
    downloadUrl: str
    data: str
