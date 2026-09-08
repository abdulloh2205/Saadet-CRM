# app/schemas/lead.py
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.lead import LeadStatus

class LeadBase(BaseModel):
    name: str | None = None
    contact: str | None = None
    source: str | None = None
    interested_in: str | None = None
    comments: str | None = None
    status: LeadStatus = LeadStatus.NEW

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    name: str | None = None
    contact: str | None = None
    source: str | None = None
    interested_in: str | None = None
    comments: str | None = None
    status: LeadStatus | None = None

class LeadOut(LeadBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
