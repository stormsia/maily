from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


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
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    mailboxes: Mapped[list[Mailbox]] = relationship(
        back_populates="gmail_parent", cascade="all, delete-orphan", passive_deletes=True
    )


class Mailbox(Base):
    __tablename__ = "mailboxes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    address: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    parent_id: Mapped[int | None] = mapped_column(
        ForeignKey("gmail_accounts.id", ondelete="CASCADE"), nullable=True, index=True
    )
    password_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    mailbox_token_enc: Mapped[str] = mapped_column(Text)
    provider_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    gmail_parent: Mapped[GmailAccount | None] = relationship(back_populates="mailboxes")
    messages: Mapped[list[Message]] = relationship(
        back_populates="mailbox", cascade="all, delete-orphan"
    )


class Message(Base):
    __tablename__ = "messages"
    __table_args__ = (UniqueConstraint("mailbox_id", "message_api_id", name="uq_message_mailbox_api_id"),)

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
