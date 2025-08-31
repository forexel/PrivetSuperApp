

from __future__ import annotations

from datetime import datetime
from typing import Literal
from pydantic import BaseModel

PlanName = Literal["simple", "medium", "premium"]
PlanPeriod = Literal["month", "year"]


class PlanItem(BaseModel):
    plan: PlanName
    period: PlanPeriod
    price_rub: int


class PlansResponse(BaseModel):
    items: list[PlanItem]


class ChooseSubscriptionRequest(BaseModel):
    plan: PlanName
    period: PlanPeriod


class SubscriptionResponse(BaseModel):
    plan: PlanName
    period: PlanPeriod
    started_at: datetime
    paid_until: datetime