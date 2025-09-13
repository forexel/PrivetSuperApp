from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, func
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
import secrets
import logging

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.phone import normalize_phone_to_10_digits
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_jwt_token,
    hash_password,
)
from app.core.config import settings
from app.core.mailer import send_email
from app.services.users import UserService
from app.schemas.users import UserCreate, UserLogin, UserResponse, TokenResponse
from app.models.users import User
from app.models.password_reset_tokens import PasswordResetToken

logger = logging.getLogger("app.auth")

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


# 2.0 Forgot password (request reset link)
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@auth_router.post("/forgot", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    payload: ForgotPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Send a one-time reset link (no plain passwords). Always 204."""
    email_norm = payload.email.strip()
    user = await db.scalar(select(User).where(func.lower(User.email) == func.lower(email_norm)))
    logger.info("FORGOT: request for %s; user_exists=%s", email_norm, bool(user))
    if not user:
        return None

    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=30)
    db.add(PasswordResetToken(user_id=user.id, token=token, expires_at=expires_at))
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.exception("FORGOT: failed to persist token for user_id=%s: %s", user.id, e)
        return None

    subject = "Восстановление доступа к PrivetSuper"
    base = settings.APP_BASE_URL or "https://app.privetsuper.ru"
    reset_url = f"{base.rstrip('/')}/reset?token={token}"
    text = (
        "Вы запросили восстановление пароля для аккаунта в PrivetSuper.\n\n"
        "Чтобы задать новый пароль, перейдите по ссылке (она действительна 30 минут):\n\n"
        f"{reset_url}\n\n"
        "Если вы не запрашивали восстановление, просто игнорируйте это письмо.\n\n— Команда PrivetSuper"
    )
    html = f"""
<!doctype html><html><body style=\"font-family:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;line-height:1.5;color:#111827\">\n  <p>Вы запросили восстановление пароля для аккаунта в <strong>PrivetSuper</strong>.</p>\n  <p><a href=\"{reset_url}\" style=\"display:inline-block;padding:12px 18px;border-radius:9999px;background:#3E8BBF;color:#fff;text-decoration:none;font-weight:700\">Задать новый пароль</a></p>\n  <p>Ссылка действительна 30 минут. Если кнопка не работает, скопируйте ссылку:<br><a href=\"{reset_url}\">{reset_url}</a></p>\n  <p style=\"color:#6B7280\">Если вы не запрашивали восстановление, просто игнорируйте это письмо.</p>\n  <p>— Команда PrivetSuper</p>\n</body></html>
    """
    headers = {"Reply-To": "support@privetsuper.ru", "List-Unsubscribe": "<mailto:postmaster@privetsuper.ru>"}
    logger.info("FORGOT: sending reset link to %s", email_norm)
    ok = await send_email(subject, text, [email_norm], html_body=html, headers=headers)
    logger.info("FORGOT: send_email result=%s for %s", ok, email_norm)
    return None


# 2.0b Apply reset token
class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


@auth_router.post("/reset", status_code=status.HTTP_204_NO_CONTENT)
async def reset_password(
    payload: ResetPasswordRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    token = (payload.token or "").strip()
    logger.info("RESET: attempt token_len=%s", len(token))
    if not token:
        raise HTTPException(status_code=400, detail="token is required")
    rec = await db.scalar(select(PasswordResetToken).where(PasswordResetToken.token == token))
    if not rec or rec.used_at is not None or rec.expires_at < datetime.now(timezone.utc):
        logger.warning(
            "RESET: invalid_or_expired token_found=%s used=%s expires_at=%s now=%s",
            bool(rec), getattr(rec, 'used_at', None), getattr(rec, 'expires_at', None), datetime.utcnow()
        )
        raise HTTPException(status_code=400, detail="invalid_or_expired_token")
    user = await db.get(User, rec.user_id)
    if not user:
        logger.warning("RESET: user_not_found user_id=%s", rec.user_id)
        raise HTTPException(status_code=400, detail="user_not_found")
    user.password_hash = hash_password(payload.new_password)
    rec.used_at = datetime.utcnow()
    await db.commit()
    logger.info("RESET: success user_id=%s", user.id)
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    sub = decoded.get("sub")
    if not sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = await db.get(User, sub) or await db.scalar(select(User).where(User.phone == str(sub)))
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
    except IntegrityError:
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
