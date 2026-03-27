import enum
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, PgEnum, UUIDMixin


class RiskDomain(str, enum.Enum):
    CARDIOVASCULAR = "cardiovascular"
    METABOLIC = "metabolic"
    NEUROLOGICAL = "neurological"
    CANCER = "cancer"


class RAGStatus(str, enum.Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"
    INSUFFICIENT_DATA = "insufficient_data"


class RiskScore(Base, UUIDMixin):
    __tablename__ = "risk_scores"

    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    domain: Mapped[RiskDomain] = mapped_column(PgEnum(RiskDomain), nullable=False, index=True)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0–100
    rag_status: Mapped[RAGStatus] = mapped_column(
        PgEnum(RAGStatus), nullable=False, default=RAGStatus.INSUFFICIENT_DATA
    )
    interpretation: Mapped[str | None] = mapped_column(Text, nullable=True)
    contributing_factors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    data_gaps: Mapped[list | None] = mapped_column(JSON, nullable=True)
    last_calculated: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    client = relationship("Client", back_populates="risk_scores")
