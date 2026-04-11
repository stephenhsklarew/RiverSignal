"""Silver and Gold medallion layers

Revision ID: medallion_001
Revises: 1479f57b36fb
Create Date: 2026-04-10
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = 'medallion_001'
down_revision: Union[str, Sequence[str]] = '1479f57b36fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# NOTE: The actual materialized view DDL is in pipeline/medallion_ddl.py
# This migration creates the schemas and additional bronze-layer tables
# that were added after the initial schema migration.

def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS silver")
    op.execute("CREATE SCHEMA IF NOT EXISTS gold")

    # Additional bronze tables (added post-initial migration)
    op.execute("""
        CREATE TABLE IF NOT EXISTS fire_perimeters (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id uuid NOT NULL,
            fire_name varchar(255),
            fire_id varchar(100),
            fire_year int,
            acres float,
            burn_severity varchar(50),
            ig_date date,
            perimeter geometry(MULTIPOLYGON, 4326),
            source_type varchar(50) DEFAULT 'mtbs',
            data_payload jsonb,
            ingested_at timestamptz DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS stream_flowlines (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id uuid NOT NULL,
            reach_code varchar(50),
            gnis_name varchar(255),
            stream_order int,
            length_km float,
            ftype varchar(50),
            flowline geometry(MULTILINESTRING, 4326),
            source_type varchar(50) DEFAULT 'nhdplus',
            data_payload jsonb,
            ingested_at timestamptz DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS impaired_waters (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id uuid NOT NULL,
            assessment_unit varchar(255),
            water_name varchar(255),
            parameter varchar(255),
            category varchar(50),
            tmdl_status varchar(100),
            listing_year int,
            geometry geometry(GEOMETRY, 4326),
            source_type varchar(50) DEFAULT 'deq_303d',
            data_payload jsonb,
            ingested_at timestamptz DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS wetlands (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id uuid NOT NULL,
            wetland_type varchar(100),
            attribute varchar(50),
            acres float,
            geometry geometry(GEOMETRY, 4326),
            source_type varchar(50) DEFAULT 'nwi',
            data_payload jsonb,
            ingested_at timestamptz DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS watershed_boundaries (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            site_id uuid NOT NULL,
            huc12 varchar(12),
            name varchar(255),
            area_sqkm float,
            geometry geometry(MULTIPOLYGON, 4326),
            data_payload jsonb,
            ingested_at timestamptz DEFAULT now()
        )
    """)


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS gold CASCADE")
    op.execute("DROP SCHEMA IF EXISTS silver CASCADE")
    op.execute("DROP TABLE IF EXISTS watershed_boundaries")
    op.execute("DROP TABLE IF EXISTS wetlands")
    op.execute("DROP TABLE IF EXISTS impaired_waters")
    op.execute("DROP TABLE IF EXISTS stream_flowlines")
    op.execute("DROP TABLE IF EXISTS fire_perimeters")
