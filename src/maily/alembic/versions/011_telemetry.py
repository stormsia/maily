"""telemetry state, reports, and events

Revision ID: 011
Revises: 010
Create Date: 2026-11-13
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "011"
down_revision: str | Sequence[str] | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "telemetry_state",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("installation_id", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("app_start_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("first_version", sa.String(32), server_default="", nullable=False),
        sa.Column("last_version", sa.String(32), server_default="", nullable=False),
        sa.Column("last_start_at", sa.DateTime(), nullable=True),
        sa.Column("last_flush_at", sa.DateTime(), nullable=True),
        sa.Column("last_snapshot_day", sa.Date(), nullable=True),
        sa.Column("setup_completed_at", sa.DateTime(), nullable=True),
        sa.Column("geo_json", sa.Text(), server_default="{}", nullable=False),
        sa.Column("geo_updated_at", sa.DateTime(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "uq_telemetry_state_installation_id",
        "telemetry_state",
        ["installation_id"],
        unique=True,
    )

    op.create_table(
        "telemetry_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_day", sa.Date(), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
    )
    op.create_index(
        "uq_telemetry_reports_report_day", "telemetry_reports", ["report_day"], unique=True
    )
    op.create_index("ix_telemetry_reports_due", "telemetry_reports", ["status", "next_attempt_at"])
    op.create_index("ix_telemetry_reports_created_at", "telemetry_reports", ["created_at"])
    op.create_index("ix_telemetry_reports_sent_at", "telemetry_reports", ["sent_at"])

    op.create_table(
        "telemetry_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("report_id", sa.Integer(), nullable=True),
        sa.Column("event_uuid", sa.String(36), nullable=False),
        sa.Column("event_name", sa.String(128), nullable=False),
        sa.Column("distinct_id", sa.String(64), nullable=False),
        sa.Column("properties_json", sa.Text(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(16), server_default="pending", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("next_attempt_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["report_id"], ["telemetry_reports.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "uq_telemetry_events_event_uuid", "telemetry_events", ["event_uuid"], unique=True
    )
    op.create_index("ix_telemetry_events_report_id", "telemetry_events", ["report_id"])
    op.create_index("ix_telemetry_events_event_name", "telemetry_events", ["event_name"])
    op.create_index("ix_telemetry_events_due", "telemetry_events", ["status", "next_attempt_at"])
    op.create_index("ix_telemetry_events_created_at", "telemetry_events", ["created_at"])
    op.create_index("ix_telemetry_events_sent_at", "telemetry_events", ["sent_at"])


def downgrade() -> None:
    op.drop_index("ix_telemetry_events_sent_at", table_name="telemetry_events")
    op.drop_index("ix_telemetry_events_created_at", table_name="telemetry_events")
    op.drop_index("ix_telemetry_events_due", table_name="telemetry_events")
    op.drop_index("ix_telemetry_events_event_name", table_name="telemetry_events")
    op.drop_index("ix_telemetry_events_report_id", table_name="telemetry_events")
    op.drop_index("uq_telemetry_events_event_uuid", table_name="telemetry_events")
    op.drop_table("telemetry_events")

    op.drop_index("ix_telemetry_reports_sent_at", table_name="telemetry_reports")
    op.drop_index("ix_telemetry_reports_created_at", table_name="telemetry_reports")
    op.drop_index("ix_telemetry_reports_due", table_name="telemetry_reports")
    op.drop_index("uq_telemetry_reports_report_day", table_name="telemetry_reports")
    op.drop_table("telemetry_reports")

    op.drop_index("uq_telemetry_state_installation_id", table_name="telemetry_state")
    op.drop_table("telemetry_state")
