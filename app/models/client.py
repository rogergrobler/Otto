import enum
from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class BiologicalSex(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class SubscriptionTier(str, enum.Enum):
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"


class Client(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "clients"

    # Auth
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    telegram_chat_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    telegram_username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    # Health profile
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    sex: Mapped[BiologicalSex | None] = mapped_column(Enum(BiologicalSex), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    subscription_tier: Mapped[SubscriptionTier] = mapped_column(
        Enum(SubscriptionTier), nullable=False, default=SubscriptionTier.STANDARD
    )

    # Daily nutrition targets (personalised; defaults applied on registration)
    daily_protein_target_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_fibre_target_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_calories_target: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # AI memory
    memory_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Coach notes (admin-facing)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Optional: linked admin who created this account
    created_by_id: Mapped[str | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )

    # Relationships
    created_by = relationship("User", back_populates="clients")
    conversations = relationship("Conversation", back_populates="client")
    coursework_assignments = relationship("ClientCoursework", back_populates="client")
    lab_results = relationship("LabResult", back_populates="client", order_by="LabResult.test_date.desc()")
    nutrition_logs = relationship("NutritionLog", back_populates="client", order_by="NutritionLog.log_date.desc()")
    goals = relationship("Goal", back_populates="client")
    risk_scores = relationship("RiskScore", back_populates="client")
    wearable_data = relationship("WearableData", back_populates="client", order_by="WearableData.data_date.desc()")
    nudges = relationship("Nudge", back_populates="client")
    coach_notes = relationship("CoachNote", back_populates="client")
