

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Dict
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscriptions import Subscription, TariffPlan, TariffPeriod
from app.models.users import User


PRICES_RUB: Dict[str, Dict[str, Decimal]] = {
    TariffPeriod.MONTH.value: {
        TariffPlan.SIMPLE.value: Decimal("1"),
        TariffPlan.MEDIUM.value: Decimal("7999"),
        TariffPlan.PREMIUM.value: Decimal("13999"),
    },
    TariffPeriod.YEAR.value: {
        TariffPlan.SIMPLE.value: Decimal("39990"),
        TariffPlan.MEDIUM.value: Decimal("79990"),
        TariffPlan.PREMIUM.value: Decimal("139990"),
    },
}

# Static catalogue for Swagger/demo purposes
PLANS: List[Dict] = [
    {
        "plan": plan,
        "period": period,
        "price_rub": int(price),
    }
    for period, items in PRICES_RUB.items()
    for plan, price in items.items()
]


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_plans(self) -> List[Dict]:
        return PLANS

    @staticmethod
    def get_price(plan: str, period: str) -> Decimal:
        try:
            return PRICES_RUB[period][plan]
        except KeyError as exc:
            raise ValueError("unknown plan or period") from exc

    async def get_active_for_user(self, user_id) -> Subscription | None:
        now = datetime.now(timezone.utc)
        # Deactivate expired subscriptions for the user.
        await self.db.execute(
            update(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.active == True)  # noqa: E712
            .where(Subscription.paid_until < now)
            .values(active=False)
        )

        stmt = (
            select(Subscription)
            .where(Subscription.user_id == user_id)
            .where(Subscription.active == True)  # noqa: E712
            .where(Subscription.paid_until >= now)
            .order_by(Subscription.paid_until.desc())
        )
        sub = await self.db.scalar(stmt)

        # Keep the fast flag in sync.
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(has_subscription=bool(sub))
        )
        await self.db.commit()
        return sub

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
