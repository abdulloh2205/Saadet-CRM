# app/api/lead_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadCreate, LeadOut, LeadUpdate
from app.bot.alerts import send_admin_alert

router = APIRouter(prefix="/api/leads", tags=["leads"])

@router.get("", response_model=list[LeadOut])
async def get_leads(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).order_by(Lead.created_at.desc()))
    return result.scalars().all()

@router.post("", response_model=LeadOut, status_code=201)
async def create_lead(payload: LeadCreate, db: AsyncSession = Depends(get_db)):
    lead = Lead(**payload.model_dump())
    db.add(lead)
    await db.commit()
    await db.refresh(lead)
    
    # Send notification
    text = f"🆕 <b>Новый лид!</b>\n\n"
    if lead.name:
        text += f"Имя: <b>{lead.name}</b>\n"
    if lead.contact:
        text += f"Контакт: <b>{lead.contact}</b>\n"
    if lead.source:
        text += f"Источник: {lead.source}\n"
    if lead.interested_in:
        text += f"Интересует: {lead.interested_in}\n"
    if lead.comments:
        text += f"Комментарий: {lead.comments}\n"
    
    await send_admin_alert(text)
    
    return lead

@router.patch("/{lead_id}", response_model=LeadOut)
async def update_lead(lead_id: int, payload: LeadUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Lead).where(Lead.id == lead_id))
    lead = result.scalar_one_or_none()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
        
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(lead, key, value)
        
    await db.commit()
    await db.refresh(lead)
    return lead
