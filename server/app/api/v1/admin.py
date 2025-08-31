from __future__ import annotations


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.core.deps import get_current_user
from app.core.database import get_db
from app.services.users import UserService
from app.schemas.users import UserLogin, TokenResponse
from app.core.security import create_access_token, create_refresh_token

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/ping")
async def admin_ping(current_user: Annotated[object, Depends(get_current_user)]):
    # TODO: add admin role check when roles are introduced
    return {"status": "admin-ok"}


# Admin login endpoint
@router.post("/login", response_model=TokenResponse)
async def admin_login(payload: UserLogin, db: Annotated[AsyncSession, Depends(get_db)]):
    service = UserService(db)
    user = await service.authenticate(payload.phone, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    # TODO: add real admin check when roles are implemented
    return {
        "access_token": create_access_token(str(user.id)),
        "refresh_token": create_refresh_token(str(user.id)),
        "token_type": "bearer",
    }

