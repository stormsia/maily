"""add domain_cache (providers' domain lists cached in DB)

Revision ID: 004
Revises: 003
Create Date: 2026-09-16
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: str | Sequence[str] | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "domain_cache",
        sa.Column("provider", sa.String(64), primary_key=True),
        sa.Column("domains_json", sa.Text(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("domain_cache")
