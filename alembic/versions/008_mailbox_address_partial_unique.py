"""live mailbox addresses are unique; deleted addresses can be reused

Revision ID: 008
Revises: 007
Create Date: 2026-09-25
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "008"
down_revision: str | Sequence[str] | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Column unique=True was emitted as a unique index, not a table constraint.
    op.drop_index("ix_mailboxes_address", table_name="mailboxes")
    op.create_index("ix_mailboxes_address", "mailboxes", ["address"])
    op.create_index(
        "uq_mailboxes_address_live",
        "mailboxes",
        ["address"],
        unique=True,
        sqlite_where=sa.text("is_deleted = 0"),
    )


def downgrade() -> None:
    op.drop_index("uq_mailboxes_address_live", table_name="mailboxes")
    op.drop_index("ix_mailboxes_address", table_name="mailboxes")
    op.create_index("ix_mailboxes_address", "mailboxes", ["address"], unique=True)
