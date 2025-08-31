from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_user
from app.core.database import get_db
from app.services.devices import DeviceService
from app.schemas.devices import (
    DeviceUpdate,
    DeviceCreate,
    DeviceDetail,
    DeviceListItem,
)

router = APIRouter(prefix="/devices", tags=["devices"])


# List all devices for current user (GET /devices)
@router.get("", response_model=list[DeviceListItem])
async def list_devices(
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = DeviceService(db)
    return await service.get_user_devices(getattr(current_user, "id"))


@router.get("/my", response_model=list[DeviceListItem])
async def get_my_devices(
    current_user: Annotated[object, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = DeviceService(db)
    return await service.get_user_devices(getattr(current_user, "id"))


@router.get("/search", response_model=list[DeviceListItem])
async def search_devices(
    user_id: Optional[str] = Query(None),
    device_id: Optional[str] = Query(None),
    title: Optional[str] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    serial_number: Optional[str] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    """Поиск без авторизации. Если user_id не указан — ищем по всей базе."""
    uid = None
    if user_id:
        try:
            uid = UUID(user_id)
        except ValueError:
            uid = None

    did = None
    if device_id:
        try:
            did = UUID(device_id)
        except ValueError:
            did = None

    service = DeviceService(db)
    return await service.search(
        user_id=uid,
        device_id=did,
        title=title,
        brand=brand,
        model=model,
        serial_number=serial_number,
    )


@router.get("/{device_id}", response_model=DeviceDetail)
async def get_device(
    device_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = DeviceService(db)
    device = await service.get_by_id(device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return device


@router.patch("/{device_id}", response_model=DeviceDetail)
async def update_device(
    device_id: UUID,
    payload: DeviceUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    service = DeviceService(db)
    device = await service.get_by_id(device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    device = await service.update(device, **payload.model_dump(exclude_unset=True))
    return device


@router.post("", status_code=status.HTTP_201_CREATED, response_model=DeviceDetail)
async def create_device(
    payload: DeviceCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Создание устройства без авторизации. Требуется явный user_id в теле запроса."""
    data = payload.model_dump(exclude_unset=True)
    if not data.get("user_id"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="user_id is required")

    service = DeviceService(db)
    try:
        return await service.create(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(e)
        )