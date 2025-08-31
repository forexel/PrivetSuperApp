

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


# ==== Входные схемы (auth) ====

class UserCreate(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    name: Optional[str] = None
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    username: EmailStr
    password: str


# Alias for backward-compat with code expecting LoginRequest.
class LoginRequest(UserLogin):
    """Alias for backward-compat with code expecting LoginRequest."""
    pass


class RefreshRequest(BaseModel):
    refresh_token: str


# ==== Токены ====

class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str  # user id
    exp: int  # unix timestamp
    iat: Optional[int] = None


# ==== Упрощённое представление пользователя ====

class UserRead(BaseModel):
    id: str
    email: EmailStr
    phone: Optional[str] = None
    name: Optional[str] = None
    status: Optional[str] = None
    created_at: Optional[datetime] = None