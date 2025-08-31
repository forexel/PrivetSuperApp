

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class Session(Base):
    """SQLAlchemy model for sessions table.

    Mirrors the DDL:
      id UUID PK,
      user_id UUID FK -> users.id,
      refresh_token TEXT UNIQUE NOT NULL,
      user_agent TEXT NULL,
      ip INET NULL,
      expires_at timestamptz NOT NULL,
      created_at timestamptz DEFAULT now()
    """

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    refresh_token = Column(Text, unique=True, nullable=False)
    user_agent = Column(Text, nullable=True)
    ip = Column(INET, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Session id={self.id} user_id={self.user_id} expires_at={self.expires_at}>"