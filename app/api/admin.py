from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_admin
from app.models.training_note import TrainingNote
from app.models.user import User
from app.tasks.daily_summary import generate_daily_summary

router = APIRouter(prefix="/admin", tags=["admin"])


class TrainingNoteCreate(BaseModel):
    guidance: str
    conversation_id: str | None = None
    message_id: str | None = None


class TrainingNoteResponse(BaseModel):
    id: str
    guidance: str
    created_at: str

    model_config = {"from_attributes": True}


@router.get("/daily-summary")
async def get_daily_summary(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    summary = await generate_daily_summary(db)
    return {"summary": summary}


@router.post("/training-notes", status_code=201)
async def create_training_note(
    data: TrainingNoteCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    note = TrainingNote(
        user_id=admin.id,
        guidance=data.guidance,
        conversation_id=data.conversation_id,
        message_id=data.message_id,
    )
    db.add(note)
    await db.flush()
    return {"id": str(note.id), "guidance": note.guidance}


@router.get("/training-notes")
async def list_training_notes(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(TrainingNote).order_by(TrainingNote.created_at.desc())
    )
    notes = result.scalars().all()
    return [
        {"id": str(n.id), "guidance": n.guidance, "created_at": str(n.created_at)}
        for n in notes
    ]
