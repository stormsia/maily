"""unique stats bucket + retention sweep indexes

Revision ID: 007
Revises: 006
Create Date: 2026-09-23
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "007"
down_revision: str | Sequence[str] | None = "006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Collapse duplicate (day, provider, event) rows so the unique constraint
    # can land. Concurrent record() calls used to insert two rows for one bucket.
    conn = op.get_bind()
    dupes = conn.execute(
        sa.text(
            """
            SELECT day, provider, event, MIN(id) AS keep_id, SUM(count) AS total
            FROM stats_events
            GROUP BY day, provider, event
            HAVING COUNT(*) > 1
            """
        )
    ).all()
    for day, provider, event, keep_id, total in dupes:
        conn.execute(
            sa.text("UPDATE stats_events SET count = :total WHERE id = :keep_id"),
            {"total": total, "keep_id": keep_id},
        )
        conn.execute(
            sa.text(
                """
                DELETE FROM stats_events
                WHERE day = :day AND provider = :provider AND event = :event AND id != :keep_id
                """
            ),
            {"day": day, "provider": provider, "event": event, "keep_id": keep_id},
        )
    op.drop_index("ix_stats_events_day_provider_event", table_name="stats_events")
    op.create_index(
        "uq_stats_events_bucket",
        "stats_events",
        ["day", "provider", "event"],
        unique=True,
    )
    op.create_index(
        "ix_mailboxes_provider_deleted_created",
        "mailboxes",
        ["provider", "is_deleted", "created_at"],
    )
    op.create_index(
        "ix_messages_provider_deleted_received",
        "messages",
        ["provider", "is_deleted", "received_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_messages_provider_deleted_received", table_name="messages")
    op.drop_index("ix_mailboxes_provider_deleted_created", table_name="mailboxes")
    op.drop_index("uq_stats_events_bucket", table_name="stats_events")
    op.create_index(
        "ix_stats_events_day_provider_event",
        "stats_events",
        ["day", "provider", "event"],
    )
