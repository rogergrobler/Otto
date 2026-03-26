"""
Coach Service — generates AI pre-consultation summaries for health professionals.
"""
import logging
from datetime import date, timedelta

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.client import Client
from app.models.goal import Goal, GoalStatus
from app.models.lab_result import LabResult
from app.models.nudge import Nudge
from app.models.nutrition_log import NutritionLog
from app.models.risk_score import RiskScore
from app.models.wearable_data import WearableData

logger = logging.getLogger(__name__)

PRE_CONSULT_PROMPT = """You are preparing a pre-consultation briefing for a health coach or doctor
who is about to meet with their patient. Summarise the patient's current health status concisely
and flag the most important items for discussion.

Structure your response as follows:
## Health Snapshot
<2-3 sentences on overall status>

## Key Metrics This Period
<bullet list of most important recent data points>

## Progress on Goals
<brief status on each active goal>

## Flags for Discussion
<numbered list of the 3-5 most important items the coach should address>

## Suggested Talking Points
<2-3 evidence-based recommendations based on the data>

Keep it factual, clinical, and concise. This is for a professional, not the patient."""


async def generate_preconsultation_summary(db: AsyncSession, client: Client) -> str:
    """Generate an AI pre-consultation summary for this client's health coach."""
    thirty_days_ago = date.today() - timedelta(days=30)

    # Recent labs
    labs_result = await db.execute(
        select(LabResult)
        .where(LabResult.client_id == client.id, LabResult.test_date >= thirty_days_ago)
        .order_by(LabResult.test_date.desc())
        .limit(50)
    )
    labs = labs_result.scalars().all()

    # Active goals
    goals_result = await db.execute(
        select(Goal).where(Goal.client_id == client.id, Goal.status == GoalStatus.ACTIVE)
    )
    goals = goals_result.scalars().all()

    # Risk scores
    risk_result = await db.execute(
        select(RiskScore).where(RiskScore.client_id == client.id)
    )
    risk_scores = risk_result.scalars().all()

    # Recent nutrition (last 7 days avg)
    nutrition_result = await db.execute(
        select(NutritionLog).where(
            NutritionLog.client_id == client.id,
            NutritionLog.log_date >= date.today() - timedelta(days=7),
        )
    )
    nutrition = nutrition_result.scalars().all()

    # Recent wearable (last 7 days)
    wearable_result = await db.execute(
        select(WearableData).where(
            WearableData.client_id == client.id,
            WearableData.data_date >= date.today() - timedelta(days=7),
        ).order_by(WearableData.data_date.desc())
    )
    wearables = wearable_result.scalars().all()

    # Build context
    from datetime import datetime
    age = (date.today() - client.date_of_birth).days // 365 if client.date_of_birth else "unknown"

    context_parts = [
        f"Patient: {client.full_name}, Age: {age}, Sex: {client.sex.value if client.sex else 'unknown'}",
        f"Weight: {client.weight_kg}kg" if client.weight_kg else "",
    ]

    if risk_scores:
        context_parts.append("\nRisk Domain Scores:")
        for rs in risk_scores:
            context_parts.append(
                f"- {rs.domain.value.title()}: {rs.rag_status.value.upper()} "
                f"(score: {rs.score}) — {rs.interpretation or 'No interpretation available'}"
            )

    if labs:
        context_parts.append("\nRecent Lab Results:")
        for lab in labs[:20]:
            val = f"{lab.value} {lab.unit or ''}".strip() if lab.value else lab.value_text or "N/A"
            flag = f" [{lab.flag.value.upper()}]" if lab.flag else ""
            context_parts.append(f"- {lab.marker_name}: {val}{flag} ({lab.test_date})")

    if goals:
        context_parts.append("\nActive Goals:")
        for g in goals:
            context_parts.append(
                f"- [{g.domain.value}] {g.goal_text} | "
                f"Current: {g.current_value or 'not set'} → Target: {g.target_value or 'not set'} "
                f"(deadline: {g.deadline or 'none'})"
            )

    if nutrition:
        avg_protein = round(sum(n.protein_g or 0 for n in nutrition) / len(nutrition), 0)
        avg_fibre = round(sum(n.fibre_g or 0 for n in nutrition) / len(nutrition), 0)
        context_parts.append(
            f"\nNutrition (7-day avg): Protein {avg_protein}g/day, Fibre {avg_fibre}g/day"
        )

    if wearables:
        avg_hrv = round(sum(w.hrv_ms or 0 for w in wearables if w.hrv_ms) / max(len([w for w in wearables if w.hrv_ms]), 1), 0)
        avg_sleep = round(sum(w.sleep_hours or 0 for w in wearables if w.sleep_hours) / max(len([w for w in wearables if w.sleep_hours]), 1), 1)
        context_parts.append(f"Wearables (7-day avg): HRV {avg_hrv}ms, Sleep {avg_sleep}h")

    context = "\n".join(p for p in context_parts if p)

    anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = await anthropic_client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1500,
        system=PRE_CONSULT_PROMPT,
        messages=[{"role": "user", "content": f"Generate pre-consultation summary for:\n\n{context}"}],
        temperature=0.2,
    )
    return response.content[0].text.strip()
