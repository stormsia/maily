"""add provider_headers (dynamic per-provider request headers, e.g. temp-mail.io CORS token)

Revision ID: 005
Revises: 004
Create Date: 2026-09-22
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: str | Sequence[str] | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "provider_headers",
        sa.Column("provider", sa.String(64), primary_key=True),
        sa.Column("headers_json", sa.Text(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("provider_headers")
