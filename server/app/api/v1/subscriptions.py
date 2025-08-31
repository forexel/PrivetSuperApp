from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional

from app.core.deps import get_current_user, get_db
from app.services.subscriptions import SubscriptionService
from app.schemas.subscriptions import ChooseSubscriptionRequest, SubscriptionResponse, PlansResponse, PlanItem
from app.models.subscriptions import TariffPlan, TariffPeriod

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@router.get("/plans", response_model=PlansResponse)
async def list_plans(db: AsyncSession = Depends(get_db)):
    items = await SubscriptionService(db).list_plans()
    return {"items": [PlanItem(**it) for it in items]}

@router.post("/create", response_model=SubscriptionResponse)
async def subscribe(payload: ChooseSubscriptionRequest, user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = await SubscriptionService(db).choose_plan(user, payload.plan, payload.period)
    return {
        "plan": sub.plan,
        "period": sub.period,
        "started_at": sub.started_at,
        "paid_until": sub.paid_until,
    }

class ActiveSubResp(SubscriptionResponse):
    pass

@router.get("/active", response_model=Optional[ActiveSubResp])
async def active_subscription(user=Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    sub = await SubscriptionService(db).get_active_for_user(user.id)
    if not sub:
        return None
    return {
        "plan": sub.plan,
        "period": sub.period,
        "started_at": sub.started_at,
        "paid_until": sub.paid_until,
    }