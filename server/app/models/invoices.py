from __future__ import annotations

import uuid
from datetime import datetime

from enum import Enum
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class InvoiceStatus(str, Enum):
    new = "new"
    pending = "pending"
    paid = "paid"
    canceled = "canceled"


class ManagerInvoice(Base):
    __tablename__ = "user_invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    contract_number: Mapped[str | None] = mapped_column(String(64), nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[InvoiceStatus] = mapped_column(
        SAEnum(
            InvoiceStatus,
            name="invoice_status_t",
            native_enum=False,
            create_constraint=False,
            values_callable=lambda enum: [member.value for member in enum],
        ),
        nullable=False,
        default=InvoiceStatus.pending,
    )

    payments: Mapped[list["InvoicePayment"]] = relationship(
        "InvoicePayment",
        back_populates="invoice",
        cascade="all, delete-orphan",
    )


class InvoicePayment(Base):
    __tablename__ = "user_invoice_payments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_invoices.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="success")
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    invoice: Mapped[ManagerInvoice] = relationship("ManagerInvoice", back_populates="payments")


__all__ = ["ManagerInvoice", "InvoicePayment", "InvoiceStatus"]
