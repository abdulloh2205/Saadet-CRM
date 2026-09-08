# app/models/lead.py
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class LeadStatus(str, enum.Enum):
    NEW = "NEW"
    IN_PROGRESS = "IN_PROGRESS"
    ORDERED = "ORDERED"
    CANCELLED = "CANCELLED"


class Lead(Base):
    __tablename__ = "leads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    interested_in: Mapped[str | None] = mapped_column(String(200), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    status: Mapped[LeadStatus] = mapped_column(Enum(LeadStatus), default=LeadStatus.NEW)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
