"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-09-14
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "gmail_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("refresh_token_enc", sa.Text(), nullable=False),
        sa.Column("access_token_enc", sa.Text(), nullable=True),
        sa.Column("access_expires_at", sa.DateTime(), nullable=True),
        sa.Column("scopes", sa.Text(), nullable=False, server_default=""),
        sa.Column("send_as_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_gmail_accounts_email", "gmail_accounts", ["email"], unique=True)
    op.create_index("ix_gmail_accounts_status", "gmail_accounts", ["status"])

    op.create_table(
        "mailboxes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("address", sa.String(255), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("password_enc", sa.Text(), nullable=True),
        sa.Column("mailbox_token_enc", sa.Text(), nullable=False),
        sa.Column("provider_account_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["gmail_accounts.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_mailboxes_provider", "mailboxes", ["provider"])
    op.create_index("ix_mailboxes_address", "mailboxes", ["address"], unique=True)
    op.create_index("ix_mailboxes_parent_id", "mailboxes", ["parent_id"])
    op.create_index("ix_mailboxes_is_active", "mailboxes", ["is_active"])
    op.create_index("ix_mailboxes_created_at", "mailboxes", ["created_at"])

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("mailbox_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("message_api_id", sa.String(255), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False, server_default=""),
        sa.Column("from_address", sa.String(255), nullable=False, server_default=""),
        sa.Column("from_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("seen", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_attachments", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("body_html", sa.Text(), nullable=True),
        sa.Column("size", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("received_at", sa.DateTime(), nullable=True),
        sa.Column("cached_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("mailbox_id", "message_api_id", name="uq_message_mailbox_api_id"),
    )
    op.create_index("ix_messages_mailbox_id", "messages", ["mailbox_id"])
    op.create_index("ix_messages_provider", "messages", ["provider"])
    op.create_index("ix_messages_message_api_id", "messages", ["message_api_id"])
    op.create_index("ix_messages_from_address", "messages", ["from_address"])
    op.create_index("ix_messages_seen", "messages", ["seen"])
    op.create_index("ix_messages_received_at", "messages", ["received_at"])


def downgrade() -> None:
    op.drop_table("messages")
    op.drop_table("mailboxes")
    op.drop_table("gmail_accounts")
