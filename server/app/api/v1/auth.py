from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
import logging, time, uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import create_access_token, create_refresh_token
from app.schemas.users import UserCreate, UserLogin, UserResponse, TokenResponse
from app.services.users import UserService

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = UserService(db)
    try:
        user = await service.create(**user_data.model_dump())
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )

auth_logger = logging.getLogger("app.auth")


@router.post("/login", response_model=TokenResponse)
async def login(
    credentials: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
    request: Request,
):
    started = time.perf_counter()
    req_id = str(uuid.uuid4())[:8]
    ip = request.client.host if request.client else "-"
    ua = request.headers.get("user-agent", "-")
    phone_masked = (credentials.phone[:-2] + "**") if credentials.phone else ""
    auth_logger.info("LOGIN attempt id=%s ip=%s ua=%s phone=%s", req_id, ip, ua, phone_masked)
    service = UserService(db)
    user = await service.authenticate(credentials.phone, credentials.password)
    if not user:
        duration = int((time.perf_counter() - started) * 1000)
        auth_logger.warning("LOGIN fail_bad_credentials id=%s phone=%s dur_ms=%s", req_id, phone_masked, duration)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    duration = int((time.perf_counter() - started) * 1000)
    auth_logger.info("LOGIN success id=%s user_id=%s dur_ms=%s", req_id, user.id, duration)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token
    )
