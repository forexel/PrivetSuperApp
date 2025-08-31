# app/services/support.py
import uuid
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.base import BaseService
from app.models.support import (
    SupportTicket,
    SupportMessage,
    MessageAuthor,
    SupportCaseStatus as S,
)
from app.schemas.support import SupportTicketCreate, SupportMessageCreate

class SupportService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create_ticket(self, user_id: uuid.UUID, data: SupportTicketCreate) -> SupportTicket:
        ticket = SupportTicket(user_id=user_id, subject=data.subject)
        self.db.add(ticket)
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def get_ticket(self, ticket_id: uuid.UUID) -> SupportTicket | None:
        res = await self.db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
        return res.scalar_one_or_none()

    async def list_messages(self, ticket_id: uuid.UUID) -> Sequence[SupportMessage]:
        res = await self.db.execute(
            select(SupportMessage)
            .where(SupportMessage.ticket_id == ticket_id)
            .order_by(SupportMessage.created_at.asc())
        )
        return list(res.scalars())

    async def add_message(self, ticket_id: uuid.UUID, author: MessageAuthor, data: SupportMessageCreate) -> SupportMessage:
        msg = SupportMessage(ticket_id=ticket_id, author=author, body=data.body)
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def list_tickets_for_user(self, user_id: uuid.UUID) -> Sequence[SupportTicket]:
        res = await self.db.execute(
            select(SupportTicket)
            .where(SupportTicket.user_id == user_id)
            .order_by(SupportTicket.created_at.desc())
        )
        return list(res.scalars())
    
    async def counts_for_user(self, user_id: uuid.UUID) -> dict[str, int]:
        total_q = select(func.count(SupportTicket.id)).where(SupportTicket.user_id == user_id)
        total = (await self.db.execute(total_q)).scalar_one() or 0

        active_q = select(func.count(SupportTicket.id)).where(
            SupportTicket.user_id == user_id,
            SupportTicket.status.in_([S.open, S.pending]),
        )
        active = (await self.db.execute(active_q)).scalar_one() or 0

        return {"active": int(active), "total": int(total)}    
        