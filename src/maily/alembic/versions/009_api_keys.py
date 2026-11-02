"""api keys, per-key retention, and nullable owner columns

Revision ID: 009
Revises: 008
Create Date: 2026-09-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "009"
down_revision: str | Sequence[str] | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("prefix", sa.String(32), nullable=False),
        sa.Column("secret_enc", sa.Text(), nullable=False),
        sa.Column("secret_sha256", sa.String(64), nullable=False),
        sa.Column("scope_json", sa.Text(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_api_keys_secret_sha256", "api_keys", ["secret_sha256"], unique=True)

    op.create_table(
        "key_retention",
        sa.Column("key_id", sa.Integer(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("mailbox_ttl_hours", sa.Integer(), nullable=True),
        sa.Column("message_ttl_hours", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["key_id"], ["api_keys.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("key_id", "provider"),
    )

    # No ON DELETE action: SQLite cannot RESTRICT. 409 is enforced in the service.
    # Existing rows stay NULL (root-owned). Do not backfill.
    # Batch mode: SQLite cannot ALTER constraints in place.
    with op.batch_alter_table("mailboxes") as batch:
        batch.add_column(sa.Column("owner_key_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_mailboxes_owner_key_id_api_keys",
            "api_keys",
            ["owner_key_id"],
            ["id"],
        )
        batch.create_index("ix_mailboxes_owner_key_id", ["owner_key_id"])

    with op.batch_alter_table("gmail_accounts") as batch:
        batch.add_column(sa.Column("owner_key_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            "fk_gmail_accounts_owner_key_id_api_keys",
            "api_keys",
            ["owner_key_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("gmail_accounts") as batch:
        batch.drop_constraint("fk_gmail_accounts_owner_key_id_api_keys", type_="foreignkey")
        batch.drop_column("owner_key_id")
    with op.batch_alter_table("mailboxes") as batch:
        batch.drop_index("ix_mailboxes_owner_key_id")
        batch.drop_constraint("fk_mailboxes_owner_key_id_api_keys", type_="foreignkey")
        batch.drop_column("owner_key_id")
    op.drop_table("key_retention")
    op.drop_index("ix_api_keys_secret_sha256", table_name="api_keys")
    op.drop_table("api_keys")
