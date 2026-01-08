from __future__ import annotations

import uuid
from typing import Sequence

from datetime import datetime, timezone

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.invoices import ManagerInvoice, InvoicePayment, InvoiceStatus
from app.services.base import BaseService


class InvoiceService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def list_for_user(self, user_id: uuid.UUID, include_paid: bool = False) -> Sequence[ManagerInvoice]:
        now = datetime.now(timezone.utc)
        stmt = select(ManagerInvoice).where(
            ManagerInvoice.client_id == user_id,
            or_(ManagerInvoice.due_date.is_(None), ManagerInvoice.due_date >= now),
        )
        if not include_paid:
            stmt = stmt.where(ManagerInvoice.status != InvoiceStatus.paid)
        stmt = stmt.order_by(ManagerInvoice.due_date.asc().nullslast(), ManagerInvoice.created_at.desc())
        res = await self.db.execute(stmt)
        return list(res.scalars())

    async def get_payable_invoices(
        self,
        user_id: uuid.UUID,
        invoice_ids: list[uuid.UUID],
    ) -> Sequence[ManagerInvoice]:
        if not invoice_ids:
            return []
        now = datetime.now(timezone.utc)
        stmt = select(ManagerInvoice).where(
            ManagerInvoice.client_id == user_id,
            ManagerInvoice.id.in_(invoice_ids),
            or_(ManagerInvoice.due_date.is_(None), ManagerInvoice.due_date >= now),
            ManagerInvoice.status != InvoiceStatus.paid,
        )
        res = await self.db.execute(stmt)
        return list(res.scalars())

    async def pay_invoices(
        self,
        user_id: uuid.UUID,
        invoice_ids: list[uuid.UUID],
        success: bool,
    ) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
        if not success:
            return [], list(invoice_ids)

        stmt = select(ManagerInvoice).where(
            ManagerInvoice.client_id == user_id,
            ManagerInvoice.id.in_(invoice_ids),
        )
        res = await self.db.execute(stmt)
        invoices = list(res.scalars())
        found_ids = {inv.id for inv in invoices}
        skipped_ids = [inv_id for inv_id in invoice_ids if inv_id not in found_ids]

        processed_ids: list[uuid.UUID] = []
        for inv in invoices:
            if inv.status == InvoiceStatus.paid:
                skipped_ids.append(inv.id)
                continue
            inv.status = InvoiceStatus.paid
            payment = InvoicePayment(
                invoice_id=inv.id,
                client_id=user_id,
                amount=inv.amount,
                status="success",
            )
            self.db.add(payment)
            processed_ids.append(inv.id)

        await self.db.commit()
        return processed_ids, skipped_ids
