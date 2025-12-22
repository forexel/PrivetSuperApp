"""add address column to users

Revision ID: a3d9a7c45bc1
Revises: 865cbc827c40
Create Date: 2025-09-10
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a3d9a7c45bc1"
down_revision = "865cbc827c40"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("address", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("users", "address")
