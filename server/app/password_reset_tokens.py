

from __future__ import annotations

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from app.db.base import Base


class PasswordResetToken(Base):
    """SQLAlchemy model for password_reset_tokens table.

    Mirrors the DDL:
      id UUID PK,
      user_id UUID FK -> users.id,
      token TEXT UNIQUE NOT NULL,
      expires_at timestamptz NOT NULL,
      used_at timestamptz NULL,
      created_at timestamptz DEFAULT now()
    """

    __tablename__ = "password_reset_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(Text, unique=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<PasswordResetToken id={self.id} user_id={self.user_id} used_at={self.used_at}>"