"""add address to users

Revision ID: 8a1b2c3d4e5f
Revises: 34e296af6fe9
Create Date: 2025-09-01 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '8a1b2c3d4e5f'
down_revision = '34e296af6fe9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('address', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'address')
