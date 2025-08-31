

from __future__ import annotations

import uuid
from enum import Enum as PyEnum

from sqlalchemy import Column, DateTime, Enum as SAEnum, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, CITEXT
from sqlalchemy.sql import func

# If you later move models under app/models/, just adjust the import below
from app.db.base import Base


class UserStatus(PyEnum):
    GHOST = "ghost"
    ACTIVE = "active"


class User(Base):
    """SQLAlchemy model for users table.

    Mirrors the DDL:
      id UUID PK,
      email CITEXT UNIQUE NOT NULL,
      phone TEXT NULL,
      password_hash TEXT NOT NULL,
      name TEXT NULL,
      status enum('ghost','active') DEFAULT 'ghost',
      created_at timestamptz DEFAULT now(),
      updated_at timestamptz DEFAULT now(),
      deleted_at timestamptz NULL
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(CITEXT(), unique=True, nullable=False)
    phone = Column(String, nullable=True)
    password_hash = Column(Text, nullable=False)
    name = Column(Text, nullable=True)
    status = Column(
        SAEnum(
            UserStatus,
            name="user_status_t",
            create_constraint=False,
            values_callable=lambda e: [x.value for x in e],
        ),
        nullable=False,
        default=UserStatus.GHOST.value,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    devices = relationship(
        "Device",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    sessions = relationship(
        "Session",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User id={self.id} email={self.email!r} status={self.status.value}>"