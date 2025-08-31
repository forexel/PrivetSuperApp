import uuid
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.devices import Device, DevicePhoto
from app.services.base import BaseService

class DeviceService(BaseService):
    async def create(self, device_data: dict) -> Device:
        device = Device(**device_data)
        self.db.add(device)
        try:
            await self.db.commit()
            return device
        except IntegrityError:
            await self.db.rollback()
            raise ValueError("Serial number must be unique")

    async def get_by_id(self, device_id: uuid.UUID, user_id: uuid.UUID = None) -> Device | None:
        query = select(Device).where(Device.id == device_id)
        if user_id:
            query = query.where(Device.user_id == user_id)
        return await self.db.scalar(query)

    async def get_user_devices(self, user_id: uuid.UUID) -> list[Device]:
        result = await self.db.scalars(
            select(Device).where(Device.user_id == user_id)
        )
        return list(result)

    async def add_photo(self, device_id: uuid.UUID, photo_data: dict) -> DevicePhoto:
        photo = DevicePhoto(device_id=device_id, **photo_data)
        self.db.add(photo)
        await self.db.commit()
        return photo


    async def update(self, device: Device, **kwargs) -> Device:
        allowed = {"title", "brand", "model", "serial_number", "purchase_date", "warranty_until"}
        for field, value in kwargs.items():
            if field in allowed:
                setattr(device, field, value)
        await self.db.commit()
        return device

    async def search(
        self,
        *,
        user_id: uuid.UUID | None = None,
        device_id: uuid.UUID | None = None,
        title: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
    ) -> list[Device]:
        query = select(Device)
        if device_id:
            query = query.where(Device.id == device_id)
        if user_id:
            query = query.where(Device.user_id == user_id)
        if title:
            query = query.where(Device.title.ilike(f"%{title}%"))
        if brand:
            query = query.where(Device.brand.ilike(f"%{brand}%"))
        if model:
            query = query.where(Device.model.ilike(f"%{model}%"))
        if serial_number:
            query = query.where(Device.serial_number.ilike(f"%{serial_number}%"))

        result = await self.db.scalars(query)
        return list(result)
