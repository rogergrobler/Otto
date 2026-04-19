from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.dependencies import get_current_client
from app.models.client import Client
from app.models.risk_score import RAGStatus, RiskDomain, RiskScore
from app.services.risk_engine import calculate_all_domains, calculate_health_score

RISK_STALE_AFTER = timedelta(hours=1)

router = APIRouter(prefix="/risk", tags=["health"])


class RiskScoreResponse(BaseModel):
    id: UUID
    domain: RiskDomain
    score: Optional[float]
    rag_status: RAGStatus
    interpretation: Optional[str]
    contributing_factors: Optional[list]
    data_gaps: Optional[list]

    model_config = {"from_attributes": True}


class HealthScoreResponse(BaseModel):
    health_score: int
    domains: list[RiskScoreResponse]


@router.get("", response_model=HealthScoreResponse)
async def get_risk_scores(
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """Get current risk scores and composite Health Score. Auto-recomputes if stale or missing."""
    result = await db.execute(
        select(RiskScore).where(RiskScore.client_id == client.id)
    )
    scores = result.scalars().all()

    # Auto-recompute if no scores exist, or if the oldest calculation is stale
    should_recalc = not scores
    if scores:
        oldest = min(s.last_calculated for s in scores)
        if oldest.tzinfo is None:
            oldest = oldest.replace(tzinfo=timezone.utc)
        should_recalc = (datetime.now(timezone.utc) - oldest) > RISK_STALE_AFTER

    if should_recalc:
        scores = await calculate_all_domains(db, client)
        await db.commit()

    return HealthScoreResponse(
        health_score=calculate_health_score(scores),
        domains=scores,
    )


@router.post("/calculate", response_model=HealthScoreResponse)
async def calculate_risk(
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """Trigger a full risk recalculation across all Four Horsemen domains."""
    scores = await calculate_all_domains(db, client)
    await db.commit()
    return HealthScoreResponse(
        health_score=calculate_health_score(scores),
        domains=scores,
    )
