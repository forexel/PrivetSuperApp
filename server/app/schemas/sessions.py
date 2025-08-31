from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


# ---- User Schemas ----

class UserBase(BaseModel):
    email: EmailStr
    phone: Optional[str] = Field(default=None, examples=["+79991234567"])
    name: Optional[str] = Field(default=None, examples=["Danila"])


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, examples=["secret123"])


class UserRead(UserBase):
    id: UUID
    status: Optional[str] = Field(default=None, examples=["ACTIVE"])  # keep as str to avoid enum coupling
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
