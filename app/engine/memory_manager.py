from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.llm.factory import get_llm_provider
from app.models.client import Client
from app.models.conversation import Conversation
from app.models.message import Message

SUMMARIZE_PROMPT = """Summarize the following coaching conversation concisely.
Focus on: key themes discussed, client's emotional state, insights gained,
action items, and anything important for continuity in future sessions.
Keep it under 500 words.

Conversation:
{conversation}"""

COMPRESS_MEMORY_PROMPT = """You are maintaining a rolling summary of a coaching client's history.
Compress the following summary while preserving the most important information:
- Key themes and patterns
- Major breakthroughs or insights
- Current goals and action items
- Emotional patterns
- Important life context

Current summary:
{summary}

Produce a compressed version under 800 words that retains the essential information."""


async def summarize_conversation(db: AsyncSession, conversation: Conversation) -> str:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    if not messages:
        return ""

    conversation_text = "\n".join(
        f"{msg.role.value}: {msg.content}" for msg in messages
    )

    llm = get_llm_provider()
    summary = await llm.chat(
        messages=[{"role": "user", "content": SUMMARIZE_PROMPT.format(conversation=conversation_text)}],
        max_tokens=1024,
        temperature=0.3,
    )
    return summary


async def update_client_memory(
    db: AsyncSession, client: Client, new_summary: str
) -> None:
    if client.memory_summary:
        combined = f"{client.memory_summary}\n\n---\n\n{new_summary}"
    else:
        combined = new_summary

    # Check if memory needs compression (rough token estimate: 1 token ≈ 4 chars)
    estimated_tokens = len(combined) // 4
    if estimated_tokens > settings.MEMORY_SUMMARY_MAX_TOKENS:
        llm = get_llm_provider()
        compressed = await llm.chat(
            messages=[{"role": "user", "content": COMPRESS_MEMORY_PROMPT.format(summary=combined)}],
            max_tokens=1024,
            temperature=0.3,
        )
        client.memory_summary = compressed
    else:
        client.memory_summary = combined

    await db.flush()
