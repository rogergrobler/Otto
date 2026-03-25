from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_client
from app.engine.health_engine import get_or_create_conversation, process_health_message
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
    """Send a text message to Otto."""
    response_text = await process_health_message(
        db, client, request.message, Channel.WEB
    )
    await db.commit()
    conversation = await get_or_create_conversation(db, client, Channel.WEB)
    return ChatResponse(response=response_text, conversation_id=conversation.id)


@router.post("/with-image", response_model=ChatResponse)
async def send_message_with_image(
    message: str = Form(default=""),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """Send a message with an image to Otto (e.g. meal photo)."""
    image_bytes = await image.read()
    media_type = image.content_type or "image/jpeg"

    response_text = await process_health_message(
        db,
        client,
        message or "What did I eat? Please analyse this meal.",
        Channel.WEB,
        image_bytes=image_bytes,
        image_media_type=media_type,
    )
    await db.commit()
    conversation = await get_or_create_conversation(db, client, Channel.WEB)
    return ChatResponse(response=response_text, conversation_id=conversation.id)


@router.get("/history", response_model=list[MessageResponse])
async def get_chat_history(
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
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
