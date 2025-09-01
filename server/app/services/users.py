from datetime import datetime
import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.models.users import User, UserStatus
from app.services.base import BaseService

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

class UserService(BaseService):
    async def create(self, phone: str, password: str, name: str = None, email: str = None, address: str | None = None) -> User:
        # нормализация входа
        phone = (phone or "").strip()
        name  = (name  or "").strip()        # чтобы не улетал NULL в NOT NULL колонку
        email = (email or None)
        address = (address or None)

        # быстрые явные проверки дублей — для понятных сообщений
        exists_phone = await self.db.scalar(select(User.id).where(User.phone == phone))
        if exists_phone:
            raise ValueError("Phone already exists")

        if email:
            exists_email = await self.db.scalar(select(User.id).where(User.email == email))
            if exists_email:
                raise ValueError("Email already exists")

        user = User(
            phone=phone,
            password_hash=hash_password(password),
            name=name,
            email=email,
            address=address,
        )
        self.db.add(user)
        try:
            await self.db.commit()
            return user
        except IntegrityError as e:
            await self.db.rollback()
            # тонкая диагностика на случай гонок/других ограничений
            msg = str(getattr(e, "orig", e)).lower()
            if "phone" in msg and "duplicate" in msg:
                raise ValueError("Phone already exists")
            if "email" in msg and "duplicate" in msg:
                raise ValueError("Email already exists")
            if "null value" in msg and "name" in msg:
                raise ValueError("Name is required")
            if "null value" in msg and "phone" in msg:
                raise ValueError("Phone is required")
            raise ValueError("Registration failed")

    async def authenticate(self, phone: str, password: str) -> User | None:
        # Find user strictly by phone (no status filter in SQL)
        user = await self.db.scalar(select(User).where(User.phone == phone))
        if not user:
            return None

        # Normalize status value (support Enum or raw string from DB)
        raw_status = getattr(user.status, "value", user.status)
        raw_status = str(raw_status).lower() if raw_status is not None else ""

        # Allow login for any status EXCEPT explicitly forbidden ones
        # e.g., 'deleted' or 'blocked'. 'gost' (guest) is allowed.
        if raw_status in {"deleted", "blocked"}:
            return None

        # Verify password (argon2/bcrypt supported by core/security.py)
        return user if verify_password(password, user.password_hash) else None

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def update(self, user: User, **kwargs) -> User:
        # allowlist only safe fields to update
        allowed = { 'name', 'email', 'address' }
        for key, value in kwargs.items():
            if key in allowed:
                setattr(user, key, value)
        await self.db.commit()
        return user

    async def delete(self, user: User) -> None:
        user.status = UserStatus.DELETED
        user.deleted_at = datetime.utcnow()
        await self.db.commit()


    async def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        if not verify_password(old_password, user.password_hash):
            return False
        user.password_hash = hash_password(new_password)
        await self.db.commit()
        return True
