from __future__ import annotations

from typing import Annotated
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.database import get_db
from app.services.users import UserService
from app.schemas.users import UserCreate, UserLogin, UserResponse, TokenResponse
from app.core.security import create_access_token, create_refresh_token, decode_jwt_token
from app.core.phone import normalize_phone_to_10_digits
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from app.models.users import User
from app.models.password_reset_tokens import PasswordResetToken
from datetime import datetime, timedelta
import secrets
from app.core.mailer import send_email
import logging
logger = logging.getLogger("app.auth")
from app.core.config import settings

router = APIRouter(prefix="/user", tags=["user"])  # user section
auth_router = APIRouter(prefix="/auth", tags=["user"])  # auth section

# 1 Registration endpoint
@auth_router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = UserService(db)
    phone10 = normalize_phone_to_10_digits(payload.phone)
    try:
        user = await service.create(
            phone=phone10,
            password=payload.password,
            name=payload.name,
            email=payload.email,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }


# 2.0 Forgot password (request reset)
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@auth_router.post("/forgot", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Always return 204 to avoid leaking whether the account exists.
    user = await db.scalar(select(User).where(User.email == payload.email))
    logger.info("Forgot-password requested for %s; user_exists=%s", payload.email, bool(user))
    if user:
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        db.add(PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at))
        try:
            await db.commit()
            logger.info("Password reset token created for user_id=%s", user.id)
        except Exception as e:
            logger.exception("Failed to create reset token: %s", e)
            await db.rollback()
        try:
            base_url = settings.APP_BASE_URL or "http://localhost:5173"
            link = f"{base_url.rstrip('/')}/reset-password?token={token}"
            subject = "Восстановление пароля"
            body = (
                "Мы получили запрос на восстановление пароля.\n\n"
                f"Ссылка для восстановления (действует 1 час):\n{link}\n\n"
                "Если вы не делали этот запрос, просто проигнорируйте письмо."
            )
            await send_email(subject, body, [payload.email])
        except Exception:
            # already logged inside send_email
            pass
    return None

# 2 Login endpoint
@auth_router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLogin,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = UserService(db)
    phone10 = normalize_phone_to_10_digits(payload.phone)
    user = await service.authenticate(phone10, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }


# 2.1 Refresh tokens endpoint
class RefreshRequest(BaseModel):
    refresh_token: str


@auth_router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    try:
        decoded = decode_jwt_token(payload.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    if decoded.get("typ") not in ("refresh", None):
        # Accept only refresh tokens (older tokens may omit typ; enforce when present)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    sub = decoded.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Ensure user still exists
    user = await db.get(User, sub)
    if user is None:
        user = await db.scalar(select(User).where(User.phone == str(sub)))
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }


# 3 Me about
@router.get("/me", response_model=UserResponse, tags=["user"])
async def get_me(current_user: Annotated[object, Depends(get_current_user)]):
    return current_user


# 3.1 Update current user (name/email)
class UserUpdateRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


@router.put("", response_model=UserResponse)
async def update_me(
    payload: UserUpdateRequest,
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = UserService(db)
    try:
        updated = await service.update(current_user, **{k: v for k, v in payload.model_dump().items() if v is not None})
        return updated
    except IntegrityError as e:
        # Email uniqueness or other constraints
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Conflict: email or data already used")


# 4 Change password endpoint
class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = UserService(db)
    ok = await service.change_password(current_user, payload.old_password, payload.new_password)
    if not ok:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Old password is incorrect")
    return None


# 5 Delete user endpoint
@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = UserService(db)
    await service.delete(current_user)
    return None
