from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, constr


# ---------- User Schemas ----------

class UserBase(BaseModel):
    id: uuid.UUID
    email: EmailStr
    phone: Optional[str] = None
    name: Optional[str] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    email: EmailStr
    phone: Optional[str] = None
    name: Optional[str] = None
    password: constr(min_length=6)


class UserRead(UserBase):
    pass


# ---------- Auth Schemas ----------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"