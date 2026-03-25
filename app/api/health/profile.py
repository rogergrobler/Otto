from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_current_client
from app.models.client import Client
from app.schemas.health import HealthProfileResponse, HealthProfileUpdate

router = APIRouter(prefix="/profile", tags=["health"])


@router.get("", response_model=HealthProfileResponse)
async def get_profile(client: Client = Depends(get_current_client)):
    return client


@router.patch("", response_model=HealthProfileResponse)
async def update_profile(
    update: HealthProfileUpdate,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    for field, value in update.model_dump(exclude_none=True).items():
        setattr(client, field, value)

    # Auto-calculate protein target from weight if not set
    if client.weight_kg and not client.daily_protein_target_g:
        client.daily_protein_target_g = int(client.weight_kg * 1.8)

    await db.commit()
    await db.refresh(client)
    return client
