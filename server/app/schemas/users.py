from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    phone: str = Field(..., pattern=r'^\d{10}$', description="10 digits only, no +7/8")
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    phone: str = Field(..., pattern=r'^\d{10}$', description="10 digits only, no +7/8")
    password: str

class UserResponse(UserBase):
    id: uuid.UUID
    has_subscription: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserProfileResponse(UserResponse):
    tariff_name: Optional[str] = None
    paid_until: Optional[datetime] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
