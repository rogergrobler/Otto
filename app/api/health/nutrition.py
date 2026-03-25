import uuid
from datetime import date
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.dependencies import get_current_client
from app.models.client import Client
from app.models.nutrition_log import NutritionLog
from app.schemas.health import (
    DailyNutritionSummary,
    MealAnalysis,
    NutritionLogCreate,
    NutritionLogResponse,
)
from app.services.nutrition_service import analyse_meal_from_bytes

router = APIRouter(prefix="/nutrition", tags=["health"])

UPLOAD_DIR = Path(settings.UPLOAD_DIR) / "meals"


@router.get("/today", response_model=DailyNutritionSummary)
async def get_today_nutrition(
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    return await _get_daily_summary(db, client, date.today())


@router.get("/{log_date}", response_model=DailyNutritionSummary)
async def get_nutrition_by_date(
    log_date: date,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    return await _get_daily_summary(db, client, log_date)


async def _get_daily_summary(
    db: AsyncSession, client: Client, target_date: date
) -> DailyNutritionSummary:
    result = await db.execute(
        select(NutritionLog)
        .where(NutritionLog.client_id == client.id, NutritionLog.log_date == target_date)
        .order_by(NutritionLog.created_at)
    )
    logs = result.scalars().all()

    def _sum(attr):
        return round(sum(getattr(l, attr) or 0 for l in logs), 1)

    return DailyNutritionSummary(
        date=target_date,
        total_calories=int(_sum("calories")),
        total_protein_g=_sum("protein_g"),
        total_fibre_g=_sum("fibre_g"),
        total_fat_g=_sum("fat_g"),
        total_carbs_net_g=_sum("carbs_net_g"),
        total_omega3_g=_sum("omega3_g"),
        total_alcohol_units=_sum("alcohol_units"),
        meals=logs,
        targets={
            "protein_g": client.daily_protein_target_g,
            "fibre_g": client.daily_fibre_target_g,
            "calories": client.daily_calories_target,
        },
    )


@router.post("/analyse", response_model=MealAnalysis)
async def analyse_meal_photo(
    file: UploadFile,
    client: Client = Depends(get_current_client),
):
    """
    Upload a meal photo for AI nutrition analysis.
    Returns an estimate for user confirmation — does NOT save automatically.
    Call POST /nutrition to save after confirming.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are accepted.")

    contents = await file.read()
    try:
        return await analyse_meal_from_bytes(contents, media_type=file.content_type)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to analyse meal photo: {e}")


@router.post("", response_model=NutritionLogResponse, status_code=status.HTTP_201_CREATED)
async def log_meal(
    meal: NutritionLogCreate,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """Log a meal (manually or after confirming an AI analysis)."""
    log = NutritionLog(client_id=client.id, **meal.model_dump())
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.post("/confirm", response_model=NutritionLogResponse, status_code=status.HTTP_201_CREATED)
async def confirm_meal_analysis(
    analysis: MealAnalysis,
    log_date: date | None = None,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    """Save a confirmed AI meal analysis as a nutrition log entry."""
    log = NutritionLog(
        client_id=client.id,
        log_date=log_date or date.today(),
        meal_type=analysis.meal_type,
        description=analysis.description,
        calories=analysis.calories,
        protein_g=analysis.protein_g,
        fat_g=analysis.fat_g,
        carbs_net_g=analysis.carbs_net_g,
        fibre_g=analysis.fibre_g,
        omega3_g=analysis.omega3_g,
        ai_analysed=True,
        notes=analysis.notes,
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nutrition_log(
    log_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    client: Client = Depends(get_current_client),
):
    result = await db.execute(
        select(NutritionLog).where(
            NutritionLog.id == log_id, NutritionLog.client_id == client.id
        )
    )
    log = result.scalars().first()
    if not log:
        raise HTTPException(status_code=404, detail="Nutrition log not found.")
    await db.delete(log)
    await db.commit()
