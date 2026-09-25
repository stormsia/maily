from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class ApiKey(Base):
    """Issued API key. Mutation is required by SQLAlchemy mapped columns. # noqa: MUTABLE_OK"""

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    prefix: Mapped[str] = mapped_column(String(32))
    secret_enc: Mapped[str] = mapped_column(Text)
    secret_sha256: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    scope_json: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    retention_rules: Mapped[list[KeyRetention]] = relationship(
        back_populates="api_key", cascade="all, delete-orphan", passive_deletes=True
    )


class KeyRetention(Base):
    """Per-key retention override. Mutation is required by SQLAlchemy. # noqa: MUTABLE_OK"""

    __tablename__ = "key_retention"

    key_id: Mapped[int] = mapped_column(
        ForeignKey("api_keys.id", ondelete="CASCADE"), primary_key=True
    )
    provider: Mapped[str] = mapped_column(String(64), primary_key=True)
    mailbox_ttl_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message_ttl_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)

    api_key: Mapped[ApiKey] = relationship(back_populates="retention_rules")


class GmailAccount(Base):
    __tablename__ = "gmail_accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    refresh_token_enc: Mapped[str] = mapped_column(Text)
    access_token_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    access_expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    scopes: Mapped[str] = mapped_column(Text, default="")
    send_as_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    owner_key_id: Mapped[int | None] = mapped_column(
        ForeignKey("api_keys.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    mailboxes: Mapped[list[Mailbox]] = relationship(
        back_populates="gmail_parent", cascade="all, delete-orphan", passive_deletes=True
    )


class Mailbox(Base):
    __tablename__ = "mailboxes"
    __table_args__ = (
        Index("ix_mailboxes_provider_deleted_created", "provider", "is_deleted", "created_at"),
        # Soft-deleted addresses must be reusable. SQLite stores Boolean as 0/1.
        Index(
            "uq_mailboxes_address_live",
            "address",
            unique=True,
            sqlite_where=text("is_deleted = 0"),
        ),
        Index("ix_mailboxes_address", "address"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    address: Mapped[str] = mapped_column(String(255))
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("gmail_accounts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    password_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    mailbox_token_enc: Mapped[str] = mapped_column(Text)
    provider_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_key_id: Mapped[int | None] = mapped_column(
        ForeignKey("api_keys.id"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    gmail_parent: Mapped[GmailAccount | None] = relationship(back_populates="mailboxes")
    messages: Mapped[list[Message]] = relationship(
        back_populates="mailbox", cascade="all, delete-orphan", passive_deletes=True
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (
        UniqueConstraint("mailbox_id", "message_api_id", name="uq_message_mailbox_api_id"),
        Index("ix_messages_provider_deleted_received", "provider", "is_deleted", "received_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    mailbox_id: Mapped[int] = mapped_column(
        ForeignKey("mailboxes.id", ondelete="CASCADE"), index=True
    )
    provider: Mapped[str] = mapped_column(String(64), index=True)
    message_api_id: Mapped[str] = mapped_column(String(255), index=True)
    subject: Mapped[str] = mapped_column(Text, default="")
    from_address: Mapped[str] = mapped_column(String(255), default="", index=True)
    from_name: Mapped[str] = mapped_column(String(255), default="")
    seen: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    has_attachments: Mapped[bool] = mapped_column(Boolean, default=False)
    body_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    body_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    size: Mapped[int] = mapped_column(Integer, default=0)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, index=True)
    cached_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    mailbox: Mapped[Mailbox] = relationship(back_populates="messages")


class Retention(Base):
    __tablename__ = "retention"

    provider: Mapped[str] = mapped_column(String(64), primary_key=True)
    mailbox_ttl_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message_ttl_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class DomainCache(Base):
    __tablename__ = "domain_cache"

    provider: Mapped[str] = mapped_column(String(64), primary_key=True)
    domains_json: Mapped[str] = mapped_column(Text)  # JSON list of domain strings
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class StatsEvent(Base):
    """Aggregated activity ledger that survives retention deletes.

    One row per (UTC day, provider, event) with an incrementing counter, so a
    mailbox/message deleted by retention still counts here. Rows older than a
    window (10 days) are pruned by the retention sweep. This is what the
    dashboard's "last 10 days" block and the 7-day trend are based on.
    """

    __tablename__ = "stats_events"
    __table_args__ = (
        UniqueConstraint("day", "provider", "event", name="uq_stats_events_bucket"),
        Index("ix_stats_events_day_event", "day", "event"),
    )

    #: mailbox_created | mailbox_deleted | message_received | message_deleted
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day: Mapped[date] = mapped_column(Date)
    provider: Mapped[str] = mapped_column(String(64))
    event: Mapped[str] = mapped_column(String(32))
    count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ProviderHeaders(Base):
    """Dynamically discovered provider request headers (e.g. temp-mail.io X-CORS-Header)."""

    __tablename__ = "provider_headers"

    provider: Mapped[str] = mapped_column(String(64), primary_key=True)
    headers_json: Mapped[str] = mapped_column(Text)  # JSON object of header name -> value
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
