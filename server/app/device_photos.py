from __future__ import annotations

import uuid
from sqlalchemy import Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class DevicePhoto(Base):
    __tablename__ = "device_photos"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    device_id = Column(UUID(as_uuid=True), ForeignKey("devices.id", ondelete="CASCADE"), nullable=False)
    file_url = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    device = relationship("Device", back_populates="photos")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DevicePhoto id={self.id} device_id={self.device_id} url={self.file_url!r}>"