


from __future__ import annotations

import uuid
from sqlalchemy import Column, String, Date, ForeignKey, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.device_photos import DevicePhoto


class Device(Base):
    __tablename__ = "devices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    title = Column(String, nullable=False)           # свободное имя карточки
    brand = Column(String, nullable=True)
    model = Column(String, nullable=True)
    serial_number = Column(String, nullable=True, unique=True)
    purchase_date = Column(Date, nullable=True)
    warranty_until = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="devices")
    photos = relationship(DevicePhoto, back_populates="device", cascade="all, delete-orphan")