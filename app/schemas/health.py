from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.client import BiologicalSex, SubscriptionTier
from app.models.goal import GoalDomain, GoalStatus
from app.models.lab_result import BiomarkerFlag
from app.models.nutrition_log import MealType


# ── Health Profile ────────────────────────────────────────────────────────────

class HealthProfileUpdate(BaseModel):
    date_of_birth: Optional[date] = None
    sex: Optional[BiologicalSex] = None
    height_cm: Optional[float] = Field(None, gt=0, lt=300)
    weight_kg: Optional[float] = Field(None, gt=0, lt=500)
    daily_protein_target_g: Optional[int] = Field(None, gt=0)
    daily_fibre_target_g: Optional[int] = Field(None, gt=0)
    daily_calories_target: Optional[int] = Field(None, gt=0)


class HealthProfileResponse(BaseModel):
    id: UUID
    full_name: str
    email: Optional[str]
    date_of_birth: Optional[date]
    sex: Optional[BiologicalSex]
    height_cm: Optional[float]
    weight_kg: Optional[float]
    subscription_tier: SubscriptionTier
    daily_protein_target_g: Optional[int]
    daily_fibre_target_g: Optional[int]
    daily_calories_target: Optional[int]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=255)
    email: str
    password: str = Field(..., min_length=8)
    date_of_birth: Optional[date] = None
    sex: Optional[BiologicalSex] = None
    height_cm: Optional[float] = Field(None, gt=0)
    weight_kg: Optional[float] = Field(None, gt=0)


# ── Lab Results ───────────────────────────────────────────────────────────────

class LabResultCreate(BaseModel):
    marker_name: str
    value: Optional[float] = None
    value_text: Optional[str] = None
    unit: Optional[str] = None
    ref_range_low: Optional[float] = None
    ref_range_high: Optional[float] = None
    optimal_low: Optional[float] = None
    optimal_high: Optional[float] = None
    flag: Optional[BiomarkerFlag] = None
    test_date: date
    lab_name: Optional[str] = None
    notes: Optional[str] = None


class LabResultResponse(BaseModel):
    id: UUID
    marker_name: str
    value: Optional[float]
    value_text: Optional[str]
    unit: Optional[str]
    ref_range_low: Optional[float]
    ref_range_high: Optional[float]
    optimal_low: Optional[float]
    optimal_high: Optional[float]
    flag: Optional[BiomarkerFlag]
    test_date: date
    lab_name: Optional[str]
    source_pdf_url: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class LabOCRResult(BaseModel):
    """Structured result from the lab PDF OCR pipeline — returned to user for confirmation."""
    lab_name: Optional[str]
    test_date: Optional[date]
    markers: list[LabResultCreate]


# ── Nutrition ─────────────────────────────────────────────────────────────────

class NutritionLogCreate(BaseModel):
    log_date: date
    meal_type: MealType = MealType.OTHER
    description: Optional[str] = None
    calories: Optional[int] = Field(None, ge=0)
    protein_g: Optional[float] = Field(None, ge=0)
    fat_g: Optional[float] = Field(None, ge=0)
    carbs_net_g: Optional[float] = Field(None, ge=0)
    fibre_g: Optional[float] = Field(None, ge=0)
    omega3_g: Optional[float] = Field(None, ge=0)
    alcohol_units: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class NutritionLogResponse(BaseModel):
    id: UUID
    log_date: date
    meal_type: MealType
    description: Optional[str]
    calories: Optional[int]
    protein_g: Optional[float]
    fat_g: Optional[float]
    carbs_net_g: Optional[float]
    fibre_g: Optional[float]
    omega3_g: Optional[float]
    alcohol_units: Optional[float]
    photo_url: Optional[str]
    ai_analysed: bool
    notes: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


class DailyNutritionSummary(BaseModel):
    date: date
    total_calories: int
    total_protein_g: float
    total_fibre_g: float
    total_fat_g: float
    total_carbs_net_g: float
    total_omega3_g: float
    total_alcohol_units: float
    meals: list[NutritionLogResponse]
    targets: dict  # protein_g, fibre_g, calories targets for context


class MealAnalysis(BaseModel):
    """Returned from AI meal photo analysis — user confirms before saving."""
    description: str
    meal_type: MealType
    calories: Optional[int]
    protein_g: Optional[float]
    fat_g: Optional[float]
    carbs_net_g: Optional[float]
    fibre_g: Optional[float]
    omega3_g: Optional[float]
    confidence: str  # "high", "medium", "low"
    notes: Optional[str]


# ── Goals ─────────────────────────────────────────────────────────────────────

class GoalCreate(BaseModel):
    domain: GoalDomain
    goal_text: str
    target_metric: Optional[str] = None
    current_value: Optional[str] = None
    target_value: Optional[str] = None
    deadline: Optional[date] = None
    interventions: Optional[str] = None
    notes: Optional[str] = None


class GoalUpdate(BaseModel):
    goal_text: Optional[str] = None
    target_metric: Optional[str] = None
    current_value: Optional[str] = None
    target_value: Optional[str] = None
    deadline: Optional[date] = None
    status: Optional[GoalStatus] = None
    interventions: Optional[str] = None
    notes: Optional[str] = None


class GoalResponse(BaseModel):
    id: UUID
    domain: GoalDomain
    goal_text: str
    target_metric: Optional[str]
    current_value: Optional[str]
    target_value: Optional[str]
    deadline: Optional[date]
    status: GoalStatus
    interventions: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
