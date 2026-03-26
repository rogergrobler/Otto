"""
Otto Risk Assessment Engine.

Calculates Four Horsemen domain risk scores using Claude, grounded in the
user's actual lab results, wearable data, and health profile.

Each domain produces:
  - score: 0–100 (higher = better health / lower risk)
  - rag_status: green / amber / red / insufficient_data
  - interpretation: 2–3 sentence plain-language summary
  - contributing_factors: top 3 factors driving the score
  - data_gaps: key missing data that would improve the assessment
"""
import json
import logging
from datetime import date, timedelta

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.client import Client
from app.models.lab_result import LabResult
from app.models.risk_score import RAGStatus, RiskDomain, RiskScore
from app.models.wearable_data import WearableData

logger = logging.getLogger(__name__)

# ── Domain prompts ────────────────────────────────────────────────────────────

RISK_SYSTEM = """You are a longevity medicine expert assessing patient risk across the Four Horsemen
of chronic disease (cardiovascular, metabolic, neurodegeneration, cancer). You have access to the
patient's lab results and health data. Provide evidence-based, personalised risk assessments.

Always return valid JSON only — no markdown, no preamble."""

DOMAIN_PROMPTS = {
    RiskDomain.CARDIOVASCULAR: """
Assess this patient's cardiovascular (ASCVD) risk based on the provided data.

Key markers to consider: ApoB, LDL cholesterol, Lp(a), homocysteine, hsCRP, triglycerides,
HDL, blood pressure, CAC score, family history, age, sex, smoking status.

Patient profile:
{profile}

Available lab results (most recent per marker):
{labs}

Return JSON:
{{
  "score": <integer 0-100, higher=better/lower risk>,
  "rag_status": <"green"|"amber"|"red"|"insufficient_data">,
  "interpretation": "<2-3 sentence plain-language summary of cardiovascular risk and key drivers>",
  "contributing_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
  "data_gaps": ["<missing test or data that would improve assessment>"]
}}

RAG guidance: Green = all key markers optimal, low risk. Amber = 1-2 markers borderline or suboptimal. Red = elevated ApoB/Lp(a), high hsCRP, or other significant risk factor present.
""",

    RiskDomain.METABOLIC: """
Assess this patient's metabolic disease risk based on the provided data.

Key markers: HbA1c, fasting glucose, fasting insulin, HOMA-IR, triglycerides, HDL,
uric acid, ALT/AST (liver), body weight, waist circumference, body fat %.

Patient profile:
{profile}

Available lab results (most recent per marker):
{labs}

Wearable/body data:
{wearables}

Return JSON:
{{
  "score": <integer 0-100, higher=better/lower risk>,
  "rag_status": <"green"|"amber"|"red"|"insufficient_data">,
  "interpretation": "<2-3 sentence plain-language summary of metabolic health and insulin resistance status>",
  "contributing_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
  "data_gaps": ["<missing test or data that would improve assessment>"]
}}

RAG guidance: Green = HbA1c <5.4%, fasting insulin <8, optimal lipids. Amber = HbA1c 5.4-5.7%, early insulin resistance signs. Red = HbA1c ≥5.7%, HOMA-IR >2.5, or significant metabolic dysfunction.
""",

    RiskDomain.NEUROLOGICAL: """
Assess this patient's neurodegeneration risk based on the provided data.

Key factors: VO₂ max (most important modifiable factor), sleep quality and duration, HRV trend,
omega-3 status (EPA+DHA), APOE genotype if known, homocysteine, hsCRP, strength training frequency,
cognitive symptoms.

Patient profile:
{profile}

Available lab results (most recent per marker):
{labs}

Wearable/sleep data (last 14 days average):
{wearables}

Return JSON:
{{
  "score": <integer 0-100, higher=better/lower risk>,
  "rag_status": <"green"|"amber"|"red"|"insufficient_data">,
  "interpretation": "<2-3 sentence plain-language summary of neurological health and key protective/risk factors>",
  "contributing_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
  "data_gaps": ["<missing test or data that would improve assessment>"]
}}

RAG guidance: Green = VO₂ max age-appropriate or above, good sleep, omega-3 adequate. Amber = some lifestyle gaps or borderline markers. Red = very low VO₂ max, chronic poor sleep, APOE ε4, or elevated homocysteine.
""",

    RiskDomain.CANCER: """
Assess this patient's cancer screening adherence and modifiable risk factors.

Key factors: screening compliance (colonoscopy, PSA for males, skin checks, mammogram for females),
inflammatory markers (hsCRP, ferritin), family history, smoking, alcohol consumption, BMI,
relevant genetic variants.

Patient profile:
{profile}

Available lab results (most recent per marker):
{labs}

Return JSON:
{{
  "score": <integer 0-100, higher=better/lower risk>,
  "rag_status": <"green"|"amber"|"red"|"insufficient_data">,
  "interpretation": "<2-3 sentence plain-language summary of cancer screening status and key modifiable risk factors>",
  "contributing_factors": ["<factor 1>", "<factor 2>", "<factor 3>"],
  "data_gaps": ["<missing screening or data that would improve assessment>"]
}}

RAG guidance: Green = all age-appropriate screenings current, low inflammation, no major risk factors. Amber = some screenings overdue or borderline risk factors. Red = screenings significantly overdue, elevated CRP/ferritin, or known high-risk factors.
""",
}


# ── Data formatters ───────────────────────────────────────────────────────────

def _format_profile(client: Client) -> str:
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
        bmi = client.weight_kg / ((client.height_cm / 100) ** 2) if client.height_cm else None
        if bmi:
            parts.append(f"BMI: {bmi:.1f}")
    return "\n".join(parts)


def _format_labs(labs: list[LabResult]) -> str:
    if not labs:
        return "No lab results available."
    # Deduplicate — keep most recent per marker
    seen: dict[str, LabResult] = {}
    for lab in sorted(labs, key=lambda l: l.test_date, reverse=True):
        key = lab.marker_name.lower().strip()
        if key not in seen:
            seen[key] = lab
    lines = []
    for lab in sorted(seen.values(), key=lambda l: l.marker_name):
        val = f"{lab.value} {lab.unit or ''}".strip() if lab.value is not None else lab.value_text or "N/A"
        ref = f" (ref: {lab.ref_range_low}–{lab.ref_range_high})" if lab.ref_range_low and lab.ref_range_high else ""
        flag = f" [{lab.flag.value.upper()}]" if lab.flag else ""
        lines.append(f"- {lab.marker_name}: {val}{ref}{flag} ({lab.test_date})")
    return "\n".join(lines)


def _format_wearables(records: list[WearableData]) -> str:
    if not records:
        return "No wearable data available."
    recent = records[:14]
    avg = lambda attr: round(
        sum(getattr(r, attr) for r in recent if getattr(r, attr) is not None) /
        max(len([r for r in recent if getattr(r, attr) is not None]), 1), 1
    )
    lines = [
        f"- Sleep (avg): {avg('sleep_hours')} hrs, {avg('sleep_efficiency')}% efficiency",
        f"- HRV (avg): {avg('hrv_ms')} ms",
        f"- Resting HR (avg): {avg('resting_hr')} bpm",
        f"- Recovery score (avg): {avg('recovery_score')}",
        f"- Zone 2 minutes (avg/day): {avg('zone2_minutes')}",
    ]
    vo2_vals = [r.vo2_max for r in recent if r.vo2_max]
    if vo2_vals:
        lines.append(f"- VO₂ max: {max(vo2_vals):.1f} ml/kg/min")
    weight_vals = [r.weight_kg for r in recent if r.weight_kg]
    if weight_vals:
        lines.append(f"- Weight (latest): {weight_vals[0]} kg")
    return "\n".join(lines)


# ── Core calculator ───────────────────────────────────────────────────────────

async def calculate_domain_risk(
    db: AsyncSession,
    client: Client,
    domain: RiskDomain,
) -> RiskScore:
    """Calculate risk score for a single domain and upsert to database."""
    # Fetch data
    labs_result = await db.execute(
        select(LabResult)
        .where(LabResult.client_id == client.id)
        .order_by(LabResult.test_date.desc())
        .limit(200)
    )
    labs = labs_result.scalars().all()

    wearables_result = await db.execute(
        select(WearableData)
        .where(WearableData.client_id == client.id)
        .order_by(WearableData.data_date.desc())
        .limit(30)
    )
    wearables = wearables_result.scalars().all()

    profile_text = _format_profile(client)
    labs_text = _format_labs(labs)
    wearables_text = _format_wearables(wearables)

    prompt = DOMAIN_PROMPTS[domain].format(
        profile=profile_text,
        labs=labs_text,
        wearables=wearables_text,
    )

    anthropic_client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    response = await anthropic_client.messages.create(
        model=settings.LLM_MODEL,
        max_tokens=1024,
        system=RISK_SYSTEM,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    data = json.loads(raw)

    try:
        rag = RAGStatus(data.get("rag_status", "insufficient_data"))
    except ValueError:
        rag = RAGStatus.INSUFFICIENT_DATA

    # Upsert — replace existing score for this domain
    existing = await db.execute(
        select(RiskScore).where(
            RiskScore.client_id == client.id,
            RiskScore.domain == domain,
        )
    )
    risk_score = existing.scalars().first()

    if risk_score:
        risk_score.score = data.get("score")
        risk_score.rag_status = rag
        risk_score.interpretation = data.get("interpretation")
        risk_score.contributing_factors = data.get("contributing_factors", [])
        risk_score.data_gaps = data.get("data_gaps", [])
        from datetime import datetime, timezone
        risk_score.last_calculated = datetime.now(timezone.utc)
    else:
        risk_score = RiskScore(
            client_id=client.id,
            domain=domain,
            score=data.get("score"),
            rag_status=rag,
            interpretation=data.get("interpretation"),
            contributing_factors=data.get("contributing_factors", []),
            data_gaps=data.get("data_gaps", []),
        )
        db.add(risk_score)

    await db.flush()
    logger.info(f"Risk score [{domain.value}] for {client.full_name}: {rag.value} ({data.get('score')})")
    return risk_score


async def calculate_all_domains(db: AsyncSession, client: Client) -> list[RiskScore]:
    """Calculate all four domain risk scores and return them."""
    scores = []
    for domain in RiskDomain:
        try:
            score = await calculate_domain_risk(db, client, domain)
            scores.append(score)
        except Exception as e:
            logger.error(f"Risk calculation failed [{domain.value}] for {client.id}: {e}")
    return scores


def calculate_health_score(risk_scores: list[RiskScore]) -> int:
    """
    Derive composite Health Score (0–100) from domain scores.
    Weights: ASCVD 30%, Metabolic 30%, Neuro 25%, Cancer 15%.
    Returns 0 if no scores available.
    """
    weights = {
        RiskDomain.CARDIOVASCULAR: 0.30,
        RiskDomain.METABOLIC: 0.30,
        RiskDomain.NEUROLOGICAL: 0.25,
        RiskDomain.CANCER: 0.15,
    }
    total, weight_sum = 0.0, 0.0
    for rs in risk_scores:
        if rs.score is not None and rs.domain in weights:
            total += rs.score * weights[rs.domain]
            weight_sum += weights[rs.domain]
    if weight_sum == 0:
        return 0
    return round(total / weight_sum)
