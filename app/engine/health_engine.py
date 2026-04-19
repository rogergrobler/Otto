"""
Otto health engine — processes user messages using Claude tool use.

Tools give Claude real-time access to the user's health repository so every
response is grounded in actual data, not generic advice.
"""
import json
import logging
from datetime import date, datetime, timedelta, timezone

import anthropic
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.engine.memory_manager import summarize_conversation, update_client_memory
from app.llm.prompts import OTTO_DEFAULT_SOUL, build_system_prompt
from app.models.client import Client
from app.models.conversation import Channel, Conversation
from app.models.goal import Goal, GoalStatus
from app.models.lab_result import LabResult
from app.models.message import Message, MessageRole
from app.models.nutrition_log import NutritionLog
from app.models.risk_score import RiskScore
from app.models.training_note import TrainingNote
from app.models.wearable_data import WearableData

logger = logging.getLogger(__name__)

# ── Tool definitions ──────────────────────────────────────────────────────────

HEALTH_TOOLS = [
    {
        "name": "query_labs",
        "description": (
            "Query the user's lab results. Returns recent biomarker values with dates, units, "
            "reference ranges, and flags. Use this when the user asks about blood work, biomarkers, "
            "test results, or any specific marker like ApoB, HbA1c, cholesterol, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "marker_name": {
                    "type": "string",
                    "description": "Filter by marker name (partial match). Leave empty to get all recent results.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results to return. Default 20.",
                    "default": 20,
                },
            },
            "required": [],
        },
    },
    {
        "name": "query_nutrition",
        "description": (
            "Query the user's nutrition log. Returns meals logged and daily totals for protein, "
            "fibre, calories, fat, carbs, and omega-3. Use when the user asks about food, meals, "
            "nutrition, macros, protein intake, fibre, or daily targets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today.",
                },
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (max 14). Default 1 (today only).",
                    "default": 1,
                },
            },
            "required": [],
        },
    },
    {
        "name": "query_goals",
        "description": (
            "Query the user's active health goals. Returns goals with domain, target metric, "
            "current and target values, deadlines, and status. Use when the user asks about "
            "their goals, progress, targets, or what they are working on."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": (
                        "Filter by domain: cardiovascular, metabolic, neurological, "
                        "cancer_prevention, nutrition, training, body_composition, "
                        "sleep, supplements, general"
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "log_meal",
        "description": (
            "Log a meal entry for the user. Use this when the user tells you what they ate "
            "and you have estimated or been given the nutritional breakdown. Always confirm "
            "with the user before calling this tool."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "Description of the meal"},
                "meal_type": {
                    "type": "string",
                    "enum": ["breakfast", "lunch", "dinner", "snack", "other"],
                },
                "calories": {"type": "integer"},
                "protein_g": {"type": "number"},
                "fat_g": {"type": "number"},
                "carbs_net_g": {"type": "number"},
                "fibre_g": {"type": "number"},
                "omega3_g": {"type": "number"},
                "log_date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format. Defaults to today.",
                },
            },
            "required": ["description", "meal_type"],
        },
    },
    {
        "name": "query_risk",
        "description": (
            "Query the user's current risk scores across the Four Horsemen domains "
            "(cardiovascular, metabolic, neurological, cancer). Returns RAG status, "
            "score, interpretation, contributing factors, and data gaps. Use when the "
            "user asks about their health risk, overall health score, or any disease domain."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": (
                        "Filter to a specific domain: cardiovascular, metabolic, "
                        "neurological, cancer. Leave empty to get all domains."
                    ),
                },
            },
            "required": [],
        },
    },
    {
        "name": "query_wearables",
        "description": (
            "Query the user's wearable data: sleep, HRV, resting heart rate, recovery score, "
            "readiness, Zone 2 minutes, steps, VO2 max, and strain. Use when the user asks "
            "about their sleep, recovery, training load, or wearable metrics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days to look back (max 30). Default 7.",
                    "default": 7,
                },
            },
            "required": [],
        },
    },
    {
        "name": "update_goal",
        "description": (
            "Update the current_value or status of an existing goal. Use this to record progress "
            "when the user reports an updated measurement or wants to mark a goal complete."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "goal_id": {"type": "string", "description": "UUID of the goal to update"},
                "current_value": {"type": "string", "description": "Updated current value"},
                "status": {
                    "type": "string",
                    "enum": ["active", "completed", "paused", "abandoned"],
                },
                "notes": {"type": "string"},
            },
            "required": ["goal_id"],
        },
    },
]


# ── Tool executors ────────────────────────────────────────────────────────────

async def _execute_query_labs(db: AsyncSession, client_id, inputs: dict) -> dict:
    marker_name = inputs.get("marker_name", "")
    limit = inputs.get("limit", 20)

    query = select(LabResult).where(LabResult.client_id == client_id)
    if marker_name:
        query = query.where(LabResult.marker_name.ilike(f"%{marker_name}%"))
    query = query.order_by(LabResult.test_date.desc()).limit(limit)

    result = await db.execute(query)
    rows = result.scalars().all()

    if not rows:
        return {"results": [], "message": "No lab results found."}

    return {
        "results": [
            {
                "marker_name": r.marker_name,
                "value": r.value,
                "value_text": r.value_text,
                "unit": r.unit,
                "flag": r.flag.value if r.flag else None,
                "ref_range": f"{r.ref_range_low}–{r.ref_range_high}"
                if r.ref_range_low and r.ref_range_high
                else None,
                "test_date": str(r.test_date),
                "lab_name": r.lab_name,
                "notes": r.notes,
            }
            for r in rows
        ]
    }


async def _execute_query_nutrition(db: AsyncSession, client_id, client: Client, inputs: dict) -> dict:
    date_str = inputs.get("date")
    days = min(inputs.get("days", 1), 14)

    if date_str:
        try:
            end_date = date.fromisoformat(date_str)
        except ValueError:
            end_date = date.today()
    else:
        end_date = date.today()

    start_date = end_date - timedelta(days=days - 1)

    result = await db.execute(
        select(NutritionLog)
        .where(
            NutritionLog.client_id == client_id,
            NutritionLog.log_date >= start_date,
            NutritionLog.log_date <= end_date,
        )
        .order_by(NutritionLog.log_date.desc(), NutritionLog.created_at)
    )
    logs = result.scalars().all()

    # Group by date
    by_date: dict[str, list] = {}
    for log in logs:
        d = str(log.log_date)
        by_date.setdefault(d, [])
        by_date[d].append({
            "meal_type": log.meal_type.value,
            "description": log.description,
            "calories": log.calories,
            "protein_g": log.protein_g,
            "fat_g": log.fat_g,
            "carbs_net_g": log.carbs_net_g,
            "fibre_g": log.fibre_g,
            "omega3_g": log.omega3_g,
        })

    # Compute daily totals
    totals_by_date = {}
    for d, meals in by_date.items():
        totals_by_date[d] = {
            "calories": sum(m["calories"] or 0 for m in meals),
            "protein_g": round(sum(m["protein_g"] or 0 for m in meals), 1),
            "fibre_g": round(sum(m["fibre_g"] or 0 for m in meals), 1),
            "fat_g": round(sum(m["fat_g"] or 0 for m in meals), 1),
            "omega3_g": round(sum(m["omega3_g"] or 0 for m in meals), 2),
            "meals_count": len(meals),
        }

    return {
        "period": f"{start_date} to {end_date}",
        "targets": {
            "protein_g": client.daily_protein_target_g,
            "fibre_g": client.daily_fibre_target_g,
            "calories": client.daily_calories_target,
        },
        "by_date": {d: {"meals": by_date[d], "totals": totals_by_date[d]} for d in sorted(by_date.keys(), reverse=True)},
        "message": f"{len(logs)} meal entries found." if logs else "No nutrition logged for this period.",
    }


async def _execute_query_goals(db: AsyncSession, client_id, inputs: dict) -> dict:
    domain = inputs.get("domain")
    query = select(Goal).where(
        Goal.client_id == client_id,
        Goal.status == GoalStatus.ACTIVE,
    )
    if domain:
        query = query.where(Goal.domain == domain)

    result = await db.execute(query)
    goals = result.scalars().all()

    if not goals:
        return {"goals": [], "message": "No active goals found."}

    return {
        "goals": [
            {
                "id": str(g.id),
                "domain": g.domain.value,
                "goal_text": g.goal_text,
                "target_metric": g.target_metric,
                "current_value": g.current_value,
                "target_value": g.target_value,
                "deadline": str(g.deadline) if g.deadline else None,
                "status": g.status.value,
                "interventions": g.interventions,
            }
            for g in goals
        ]
    }


async def _execute_log_meal(db: AsyncSession, client_id, inputs: dict) -> dict:
    from app.models.nutrition_log import MealType, NutritionLog

    date_str = inputs.get("log_date")
    try:
        log_date = date.fromisoformat(date_str) if date_str else date.today()
    except ValueError:
        log_date = date.today()

    meal_type_str = inputs.get("meal_type", "other")
    try:
        meal_type = MealType(meal_type_str)
    except ValueError:
        meal_type = MealType.OTHER

    description = inputs.get("description")

    # Dedup: if an identical meal (same client, date, description) was logged in the
    # last 2 minutes, return the existing entry rather than creating a duplicate.
    # This prevents double-logging when Claude calls the tool during both the
    # estimate pass and the confirmation pass.
    if description:
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=2)
        existing = await db.execute(
            select(NutritionLog).where(
                NutritionLog.client_id == client_id,
                NutritionLog.log_date == log_date,
                NutritionLog.description == description,
                NutritionLog.created_at >= cutoff,
            )
        )
        dupe = existing.scalars().first()
        if dupe:
            return {"success": True, "log_id": str(dupe.id), "message": f"Meal already logged for {log_date} (duplicate prevented)."}

    log = NutritionLog(
        client_id=client_id,
        log_date=log_date,
        meal_type=meal_type,
        description=description,
        calories=inputs.get("calories"),
        protein_g=inputs.get("protein_g"),
        fat_g=inputs.get("fat_g"),
        carbs_net_g=inputs.get("carbs_net_g"),
        fibre_g=inputs.get("fibre_g"),
        omega3_g=inputs.get("omega3_g"),
        ai_analysed=True,
    )
    db.add(log)
    await db.flush()

    return {"success": True, "log_id": str(log.id), "message": f"Meal logged for {log_date}."}


async def _execute_query_risk(db: AsyncSession, client_id, inputs: dict) -> dict:
    domain = inputs.get("domain")
    query = select(RiskScore).where(RiskScore.client_id == client_id)
    if domain:
        query = query.where(RiskScore.domain == domain)

    result = await db.execute(query)
    scores = result.scalars().all()

    if not scores:
        return {"scores": [], "message": "No risk scores calculated yet. Use /health/risk/calculate to generate them."}

    from app.services.risk_engine import calculate_health_score
    return {
        "health_score": calculate_health_score(scores),
        "scores": [
            {
                "domain": s.domain.value,
                "score": s.score,
                "rag_status": s.rag_status.value,
                "interpretation": s.interpretation,
                "contributing_factors": s.contributing_factors,
                "data_gaps": s.data_gaps,
                "last_calculated": str(s.last_calculated) if s.last_calculated else None,
            }
            for s in scores
        ],
    }


async def _execute_query_wearables(db: AsyncSession, client_id, inputs: dict) -> dict:
    days = min(inputs.get("days", 7), 30)
    cutoff = date.today() - timedelta(days=days - 1)

    result = await db.execute(
        select(WearableData)
        .where(WearableData.client_id == client_id, WearableData.data_date >= cutoff)
        .order_by(WearableData.data_date.desc())
    )
    rows = result.scalars().all()

    if not rows:
        return {"records": [], "message": f"No wearable data found in the last {days} days."}

    return {
        "records": [
            {
                "date": str(r.data_date),
                "source": r.source.value,
                "sleep_hours": r.sleep_hours,
                "sleep_efficiency": r.sleep_efficiency,
                "hrv_ms": r.hrv_ms,
                "resting_hr": r.resting_hr,
                "recovery_score": r.recovery_score,
                "readiness_score": r.readiness_score,
                "strain_score": r.strain_score,
                "steps": r.steps,
                "zone2_minutes": r.zone2_minutes,
                "vo2_max": r.vo2_max,
            }
            for r in rows
        ]
    }


async def _execute_update_goal(db: AsyncSession, inputs: dict) -> dict:
    import uuid as _uuid

    goal_id = inputs.get("goal_id")
    try:
        goal_uuid = _uuid.UUID(goal_id)
    except (ValueError, TypeError):
        return {"success": False, "message": "Invalid goal ID."}

    result = await db.execute(select(Goal).where(Goal.id == goal_uuid))
    goal = result.scalars().first()
    if not goal:
        return {"success": False, "message": "Goal not found."}

    if "current_value" in inputs:
        goal.current_value = inputs["current_value"]
    if "status" in inputs:
        from app.models.goal import GoalStatus
        try:
            goal.status = GoalStatus(inputs["status"])
        except ValueError:
            pass
    if "notes" in inputs and inputs["notes"]:
        goal.notes = (goal.notes or "") + f"\n{inputs['notes']}"

    await db.flush()
    return {"success": True, "message": "Goal updated."}


async def execute_tool(
    db: AsyncSession, client: Client, tool_name: str, tool_input: dict
) -> dict:
    """Dispatch a tool call to the appropriate executor."""
    client_id = client.id
    try:
        if tool_name == "query_labs":
            return await _execute_query_labs(db, client_id, tool_input)
        elif tool_name == "query_nutrition":
            return await _execute_query_nutrition(db, client_id, client, tool_input)
        elif tool_name == "query_goals":
            return await _execute_query_goals(db, client_id, tool_input)
        elif tool_name == "log_meal":
            return await _execute_log_meal(db, client_id, tool_input)
        elif tool_name == "query_risk":
            return await _execute_query_risk(db, client_id, tool_input)
        elif tool_name == "query_wearables":
            return await _execute_query_wearables(db, client_id, tool_input)
        elif tool_name == "update_goal":
            return await _execute_update_goal(db, tool_input)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    except Exception as e:
        logger.error(f"Tool execution error [{tool_name}]: {e}")
        return {"error": str(e)}


# ── Context helpers ───────────────────────────────────────────────────────────

def _build_client_profile(client: Client) -> str:
    parts = [f"Name: {client.full_name}"]
    if client.date_of_birth:
        age = (date.today() - client.date_of_birth).days // 365
        parts.append(f"Age: {age}")
    if client.sex:
        parts.append(f"Sex: {client.sex.value}")
    if client.height_cm:
        parts.append(f"Height: {client.height_cm} cm")
    if client.weight_kg:
        parts.append(f"Weight: {client.weight_kg} kg")
    if client.daily_protein_target_g:
        parts.append(f"Daily protein target: {client.daily_protein_target_g}g")
    if client.daily_fibre_target_g:
        parts.append(f"Daily fibre target: {client.daily_fibre_target_g}g")
    if client.daily_calories_target:
        parts.append(f"Daily calorie target: {client.daily_calories_target} kcal")
    if client.notes:
        parts.append(f"Coach notes: {client.notes}")
    return "\n".join(parts)


async def _get_training_notes(db: AsyncSession) -> list[str]:
    result = await db.execute(select(TrainingNote).order_by(TrainingNote.created_at.desc()))
    return [note.guidance for note in result.scalars().all()]


async def _get_recent_messages(db: AsyncSession, conversation: Conversation, limit: int = 20) -> list[dict]:
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


# ── Conversation management ───────────────────────────────────────────────────

async def get_or_create_conversation(
    db: AsyncSession, client: Client, channel: Channel
) -> Conversation:
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

    # Close and summarize old open conversations
    old = await db.execute(
        select(Conversation).where(
            Conversation.client_id == client.id,
            Conversation.ended_at.is_(None),
        )
    )
    for old_conv in old.scalars().all():
        old_conv.ended_at = datetime.now(timezone.utc)
        try:
            summary = await summarize_conversation(db, old_conv)
            old_conv.summary = summary
            await update_client_memory(db, client, summary)
        except Exception:
            pass

    conversation = Conversation(client_id=client.id, channel=channel)
    db.add(conversation)
    await db.flush()
    return conversation


# ── Main message processor ────────────────────────────────────────────────────

async def process_health_message(
    db: AsyncSession,
    client: Client,
    text: str,
    channel: Channel,
    image_bytes: bytes | None = None,
    image_media_type: str = "image/jpeg",
) -> str:
    """
    Process a user message through Otto's health engine.

    Uses Claude tool use to query the health repository in real time.
    Supports optional image input (meal photos, lab report images).
    """
    conversation = await get_or_create_conversation(db, client, channel)

    # Store user message
    user_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.CLIENT,
        content=text,
    )
    db.add(user_msg)
    await db.flush()

    # Build system prompt
    training_notes = await _get_training_notes(db)
    client_profile = _build_client_profile(client)
    system = build_system_prompt(
        soul_doc=OTTO_DEFAULT_SOUL,
        training_notes=training_notes,
        client_profile=client_profile,
        memory_summary=client.memory_summary,
        health_context=f"Today's date: {date.today().isoformat()}",
    )

    # Build message history
    messages = await _get_recent_messages(db, conversation, limit=18)

    # Build current user message content
    if image_bytes:
        import base64
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        current_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_media_type,
                    "data": image_b64,
                },
            },
            {"type": "text", "text": text or "What did I eat? Please analyse this meal."},
        ]
    else:
        current_content = text

    messages.append({"role": "user", "content": current_content})

    # Tool use loop
    anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    final_response = ""
    max_iterations = 5

    for _ in range(max_iterations):
        response = await anthropic_client.messages.create(
            model=settings.LLM_MODEL,
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=HEALTH_TOOLS,
        )

        if response.stop_reason == "tool_use":
            # Execute all tool calls and collect results
            tool_results = []
            assistant_content = []

            for block in response.content:
                if block.type == "tool_use":
                    logger.info(f"Tool call: {block.name}({json.dumps(block.input)[:200]})")
                    result = await execute_tool(db, client, block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(result),
                    })
                    assistant_content.append({
                        "type": "tool_use",
                        "id": block.id,
                        "name": block.name,
                        "input": block.input,
                    })
                elif block.type == "text" and block.text:
                    assistant_content.append({"type": "text", "text": block.text})

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

        else:
            # Final text response
            for block in response.content:
                if hasattr(block, "text"):
                    final_response = block.text
                    break
            break

    if not final_response:
        final_response = "I'm sorry, I wasn't able to process that. Please try again."

    # Store Otto's response
    otto_msg = Message(
        conversation_id=conversation.id,
        role=MessageRole.OTTO,
        content=final_response,
    )
    db.add(otto_msg)
    await db.flush()

    return final_response
