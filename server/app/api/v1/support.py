# app/api/v1/support.py
import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.deps import get_db, get_current_user
from app.models.users import User
from app.models.support import SupportTicket, SupportCaseStatus as S
from app.services.support import SupportService
from app.schemas.support import (
    SupportTicketCreate,
    SupportTicketOut,
    SupportMessageCreate,
    SupportMessageOut,
)
from app.models.support import MessageAuthor

router = APIRouter(prefix="/support", tags=["support"])

@router.get("/", response_model=list[SupportTicketOut])
async def list_tickets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await SupportService(db).list_tickets_for_user(current_user.id)

@router.post("/", response_model=SupportTicketOut, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    payload: SupportTicketCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await SupportService(db).create_ticket(current_user.id, payload)

@router.get("/meta")
async def support_meta(current_user: Annotated[User, Depends(get_current_user)],
                       db: Annotated[AsyncSession, Depends(get_db)]):
    return await SupportService(db).counts_for_user(current_user.id)

@router.get("/{ticket_id}", response_model=SupportTicketOut)
async def get_ticket(
    ticket_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await SupportService(db).get_ticket(ticket_id)
    if not ticket or ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return ticket

@router.get("/{ticket_id}/messages", response_model=list[SupportMessageOut])
async def list_messages(
    ticket_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await SupportService(db).get_ticket(ticket_id)
    if not ticket or ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return await SupportService(db).list_messages(ticket_id)

@router.post("/{ticket_id}/messages/user", response_model=SupportMessageOut, status_code=status.HTTP_201_CREATED)
async def add_user_message(
    ticket_id: uuid.UUID,
    payload: SupportMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    ticket = await SupportService(db).get_ticket(ticket_id)
    if not ticket or ticket.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return await SupportService(db).add_message(ticket_id, MessageAuthor.user, payload)

@router.post("/{ticket_id}/messages/support", response_model=SupportMessageOut, status_code=status.HTTP_201_CREATED)
async def add_support_message(
    ticket_id: uuid.UUID,
    payload: SupportMessageCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not getattr(current_user, "is_admin", False) and getattr(current_user, "role", None) != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return await SupportService(db).add_message(ticket_id, MessageAuthor.support, payload)

@router.get("/meta")
async def support_meta(current_user: Annotated[User, Depends(get_current_user)],
                       db: Annotated[AsyncSession, Depends(get_db)]):
    return await SupportService(db).counts_for_user(current_user.id)