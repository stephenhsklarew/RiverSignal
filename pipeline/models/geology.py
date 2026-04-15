"""Geology data models: geologic units, fossil occurrences, land ownership, deep time stories."""

import uuid
from datetime import datetime

from geoalchemy2 import Geometry
from sqlalchemy import DateTime, Float, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from pipeline.models.base import Base


class GeologicUnit(Base):
    __tablename__ = "geologic_units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50))  # ngmdb, dogami, macrostrat
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    formation: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    rock_type: Mapped[str | None] = mapped_column(String(100), nullable=True)  # igneous, sedimentary, metamorphic
    lithology: Mapped[str | None] = mapped_column(String(255), nullable=True)  # basalt, sandstone, etc.
    age_min_ma: Mapped[float | None] = mapped_column(Float, nullable=True)
    age_max_ma: Mapped[float | None] = mapped_column(Float, nullable=True)
    period: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    geometry = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    data_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_geologic_units_geometry", "geometry", postgresql_using="gist"),
        Index("ix_geologic_units_source_id", "source", "source_id"),
    )


class FossilOccurrence(Base):
    __tablename__ = "fossil_occurrences"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50))  # pbdb, idigbio, gbif
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    taxon_name: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    taxon_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    common_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phylum: Mapped[str | None] = mapped_column(String(100), nullable=True)
    class_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    order_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    family: Mapped[str | None] = mapped_column(String(100), nullable=True)
    age_min_ma: Mapped[float | None] = mapped_column(Float, nullable=True)
    age_max_ma: Mapped[float | None] = mapped_column(Float, nullable=True)
    period: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    formation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    collector: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reference: Mapped[str | None] = mapped_column(Text, nullable=True)
    museum: Mapped[str | None] = mapped_column(String(255), nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_license: Mapped[str | None] = mapped_column(String(50), nullable=True)
    image_source: Mapped[str | None] = mapped_column(String(20), nullable=True)  # specimen, wikimedia, phylopic
    data_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_fossil_occurrences_location", "location", postgresql_using="gist"),
        Index("ix_fossil_source_id", "source", "source_id", unique=True),
    )


class LandOwnership(Base):
    __tablename__ = "land_ownership"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50))  # blm_sma
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    agency: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)  # BLM, USFS, NPS, State, Private
    designation: Mapped[str | None] = mapped_column(String(255), nullable=True)
    admin_unit: Mapped[str | None] = mapped_column(String(255), nullable=True)
    collecting_status: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)  # permitted, restricted, prohibited
    collecting_rules: Mapped[str | None] = mapped_column(Text, nullable=True)
    geometry = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    data_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_land_ownership_geometry", "geometry", postgresql_using="gist"),
    )


class MineralDeposit(Base):
    __tablename__ = "mineral_deposits"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source: Mapped[str] = mapped_column(String(50))  # mrds
    source_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    site_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    commodity: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    dev_status: Mapped[str | None] = mapped_column(String(100), nullable=True)  # Prospect, Past Producer, etc.
    location = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_license: Mapped[str | None] = mapped_column(String(50), nullable=True)
    image_source: Mapped[str | None] = mapped_column(String(20), nullable=True)  # wikimedia, phylopic
    data_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("idx_mineral_deposits_location", "location", postgresql_using="gist"),
        Index("ix_mineral_source_id", "source", "source_id", unique=True),
    )


class DeepTimeStory(Base):
    __tablename__ = "deep_time_stories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    geologic_unit_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True, index=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    reading_level: Mapped[str] = mapped_column(String(50))  # expert, adult, kid_friendly
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_cited: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(100), nullable=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index("ix_deep_time_unit_level", "geologic_unit_id", "reading_level", unique=True),
    )
