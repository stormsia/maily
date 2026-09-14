"""add retention settings

Revision ID: 002
Revises: 001
Create Date: 2026-09-14
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, Sequence[str], None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "retention",
        sa.Column("provider", sa.String(64), primary_key=True),
        sa.Column("mailbox_ttl_hours", sa.Integer(), nullable=True),
        sa.Column("message_ttl_hours", sa.Integer(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("retention")