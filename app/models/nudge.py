import enum
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, PgEnum, UUIDMixin


class NudgeType(str, enum.Enum):
    DAILY_CHECKIN = "daily_checkin"
    MEAL_REMINDER = "meal_reminder"
    TRAINING_PROMPT = "training_prompt"
    BIOMARKER_DUE = "biomarker_due"
    GOAL_MILESTONE = "goal_milestone"
    WEEKLY_SUMMARY = "weekly_summary"
    RISK_FLAG = "risk_flag"


class Nudge(Base, UUIDMixin):
    __tablename__ = "nudges"

    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    nudge_type: Mapped[NudgeType] = mapped_column(PgEnum(NudgeType), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    client = relationship("Client", back_populates="nudges")
