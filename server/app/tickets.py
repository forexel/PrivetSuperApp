from __future__ import annotations
from enum import Enum
from uuid import uuid4

from sqlalchemy import Column, Date, DateTime, Enum as SAEnum, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class TicketStatus(str, Enum):
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    REJECTED = "rejected"


class ChangedBy(str, Enum):
    SYSTEM = "system"
    USER = "user"
    OPERATOR = "operator"
    MASTER = "master"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="SET NULL"), nullable=True)

    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    preferred_date = Column(Date, nullable=True)

    status = Column(
        SAEnum(
            TicketStatus,
            name="ticket_status_t",
            create_constraint=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
        default=TicketStatus.ACCEPTED.value,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)

    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan", passive_deletes=True)
    history = relationship("TicketStatusHistory", back_populates="ticket", cascade="all, delete-orphan", passive_deletes=True)


class TicketStatusHistory(Base):
    __tablename__ = "ticket_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)

    from_status = Column(Text, nullable=True)
    to_status = Column(Text, nullable=False)
    changed_by = Column(
        SAEnum(
            ChangedBy,
            name="changed_by_t",
            create_constraint=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
        default=ChangedBy.USER.value,
    )
    changed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    comment = Column(Text, nullable=True)

    ticket = relationship("Ticket", back_populates="history")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    ticket_id = Column(UUID(as_uuid=True), ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False)
    file_url = Column(Text, nullable=False)
    file_type = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    ticket = relationship("Ticket", back_populates="attachments")
