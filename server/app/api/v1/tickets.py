from __future__ import annotations
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.tickets import (
    TicketCreate,
    TicketUpdate,
    TicketDetail,
    TicketRead,
    TicketListResponse,
    TicketStatusUpdate,
)
from app.services.tickets import TicketService

# Map DB statuses to API statuses
# DB: 'accepted'|'in_progress'|'done'|'rejected'  -> API: 'new'|'in_progress'|'completed'|'reject'
_DB_TO_API = {
    "new": "new",
    "accepted": "in_progress",   # если «accepted» у вас = «взяли в работу»
    "in_progress": "in_progress",
    "done": "completed",
    "rejected": "reject",
}

def _history_item(h) -> dict:
    db_status = h.to_status.value if hasattr(h.to_status, "value") else h.to_status
    return {"status": _to_api_status(db_status), "at": h.created_at}

def _to_api_status(db_status: str) -> str:
    return _DB_TO_API.get((db_status or "").lower(), "new")

router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.get("/", response_model=List[TicketListResponse])
async def list_my_tickets(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = TicketService(db)
    items = await service.get_user_tickets(current_user.id)
    # Сузим поля под список
    return [
        TicketListResponse(
            id=t.id,
            title=t.title,
            status=_to_api_status(t.status),
            created_at=t.created_at,
        )
        for t in items
    ]


@router.post("/", response_model=TicketDetail, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = TicketService(db)
    ticket = await service.create(current_user.id, payload)
    detailed = await service.get_by_id(ticket.id, user_id=current_user.id)
    if not detailed:
        raise HTTPException(status_code=500, detail="Ticket created but not found")
    
    history = await service.get_history(detailed.id)
    # Вернем детальные данные (attachments + history через selectinload в сервисе)
    # Map DB status -> API status on the fly
    return TicketDetail(
        id=detailed.id,
        title=detailed.title,
        status=_to_api_status(detailed.status),
        created_at=detailed.created_at,
        updated_at=getattr(detailed, "updated_at", None),
        description=getattr(detailed, "description", None),
        device_id=getattr(detailed, "device_id", None),
        attachment_urls=[],
        status_history=[_history_item(h) for h in history],
    )


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = TicketService(db)
    ticket = await service.get_by_id(ticket_id, user_id=current_user.id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    history = await service.get_history(ticket.id)
    return TicketDetail(
        id=ticket.id,
        title=ticket.title,
        status=_to_api_status(ticket.status),
        created_at=ticket.created_at,
        updated_at=getattr(ticket, "updated_at", None),
        description=getattr(ticket, "description", None),
        device_id=getattr(ticket, "device_id", None),
        attachment_urls=[a.file_url for a in getattr(ticket, "attachments", [])],
        status_history=[_history_item(h) for h in history],
    )


@router.patch("/{ticket_id}", response_model=TicketRead)
async def update_ticket(
    ticket_id: uuid.UUID,
    payload: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = TicketService(db)
    ticket = await service.get_by_id(ticket_id, user_id=current_user.id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    updated = await service.update(ticket, payload)
    return TicketRead(
        id=updated.id,
        title=updated.title,
        status=_to_api_status(updated.status),
        created_at=updated.created_at,
        updated_at=getattr(updated, "updated_at", None),
    )


@router.patch("/{ticket_id}/status", response_model=TicketRead)
async def update_ticket_status(
    ticket_id: uuid.UUID,
    payload: TicketStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = TicketService(db)
    ticket = await service.get_by_id(ticket_id, user_id=current_user.id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    updated = await service.update_status(ticket, payload, actor_id=current_user.id)
    return TicketRead(
        id=updated.id,
        title=updated.title,
        status=_to_api_status(updated.status),
        created_at=updated.created_at,
        updated_at=getattr(updated, "updated_at", None),
    )
