from __future__ import annotations
from datetime import datetime, date
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class TicketStatus(str, Enum):
    new = "new"
    in_progress = "in_progress"
    completed = "completed"
    reject = "reject"


class TicketCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    device_id: Optional[UUID] = None
    preferred_date: Optional[date] = None
    # client can upload separately; keep ids/urls here if used
    attachment_urls: List[str] = []


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=5000)
    preferred_date: Optional[date] = None


class TicketStatusUpdate(BaseModel):
    status: TicketStatus


class TicketRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: TicketStatus
    created_at: datetime
    updated_at: Optional[datetime] = None


class TicketListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: TicketStatus
    created_at: datetime


class TicketDetail(TicketRead):
    description: Optional[str] = None
    device_id: Optional[UUID] = None
    # simplified presentation fields
    attachment_urls: List[str] = []
    status_history: List[dict] = []  # service may map ORM -> dicts
