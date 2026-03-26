"""
Otto Nudge Service.

Generates personalised, data-driven nudge messages for each user.
Called by the APScheduler jobs defined in tasks/nudge_scheduler.py.
"""
import logging
from datetime import date, datetime, timedelta, timezone

import anthropic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.client import Client
from app.models.goal import Goal, GoalStatus
from app.models.lab_result import LabResult
from app.models.nudge import Nudge, NudgeType
from app.models.nutrition_log import NutritionLog
from app.models.risk_score import RiskScore
from app.models.wearable_data import WearableData

logger = logging.getLogger(__name__)

NUDGE_SYSTEM = """You are Otto, a personal health twin assistant. Generate a short, warm,
personalised nudge message for the user. Be direct and specific — reference their actual data.
Never be preachy. Keep it to 1-2 sentences. No emojis."""


async def _llm_nudge(prompt: str) -> str:
    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = await client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=150,
        system=NUDGE_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )
    return response.content[0].text.strip()


async def _already_sent_today(db: AsyncSession, client_id, nudge_type: NudgeType) -> bool:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(Nudge).where(
            Nudge.client_id == client_id,
            Nudge.nudge_type == nudge_type,
            Nudge.scheduled_at >= today_start,
        )
    )
    return result.scalars().first() is not None


async def generate_daily_checkin(db: AsyncSession, client: Client) -> Nudge | None:
    if await _already_sent_today(db, client.id, NudgeType.DAILY_CHECKIN):
        return None

    # Pull yesterday's wearable data
    yesterday = date.today() - timedelta(days=1)
    result = await db.execute(
        select(WearableData).where(
            WearableData.client_id == client.id,
            WearableData.data_date == yesterday,
        )
    )
    wearable = result.scalars().first()

    if wearable:
        data_summary = (
            f"Sleep: {wearable.sleep_hours}h, "
            f"HRV: {wearable.hrv_ms}ms, "
            f"Recovery: {wearable.recovery_score}"
        )
        prompt = (
            f"Generate a morning check-in for {client.first_name if hasattr(client, 'first_name') else client.full_name.split()[0]}. "
            f"Yesterday's data: {data_summary}. "
            "Acknowledge the data briefly and suggest what kind of day this sets up for (training, recovery, etc.)."
        )
    else:
        prompt = (
            f"Generate a brief morning check-in message for {client.full_name.split()[0]}. "
            "No wearable data available. Encourage them to log their day."
        )

    message = await _llm_nudge(prompt)
    nudge = Nudge(
        client_id=client.id,
        nudge_type=NudgeType.DAILY_CHECKIN,
        message=message,
        scheduled_at=datetime.now(timezone.utc),
    )
    db.add(nudge)
    await db.flush()
    return nudge


async def generate_meal_reminder(db: AsyncSession, client: Client) -> Nudge | None:
    if await _already_sent_today(db, client.id, NudgeType.MEAL_REMINDER):
        return None

    today = date.today()
    result = await db.execute(
        select(func.count()).where(
            NutritionLog.client_id == client.id,
            NutritionLog.log_date == today,
        )
    )
    meals_today = result.scalar() or 0

    if meals_today >= 2:
        return None  # Already logging well

    protein_result = await db.execute(
        select(func.sum(NutritionLog.protein_g)).where(
            NutritionLog.client_id == client.id,
            NutritionLog.log_date == today,
        )
    )
    protein_so_far = round(protein_result.scalar() or 0, 0)
    target = client.daily_protein_target_g or 150

    prompt = (
        f"Generate a gentle meal logging reminder for {client.full_name.split()[0]}. "
        f"They've logged {meals_today} meal(s) today with {protein_so_far}g protein so far "
        f"(target: {target}g). Mention the protein gap without being naggy."
    )
    message = await _llm_nudge(prompt)
    nudge = Nudge(
        client_id=client.id,
        nudge_type=NudgeType.MEAL_REMINDER,
        message=message,
        scheduled_at=datetime.now(timezone.utc),
    )
    db.add(nudge)
    await db.flush()
    return nudge


async def generate_training_prompt(db: AsyncSession, client: Client) -> Nudge | None:
    if await _already_sent_today(db, client.id, NudgeType.TRAINING_PROMPT):
        return None

    # Check if any wearable data (Zone 2) in last 2 days
    two_days_ago = date.today() - timedelta(days=2)
    result = await db.execute(
        select(WearableData).where(
            WearableData.client_id == client.id,
            WearableData.data_date >= two_days_ago,
            WearableData.zone2_minutes > 0,
        )
    )
    recent_training = result.scalars().first()

    if recent_training:
        return None  # Already trained recently

    # Check recovery score — don't nudge if low recovery
    latest_wearable = await db.execute(
        select(WearableData)
        .where(WearableData.client_id == client.id)
        .order_by(WearableData.data_date.desc())
        .limit(1)
    )
    wearable = latest_wearable.scalars().first()
    if wearable and wearable.recovery_score and wearable.recovery_score < 40:
        return None  # Low recovery — don't push training

    recovery_text = f"Recovery score: {wearable.recovery_score}" if wearable and wearable.recovery_score else "No recovery data"

    prompt = (
        f"Generate a training nudge for {client.full_name.split()[0]}. "
        f"They haven't logged any Zone 2 training in 2+ days. {recovery_text}. "
        "Suggest getting a session in without being pushy."
    )
    message = await _llm_nudge(prompt)
    nudge = Nudge(
        client_id=client.id,
        nudge_type=NudgeType.TRAINING_PROMPT,
        message=message,
        scheduled_at=datetime.now(timezone.utc),
    )
    db.add(nudge)
    await db.flush()
    return nudge


async def generate_biomarker_due_nudge(db: AsyncSession, client: Client) -> Nudge | None:
    """Flag if no blood work in 90+ days."""
    if await _already_sent_today(db, client.id, NudgeType.BIOMARKER_DUE):
        return None

    ninety_days_ago = date.today() - timedelta(days=90)
    result = await db.execute(
        select(LabResult).where(
            LabResult.client_id == client.id,
            LabResult.test_date >= ninety_days_ago,
        ).limit(1)
    )
    recent_labs = result.scalars().first()

    if recent_labs:
        return None

    # Find most recent test date
    latest = await db.execute(
        select(LabResult.test_date)
        .where(LabResult.client_id == client.id)
        .order_by(LabResult.test_date.desc())
        .limit(1)
    )
    last_date = latest.scalar()
    days_ago = (date.today() - last_date).days if last_date else None
    days_text = f"{days_ago} days ago" if days_ago else "a while ago"

    message = await _llm_nudge(
        f"Remind {client.full_name.split()[0]} that their last blood panel was {days_text}. "
        "Suggest scheduling a new one. Keep it brief."
    )
    nudge = Nudge(
        client_id=client.id,
        nudge_type=NudgeType.BIOMARKER_DUE,
        message=message,
        scheduled_at=datetime.now(timezone.utc),
    )
    db.add(nudge)
    await db.flush()
    return nudge


async def generate_weekly_summary(db: AsyncSession, client: Client) -> Nudge | None:
    """Sunday evening weekly summary nudge."""
    if datetime.now(timezone.utc).weekday() != 6:  # Sunday = 6
        return None

    # Check not already sent this week
    week_start = datetime.now(timezone.utc) - timedelta(days=7)
    result = await db.execute(
        select(Nudge).where(
            Nudge.client_id == client.id,
            Nudge.nudge_type == NudgeType.WEEKLY_SUMMARY,
            Nudge.scheduled_at >= week_start,
        )
    )
    if result.scalars().first():
        return None

    # Gather week's stats
    today = date.today()
    week_ago = today - timedelta(days=7)

    nutrition = await db.execute(
        select(
            func.avg(NutritionLog.protein_g),
            func.avg(NutritionLog.fibre_g),
            func.count(NutritionLog.id),
        ).where(
            NutritionLog.client_id == client.id,
            NutritionLog.log_date >= week_ago,
        )
    )
    avg_protein, avg_fibre, meal_count = nutrition.first()

    wearables = await db.execute(
        select(func.sum(WearableData.zone2_minutes), func.avg(WearableData.hrv_ms))
        .where(
            WearableData.client_id == client.id,
            WearableData.data_date >= week_ago,
        )
    )
    total_zone2, avg_hrv = wearables.first()

    summary_data = (
        f"Meals logged: {meal_count or 0}, "
        f"Avg protein: {round(avg_protein or 0)}g (target: {client.daily_protein_target_g or 150}g), "
        f"Avg fibre: {round(avg_fibre or 0)}g, "
        f"Zone 2 total: {round(total_zone2 or 0)} min, "
        f"Avg HRV: {round(avg_hrv or 0)}ms"
    )

    message = await _llm_nudge(
        f"Generate a brief Sunday weekly summary for {client.full_name.split()[0]}. "
        f"Week stats: {summary_data}. Highlight 1 win and 1 thing to focus on next week."
    )
    nudge = Nudge(
        client_id=client.id,
        nudge_type=NudgeType.WEEKLY_SUMMARY,
        message=message,
        scheduled_at=datetime.now(timezone.utc),
    )
    db.add(nudge)
    await db.flush()
    return nudge


async def generate_risk_flag(db: AsyncSession, client: Client) -> Nudge | None:
    """Flag if any risk domain is RED and user hasn't been notified recently."""
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    already = await db.execute(
        select(Nudge).where(
            Nudge.client_id == client.id,
            Nudge.nudge_type == NudgeType.RISK_FLAG,
            Nudge.scheduled_at >= seven_days_ago,
        )
    )
    if already.scalars().first():
        return None

    from app.models.risk_score import RAGStatus
    red_scores = await db.execute(
        select(RiskScore).where(
            RiskScore.client_id == client.id,
            RiskScore.rag_status == RAGStatus.RED,
        )
    )
    red_domains = red_scores.scalars().all()
    if not red_domains:
        return None

    domain_names = ", ".join(d.domain.value for d in red_domains)
    message = await _llm_nudge(
        f"Alert {client.full_name.split()[0]} that their {domain_names} risk assessment is showing red. "
        "Recommend speaking with their health coach or doctor. Be calm, not alarming."
    )
    nudge = Nudge(
        client_id=client.id,
        nudge_type=NudgeType.RISK_FLAG,
        message=message,
        scheduled_at=datetime.now(timezone.utc),
    )
    db.add(nudge)
    await db.flush()
    return nudge
