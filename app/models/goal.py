import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, PgEnum, UUIDMixin


class GoalDomain(str, enum.Enum):
    CARDIOVASCULAR = "cardiovascular"
    METABOLIC = "metabolic"
    NEUROLOGICAL = "neurological"
    CANCER_PREVENTION = "cancer_prevention"
    NUTRITION = "nutrition"
    TRAINING = "training"
    BODY_COMPOSITION = "body_composition"
    SLEEP = "sleep"
    SUPPLEMENTS = "supplements"
    GENERAL = "general"


class GoalStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ABANDONED = "abandoned"


class Goal(Base, UUIDMixin):
    __tablename__ = "goals"

    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    domain: Mapped[GoalDomain] = mapped_column(PgEnum(GoalDomain), nullable=False)
    goal_text: Mapped[str] = mapped_column(Text, nullable=False)
    target_metric: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_value: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deadline: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[GoalStatus] = mapped_column(
        PgEnum(GoalStatus), nullable=False, default=GoalStatus.ACTIVE
    )
    interventions: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    client = relationship("Client", back_populates="goals")
