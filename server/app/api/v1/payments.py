from __future__ import annotations

import uuid
from decimal import Decimal, ROUND_HALF_UP

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_user, get_db
from app.models.users import User
from app.schemas.payments import (
    CreateInvoicePaymentRequest,
    CreateSubscriptionPaymentRequest,
    PaymentRedirectResponse,
)
from app.services.invoices import InvoiceService
from app.services.subscriptions import SubscriptionService


router = APIRouter(prefix="/payments", tags=["payments"])

YOOKASSA_API_URL = "https://api.yookassa.ru/v3/payments"


def _require_yookassa_config() -> None:
    if not settings.YOOKASSA_SHOP_ID:
        raise HTTPException(status_code=500, detail="YOOKASSA_SHOP_ID is not configured")
    if not settings.YOOKASSA_SECRET_KEY:
        raise HTTPException(status_code=500, detail="YOOKASSA_SECRET_KEY is not configured")
    if not settings.APP_BASE_URL:
        raise HTTPException(status_code=500, detail="APP_BASE_URL is not configured")


def _build_return_url(path: str) -> str:
    base = settings.APP_BASE_URL.rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _format_amount(value: Decimal | str | float) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"{amount:.2f}"


def _normalize_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    cleaned = "".join(ch for ch in str(phone) if ch.isdigit() or ch == "+")
    if cleaned.startswith("+"):
        return cleaned
    digits = "".join(ch for ch in cleaned if ch.isdigit())
    if len(digits) == 10:
        return f"+7{digits}"
    if len(digits) == 11 and digits.startswith("7"):
        return f"+{digits}"
    return cleaned if cleaned else None


def _build_receipt(
    *,
    amount: Decimal | str | float,
    description: str,
    customer_phone: str | None,
    customer_email: str | None,
) -> dict:
    customer: dict[str, str] = {}
    if customer_email:
        customer["email"] = customer_email
    phone = _normalize_phone(customer_phone)
    if phone:
        customer["phone"] = phone
    receipt = {
        "customer": customer,
        "items": [
            {
                "description": description,
                "quantity": "1",
                "amount": {"value": _format_amount(amount), "currency": "RUB"},
                "vat_code": 1,
                "payment_mode": "full_payment",
                "payment_subject": "service",
            }
        ],
        "tax_system_code": 2,
    }
    return receipt


async def _create_yookassa_payment(
    *,
    amount: Decimal | str | float,
    description: str,
    return_path: str,
    metadata: dict[str, str],
    receipt: dict | None = None,
) -> str:
    _require_yookassa_config()
    idempotence_key = str(uuid.uuid4())
    payload = {
        "amount": {"value": _format_amount(amount), "currency": "RUB"},
        "confirmation": {"type": "redirect", "return_url": _build_return_url(return_path)},
        "capture": True,
        "description": description,
        "metadata": metadata,
    }
    if receipt:
        payload["receipt"] = receipt
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(
            YOOKASSA_API_URL,
            json=payload,
            headers={"Idempotence-Key": idempotence_key},
            auth=(settings.YOOKASSA_SHOP_ID, settings.YOOKASSA_SECRET_KEY),
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=502, detail="YooKassa payment creation failed")
    data = resp.json()
    confirmation = data.get("confirmation") or {}
    confirmation_url = confirmation.get("confirmation_url")
    if not confirmation_url:
        raise HTTPException(status_code=502, detail="YooKassa confirmation_url missing")
    return confirmation_url


def _verify_webhook_secret(request: Request) -> None:
    if not settings.YOOKASSA_WEBHOOK_SECRET:
        return
    provided = request.headers.get("Authorization") or request.headers.get("X-Webhook-Secret")
    if not provided:
        raise HTTPException(status_code=400, detail="Webhook secret missing")
    if provided == settings.YOOKASSA_WEBHOOK_SECRET:
        return
    if provided == f"Bearer {settings.YOOKASSA_WEBHOOK_SECRET}":
        return
    raise HTTPException(status_code=400, detail="Invalid webhook secret")


@router.post("/yookassa/invoices", response_model=PaymentRedirectResponse)
async def create_invoice_payment(
    payload: CreateInvoicePaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = InvoiceService(db)
    invoices = await service.get_payable_invoices(current_user.id, payload.invoice_ids)
    if not invoices:
        raise HTTPException(status_code=404, detail="No payable invoices found")

    found_ids = {inv.id for inv in invoices}
    missing_ids = [str(inv_id) for inv_id in payload.invoice_ids if inv_id not in found_ids]
    if missing_ids:
        raise HTTPException(status_code=400, detail="Some invoices are not available for payment")

    total = sum(Decimal(str(inv.amount)) for inv in invoices)
    receipt = _build_receipt(
        amount=total,
        description="Invoice payment",
        customer_phone=current_user.phone,
        customer_email=current_user.email,
    )
    confirmation_url = await _create_yookassa_payment(
        amount=total,
        description="Invoice payment",
        return_path="/invoices/success",
        metadata={
            "kind": "invoice",
            "user_id": str(current_user.id),
            "invoice_ids": ",".join(str(inv.id) for inv in invoices),
        },
        receipt=receipt,
    )
    return PaymentRedirectResponse(redirect_url=confirmation_url)


@router.post("/yookassa/subscription", response_model=PaymentRedirectResponse)
async def create_subscription_payment(
    payload: CreateSubscriptionPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        price = SubscriptionService.get_price(payload.plan, payload.period)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Unknown plan or period") from exc

    receipt = _build_receipt(
        amount=price,
        description=f"Subscription {payload.plan}/{payload.period}",
        customer_phone=current_user.phone,
        customer_email=current_user.email,
    )
    confirmation_url = await _create_yookassa_payment(
        amount=price,
        description=f"Subscription {payload.plan}/{payload.period}",
        return_path="/subscriptions/success",
        metadata={
            "kind": "subscription",
            "user_id": str(current_user.id),
            "plan": payload.plan,
            "period": payload.period,
        },
        receipt=receipt,
    )
    return PaymentRedirectResponse(redirect_url=confirmation_url)


@router.post("/yookassa/notify")
async def yookassa_notify(request: Request, db: AsyncSession = Depends(get_db)):
    _verify_webhook_secret(request)
    data = await request.json()
    event = data.get("event")
    obj = data.get("object") or {}

    if event not in {"payment.succeeded", "payment.canceled"}:
        return {"status": "ignored"}

    if obj.get("status") != "succeeded":
        return {"status": "ignored"}

    metadata = obj.get("metadata") or {}
    kind = metadata.get("kind")
    amount_data = obj.get("amount") or {}
    try:
        amount = Decimal(str(amount_data.get("value", "0")))
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid amount") from exc

    if kind == "invoice":
        try:
            user_id = uuid.UUID(metadata.get("user_id", ""))
            invoice_ids = [
                uuid.UUID(inv_id)
                for inv_id in (metadata.get("invoice_ids", "")).split(",")
                if inv_id
            ]
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid invoice metadata") from exc
        invoices = await InvoiceService(db).get_payable_invoices(user_id, invoice_ids)
        if not invoices or len(invoices) != len(invoice_ids):
            raise HTTPException(status_code=400, detail="Invoices not found")
        expected = sum(Decimal(str(inv.amount)) for inv in invoices)
        if _format_amount(expected) != _format_amount(amount):
            raise HTTPException(status_code=400, detail="Invalid amount")
        await InvoiceService(db).pay_invoices(user_id=user_id, invoice_ids=invoice_ids, success=True)
        return {"status": "ok"}

    if kind == "subscription":
        try:
            user_id = uuid.UUID(metadata.get("user_id", ""))
        except Exception as exc:
            raise HTTPException(status_code=400, detail="Invalid subscription metadata") from exc
        plan = metadata.get("plan")
        period = metadata.get("period")
        if not plan or not period:
            raise HTTPException(status_code=400, detail="Invalid subscription metadata")
        try:
            expected = SubscriptionService.get_price(plan, period)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Unknown plan or period") from exc
        if _format_amount(expected) != _format_amount(amount):
            raise HTTPException(status_code=400, detail="Invalid amount")
        res = await db.execute(select(User).where(User.id == user_id))
        user = res.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await SubscriptionService(db).choose_plan(user, plan, period)
        return {"status": "ok"}

    return {"status": "ignored"}
