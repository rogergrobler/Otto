from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_client
from app.models.client import Client
from app.models.nudge import Nudge, NudgeType

router = APIRouter(prefix="/nudges", tags=["nudges"])


class NudgeResponse(BaseModel):
    id: UUID
    nudge_type: NudgeType
    message: str
    scheduled_at: datetime
    sent_at: Optional[datetime]
    acknowledged_at: Optional[datetime]

    model_config = {"from_attributes": True}


@router.get("", response_model=list[NudgeResponse])
async def list_nudges(
    unread_only: bool = True,
    limit: int = 20,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """Get nudges for the current user."""
    query = select(Nudge).where(Nudge.client_id == client.id)
    if unread_only:
        query = query.where(Nudge.acknowledged_at.is_(None))
    query = query.order_by(Nudge.scheduled_at.desc()).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{nudge_id}/acknowledge", response_model=NudgeResponse)
async def acknowledge_nudge(
    nudge_id: UUID,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    result = await db.execute(
        select(Nudge).where(Nudge.id == nudge_id, Nudge.client_id == client.id)
    )
    nudge = result.scalars().first()
    if not nudge:
        raise HTTPException(status_code=404, detail="Nudge not found.")
    nudge.acknowledged_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(nudge)
    return nudge
