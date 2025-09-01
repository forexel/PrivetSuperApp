from __future__ import annotations

from typing import Annotated
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.core.deps import get_current_user
from app.core.database import get_db
from app.services.users import UserService
from app.services.email_service import send_email
from app.schemas.users import UserCreate, UserLogin, UserResponse, TokenResponse
from app.core.security import create_access_token, create_refresh_token
from app.core.phone import normalize_phone_to_10_digits

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
            address=payload.address,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }

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


# 3 Forgot password (by email)
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@auth_router.post("/forgot", status_code=status.HTTP_204_NO_CONTENT)
async def forgot_password(
    payload: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = UserService(db)

    # Find user by email; if not found, return 204 to avoid leaking
    from sqlalchemy import select, func
    from app.models.users import User
    email = payload.email
    user = await db.scalar(select(User).where(func.lower(User.email) == func.lower(email)))
    if not user:
        return None

    # Generate a new password and update hash
    import secrets, string
    alphabet = string.ascii_letters + string.digits
    new_password = ''.join(secrets.choice(alphabet) for _ in range(12))

    from app.core.security import hash_password
    user.password_hash = hash_password(new_password)
    await db.commit()

    # Send email in background; do not fail API if SMTP is misconfigured
    subject = "new password"
    body = f"Ваш новый пароль {new_password}"
    background_tasks.add_task(send_email, email, subject, body)
    return None


# 3 Me about
@router.get("/me", response_model=UserResponse, tags=["user"])
async def get_me(current_user: Annotated[object, Depends(get_current_user)]):
    return current_user


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
    # Hard delete user and related data
    await service.purge_user(current_user)
    return None


# 6 Update current user profile
class UpdateUserRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None
    address: str | None = None


@router.put("", response_model=UserResponse)
async def update_me(
    payload: UpdateUserRequest,
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = UserService(db)
    try:
        user = await service.update(current_user, **payload.model_dump(exclude_unset=True))
        return user
    except IntegrityError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already exists")
