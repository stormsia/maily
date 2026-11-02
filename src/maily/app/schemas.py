from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from ..schemas import (
    CreateMailboxIn,
    DomainCacheIn,
    DomainCacheOut,
    DomainCacheProviderOut,
    DomainCacheRun,
    GmailAccountOut,
    GmailCredsIn,
    GmailCredsOut,
    HealthOut,
    ImportGmailIn,
    MailboxOut,
    MessageDetailOut,
    MessageOut,
    OAuthCallbackIn,
    OAuthStartOut,
    ProviderCapabilitiesOut,
    ProviderOut,
    RetentionIn,
    RetentionOut,
    SourceOut,
    SweepResult,
    TargetOut,
)

__all__ = [
    "CreateMailboxIn",
    "DomainCacheIn",
    "DomainCacheOut",
    "DomainCacheProviderOut",
    "DomainCacheRun",
    "GmailAccountOut",
    "GmailCredsIn",
    "GmailCredsOut",
    "HealthOut",
    "ImportGmailIn",
    "MailboxOut",
    "MessageDetailOut",
    "MessageOut",
    "OAuthCallbackIn",
    "OAuthStartOut",
    "ProviderOut",
    "ProviderCapabilitiesOut",
    "RetentionIn",
    "RetentionOut",
    "SourceOut",
    "SweepResult",
    "TargetOut",
    "KeyScopeIn",
    "KeyRetentionIn",
    "KeyCreateIn",
    "KeyUpdateIn",
    "KeyRetentionOut",
    "KeyOut",
    "CreatedKeyOut",
    "SecretOut",
    "RootMeOut",
    "IssuedMeOut",
]


class KeyScopeIn(BaseModel):
    """Write-time scope. Unknown parent ids are stored, not checked."""

    model_config = ConfigDict(extra="forbid")

    providers: list[str]
    parent_ids: list[int]
    actions: list[str]


class KeyRetentionIn(BaseModel):
    """One key_retention row in a full replacement list."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class KeyCreateIn(BaseModel):
    """POST /v1/admin/keys body. root_key is filled by the router, not the client."""

    model_config = ConfigDict(extra="forbid")

    name: str
    expires_at: datetime | None = None
    scope: KeyScopeIn
    retention: list[KeyRetentionIn] = Field(default_factory=list)


class KeyUpdateIn(BaseModel):
    """PATCH body. Does not include the secret or retention rows."""

    model_config = ConfigDict(extra="forbid")

    name: str
    expires_at: datetime | None = None
    scope: KeyScopeIn


class KeyRetentionOut(BaseModel):
    """One stored key_retention row. No secret material."""

    model_config = ConfigDict(frozen=True)

    provider: str
    mailbox_ttl_hours: int | None = None
    message_ttl_hours: int | None = None


class KeyOut(BaseModel):
    """Key row without secret or secret_enc."""

    model_config = ConfigDict(frozen=True)

    id: int
    name: str
    prefix: str
    scope: KeyScopeIn
    expires_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    key_retention: list[KeyRetentionOut] = Field(default_factory=list)


class CreatedKeyOut(KeyOut):
    """Create or rotate result. secret is present only on these responses."""

    secret: str


class SecretOut(BaseModel):
    """GET /{id}/secret body."""

    model_config = ConfigDict(frozen=True)

    secret: str


class RootMeOut(BaseModel):
    """GET /me for the env root key."""

    model_config = ConfigDict(frozen=True)

    is_root: bool = True


class IssuedMeOut(BaseModel):
    """GET /me for an issued key. No secret and no secret_enc."""

    model_config = ConfigDict(frozen=True)

    name: str
    expires_at: datetime | None = None
    scope: KeyScopeIn
    key_retention: list[KeyRetentionOut]
