import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base, UUIDMixin


class WearableSource(str, enum.Enum):
    WHOOP = "whoop"
    OURA = "oura"
    GARMIN = "garmin"
    APPLE_HEALTH = "apple_health"
    MANUAL = "manual"


class WearableData(Base, UUIDMixin):
    __tablename__ = "wearable_data"

    client_id: Mapped[str] = mapped_column(
        UUID(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True
    )
    data_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    source: Mapped[WearableSource] = mapped_column(
        Enum(WearableSource), nullable=False, default=WearableSource.MANUAL
    )

    # Sleep
    sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    sleep_efficiency: Mapped[float | None] = mapped_column(Float, nullable=True)  # %
    deep_sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    rem_sleep_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Recovery / readiness
    hrv_ms: Mapped[float | None] = mapped_column(Float, nullable=True)  # HRV in ms
    resting_hr: Mapped[int | None] = mapped_column(Integer, nullable=True)  # bpm
    recovery_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0–100
    readiness_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0–100

    # Activity
    strain_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    active_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    zone2_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vo2_max: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Body
    skin_temp_deviation: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    client = relationship("Client", back_populates="wearable_data")
