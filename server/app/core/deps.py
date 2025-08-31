from __future__ import annotations
import uuid
import base64
import binascii
from typing import Annotated, Optional
from fastapi import Depends, HTTPException, Request, status

from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_jwt_token
from app.models.users import User
from app.services.users import UserService

# Allow both Bearer and Basic in Swagger Authorize (we defined both in main.py)
bearer_scheme = HTTPBearer(auto_error=False)

async def get_current_user(
    request: Request,
    creds: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
) -> User:
    """Resolve current user via Authorization header.

    Supported:
    - Bearer JWT:  Authorization: Bearer <access_token>
    - Basic auth:  Authorization: Basic base64(phone:password)
    """
    # Prefer Bearer if present
    if creds and (creds.scheme or "").lower() == "bearer":
        token = creds.credentials
        try:
            payload = decode_jwt_token(token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        # Try user by id, then by phone
        user = await db.get(User, sub)
        if user is None:
            user = await db.scalar(select(User).where(User.phone == str(sub)))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    # Fallback: Basic (username=phone, password)
    auth_header = request.headers.get("authorization") or ""
    if auth_header.lower().startswith("basic "):
        b64 = auth_header.split(" ", 1)[1].strip()
        try:
            raw = base64.b64decode(b64).decode("utf-8")
        except (binascii.Error, UnicodeDecodeError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Basic auth header",
                headers={"WWW-Authenticate": "Basic"},
            )
        if ":" not in raw:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Basic credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        phone, password = raw.split(":", 1)
        service = UserService(db)
        user = await service.authenticate(phone, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        return user

    # No acceptable Authorization
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing Authorization header",
        headers={"WWW-Authenticate": "Bearer, Basic"},
    )

async def require_admin(current_user: Annotated[User, Depends(get_current_user)]):
    # current_user — это модель User, а не dict
    is_admin = getattr(current_user, "is_admin", False) or getattr(current_user, "role", None) == "admin"
    if not is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current_user
