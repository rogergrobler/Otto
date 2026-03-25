import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_client
from app.models.client import Client
from app.models.goal import Goal, GoalStatus
from app.schemas.health import GoalCreate, GoalResponse, GoalUpdate

router = APIRouter(prefix="/goals", tags=["health"])


@router.get("", response_model=list[GoalResponse])
async def list_goals(
    status: GoalStatus | None = None,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    query = select(Goal).where(Goal.client_id == client.id)
    if status:
        query = query.where(Goal.status == status)
    else:
        query = query.where(Goal.status == GoalStatus.ACTIVE)
    query = query.order_by(Goal.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
async def create_goal(
    goal: GoalCreate,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    new_goal = Goal(client_id=client.id, **goal.model_dump())
    db.add(new_goal)
    await db.commit()
    await db.refresh(new_goal)
    return new_goal


@router.patch("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: uuid.UUID,
    update: GoalUpdate,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.client_id == client.id)
    )
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")

    for field, value in update.model_dump(exclude_none=True).items():
        setattr(goal, field, value)

    await db.commit()
    await db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    goal_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    result = await db.execute(
        select(Goal).where(Goal.id == goal_id, Goal.client_id == client.id)
    )
    goal = result.scalars().first()
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found.")
    await db.delete(goal)
    await db.commit()
