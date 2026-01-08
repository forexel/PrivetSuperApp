from __future__ import annotations

import uuid
from pydantic import BaseModel, Field

from app.schemas.subscriptions import PlanName, PlanPeriod


class PaymentRedirectResponse(BaseModel):
    redirect_url: str


class CreateInvoicePaymentRequest(BaseModel):
    invoice_ids: list[uuid.UUID] = Field(min_length=1)


class CreateSubscriptionPaymentRequest(BaseModel):
    plan: PlanName
    period: PlanPeriod
