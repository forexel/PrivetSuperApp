from __future__ import annotations

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db, get_current_user
from app.models.users import User
from app.schemas.invoices import InvoiceOut, InvoicePayRequest, InvoicePayResponse
from app.services.invoices import InvoiceService


router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.get("/my", response_model=list[InvoiceOut])
async def list_my_invoices(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    include_paid: bool = False,
):
    return await InvoiceService(db).list_for_user(current_user.id, include_paid=include_paid)


@router.post("/pay", response_model=InvoicePayResponse, status_code=status.HTTP_200_OK)
async def pay_invoices(
    payload: InvoicePayRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if not payload.invoice_ids:
        raise HTTPException(status_code=400, detail="invoice_ids required")
    processed_ids, skipped_ids = await InvoiceService(db).pay_invoices(
        user_id=current_user.id,
        invoice_ids=payload.invoice_ids,
        success=payload.success,
    )
    return InvoicePayResponse(processed_ids=processed_ids, skipped_ids=skipped_ids)
