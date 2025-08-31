from __future__ import annotations

from typing import Annotated
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.database import get_db
from app.services.users import UserService
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
    await service.delete(current_user)
    return None
