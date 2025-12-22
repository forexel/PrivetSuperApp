"""add user invoices and payments

Revision ID: b4e1c8f7d2a1
Revises: a3d9a7c45bc1
Create Date: 2025-09-20
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql as pg


revision = "b4e1c8f7d2a1"
down_revision = "a3d9a7c45bc1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "user_invoices" not in tables:
        op.create_table(
            "user_invoices",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "client_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("contract_number", sa.String(length=64), nullable=True),
            sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="new"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.execute("CREATE INDEX IF NOT EXISTS ix_user_invoices_client_id ON user_invoices (client_id)")

    if "user_invoice_payments" not in tables:
        op.create_table(
            "user_invoice_payments",
            sa.Column("id", pg.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column(
                "invoice_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("user_invoices.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "client_id",
                pg.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="success"),
            sa.Column("paid_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_user_invoice_payments_invoice_id "
            "ON user_invoice_payments (invoice_id)"
        )
        op.execute(
            "CREATE INDEX IF NOT EXISTS ix_user_invoice_payments_client_id "
            "ON user_invoice_payments (client_id)"
        )


def downgrade() -> None:
    op.drop_index("ix_user_invoice_payments_client_id", table_name="user_invoice_payments")
    op.drop_index("ix_user_invoice_payments_invoice_id", table_name="user_invoice_payments")
    op.drop_table("user_invoice_payments")
    op.drop_index("ix_user_invoices_client_id", table_name="user_invoices")
    op.drop_table("user_invoices")
