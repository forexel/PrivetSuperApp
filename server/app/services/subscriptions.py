

from __future__ import annotations

from datetime import datetime
from typing import List, Dict

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscriptions import Subscription, TariffPlan, TariffPeriod
from app.models.users import User


# Static catalogue for Swagger/demo purposes
PLANS: List[Dict] = [
    {"plan": TariffPlan.SIMPLE.value, "period": TariffPeriod.MONTH.value, "price_rub": 199},
    {"plan": TariffPlan.SIMPLE.value, "period": TariffPeriod.YEAR.value, "price_rub": 1990},
    {"plan": TariffPlan.MEDIUM.value, "period": TariffPeriod.MONTH.value, "price_rub": 399},
    {"plan": TariffPlan.MEDIUM.value, "period": TariffPeriod.YEAR.value, "price_rub": 3990},
    {"plan": TariffPlan.PREMIUM.value, "period": TariffPeriod.MONTH.value, "price_rub": 799},
    {"plan": TariffPlan.PREMIUM.value, "period": TariffPeriod.YEAR.value, "price_rub": 7990},
]


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_plans(self) -> List[Dict]:
        return PLANS

    async def get_active_for_user(self, user_id) -> Subscription | None:
        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.active == True)  # noqa: E712
            .order_by(Subscription.paid_until.desc())
        )
        return await self.db.scalar(stmt)

    async def choose_plan(self, user: User, plan: str, period: str) -> Subscription:
        # deactivate previous active subscriptions
        await self.db.execute(
            update(Subscription)
            .where(Subscription.user_id == user.id)
            .where(Subscription.active == True)  # noqa: E712
            .values(active=False)
        )

        paid_until = Subscription.compute_paid_until(period)
        sub = Subscription(user_id=user.id, plan=plan, period=period, paid_until=paid_until, active=True)
        self.db.add(sub)

        # Flip user flag for fast checks
        user.has_subscription = True

        await self.db.commit()
        return sub