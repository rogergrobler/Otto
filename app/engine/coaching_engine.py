from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.engine.context_builder import build_context
from app.engine.memory_manager import summarize_conversation, update_client_memory
from app.llm.factory import get_llm_provider
from app.models.client import Client
from app.models.conversation import Channel, Conversation
from app.models.message import Message, MessageRole


async def get_or_create_conversation(
    db: AsyncSession, client: Client, channel: Channel
) -> Conversation:
    """Find the active conversation or create a new one."""
    timeout = timedelta(hours=settings.CONVERSATION_TIMEOUT_HOURS)
    cutoff = datetime.now(timezone.utc) - timeout

    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.client_id == client.id,
            Conversation.ended_at.is_(None),
            Conversation.started_at > cutoff,
        )
        .order_by(Conversation.started_at.desc())
        .limit(1)
    )
    conversation = result.scalars().first()

    if conversation:
        return conversation

    # Close any old open conversations and summarize them
    old_result = await db.execute(
        select(Conversation).where(
            Conversation.client_id == client.id,
            Conversation.ended_at.is_(None),
        )
    )
    for old_conv in old_result.scalars().all():
        old_conv.ended_at = datetime.now(timezone.utc)
        try:
            summary = await summarize_conversation(db, old_conv)
            old_conv.summary = summary
            await update_client_memory(db, client, summary)
        except Exception:
            pass  # Don't block new conversation on summary failure

    # Create new conversation
    conversation = Conversation(
        client_id=client.id,
        channel=channel,
    )
    db.add(conversation)
    await db.flush()
    return conversation


async def process_message(
    db: AsyncSession,
    client: Client,
    text: str,
    channel: Channel,
) -> str:
    """Process an incoming client message and return Sofia's response."""
    # Get or create conversation
    conversation = await get_or_create_conversation(db, client, channel)

    # Store the client's message
    client_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.CLIENT,
        content=text,
    )
    db.add(client_message)
    await db.flush()

    # Build context and get LLM response
    system_prompt, messages = await build_context(db, client, conversation, text)

    # Add the current message to the conversation
    messages.append({"role": "user", "content": text})

    llm = get_llm_provider()
    response_text = await llm.chat(
        messages=messages,
        system=system_prompt,
    )

    # Store Sofia's response
    sofia_message = Message(
        conversation_id=conversation.id,
        role=MessageRole.SOFIA,
        content=response_text,
    )
    db.add(sofia_message)
    await db.flush()

    return response_text
