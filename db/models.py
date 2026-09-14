"""
Peewee ORM models for mailtmapi.

All models reference ``db_proxy`` from :mod:`mailtmapi.db.manager` so they
can be defined at import time, before the real database path is known.
Call ``db_manager.initialize(path)`` followed by
``db_manager.create_tables(ALL_MODELS)`` once at startup.

Tables
------
DomainRecord   — cached provider domains (TTL-based refresh)
AccountRecord  — temporary email accounts with bearer tokens
MessageRecord  — locally cached message metadata
"""
from __future__ import annotations

import datetime

import peewee

from .manager import db_proxy


# ---------------------------------------------------------------------------
# Base model — all tables share the same proxy
# ---------------------------------------------------------------------------

class _BaseModel(peewee.Model):
    """Common base: connects every model to the shared DatabaseProxy."""

    class Meta:
        database = db_proxy


# ---------------------------------------------------------------------------
# Domain cache
# ---------------------------------------------------------------------------

class DomainRecord(_BaseModel):
    """
    Cached domain entry per provider.

    Rows are refreshed when ``MailTMProvider.get_domains()`` detects
    that the in-memory TTL has expired.
    """

    id = peewee.AutoField(primary_key=True)

    provider = peewee.CharField(max_length=64, index=True)
    api_id = peewee.CharField(max_length=255, null=True)
    domain = peewee.CharField(max_length=255)
    is_active = peewee.BooleanField(default=True)
    is_private = peewee.BooleanField(default=False)

    # When this row was written (used for TTL queries)
    cached_at = peewee.DateTimeField(default=datetime.datetime.utcnow, index=True)

    class Meta:
        table_name = "domain_cache"
        indexes = (
            (("provider", "domain"), True),  # unique constraint
        )


# ---------------------------------------------------------------------------
# Accounts
# ---------------------------------------------------------------------------

class AccountRecord(_BaseModel):
    """
    A temporary email account created via a provider.

    ``api_id`` is the provider-assigned account identifier (used in
    API calls).  ``address`` is the human-visible email address.
    """

    id = peewee.AutoField(primary_key=True)

    provider = peewee.CharField(max_length=64, index=True)

    # Provider-assigned identifiers
    api_id = peewee.CharField(max_length=255, unique=True)
    address = peewee.CharField(max_length=255, unique=True, index=True)

    # Credentials (token stored plaintext — add encryption if needed)
    password = peewee.CharField(max_length=255)
    token = peewee.TextField()

    # Quota mirrors (updated on sync)
    quota = peewee.IntegerField(default=0)
    used = peewee.IntegerField(default=0)

    # State flags
    is_active = peewee.BooleanField(default=True, index=True)
    is_deleted = peewee.BooleanField(default=False)

    # Timestamps (UTC)
    created_at = peewee.DateTimeField(default=datetime.datetime.utcnow, index=True)
    updated_at = peewee.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "accounts"
        indexes = (
            # Fast lookup by provider + address
            (("provider", "address"), True),
            # Fast listing of active accounts per provider
            (("provider", "is_active"), False),
        )

    def touch(self) -> None:
        """Bump updated_at and persist the change."""
        self.updated_at = datetime.datetime.utcnow()
        self.save(only=[AccountRecord.updated_at])


# ---------------------------------------------------------------------------
# Messages (local cache)
# ---------------------------------------------------------------------------

class MessageRecord(_BaseModel):
    """
    Locally cached message metadata.

    Full HTML/text bodies are optional (``body_html`` / ``body_text``).
    Omit them to keep the database small; fetch on demand via the provider.
    """

    id = peewee.AutoField(primary_key=True)

    account = peewee.ForeignKeyField(
        AccountRecord,
        backref="messages",
        on_delete="CASCADE",
        index=True,
    )
    provider = peewee.CharField(max_length=64, index=True)

    # Provider-assigned message ID
    message_api_id = peewee.CharField(max_length=255, unique=True)

    # Envelope metadata
    subject = peewee.TextField(default="")
    from_address = peewee.CharField(max_length=255, default="", index=True)
    from_name = peewee.CharField(max_length=255, default="")

    # State flags
    seen = peewee.BooleanField(default=False, index=True)
    is_deleted = peewee.BooleanField(default=False)
    has_attachments = peewee.BooleanField(default=False)

    # Optional body cache (null = not yet fetched)
    body_text = peewee.TextField(null=True)
    body_html = peewee.TextField(null=True)

    # Size in bytes as reported by the provider
    size = peewee.IntegerField(default=0)

    # Timestamps (UTC)
    received_at = peewee.DateTimeField(index=True)
    cached_at = peewee.DateTimeField(default=datetime.datetime.utcnow)

    class Meta:
        table_name = "messages"
        indexes = (
            # Fast unseen-count query per account
            (("account", "seen"), False),
            # Unique per provider + message ID
            (("provider", "message_api_id"), True),
            # Sort by received date efficiently
            (("account", "received_at"), False),
        )


# ---------------------------------------------------------------------------
# Convenience list for create_tables()
# ---------------------------------------------------------------------------
ALL_MODELS: list[type[_BaseModel]] = [DomainRecord, AccountRecord, MessageRecord]
