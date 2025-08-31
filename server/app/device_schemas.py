# app/device_schemas.py
from datetime import date
from pydantic import BaseModel, ConfigDict

class DeviceBase(BaseModel):
    title: str
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    purchase_date: date | None = None
    warranty_until: date | None = None

class DeviceCreate(DeviceBase):
    # при админском создании можно передать owner_id
    owner_id: str | None = None  # UUID как строка

class DeviceUpdate(DeviceBase):
    pass

class DeviceRead(DeviceBase):
    id: str
    owner_id: str
    model_config = ConfigDict(from_attributes=True)