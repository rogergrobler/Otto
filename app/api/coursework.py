import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_admin
from app.models.client import Client
from app.models.client_coursework import ClientCoursework
from app.models.coursework import Coursework
from app.models.user import User
from app.schemas.coursework import (
    AssignCourseworkRequest,
    ClientCourseworkResponse,
    CourseworkCreate,
    CourseworkResponse,
)

router = APIRouter(prefix="/coursework", tags=["coursework"])


@router.get("", response_model=list[CourseworkResponse])
async def list_coursework(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(select(Coursework).order_by(Coursework.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=CourseworkResponse, status_code=status.HTTP_201_CREATED)
async def create_coursework(
    data: CourseworkCreate,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(get_current_admin),
):
    cw = Coursework(
        title=data.title,
        description=data.description,
        content=data.content,
        created_by_id=admin.id,
    )
    db.add(cw)
    await db.flush()
    return cw


@router.post("/{coursework_id}/assign", response_model=list[ClientCourseworkResponse])
async def assign_coursework(
    coursework_id: uuid.UUID,
    data: AssignCourseworkRequest,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    # Verify coursework exists
    result = await db.execute(select(Coursework).where(Coursework.id == coursework_id))
    cw = result.scalars().first()
    if not cw:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Coursework not found")

    assignments = []
    for client_id in data.client_ids:
        # Verify client exists
        result = await db.execute(select(Client).where(Client.id == client_id))
        client = result.scalars().first()
        if not client:
            continue

        assignment = ClientCoursework(
            client_id=client_id,
            coursework_id=coursework_id,
        )
        db.add(assignment)
        assignments.append(assignment)

        # Ping client on Telegram if requested
        if data.ping_telegram and client.telegram_chat_id:
            try:
                from app.telegram.bot import send_message

                await send_message(
                    client.telegram_chat_id,
                    f"Hi {client.full_name}! You have new coursework assigned: **{cw.title}**\n\n"
                    f"{cw.description or 'Check in with Sofia to get started!'}",
                )
            except Exception:
                pass  # Don't fail the assignment if Telegram ping fails

    await db.flush()
    return assignments


@router.get("/client/{client_id}", response_model=list[ClientCourseworkResponse])
async def list_client_coursework(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(get_current_admin),
):
    result = await db.execute(
        select(ClientCoursework)
        .where(ClientCoursework.client_id == client_id)
        .order_by(ClientCoursework.assigned_at.desc())
    )
    return result.scalars().all()
