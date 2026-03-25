from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.prompts import OTTO_DEFAULT_SOUL, build_system_prompt
from app.models.client import Client
from app.models.client_coursework import AssignmentStatus, ClientCoursework
from app.models.conversation import Conversation
from app.models.document import DocType, Document
from app.models.message import Message
from app.models.training_note import TrainingNote
from app.rag.retriever import retrieve_context


async def get_soul_document(db: AsyncSession) -> str | None:
    result = await db.execute(
        select(Document).where(Document.doc_type == DocType.SOUL, Document.is_active.is_(True))
    )
    doc = result.scalars().first()
    if doc:
        from app.rag.chunker import extract_text_from_file

        return extract_text_from_file(doc.file_path)
    return None


async def get_training_notes(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(TrainingNote).order_by(TrainingNote.created_at.desc())
    )
    notes = result.scalars().all()
    return [note.guidance for note in notes]


async def get_client_profile(client: Client) -> str:
    parts = [f"Name: {client.full_name}"]
    if client.notes:
        parts.append(f"Coach's notes: {client.notes}")
    return "\n".join(parts)


async def get_active_coursework(db: AsyncSession, client_id: str) -> str | None:
    from app.models.coursework import Coursework

    result = await db.execute(
        select(ClientCoursework, Coursework)
        .join(Coursework)
        .where(
            ClientCoursework.client_id == client_id,
            ClientCoursework.status.in_([AssignmentStatus.ASSIGNED, AssignmentStatus.IN_PROGRESS]),
        )
    )
    assignments = result.all()
    if not assignments:
        return None

    parts = []
    for assignment, coursework in assignments:
        parts.append(
            f"**{coursework.title}** (Status: {assignment.status.value})\n{coursework.content}"
        )
    return "\n\n".join(parts)


async def get_recent_messages(
    db: AsyncSession, conversation: Conversation, limit: int = 20
) -> list[dict]:
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    messages = list(reversed(result.scalars().all()))

    return [
        {
            "role": "user" if msg.role.value == "client" else "assistant",
            "content": msg.content,
        }
        for msg in messages
        if msg.role.value != "system"
    ]


async def build_context(
    db: AsyncSession,
    client: Client,
    conversation: Conversation,
    latest_message: str,
) -> tuple[str, list[dict]]:
    """Build the full context for a coaching interaction.

    Returns:
        Tuple of (system_prompt, messages_list)
    """
    # Gather all context pieces
    soul_doc = await get_soul_document(db) or OTTO_DEFAULT_SOUL
    training_notes = await get_training_notes(db)
    client_profile = await get_client_profile(client)
    coursework_context = await get_active_coursework(db, str(client.id))

    # RAG retrieval based on latest message
    rag_context = await retrieve_context(query=latest_message)

    # Build system prompt
    system = build_system_prompt(
        soul_doc=soul_doc,
        training_notes=training_notes,
        client_profile=client_profile,
        memory_summary=client.memory_summary,
        coursework_context=coursework_context,
    )

    if rag_context:
        system += f"\n\n{rag_context}"

    # Get recent messages for conversation context
    messages = await get_recent_messages(db, conversation)

    return system, messages
