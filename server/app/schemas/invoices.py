from __future__ import annotations

import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class InvoiceOut(BaseModel):
    id: uuid.UUID
    amount: float
    description: str | None = None
    contract_number: str | None = None
    due_date: datetime | None = None
    status: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class InvoicePayRequest(BaseModel):
    invoice_ids: list[uuid.UUID] = Field(min_length=1)
    success: bool = True


class InvoicePayResponse(BaseModel):
    processed_ids: list[uuid.UUID]
    skipped_ids: list[uuid.UUID]
