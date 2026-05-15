"""shenandoah fishing regulations seed (VA DWR + WV DNR special-reg streams)

Revision ID: ii09d0e1f2g3
Revises: hh08c9d0e1f2
Create Date: 2026-05-15 00:00:00.000000

Annotates the three Shenandoah river_reaches with a concise summary of the
special regulations that apply on each reach's notable tributaries / sections.

Source authority:
  - VA DWR Fishing Regulations: https://dwr.virginia.gov/fishing/regulations/
  - WV DNR Fishing Regulations: https://wvdnr.gov/wildlife/fishing-regulations/

This is a static seed (regulations change ~annually). When VA or WV publishes a
new rulebook, update this migration's payload via a new appended migration.
Append the regulation block to existing `notes` instead of replacing it, so
the auto-seeded prose (warm-water vs cold-water classification, etc.) is
preserved.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import text


revision: str = 'ii09d0e1f2g3'
down_revision: Union[str, Sequence[str], None] = 'hh08c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Reach → regulation summary. Source-cited and kept compact. Sentinel marker
# `[regs:`...`]` lets the downgrade strip the block precisely.
REG_SUMMARIES = {
    "shenandoah_north_fork": (
        "[regs: VA DWR — Smith Creek (Rockingham Co.) "
        "is a Special-Regulation Trout Stream; Mossy Creek and "
        "Beaver Creek (Augusta Co.) are Fly-Fishing-Only / "
        "catch-and-release Special-Regulation Trout Streams; "
        "Passage Creek (Shenandoah Co.) has Heritage Day Waters "
        "(youth-only days) and seasonal stocked-trout regs; "
        "smallmouth main-stem closed to harvest Jun 1–Jun 15.]"
    ),
    "shenandoah_south_fork": (
        "[regs: VA DWR — Rose River and Hughes River (Madison Co.) "
        "include Heritage Trout Waters (catch-and-release, single hook, "
        "no-bait sections); Robinson River (Madison Co.) has both stocked "
        "and Heritage sections; main-stem South Fork follows statewide "
        "smallmouth regs (closed to harvest Jun 1–Jun 15, 14-in min "
        "outside closure).]"
    ),
    "shenandoah_main_stem": (
        "[regs: VA DWR — statewide smallmouth-bass regs apply (closed to "
        "harvest Jun 1–Jun 15; 14-in min size outside closure; 1 fish/day "
        "creel). WV DNR — Bullskin Run and Evitts Run (Jefferson Co.) are "
        "stocked General-regulation trout streams; Shenandoah main stem in "
        "WV (Jefferson Co. to Harpers Ferry confluence) follows WV "
        "statewide warm-water regs.]"
    ),
}


def upgrade() -> None:
    conn = op.get_bind()
    for reach_id, regs in REG_SUMMARIES.items():
        # Append the regs block to existing notes, but only if it isn't
        # already present (idempotent re-run safety).
        conn.execute(
            text(
                "UPDATE silver.river_reaches "
                "SET notes = CASE "
                "  WHEN notes IS NULL OR notes = '' THEN :regs "
                "  WHEN notes LIKE :marker_pattern THEN notes "
                "  ELSE notes || ' ' || :regs "
                "END "
                "WHERE id = :rid"
            ),
            {"rid": reach_id, "regs": regs, "marker_pattern": "%[regs:%"},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for reach_id, regs in REG_SUMMARIES.items():
        # Strip the appended block (separator + block) on downgrade.
        conn.execute(
            text(
                "UPDATE silver.river_reaches "
                "SET notes = regexp_replace(notes, '\\s*\\[regs:[^\\]]*\\]', '', 'g') "
                "WHERE id = :rid"
            ),
            {"rid": reach_id},
        )
