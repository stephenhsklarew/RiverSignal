"""Spatial data models: fire perimeters, stream network, wetlands, impaired waters, watershed boundaries."""

import uuid
from datetime import date, datetime

from geoalchemy2 import Geometry
from sqlalchemy import Date, DateTime, Float, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from pipeline.models.base import Base


class FirePerimeter(Base):
    __tablename__ = "fire_perimeters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    fire_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fire_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    fire_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    burn_severity: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ig_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    perimeter = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), default="mtbs")
    data_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class StreamFlowline(Base):
    __tablename__ = "stream_flowlines"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    reach_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    gnis_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stream_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    length_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    ftype: Mapped[str | None] = mapped_column(String(50), nullable=True)
    flowline = mapped_column(Geometry("MULTILINESTRING", srid=4326), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), default="nhdplus")
    data_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ImpairedWater(Base):
    __tablename__ = "impaired_waters"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    assessment_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    water_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    parameter: Mapped[str | None] = mapped_column(String(255), nullable=True)
    category: Mapped[str | None] = mapped_column(String(50), nullable=True)
    tmdl_status: Mapped[str | None] = mapped_column(String(100), nullable=True)
    listing_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    geometry = mapped_column(Geometry("GEOMETRY", srid=4326), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), default="deq_303d")
    data_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Wetland(Base):
    __tablename__ = "wetlands"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    wetland_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    attribute: Mapped[str | None] = mapped_column(String(50), nullable=True)
    acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometry = mapped_column(Geometry("GEOMETRY", srid=4326), nullable=True)
    source_type: Mapped[str | None] = mapped_column(String(50), default="nwi")
    data_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WatershedBoundary(Base):
    __tablename__ = "watershed_boundaries"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    site_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    huc12: Mapped[str | None] = mapped_column(String(12), nullable=True, index=True)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    area_sqkm: Mapped[float | None] = mapped_column(Float, nullable=True)
    geometry = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    data_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
