from datetime import datetime
import uuid
from sqlalchemy import select
import logging, time
from sqlalchemy.exc import IntegrityError

from app.core.security import hash_password, verify_password
from app.models.users import User, UserStatus
from app.services.base import BaseService

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

auth_logger = logging.getLogger("app.auth")


class UserService(BaseService):
    async def create(self, phone: str, password: str, name: str = None, email: str = None) -> User:
        # нормализация входа
        phone = (phone or "").strip()
        name  = (name  or "").strip()        # чтобы не улетал NULL в NOT NULL колонку
        email = (email or None)

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
            email=email
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
        t0 = time.perf_counter()
        phone10 = (phone or "").strip()
        auth_logger.debug("AUTH find_user phone=%s", phone10[:-2] + "**" if len(phone10) >= 2 else phone10)
        # Find user strictly by phone (no status filter in SQL)
        user = await self.db.scalar(select(User).where(User.phone == phone10))
        if not user:
            auth_logger.info("AUTH user_not_found phone=%s dur_ms=%s", phone10[:-2] + "**", int((time.perf_counter()-t0)*1000))
            return None

        # Normalize status value (support Enum or raw string from DB)
        raw_status = getattr(user.status, "value", user.status)
        raw_status = str(raw_status).lower() if raw_status is not None else ""

        # Allow login for any status EXCEPT explicitly forbidden ones
        # e.g., 'deleted' or 'blocked'. 'gost' (guest) is allowed.
        if raw_status in {"deleted", "blocked"}:
            auth_logger.warning("AUTH locked status=%s user_id=%s", raw_status, user.id)
            return None

        # Verify password (argon2/bcrypt supported by core/security.py)
        ok = bool(verify_password(password, user.password_hash))
        if ok:
            auth_logger.debug("AUTH password_match user_id=%s dur_ms=%s", user.id, int((time.perf_counter()-t0)*1000))
            return user
        auth_logger.info("AUTH password_mismatch user_id=%s dur_ms=%s", user.id, int((time.perf_counter()-t0)*1000))
        return None

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        return await self.db.get(User, user_id)

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            setattr(user, key, value)
        await self.db.commit()
        return user

    async def delete(self, user: User) -> None:
        # 1) Отвязываем устройства пользователя (исчезнут из его списка)
        try:
            from app.models.devices import Device  # локальный импорт, чтобы избежать циклов
            await self.db.execute(
                Device.__table__.update().where(Device.__table__.c.user_id == user.id).values(user_id=None)
            )
        except Exception:
            # без фейла основного удаления аккаунта
            pass

        # 2) Обезличиваем уникальные поля, чтобы их можно было использовать повторно
        try:
            stamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            uid = str(user.id).replace('-', '')[:12]
            prefix = f"del_{stamp}_{uid}_"
            # Избегаем двойного префикса при повторных вызовах
            if getattr(user, 'email', None):
                if not str(user.email).startswith('del_'):
                    user.email = f"{prefix}{user.email}"
            if getattr(user, 'phone', None):
                if not str(user.phone).startswith('del_'):
                    user.phone = f"{prefix}{user.phone}"
        except Exception:
            # Если что-то пошло не так с маскировкой — не блокируем удаление
            pass

        # 3) Помечаем пользователя как удалённого
        user.status = UserStatus.DELETED
        user.deleted_at = datetime.utcnow()
        await self.db.commit()


    async def change_password(self, user: User, old_password: str, new_password: str) -> bool:
        if not verify_password(old_password, user.password_hash):
            return False
        user.password_hash = hash_password(new_password)
        await self.db.commit()
        return True
