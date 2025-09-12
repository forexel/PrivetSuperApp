from __future__ import annotations

from fastapi import APIRouter, Depends, Request
import logging, time, uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.database import get_db
from app.models.users import User
from app.schemas.users import UserProfileResponse
from app.services.subscriptions import SubscriptionService

router = APIRouter(prefix="/me", tags=["me"])


me_logger = logging.getLogger("app.auth")


@router.get("/", response_model=UserProfileResponse)
async def read_profile(request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    t0 = time.perf_counter()
    req_id = request.headers.get('x-request-id') or str(uuid.uuid4())[:8]
    svc = SubscriptionService(db)
    sub = await svc.get_active_for_user(user.id)

    resp = UserProfileResponse(
        id=user.id,
        phone=user.phone,
        email=user.email,
        name=user.name,
        has_subscription=bool(sub),
        tariff_name=(sub.plan if sub else None),
        paid_until=(sub.paid_until if sub else None),
        created_at=user.created_at,
    )
    me_logger.info("ME response id=%s user_id=%s dur_ms=%s", req_id, user.id, int((time.perf_counter()-t0)*1000))
    return resp
