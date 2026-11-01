"""add stats_events (retention-proof activity ledger for the dashboard)

Revision ID: 006
Revises: 005
Create Date: 2026-09-23
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006"
down_revision: str | Sequence[str] | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stats_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("event", sa.String(32), nullable=False),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_stats_events_day_event", "stats_events", ["day", "event"])
    op.create_index(
        "ix_stats_events_day_provider_event",
        "stats_events",
        ["day", "provider", "event"],
    )


def downgrade() -> None:
    op.drop_index("ix_stats_events_day_provider_event", table_name="stats_events")
    op.drop_index("ix_stats_events_day_event", table_name="stats_events")
    op.drop_table("stats_events")
