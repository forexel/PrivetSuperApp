from __future__ import annotations
import enum
import uuid
from datetime import datetime, timedelta

from sqlalchemy import Boolean, DateTime, Enum as SAEnum, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class TariffPlan(str, enum.Enum):
    SIMPLE = "simple"
    MEDIUM = "medium"
    PREMIUM = "premium"


class TariffPeriod(str, enum.Enum):
    MONTH = "month"
    YEAR = "year"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # IMPORTANT: use existing PostgreSQL ENUM types created by Alembic (no ORM create)
    plan: Mapped[str] = mapped_column(
        SAEnum("simple", "medium", "premium", name="tariff_plan_t", native_enum=True, create_type=False),
        nullable=False,
    )
    period: Mapped[str] = mapped_column(
        SAEnum("month", "year", name="tariff_period_t", native_enum=True, create_type=False),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"))
    paid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user = relationship("User", backref="subscriptions")

    @staticmethod
    def compute_paid_until(period: str, start: datetime | None = None) -> datetime:
        start = start or datetime.utcnow()
        return start + (timedelta(days=365) if period == TariffPeriod.YEAR.value else timedelta(days=30))


__all__ = ["Subscription", "TariffPlan", "TariffPeriod"]