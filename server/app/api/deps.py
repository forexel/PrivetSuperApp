from __future__ import annotations
from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt
import os
from datetime import datetime, timezone

from app.db.session import SessionLocal
from app.users import User


security = HTTPBearer(auto_error=False)

ALGO = "HS256"

def _jwt_secret() -> str:
    # Fallback chain for secret key
    return (
        os.getenv("SECRET_KEY")
        or os.getenv("JWT_SECRET")
        or os.getenv("JWT_SECRET_KEY")
        or "dev-secret-change-me"
    )


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and close it after the request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Extract current user from Bearer access token.

    Expects JWT with claim `sub` = user_id and typ = "access".
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing Bearer token")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[ALGO])
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if payload.get("typ") != "access":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user