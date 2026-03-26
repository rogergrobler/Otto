"""
Coach Portal API — read-only patient view, notes, goal adjustment, AI summaries.
Accessible to User accounts with role ADMIN or COACH.
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_admin
from app.models.client import Client
from app.models.coach_note import CoachNote
from app.models.goal import Goal, GoalStatus
from app.models.lab_result import LabResult
from app.models.risk_score import RiskScore
from app.models.user import User
from app.services.coach_service import generate_preconsultation_summary

router = APIRouter(prefix="/coach", tags=["coach"])


class PatientSummary(BaseModel):
    id: UUID
    full_name: str
    email: Optional[str]
    date_of_birth: Optional[str]
    sex: Optional[str]
    weight_kg: Optional[float]
    subscription_tier: str

    model_config = {"from_attributes": True}


class CoachNoteCreate(BaseModel):
    note_text: str


class CoachNoteResponse(BaseModel):
    id: UUID
    client_id: UUID
    coach_id: UUID
    note_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class GoalAdjustment(BaseModel):
    current_value: Optional[str] = None
    target_value: Optional[str] = None
    deadline: Optional[str] = None
    status: Optional[GoalStatus] = None
    notes: Optional[str] = None


@router.get("/patients", response_model=list[PatientSummary])
async def list_patients(
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(get_current_admin),
):
    """List all active patients."""
    result = await db.execute(
        select(Client).where(Client.is_active.is_(True)).order_by(Client.full_name)
    )
    return result.scalars().all()


@router.get("/patients/{client_id}/overview")
async def get_patient_overview(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(get_current_admin),
):
    """Full health overview for a patient — labs, goals, risk scores."""
    client = await _get_client_or_404(db, client_id)

    labs = await db.execute(
        select(LabResult)
        .where(LabResult.client_id == client_id)
        .order_by(LabResult.test_date.desc())
        .limit(50)
    )
    goals = await db.execute(
        select(Goal).where(Goal.client_id == client_id, Goal.status == GoalStatus.ACTIVE)
    )
    risk = await db.execute(select(RiskScore).where(RiskScore.client_id == client_id))
    notes = await db.execute(
        select(CoachNote)
        .where(CoachNote.client_id == client_id)
        .order_by(CoachNote.created_at.desc())
        .limit(10)
    )

    return {
        "client": {
            "id": str(client.id),
            "full_name": client.full_name,
            "email": client.email,
            "date_of_birth": str(client.date_of_birth) if client.date_of_birth else None,
            "sex": client.sex.value if client.sex else None,
            "weight_kg": client.weight_kg,
            "height_cm": client.height_cm,
            "daily_protein_target_g": client.daily_protein_target_g,
            "daily_fibre_target_g": client.daily_fibre_target_g,
        },
        "risk_scores": [
            {
                "domain": rs.domain.value,
                "score": rs.score,
                "rag_status": rs.rag_status.value,
                "interpretation": rs.interpretation,
                "contributing_factors": rs.contributing_factors,
            }
            for rs in risk.scalars().all()
        ],
        "active_goals": [
            {
                "id": str(g.id),
                "domain": g.domain.value,
                "goal_text": g.goal_text,
                "current_value": g.current_value,
                "target_value": g.target_value,
                "deadline": str(g.deadline) if g.deadline else None,
            }
            for g in goals.scalars().all()
        ],
        "recent_labs": [
            {
                "marker_name": l.marker_name,
                "value": l.value,
                "unit": l.unit,
                "flag": l.flag.value if l.flag else None,
                "test_date": str(l.test_date),
            }
            for l in labs.scalars().all()
        ],
        "coach_notes": [
            {"note_text": n.note_text, "created_at": str(n.created_at)}
            for n in notes.scalars().all()
        ],
    }


@router.post("/patients/{client_id}/notes", response_model=CoachNoteResponse, status_code=status.HTTP_201_CREATED)
async def add_coach_note(
    client_id: UUID,
    note: CoachNoteCreate,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(get_current_admin),
):
    await _get_client_or_404(db, client_id)
    coach_note = CoachNote(
        client_id=client_id,
        coach_id=coach.id,
        note_text=note.note_text,
    )
    db.add(coach_note)
    await db.commit()
    await db.refresh(coach_note)
    return coach_note


@router.patch("/patients/{client_id}/goals/{goal_id}")
async def adjust_goal(
    client_id: UUID,
    goal_id: UUID,
    adjustment: GoalAdjustment,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(get_current_admin),
):
    """Coach can adjust a patient's goal targets."""
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.client_id == client_id)
    )
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    for field, value in adjustment.model_dump(exclude_none=True).items():
        setattr(goal, field, value)

    await db.commit()
    await db.refresh(goal)
    return {"success": True, "goal_id": str(goal.id)}


@router.post("/patients/{client_id}/summary")
async def get_preconsultation_summary(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    coach: User = Depends(get_current_admin),
):
    """Generate an AI pre-consultation summary for a patient."""
    client = await _get_client_or_404(db, client_id)
    summary = await generate_preconsultation_summary(db, client)
    return {"client_id": str(client_id), "summary": summary}


async def _get_client_or_404(db: AsyncSession, client_id: UUID) -> Client:
    result = await db.execute(select(Client).where(Client.id == client_id))
    client = result.scalars().first()
    if not client:
        raise HTTPException(status_code=404, detail="Patient not found.")
    return client
