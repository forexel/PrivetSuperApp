from __future__ import annotations
from enum import Enum
from datetime import date, datetime
from typing import Optional
from uuid import uuid4, UUID

from sqlalchemy import String, Text, Date, DateTime, ForeignKey, Enum as SQLEnum, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

# Reuse the project's Base (shared metadata)
from app.models.base import Base

class TicketStatus(str, Enum):
    NEW = "new"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    REJECTED = "rejected"


class RequestMessageAuthor(str, Enum):
    USER = "user"
    MASTER = "master"


class ChangedBy(str, Enum):
    USER = "USER"
    STAFF = "STAFF"
    SYSTEM = "SYSTEM"


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    preferred_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Enum types are created by Alembic migration; don't attempt to (re)create from ORM
    status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(
            TicketStatus,
            name="ticket_status_t",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],  # use lowercase values
        ),
        nullable=False,
            default=TicketStatus.NEW,
    )
    assigned_master_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("master_users.id", ondelete="SET NULL"),
        nullable=True,
    )
    master_last_read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relations
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    history = relationship("TicketStatusHistory", back_populates="ticket", cascade="all, delete-orphan")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)

    file_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("Ticket", back_populates="attachments")


class TicketStatusHistory(Base):
    __tablename__ = "ticket_status_history"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)

    from_status: Mapped[Optional[TicketStatus]] = mapped_column(
        SQLEnum(
            TicketStatus,
            name="ticket_status_t",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=True,
    )
    to_status: Mapped[TicketStatus] = mapped_column(
        SQLEnum(
            TicketStatus,
            name="ticket_status_t",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    changed_by: Mapped[ChangedBy] = mapped_column(SQLEnum(ChangedBy, name="changed_by_t", create_type=False), nullable=False)

    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("Ticket", back_populates="history")


class RequestMessage(Base):
    __tablename__ = "request_messages"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    author: Mapped[RequestMessageAuthor] = mapped_column(
        SQLEnum(
            RequestMessageAuthor,
            name="request_message_author_t",
            create_type=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
    )
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    file_key: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
