"""add reach coverage: john_day lower, green river pinedale/desolation/canyonlands

Revision ID: z7d8e9f0a1b2
Revises: y6c7d8e9f0a1
Create Date: 2026-05-14 14:30:00.000000

After auditing watershed bboxes, four reach gaps were identified where
ingestion was occurring (or now occurs post-bbox-expansion) but no
reach existed to attribute TQS rows to:

  - johnday_lower:    Service Creek to Columbia confluence (lower 100 mi)
  - green_pinedale:   WY headwaters above Fontenelle Reservoir
  - green_desolation: Desolation / Gray Canyons (multi-day float)
  - green_canyonlands: Green River UT to Colorado confluence in Canyonlands NP

Adding these gives full main-stem coverage for each watershed and
ensures the TQS scorer produces rows for the now-ingested geographic
extent. Idempotent via ON CONFLICT (id) DO NOTHING.
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'z7d8e9f0a1b2'
down_revision: Union[str, Sequence[str], None] = 'y6c7d8e9f0a1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# (id, watershed, name, short_label, centroid_lat, centroid_lon,
#  primary_usgs_site_id, general_flow_bearing, is_warm_water,
#  typical_species (comma-separated for ARRAY build), notes)
EXTRA_REACHES = [
    ('johnday_lower', 'johnday', 'John Day Lower', 'Lower',
     45.25, -120.30, '14048450', 90, True,
     'smallmouth_bass,steelhead',
     'Service Creek to Columbia confluence at McDonald Ferry. Lower 100 miles, warm-water mainstem.'),

    ('green_pinedale', 'green_river', 'Green River — Pinedale', 'Pinedale',
     42.50, -109.80, '09188500', 180, False,
     'cutthroat,brown_trout,rainbow_trout',
     'Wyoming headwaters above Fontenelle Reservoir. Wind River Range drainage.'),

    ('green_desolation', 'green_river', 'Green River — Desolation / Gray', 'Desolation',
     39.45, -110.05, '09315000', 180, True,
     'rainbow_trout,smallmouth_bass,channel_catfish,colorado_pikeminnow',
     'Desolation and Gray Canyons. Multi-day floatable. Warmer water downstream from Flaming Gorge.'),

    ('green_canyonlands', 'green_river', 'Green River — Canyonlands', 'Canyonlands',
     38.55, -110.00, '09315000', 180, True,
     'channel_catfish,smallmouth_bass,colorado_pikeminnow,razorback_sucker',
     'Green River UT to confluence with Colorado in Canyonlands NP. Endangered native fish habitat.'),
]


def upgrade() -> None:
    rows = []
    for (rid, ws, name, short, lat, lon, gauge, bearing, warm, species_csv, notes) in EXTRA_REACHES:
        species_array = "ARRAY[" + ",".join(f"'{s}'" for s in species_csv.split(",")) + "]::varchar[]"
        notes_escaped = notes.replace("'", "''")
        rows.append(
            f"('{rid}','{ws}','{name}','{short}',{lat},{lon},'{gauge}',{bearing},{str(warm).lower()},"
            f"{species_array},'{notes_escaped}','v1 reach-coverage audit 2026-05-14')"
        )
    values_sql = ",\n            ".join(rows)
    op.execute(
        f"""
        INSERT INTO silver.river_reaches
            (id, watershed, name, short_label, centroid_lat, centroid_lon,
             primary_usgs_site_id, general_flow_bearing, is_warm_water,
             typical_species, notes, source)
        VALUES
            {values_sql}
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    ids = ",".join(f"'{r[0]}'" for r in EXTRA_REACHES)
    op.execute(f"DELETE FROM silver.river_reaches WHERE id IN ({ids})")
