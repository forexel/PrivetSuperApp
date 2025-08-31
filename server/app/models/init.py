

# Make ORM models importable via `app.models` and ensure mappers are configured.
from .tickets import (
    Ticket,
    TicketAttachment,
    TicketStatusHistory,
    TicketStatus,
    ChangedBy,
)

__all__ = [
    "Ticket",
    "TicketAttachment",
    "TicketStatusHistory",
    "TicketStatus",
    "ChangedBy",
]