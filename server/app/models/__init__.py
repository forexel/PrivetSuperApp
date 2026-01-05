# /Users/d.yudin/PrivetSuperApp/server/app/models/__init__.py
"""Aggregate model imports so Alembic sees them in Base.metadata."""

# Пользователи
from .users import User  # noqa

# Устройства (+ фото в этом же файле)
from .devices import Device, DevicePhoto  # noqa

# Тикеты
from .tickets import Ticket, TicketStatusHistory, TicketAttachment, RequestMessage, RequestMessageAuthor  # noqa
from .ticket_reports import TicketWorkReport, TicketWorkPhoto  # noqa

# Подписки
from .subscriptions import Subscription  # noqa

# Счета
from .invoices import ManagerInvoice, InvoicePayment  # noqa

# Саппорт
from .support import SupportTicket, SupportMessage  # noqa

# Мастера
from .master_users import MasterUser  # noqa

# FAQ
from .faq import FAQCategory, FAQArticle  # noqa

from .password_reset_tokens import PasswordResetToken  # noqa
from .sessions import Session

__all__ = [
    # users
    "User",
    # devices
    "Device", "DevicePhoto",
    # tickets
    "Ticket", "TicketStatusHistory", "TicketAttachment", "RequestMessage", "RequestMessageAuthor",
    "TicketWorkReport", "TicketWorkPhoto",
    # subscriptions
    "Subscription",
    # invoices
    "ManagerInvoice", "InvoicePayment",
    # support
    "SupportTicket", "SupportMessage",
    # masters
    "MasterUser",
    # faq
    "FAQCategory", "FAQArticle",
    "Session", "PasswordResetToken",
]
