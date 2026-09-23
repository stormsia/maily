from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, field_serializer


class _Base(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    @field_serializer("*")
    def _naive_utc_as_z(self, value: Any) -> Any:
        """Serialize datetimes as explicit UTC.

        The app stores naive UTC (SQLite CURRENT_TIMESTAMP). Without a zone
        suffix the browser would parse such an ISO string as *local* time, so
        every naive datetime is emitted with an explicit ``Z`` here — that way
        clients can render it correctly regardless of their timezone.
        """
        if isinstance(value, datetime):
            if value.tzinfo is None:
                return value.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
            return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return value


class HealthOut(_Base):
    status: str = ""


class ProviderOut(_Base):
    slug: str
    kind: str


class TargetOut(_Base):
    id: str
    kind: str
    provider: str
    label: str


class MailboxOut(_Base):
    id: int
    provider: str
    address: str
    parent_id: int | None = None
    is_active: bool
    created_at: datetime | None = None
    parent_status: str | None = None


class MessageOut(_Base):
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


class SourceOut(_Base):
    id: str
    data: str
    download_url: str = ""


class GmailAccountOut(_Base):
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


class OAuthStartOut(_Base):
    auth_url: str
    state: str


class GmailCredsIn(BaseModel):
    client_id: str
    client_secret: str
    redirect_uri: str | None = None


class GmailCredsOut(_Base):
    configured: bool
    source: str
    client_id: str | None = None
    redirect_uri: str = ""


class RetentionIn(BaseModel):
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class RetentionOut(_Base):
    provider: str
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class SweepResult(_Base):
    mailboxes_deleted: int = 0
    messages_deleted: int = 0


class DomainCacheProviderOut(_Base):
    provider: str
    kind: str = "domain"
    domains_count: int = 0
    updated_at: datetime | None = None
    error: str | None = None


class DomainCacheOut(_Base):
    enabled: bool = True
    interval_seconds: int = 1800
    providers: list[DomainCacheProviderOut] = []


class DomainCacheIn(BaseModel):
    enabled: bool | None = None
    interval_seconds: int | None = None


class DomainCacheRun(_Base):
    refreshed: list[str] = []
    failed: list[str] = []
