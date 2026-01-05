from __future__ import annotations
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.tickets import (
    TicketCreate,
    TicketUpdate,
    TicketDetail,
    TicketRead,
    TicketListResponse,
    TicketStatusUpdate,
    RequestMessageCreate,
    RequestMessageRead,
)
from app.services.tickets import TicketService
from app.services.storage import storage_service

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
    attachment_urls = []
    for attachment in getattr(detailed, "attachments", []):
        raw_url = attachment.file_url
        if raw_url and not str(raw_url).startswith("http"):
            raw_url = storage_service.generate_presigned_get_url(str(raw_url))
        attachment_urls.append(raw_url)
    return TicketDetail(
        id=detailed.id,
        title=detailed.title,
        status=_to_api_status(detailed.status),
        created_at=detailed.created_at,
        updated_at=getattr(detailed, "updated_at", None),
        description=getattr(detailed, "description", None),
        device_id=getattr(detailed, "device_id", None),
        attachment_urls=attachment_urls,
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
    attachment_urls = []
    for attachment in getattr(ticket, "attachments", []):
        raw_url = attachment.file_url
        if raw_url and not str(raw_url).startswith("http"):
            raw_url = storage_service.generate_presigned_get_url(str(raw_url))
        attachment_urls.append(raw_url)
    report = await service.get_work_report(ticket.id)
    work_report = None
    if report:
        photos = [storage_service.generate_presigned_get_url(p.file_key) for p in report.photos]
        work_report = {
            "summary": report.summary,
            "details": report.details,
            "photos": photos,
        }
    master_name = None
    if getattr(ticket, "assigned_master_id", None):
        from app.models.master_users import MasterUser  # type: ignore
        master_name = await db.scalar(
            select(MasterUser.full_name).where(MasterUser.id == ticket.assigned_master_id)
        )
    return TicketDetail(
        id=ticket.id,
        title=ticket.title,
        status=_to_api_status(ticket.status),
        created_at=ticket.created_at,
        updated_at=getattr(ticket, "updated_at", None),
        description=getattr(ticket, "description", None),
        device_id=getattr(ticket, "device_id", None),
        attachment_urls=attachment_urls,
        status_history=[_history_item(h) for h in history],
        work_report=work_report,
        master_name=master_name,
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


@router.get("/{ticket_id}/messages", response_model=list[RequestMessageRead])
async def list_ticket_messages(
    ticket_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = TicketService(db)
    ticket = await service.get_by_id(ticket_id, user_id=current_user.id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    from app.models.tickets import RequestMessage  # type: ignore
    result = await db.execute(
        select(RequestMessage)
        .where(RequestMessage.ticket_id == ticket.id)
        .order_by(RequestMessage.created_at.asc())
    )
    items = []
    for msg in result.scalars().all():
        items.append(
            RequestMessageRead(
                id=msg.id,
                author=msg.author,
                body=msg.body,
                file_key=msg.file_key,
                file_url=storage_service.generate_presigned_get_url(msg.file_key) if msg.file_key else None,
                created_at=msg.created_at,
            )
        )
    return items


@router.post("/{ticket_id}/messages", response_model=RequestMessageRead)
async def send_ticket_message(
    ticket_id: uuid.UUID,
    payload: RequestMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service = TicketService(db)
    ticket = await service.get_by_id(ticket_id, user_id=current_user.id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")

    from app.models.tickets import RequestMessage, RequestMessageAuthor, TicketStatus  # type: ignore

    if ticket.status not in (TicketStatus.ACCEPTED, TicketStatus.IN_PROGRESS):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ticket is closed")
    if not payload.body and not payload.file_key:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message is empty")

    msg = RequestMessage(
        ticket_id=ticket.id,
        author=RequestMessageAuthor.USER,
        body=payload.body.strip() if payload.body else None,
        file_key=payload.file_key,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return RequestMessageRead(
        id=msg.id,
        author=msg.author,
        body=msg.body,
        file_key=msg.file_key,
        file_url=storage_service.generate_presigned_get_url(msg.file_key) if msg.file_key else None,
        created_at=msg.created_at,
    )
