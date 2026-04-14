"""Prediction models: forecasts, outcomes, and accuracy tracking."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from pipeline.models.base import Base


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    watershed: Mapped[str] = mapped_column(String(100), index=True)
    prediction_type: Mapped[str] = mapped_column(String(50))  # species_return, fire_recovery, thermal_forecast, invasive_spread
    intervention_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    intervention_scale: Mapped[str | None] = mapped_column(String(255), nullable=True)
    horizon_months: Mapped[int] = mapped_column(Integer, default=12)
    scenario: Mapped[str | None] = mapped_column(String(100), nullable=True)  # with_intervention, baseline, drought
    parameters: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # full input params

    # Outputs
    overall_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100
    confidence_level: Mapped[str | None] = mapped_column(String(20), nullable=True)  # HIGH, MEDIUM, LOW
    predictions_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # structured predictions array
    risk_factors_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # risk factors array
    scenario_comparison: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # with vs without
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)  # LLM narrative
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Lifecycle
    status: Mapped[str] = mapped_column(String(20), default="active")  # active, resolved, expired
    check_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Accuracy (filled when resolved)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # 0-100
    actuals_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


class PredictionOutcome(Base):
    __tablename__ = "prediction_outcomes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    prediction_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    species_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    predicted_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    predicted_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    actual_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confirmed: Mapped[bool | None] = mapped_column(nullable=True)  # True=confirmed, False=not, None=pending
    scored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
