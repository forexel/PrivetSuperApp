# app/schemas/support.py
import uuid
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class SupportCaseStatus(str, Enum):
    open = "open"
    pending = "pending"
    closed = "closed"
    rejected = "rejected"

class MessageAuthor(str, Enum):
    user = "user"
    support = "support"

class SupportCaseCreate(BaseModel):
    subject: str = Field(min_length=1, max_length=255)

class SupportCaseOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    subject: str
    status: SupportCaseStatus
    created_at: datetime
    class Config:
        from_attributes = True

class SupportCaseMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)

class SupportCaseMessageOut(BaseModel):
    id: uuid.UUID
    ticket_id: uuid.UUID
    author: MessageAuthor
    body: str
    created_at: datetime
    class Config:
        from_attributes = True

# Алиасы для совместимости со старым кодом:
TicketStatus = SupportCaseStatus
SupportTicketCreate = SupportCaseCreate
SupportTicketOut = SupportCaseOut
SupportMessageCreate = SupportCaseMessageCreate
SupportMessageOut = SupportCaseMessageOut