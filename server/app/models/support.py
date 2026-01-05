# app/models/support.py
from datetime import datetime
import uuid
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column
from enum import Enum
from app.models.base import Base

class SupportCaseStatus(str, Enum):
    open = "open"
    pending = "pending"
    closed = "closed"
    rejected = "rejected"

class MessageAuthor(str, Enum):
    user = "user"
    support = "support"

class SupportCase(Base):
    __tablename__ = "support_tickets"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[SupportCaseStatus] = mapped_column(SAEnum(SupportCaseStatus), default=SupportCaseStatus.open, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    messages: Mapped[list["SupportCaseMessage"]] = relationship(
        "SupportCaseMessage", back_populates="case", cascade="all, delete-orphan"
    )

class SupportCaseMessage(Base):
    __tablename__ = "support_messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("support_tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    author: Mapped[MessageAuthor] = mapped_column(SAEnum(MessageAuthor), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    case: Mapped[SupportCase] = relationship("SupportCase", back_populates="messages")

# Алиасы, чтобы старые импорты продолжали работать
TicketStatus = SupportCaseStatus
SupportTicket = SupportCase
SupportMessage = SupportCaseMessage
