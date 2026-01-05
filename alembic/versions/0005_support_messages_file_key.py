"""support messages attachments

Revision ID: 0005
Revises: 0004
Create Date: 2026-01-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("support_messages", sa.Column("file_key", sa.String(length=512), nullable=True))
    op.alter_column("support_messages", "body", existing_type=sa.Text(), nullable=True)


def downgrade() -> None:
    op.alter_column("support_messages", "body", existing_type=sa.Text(), nullable=False)
    op.drop_column("support_messages", "file_key")
