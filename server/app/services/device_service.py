from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from app.devices import Device
from app.device_schemas import DeviceCreate, DeviceUpdate


# ---- Helpers ----

_UPDATABLE_FIELDS = (
    "title",
    "brand",
    "model",
    "serial_number",
    "purchase_date",
    "warranty_until",
)


# ---- Public service functions ----

def list_devices(db: Session, owner_id: uuid.UUID) -> List[Device]:
    """
    Return devices that belong to a specific owner.
    Soft-deleted records (if model has `deleted_at`) are excluded.
    """
    query = db.query(Device).filter(Device.owner_id == owner_id)
    # exclude soft-deleted if column exists
    if hasattr(Device, "deleted_at"):
        query = query.filter(Device.deleted_at.is_(None))
    return query.order_by(Device.created_at.desc()).all()


def get_device(db: Session, owner_id: uuid.UUID, device_id: uuid.UUID) -> Optional[Device]:
    """
    Return a single device by id if it belongs to the owner.
    """
    query = db.query(Device).filter(
        Device.id == device_id,
        Device.owner_id == owner_id,
    )
    if hasattr(Device, "deleted_at"):
        query = query.filter(Device.deleted_at.is_(None))
    return query.first()


def create_device(db: Session, owner_id: uuid.UUID, data: DeviceCreate) -> Device:
    """
    Create a device for a given owner.
    """
    device = Device(
        owner_id=owner_id,
        title=data.title,
        brand=data.brand,
        model=data.model,
        serial_number=data.serial_number,
        purchase_date=data.purchase_date,
        warranty_until=data.warranty_until,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def update_device_admin(db: Session, device_id: uuid.UUID, data: DeviceUpdate) -> Optional[Device]:
    """
    Admin-level update: update any of the allowed fields regardless of owner.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return None

    for field in _UPDATABLE_FIELDS:
        value = getattr(data, field, None)
        if value is not None:
            setattr(device, field, value)

    db.add(device)
    db.commit()
    db.refresh(device)
    return device


def delete_device_admin(db: Session, device_id: uuid.UUID) -> bool:
    """
    Admin-level delete: soft-delete if model supports it, otherwise hard-delete.
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        return False

    # Prefer soft delete if column exists
    if hasattr(Device, "deleted_at"):
        from datetime import datetime, timezone

        device.deleted_at = datetime.now(timezone.utc)
        db.add(device)
    else:
        db.delete(device)

    db.commit()
    return True
