import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, UUIDMixin


class BiomarkerFlag(str, enum.Enum):
    OPTIMAL = "optimal"
    NORMAL = "normal"
    BORDERLINE = "borderline"
    HIGH = "high"
    LOW = "low"
    CRITICAL_HIGH = "critical_high"
    CRITICAL_LOW = "critical_low"


class LabResult(Base, UUIDMixin):
    __tablename__ = "lab_results"

    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    marker_name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_text: Mapped[str | None] = mapped_column(String(100), nullable=True)  # for non-numeric
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ref_range_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    ref_range_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    optimal_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    optimal_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    flag: Mapped[BiomarkerFlag | None] = mapped_column(Enum(BiomarkerFlag), nullable=True)
    test_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    lab_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_pdf_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    client = relationship("Client", back_populates="lab_results")
