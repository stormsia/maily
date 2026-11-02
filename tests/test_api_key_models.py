"""SQLAlchemy metadata contract for issued API keys and ownership columns.

Given: imported ORM models (no engine, no Settings)
When: table columns, indexes, and foreign keys are inspected
Then: api_keys, key_retention, and nullable owner_key_id match the schema
"""

from __future__ import annotations

from sqlalchemy import DateTime, Integer, String, Text

from maily.db.models import ApiKey, GmailAccount, KeyRetention, Mailbox


def test_api_keys_columns_when_metadata_is_inspected() -> None:
    """Given the ApiKey model, secret_sha256 is unique and expires_at is nullable."""
    table = ApiKey.__table__
    names = {column.name for column in table.columns}
    assert names == {
        "id",
        "name",
        "prefix",
        "secret_enc",
        "secret_sha256",
        "scope_json",
        "expires_at",
        "created_at",
        "updated_at",
    }
    assert table.c.id.primary_key
    assert isinstance(table.c.id.type, Integer)
    assert isinstance(table.c.name.type, String)
    assert isinstance(table.c.prefix.type, String)
    assert isinstance(table.c.secret_enc.type, Text)
    assert isinstance(table.c.secret_sha256.type, String)
    assert table.c.secret_sha256.unique
    assert table.c.secret_sha256.index
    assert isinstance(table.c.scope_json.type, Text)
    assert isinstance(table.c.expires_at.type, DateTime)
    assert table.c.expires_at.nullable
    assert isinstance(table.c.created_at.type, DateTime)
    assert table.c.created_at.nullable is False
    assert isinstance(table.c.updated_at.type, DateTime)
    assert table.c.updated_at.nullable is False
    unique_indexes = {index.name for index in table.indexes if index.unique}
    assert "ix_api_keys_secret_sha256" in unique_indexes


def test_key_retention_fk_when_metadata_is_inspected() -> None:
    """Given KeyRetention, the composite PK cascades when its api key is deleted."""
    table = KeyRetention.__table__
    names = {column.name for column in table.columns}
    assert names == {
        "key_id",
        "provider",
        "mailbox_ttl_hours",
        "message_ttl_hours",
    }
    assert table.primary_key.columns.keys() == ["key_id", "provider"]
    assert isinstance(table.c.key_id.type, Integer)
    assert table.c.key_id.nullable is False
    assert isinstance(table.c.provider.type, String)
    assert isinstance(table.c.mailbox_ttl_hours.type, Integer)
    assert table.c.mailbox_ttl_hours.nullable
    assert isinstance(table.c.message_ttl_hours.type, Integer)
    assert table.c.message_ttl_hours.nullable
    fk = next(iter(table.c.key_id.foreign_keys))
    assert fk.column.table.name == "api_keys"
    assert fk.column.name == "id"
    assert fk.ondelete == "CASCADE"


def test_owner_key_id_when_mailbox_and_gmail_metadata_are_inspected() -> None:
    """Given existing tables, owner_key_id is a nullable FK with no ON DELETE action."""
    for table in (Mailbox.__table__, GmailAccount.__table__):
        column = table.c.owner_key_id
        assert isinstance(column.type, Integer)
        assert column.nullable
        fk = next(iter(column.foreign_keys))
        assert fk.column.table.name == "api_keys"
        assert fk.column.name == "id"
        assert fk.ondelete is None
    mailbox_indexes = {index.name for index in Mailbox.__table__.indexes}
    assert "ix_mailboxes_owner_key_id" in mailbox_indexes
