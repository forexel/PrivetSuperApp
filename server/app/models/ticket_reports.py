from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TicketWorkReport(Base):
    __tablename__ = "ticket_work_reports"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    master_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("master_users.id", ondelete="CASCADE"), nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)

    photos = relationship("TicketWorkPhoto", back_populates="report", cascade="all, delete-orphan")


class TicketWorkPhoto(Base):
    __tablename__ = "ticket_work_photos"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    report_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("ticket_work_reports.id", ondelete="CASCADE"), nullable=False)
    file_key: Mapped[str] = mapped_column(String(512), nullable=False)

    report = relationship("TicketWorkReport", back_populates="photos")
