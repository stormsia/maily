from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class TargetOut(BaseModel):
    id: str
    kind: str
    provider: str
    label: str


class ProviderOut(BaseModel):
    slug: str
    kind: str


class MailboxOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    provider: str
    address: str
    parent_id: int | None = None
    is_active: bool
    created_at: datetime | None = None


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    message_api_id: str
    subject: str = ""
    from_address: str = ""
    from_name: str = ""
    seen: bool = False
    has_attachments: bool = False
    size: int = 0
    received_at: datetime | None = None


class MessageDetailOut(MessageOut):
    text: str = ""
    html: list[str] = []


class SourceOut(BaseModel):
    id: str
    data: str
    download_url: str = ""


class GmailAccountOut(BaseModel):
    id: int
    email: str
    status: str
    send_as: list[str] = []


class CreateMailboxIn(BaseModel):
    provider: str | None = None
    domain: str | None = None
    parent_id: int | None = None
    address: str | None = None
    password: str | None = None


class ImportGmailIn(BaseModel):
    refresh_token: str | None = None
    access_token: str | None = None
    expires_at: float | None = None
    token_json: dict[str, Any] | str | None = None


class OAuthStartOut(BaseModel):
    auth_url: str
    state: str


class GmailCredsIn(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str | None = None


class GmailCredsOut(BaseModel):
    configured: bool
    source: str
    client_id: str | None = None
    redirect_uri: str = ""


class RetentionIn(BaseModel):
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class RetentionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class RetentionIn(BaseModel):
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class RetentionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    provider: str
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None
