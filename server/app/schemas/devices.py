from datetime import date, datetime
from typing import Optional
import uuid
from pydantic import BaseModel, HttpUrl


class DeviceBase(BaseModel):
    title: str
    brand: str
    model: str
    serial_number: str
    purchase_date: Optional[date] = None
    warranty_until: Optional[date] = None


class DeviceCreate(DeviceBase):
    user_id: Optional[uuid.UUID] = None


class DeviceResponse(DeviceBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]

    class Config:
        from_attributes = True


class DevicePhotoCreate(BaseModel):
    file_url: HttpUrl


class DeviceUpdate(BaseModel):
    title: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_until: Optional[date] = None


class DeviceRead(BaseModel):
    id: uuid.UUID
    user_id: Optional[uuid.UUID]
    title: str
    brand: str
    model: str
    serial_number: str
    purchase_date: Optional[date] = None
    warranty_until: Optional[date] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DevicePhotoRead(BaseModel):
    id: uuid.UUID
    file_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class DeviceDetail(DeviceRead):
    photos: list[DevicePhotoRead] = []

class DeviceListItem(BaseModel):
    id: uuid.UUID
    title: str
    created_at: datetime

    class Config:
        from_attributes = True
