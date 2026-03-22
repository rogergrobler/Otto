from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.llm.factory import get_llm_provider
from app.models.client import Client
from app.models.conversation import Conversation
from app.models.message import Message

DAILY_SUMMARY_PROMPT = """You are generating a daily briefing for coaching team (Max and Jenny).
Summarize the following client interactions from the past 24 hours.
For each client, include:
- Key topics discussed
- Client's emotional state and engagement level
- Any concerns or breakthroughs
- Action items or follow-ups needed

Be concise but thorough. Flag anything that needs immediate attention.

Client interactions:
{interactions}"""


async def generate_daily_summary(db: AsyncSession) -> str:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)

    # Get all messages from the last 24 hours with their conversations and clients
    result = await db.execute(
        select(Message)
        .join(Conversation)
        .join(Client)
        .where(Message.created_at > cutoff)
        .options(
            selectinload(Message.conversation).selectinload(Conversation.client)
        )
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    if not messages:
        return "No client interactions in the past 24 hours."

    # Group by client
    client_messages: dict[str, list[str]] = {}
    for msg in messages:
        client_name = msg.conversation.client.full_name
        if client_name not in client_messages:
            client_messages[client_name] = []
        client_messages[client_name].append(f"{msg.role.value}: {msg.content}")

    # Format interactions
    interactions_text = ""
    for client_name, msgs in client_messages.items():
        interactions_text += f"\n### {client_name}\n"
        interactions_text += "\n".join(msgs)
        interactions_text += "\n"

    llm = get_llm_provider()
    summary = await llm.chat(
        messages=[{
            "role": "user",
            "content": DAILY_SUMMARY_PROMPT.format(interactions=interactions_text),
        }],
        max_tokens=2048,
        temperature=0.3,
    )
    return summary
