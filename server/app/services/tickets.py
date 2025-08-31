from __future__ import annotations
import uuid
from typing import List, Optional

from sqlalchemy.orm import selectinload
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Lazy imports inside methods will avoid circular imports with models.

class TicketService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_tickets(self, user_id: uuid.UUID):
        from app.models.tickets import Ticket  # type: ignore
        stmt = select(Ticket).where(Ticket.user_id == user_id).order_by(Ticket.created_at.desc())
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, ticket_id: uuid.UUID, user_id: Optional[uuid.UUID] = None):
        from app.models.tickets import Ticket  # type: ignore
        stmt = (
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .options(selectinload(Ticket.attachments))
        )
        if user_id is not None:
            stmt = stmt.where(Ticket.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, user_id: uuid.UUID, payload):
        # Всегда создаём тикет со статусом 'new' в БД.
        norm_status = "new"

        from app.models.tickets import Ticket  # type: ignore
        ticket = Ticket(
            user_id=user_id,
            title=payload.title,
            description=getattr(payload, "description", None),
            status=norm_status,
        )
        self.db.add(ticket)
        await self.db.flush()
        from app.models.tickets import TicketStatusHistory, TicketStatus  # локальный импорт

        self.db.add(TicketStatusHistory(
            ticket_id=ticket.id,
            from_status=None,
            to_status=TicketStatus.NEW,
            changed_by="USER",           # ← нижний регистр, как в БД
            comment=None,
        ))

        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def update(self, ticket, payload):
        for field in ["title", "description"]:
            val = getattr(payload, field, None)
            if val is not None:
                setattr(ticket, field, val)
        await self.db.flush()
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket

    async def update_status(self, ticket, payload, actor_id: uuid.UUID):
        old = ticket.status
        status_val = getattr(payload, "status", None)
        if status_val is not None:
            if hasattr(status_val, "value"):
                status_val = str(getattr(status_val, "value"))
            raw = str(status_val or "").strip().lower()
            if raw in ("new", "accepted", "accept", "open", "created", ""):
                ticket.status = "accepted"
            elif raw in ("in_progress", "progress", "processing"):
                ticket.status = "in_progress"
            elif raw in ("completed", "done", "closed"):
                ticket.status = "done"
            elif raw in ("reject", "rejected", "cancel", "decline"):
                ticket.status = "rejected"
            else:
                ticket.status = "accepted"
        await self.db.flush()
        from app.models.tickets import TicketStatusHistory  # локальный импорт

        self.db.add(TicketStatusHistory(
            ticket_id=ticket.id,
            from_status=old,
            to_status=ticket.status,
            changed_by="USER",           # ← нижний регистр
            comment=None,
        ))
        await self.db.commit()
        await self.db.refresh(ticket)
        return ticket
    
    async def get_history(self, ticket_id: uuid.UUID):
        from app.models.tickets import TicketStatusHistory  # локальный импорт
        res = await self.db.execute(
            select(TicketStatusHistory)
            .where(TicketStatusHistory.ticket_id == ticket_id)
            .order_by(TicketStatusHistory.created_at.asc())
        )
        return list(res.scalars().all())
