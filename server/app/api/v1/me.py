from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.users import User
from app.schemas.users import UserProfileResponse
from app.services.subscriptions import SubscriptionService

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/", response_model=UserProfileResponse)
async def read_profile(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    svc = SubscriptionService(db)
    sub = await svc.get_active_for_user(user.id)

    return UserProfileResponse(
        id=user.id,
        phone=user.phone,
        email=user.email,
        name=user.name,
        has_subscription=bool(sub),
        tariff_name=(sub.plan if sub else None),
        paid_until=(sub.paid_until if sub else None),
        created_at=user.created_at,
    )
