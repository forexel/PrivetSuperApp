from __future__ import annotations

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.device_schemas import DeviceCreate, DeviceRead, DeviceUpdate
from app.services import device_service
from pydantic import BaseModel
from app.users import User

# ---- User-facing device endpoints ----
router = APIRouter(prefix="/devices", tags=["devices"])

@router.get("/", response_model=List[DeviceRead])
def list_devices(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return device_service.list_devices(db, current_user.id)

@router.get("/{device_id}", response_model=DeviceRead)
def get_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    device = device_service.get_device(db, device_id, current_user.id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

# ---- Admin-only endpoints (UI ограничит доступ; бекенд проверяет только аутентификацию) ----
admin_router = APIRouter(prefix="/admin/devices", tags=["admin: devices"])  # relies on get_current_user

@admin_router.post("/", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def admin_create_device(
    data: DeviceCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if data.owner_id is None:
        raise HTTPException(status_code=400, detail="owner_id is required")
    return device_service.create_device(db, data.owner_id, data)

@admin_router.patch("/{device_id}", response_model=DeviceRead)
def admin_update_device(
    device_id: uuid.UUID,
    data: DeviceUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    device = device_service.update_device_admin(db, device_id, data)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@admin_router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ok = device_service.delete_device_admin(db, device_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Device not found")
    return None

# ---- Admin: user typeahead search ----
class UserLookup(BaseModel):
    id: uuid.UUID
    email: str
    name: str | None = None
    phone: str | None = None

    class Config:
        from_attributes = True

admin_users_router = APIRouter(prefix="/admin/users", tags=["admin: users"])  # relies on get_current_user

@admin_users_router.get("/search", response_model=List[UserLookup])
def admin_search_users(
    q: str = Query(..., min_length=1, description="email/phone/name contains"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    term = f"%{q}%"
    users = (
        db.query(User)
        .filter(
            (User.email.ilike(term)) | (User.phone.ilike(term)) | (User.name.ilike(term))
        )
        .order_by(User.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return [UserLookup.model_validate(u, from_attributes=True) for u in users]