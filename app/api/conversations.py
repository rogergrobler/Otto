import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_admin
from app.engine.memory_manager import summarize_conversation
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.user import User
from app.schemas.conversation import ConversationResponse
from app.schemas.message import MessageResponse

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("/client/{client_id}", response_model=list[ConversationResponse])
async def list_client_conversations(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(Conversation)
        .where(Conversation.client_id == client_id)
        .order_by(Conversation.started_at.desc())
    )
    return result.scalars().all()


@router.get("/{conversation_id}", response_model=list[MessageResponse])
async def get_conversation_messages(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()


@router.post("/{conversation_id}/summary")
async def generate_conversation_summary(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(Conversation).where(Conversation.id == conversation_id)
    )
    conversation = result.scalars().first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    summary = await summarize_conversation(db, conversation)
    conversation.summary = summary
    await db.flush()
    return {"summary": summary}
