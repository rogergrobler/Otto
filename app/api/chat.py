from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_client
from app.engine.coaching_engine import get_or_create_conversation, process_message
from app.models.client import Client
from app.models.conversation import Channel, Conversation
from app.models.message import Message
from app.schemas.message import ChatRequest, ChatResponse, MessageResponse

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    response_text = await process_message(db, client, request.message, Channel.WEB)

    conversation = await get_or_create_conversation(db, client, Channel.WEB)
    return ChatResponse(response=response_text, conversation_id=conversation.id)


@router.get("/history", response_model=list[MessageResponse])
async def get_chat_history(
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    # Get the most recent active conversation
    result = await db.execute(
        select(Conversation)
        .where(Conversation.client_id == client.id, Conversation.ended_at.is_(None))
        .order_by(Conversation.started_at.desc())
        .limit(1)
    )
    conversation = result.scalars().first()
    if not conversation:
        return []

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    return result.scalars().all()
