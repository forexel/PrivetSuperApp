from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Dict

import jwt
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.users import User

# ---- JWT helpers (kept local to avoid circular imports) ----

ALGO = "HS256"


def _jwt_secret() -> str:
    return (
        os.getenv("SECRET_KEY")
        or os.getenv("JWT_SECRET")
        or os.getenv("JWT_SECRET_KEY")
        or "dev-secret-change-me"
    )


def _create_token(sub: str, typ: str, ttl: timedelta) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "iat": int(now.timestamp()),
        "nbf": int(now.timestamp()),
        "exp": int((now + ttl).timestamp()),
        "typ": typ,
        "sub": sub,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=ALGO)


# ---- password hashing (simple SHA256 to avoid external deps for now) ----

import hashlib


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


# ---- public service API used by routers ----

def register(db: Session, payload) -> User:
    """
    Create a new user. `payload` must provide: email, password, name, phone (optional).
    """
    # Ensure unique email
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise ValueError("User with this email already exists")

    user = User(
        email=payload.email,
        phone=getattr(payload, "phone", None),
        name=payload.name,
        password_hash=_hash_password(payload.password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("User with this email already exists")
    db.refresh(user)
    return user


def login(db: Session, payload) -> Dict[str, str]:
    """
    Authenticate by email + password. Returns token pair dict:
    {access_token, refresh_token, token_type}
    """
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not _verify_password(payload.password, user.password_hash):
        raise ValueError("Invalid credentials")

    access = _create_token(str(user.id), "access", timedelta(minutes=15))
    refresh = _create_token(str(user.id), "refresh", timedelta(days=30))
    return {
        "access_token": access,
        "refresh_token": refresh,
        "token_type": "bearer",
    }