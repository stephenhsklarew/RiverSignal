"""seed mad_river_oh rockhounding_sites (conservative — viewing / permission-required)

Revision ID: mr06a1b2c3d4
Revises: mr05a1b2c3d4
Create Date: 2026-05-30 00:00:00.000000

The Mad River source-inventory (§1.3) flagged `rockhounding_sites` as `✗`
requiring manual curation. Three conservative entries, each explicitly
tagged with land_owner + collecting_rules. Ohio's Paleozoic carbonate
surface (Ordovician–Devonian) is the draw, but legal collecting localities
on public land are scarce — most are viewing/educational or private
(permission-required). NOT collecting destinations unless permission is
documented.

Idempotent via ON CONFLICT (id) DO NOTHING on md5(name)::uuid. No-op on any
environment where mad_river_oh isn't configured (CROSS JOIN to sites).
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'mr06a1b2c3d4'
down_revision: Union[str, Sequence[str], None] = 'mr05a1b2c3d4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        INSERT INTO rockhounding_sites
            (id, name, rock_type, latitude, longitude, location,
             land_owner, collecting_rules, nearest_town, description,
             watersheds, site_id)
        SELECT
            md5(name)::uuid,
            name, rock_type, latitude, longitude,
            ST_SetSRID(ST_MakePoint(longitude, latitude), 4326),
            land_owner, collecting_rules, nearest_town, description,
            ARRAY['mad_river_oh']::text[],
            s.id
        FROM (VALUES
            (
                'Campbell Hill — Glacial Erratics (Logan Co.)',
                'glacial erratics: granite + gneiss boulders on Silurian dolomite',
                40.3690, -83.7200,
                'Mixed — public overlook + adjacent private land',
                'VIEWING / EDUCATIONAL. Ohio''s highest point sits on Wisconsinan glacial drift; granite + gneiss erratics rafted from Canada rest on the local Silurian dolomite. Observe; do not remove material from public grounds or private land without documented permission.',
                'Bellefontaine, OH',
                'The Bellefontaine Outlier and Campbell Hill area expose glacially transported crystalline erratics far from their bedrock source — a classic teaching locality for continental glaciation in west-central Ohio.'
            ),
            (
                'Bellefontaine Area Quarries — Silurian Carbonate Fossils',
                'Silurian dolomite/limestone: corals, brachiopods, bryozoans',
                40.3600, -83.7600,
                'Private — active/permit quarries; permission required',
                'PRIVATE LAND. Active and historic carbonate quarries near Bellefontaine expose richly fossiliferous Silurian dolomite. Collecting ONLY with the operator''s documented permission and required safety gear. Never enter an active quarry uninvited.',
                'Bellefontaine, OH',
                'West-central Ohio''s Silurian carbonates (Lockport/Cedarville dolomite) carry corals, brachiopods and bryozoans. Quarry exposures are the best windows but are private, hazardous, and permission-only.'
            ),
            (
                'Clark County Stream Gravels — Carbonate Float & Calcite',
                'calcite, glacial float, carbonate cobbles',
                39.9200, -83.8100,
                'Mixed — public road right-of-way vs private streambank',
                'PERMISSION REQUIRED on private streambank; surface-only on public right-of-way. Loose carbonate cobbles and calcite are reported in Clark County stream gravels. Do not dig banks, do not trespass, and follow Ohio stream-access law (landowner controls the streambed).',
                'Springfield, OH',
                'Glacial outwash + carbonate bedrock shed calcite-bearing float into Mad River-area stream gravels around Springfield. Treat as a casual surface-float / educational locality, not a dig site.'
            )
        ) AS seed(name, rock_type, latitude, longitude, land_owner, collecting_rules, nearest_town, description)
        CROSS JOIN (SELECT id FROM sites WHERE watershed = 'mad_river_oh' LIMIT 1) s
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM rockhounding_sites
         WHERE 'mad_river_oh' = ANY(watersheds)
           AND name IN (
             'Campbell Hill — Glacial Erratics (Logan Co.)',
             'Bellefontaine Area Quarries — Silurian Carbonate Fossils',
             'Clark County Stream Gravels — Carbonate Float & Calcite'
           )
    """)
