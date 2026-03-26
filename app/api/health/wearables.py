from datetime import date
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_client
from app.models.client import Client
from app.models.wearable_data import WearableData, WearableSource

router = APIRouter(prefix="/wearables", tags=["health"])


class WearableDataCreate(BaseModel):
    data_date: date
    source: WearableSource = WearableSource.MANUAL
    sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    sleep_efficiency: Optional[float] = Field(None, ge=0, le=100)
    deep_sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    rem_sleep_hours: Optional[float] = Field(None, ge=0, le=24)
    hrv_ms: Optional[float] = Field(None, ge=0)
    resting_hr: Optional[int] = Field(None, ge=20, le=250)
    recovery_score: Optional[float] = Field(None, ge=0, le=100)
    readiness_score: Optional[float] = Field(None, ge=0, le=100)
    strain_score: Optional[float] = Field(None, ge=0)
    steps: Optional[int] = Field(None, ge=0)
    active_calories: Optional[int] = Field(None, ge=0)
    zone2_minutes: Optional[int] = Field(None, ge=0)
    vo2_max: Optional[float] = Field(None, ge=0, le=100)
    weight_kg: Optional[float] = Field(None, ge=0)


class WearableDataResponse(BaseModel):
    id: UUID
    data_date: date
    source: WearableSource
    sleep_hours: Optional[float]
    sleep_efficiency: Optional[float]
    hrv_ms: Optional[float]
    resting_hr: Optional[int]
    recovery_score: Optional[float]
    readiness_score: Optional[float]
    strain_score: Optional[float]
    steps: Optional[int]
    zone2_minutes: Optional[int]
    vo2_max: Optional[float]
    weight_kg: Optional[float]

    model_config = {"from_attributes": True}


@router.get("", response_model=list[WearableDataResponse])
async def list_wearables(
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    result = await db.execute(
        select(WearableData)
        .where(WearableData.client_id == client.id)
        .order_by(WearableData.data_date.desc())
        .limit(limit)
    )
    return result.scalars().all()


@router.post("", response_model=WearableDataResponse, status_code=status.HTTP_201_CREATED)
async def log_wearable(
    data: WearableDataCreate,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    # Upsert by date+source
    existing = await db.execute(
        select(WearableData).where(
            WearableData.client_id == client.id,
            WearableData.data_date == data.data_date,
            WearableData.source == data.source,
        )
    )
    record = existing.scalars().first()
    if record:
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(record, field, value)
    else:
        record = WearableData(client_id=client.id, **data.model_dump())
        db.add(record)
    await db.commit()
    await db.refresh(record)
    return record
