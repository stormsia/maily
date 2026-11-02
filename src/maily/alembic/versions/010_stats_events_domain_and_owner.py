"""add domain and owner_key_id to stats_events

Revision ID: 010
Revises: 009
Create Date: 2026-10-31
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "010"
down_revision: str | Sequence[str] | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("stats_events") as batch:
        batch.add_column(sa.Column("domain", sa.String(255), nullable=False, server_default=""))
        batch.add_column(
            sa.Column("owner_key_id", sa.Integer(), nullable=False, server_default="0")
        )
        batch.drop_index("uq_stats_events_bucket")
        batch.create_index(
            "uq_stats_events_bucket",
            ["day", "provider", "domain", "owner_key_id", "event"],
            unique=True,
        )
        batch.create_index("ix_stats_events_domain", ["domain"])
        batch.create_index("ix_stats_events_owner", ["owner_key_id"])


def downgrade() -> None:
    with op.batch_alter_table("stats_events") as batch:
        batch.drop_index("ix_stats_events_owner")
        batch.drop_index("ix_stats_events_domain")
        batch.drop_index("uq_stats_events_bucket")
        batch.create_index(
            "uq_stats_events_bucket",
            ["day", "provider", "event"],
            unique=True,
        )
        batch.drop_column("owner_key_id")
        batch.drop_column("domain")
