"""Data freshness endpoints: when pipelines last ran, layer status."""

import json
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlalchemy import text
from sqlalchemy.engine import Connection

from pipeline.db import engine

router = APIRouter(tags=["data-status"])

# Expected refresh cadence per source, in hours. Used to compute
# fresh/stale/very-stale status indicators. Sources not listed here default
# to 168h (weekly).
SOURCE_REFRESH_HOURS: dict[str, float] = {
    # Daily ingestion (cron at 02:00 PT)
    "inaturalist": 24,
    "usgs": 24,
    "snotel": 24,
    # Weekly ingestion (Mon 04:00 PT)
    "fishing": 168,
    "wqp": 168,
    "washington": 168,
    "utah": 168,
    # Monthly ingestion (1st @ 05:00 PT)
    "biodata": 720,
    "wqp_bugs": 720,
    "gbif": 720,
    "recreation": 720,
    "pbdb": 720,
    "restoration": 720,
    "prism": 720,
    "streamnet": 720,
    "idigbio": 720,
    # Annually / rare
    "macrostrat": 8760,
    "blm_sma": 8760,
    "dogami": 8760,
    "mrds": 8760,
    "mtbs": 4380,  # quarterly
    "nhdplus": 8760,
    "wbd": 8760,
    "nwi": 8760,
    "fish_barrier": 4380,
    "deq_303d": 4380,
}


def _human_age(hours_ago: float) -> str:
    if hours_ago < 1:
        m = max(1, int(hours_ago * 60))
        return f"{m} min ago"
    if hours_ago < 24:
        return f"{int(hours_ago)}h ago"
    if hours_ago < 24 * 14:
        return f"{int(hours_ago / 24)}d ago"
    return f"{int(hours_ago / (24 * 7))}w ago"


def _status_for(source: str, hours_ago: float | None) -> str:
    """Return 'fresh' | 'stale' | 'very_stale' | 'unknown'."""
    if hours_ago is None:
        return "unknown"
    cadence = SOURCE_REFRESH_HOURS.get(source, 168)
    # Allow 1.5× the expected cadence before "stale", 3× before "very_stale".
    # Daily-cadence sources thus stay green within 36h, daily 36-72h is yellow.
    if hours_ago <= cadence * 1.5:
        return "fresh"
    if hours_ago <= cadence * 3:
        return "stale"
    return "very_stale"


def compute_data_status(conn: Connection) -> dict:
    """Aggregate pipeline sync status, record counts, and layer inventory."""
    pipelines = conn.execute(text("""
        SELECT source_type,
               max(completed_at) as last_sync,
               count(*) as total_jobs,
               count(CASE WHEN status = 'completed' THEN 1 END) as completed,
               count(CASE WHEN status = 'failed' THEN 1 END) as failed
        FROM ingestion_jobs
        GROUP BY source_type
        ORDER BY max(completed_at) DESC NULLS LAST
    """)).fetchall()

    most_recent = conn.execute(text(
        "SELECT max(completed_at) FROM ingestion_jobs WHERE status = 'completed'"
    )).scalar()
    oldest = conn.execute(text(
        "SELECT min(max_sync) FROM (SELECT source_type, max(completed_at) as max_sync FROM ingestion_jobs WHERE status = 'completed' GROUP BY source_type) sub"
    )).scalar()

    bronze_obs = conn.execute(text("SELECT count(*) FROM observations")).scalar()
    bronze_ts = conn.execute(text("SELECT count(*) FROM time_series")).scalar()
    bronze_int = conn.execute(text("SELECT count(*) FROM interventions")).scalar()

    view_counts = conn.execute(text("""
        SELECT schemaname, count(*)
        FROM pg_matviews WHERE schemaname IN ('silver', 'gold')
        GROUP BY schemaname ORDER BY schemaname
    """)).fetchall()

    bronze_tables = {}
    for tbl in ['observations', 'time_series', 'interventions', 'fire_perimeters',
                'stream_flowlines', 'impaired_waters', 'wetlands', 'watershed_boundaries',
                'geologic_units', 'fossil_occurrences', 'mineral_deposits', 'land_ownership',
                'recreation_sites', 'curated_hatch_chart', 'deep_time_stories',
                'rockhounding_sites', 'river_stories',
                'wa_salmonscape', 'wa_fish_stocking', 'wa_surface_geology',
                'wa_srfb_projects', 'wa_state_parks']:
        try:
            bronze_tables[tbl] = conn.execute(text(f"SELECT count(*) FROM {tbl}")).scalar()
        except Exception:
            conn.rollback()
            bronze_tables[tbl] = 0

    silver_views = {}
    gold_views = {}
    mv_rows = conn.execute(text(
        "SELECT schemaname, matviewname FROM pg_matviews WHERE schemaname IN ('silver','gold') ORDER BY schemaname, matviewname"
    )).fetchall()
    for r in mv_rows:
        try:
            cnt = conn.execute(text(f"SELECT count(*) FROM {r[0]}.{r[1]}")).scalar()
        except Exception:
            conn.rollback()
            cnt = 0
        if r[0] == 'silver':
            silver_views[r[1]] = cnt
        else:
            gold_views[r[1]] = cnt

    curated = []
    try:
        fly_count = conn.execute(text("SELECT count(*) FROM silver.insect_fly_patterns")).scalar()
        curated.append({
            "name": "Insect-to-Fly Pattern Mapping",
            "table": "silver.insect_fly_patterns",
            "records": fly_count,
            "description": "Aquatic insects mapped to fly fishing patterns with hook sizes, fly types, photos, seasons, and fishing tips",
            "source": "Hand-curated from fly fishing literature",
        })
    except Exception:
        conn.rollback()

    try:
        shop_count = conn.execute(text("SELECT count(*) FROM fly_shops_guides")).scalar()
        curated.append({
            "name": "Fly Shops & Guide Services",
            "table": "fly_shops_guides",
            "records": shop_count,
            "description": "Oregon fly shops and guide services with contact info, websites, and coordinates per watershed",
            "source": "Hand-curated from web research (verified businesses)",
        })
    except Exception:
        conn.rollback()

    try:
        mineral_shop_count = conn.execute(text("SELECT count(*) FROM mineral_shops")).scalar()
        curated.append({
            "name": "Mineral & Rock Shops",
            "table": "mineral_shops",
            "records": mineral_shop_count,
            "description": "Oregon mineral shops, rock ranches, and paleontology museums with contact info and coordinates",
            "source": "Hand-curated from web research (verified businesses)",
        })
    except Exception:
        conn.rollback()

    try:
        rock_count = conn.execute(text("SELECT count(*) FROM rockhounding_sites")).scalar()
        curated.append({
            "name": "Rockhounding Sites",
            "table": "rockhounding_sites",
            "records": rock_count,
            "description": "Oregon rockhounding and collecting locations — thundereggs, agates, obsidian, sunstone, petrified wood, opal, jasper with coordinates, land ownership, and collecting rules",
            "source": "Hand-curated from rockhounding guides, BLM records, and community knowledge",
        })
    except Exception:
        conn.rollback()

    fossil_common = conn.execute(text(
        "SELECT count(*) FROM fossil_occurrences WHERE common_name IS NOT NULL AND common_name != ''"
    )).scalar()
    curated.append({
        "name": "Fossil Common Names",
        "table": "fossil_occurrences.common_name",
        "records": fossil_common,
        "description": "Latin genus/species names mapped to English common names (e.g., Mesohippus → Three-toed Horse)",
        "source": "Hand-curated lookup table (~60 genera)",
    })

    fossil_img_stats = conn.execute(text("""
        SELECT COALESCE(image_source, 'none') as src, count(*)
        FROM fossil_occurrences GROUP BY 1 ORDER BY 2 DESC
    """)).fetchall()
    img_breakdown = {r[0]: r[1] for r in fossil_img_stats}
    fossil_total = conn.execute(text("SELECT count(*) FROM fossil_occurrences")).scalar()
    fossil_with_img = conn.execute(text("SELECT count(*) FROM fossil_occurrences WHERE image_url IS NOT NULL")).scalar()
    fossil_3d = conn.execute(text(
        "SELECT count(*) FROM fossil_occurrences WHERE data_payload ? 'morphosource_url'"
    )).scalar()
    pct = round(100 * fossil_with_img / fossil_total, 1) if fossil_total else 0
    curated.append({
        "name": "Fossil Images",
        "table": "fossil_occurrences.image_url",
        "records": fossil_with_img,
        "description": (
            f"{pct}% coverage ({fossil_with_img}/{fossil_total}): "
            f"{img_breakdown.get('specimen', 0)} specimen photos, "
            f"{img_breakdown.get('wikimedia', 0)} Wikimedia Commons, "
            f"{img_breakdown.get('phylopic', 0)} PhyloPic silhouettes. "
            f"Plus {fossil_3d} MorphoSource 3D links."
        ),
        "source": "iDigBio, Smithsonian NMNH, GBIF, Wikimedia Commons, PhyloPic, MorphoSource",
    })

    mineral_expanded = conn.execute(text(
        "SELECT count(*) FROM mineral_deposits WHERE commodity NOT SIMILAR TO '%[A-Z]{2,}%'"
    )).scalar()
    curated.append({
        "name": "Mineral Commodity Names",
        "table": "mineral_deposits.commodity",
        "records": mineral_expanded,
        "description": "MRDS abbreviations expanded to human-readable names (SDG → Sand & Gravel, PGE_PT → Platinum)",
        "source": "Hand-curated code-to-name mapping (~16 codes)",
    })

    mineral_total = conn.execute(text("SELECT count(*) FROM mineral_deposits")).scalar()
    mineral_with_img = conn.execute(text("SELECT count(*) FROM mineral_deposits WHERE image_url IS NOT NULL")).scalar()
    mineral_pct = round(100 * mineral_with_img / mineral_total, 1) if mineral_total else 0
    curated.append({
        "name": "Mineral Deposit Images",
        "table": "mineral_deposits.image_url",
        "records": mineral_with_img,
        "description": f"{mineral_pct}% coverage ({mineral_with_img}/{mineral_total}): representative mineral/ore photos from Wikimedia Commons matched by commodity type",
        "source": "Wikimedia Commons (CC-BY-SA, CC0, Public Domain)",
    })

    try:
        video_count = conn.execute(text("SELECT count(*) FROM fly_tying_videos")).scalar()
        curated.append({
            "name": "Fly Tying Videos",
            "table": "fly_tying_videos",
            "records": video_count,
            "description": "YouTube fly tying tutorial links for each fly pattern — opens in new tab from Hatch Intelligence",
            "source": "Curated from Tightline Productions, InTheRiffle, Tim Flagler, Davie McPhail",
        })
    except Exception:
        conn.rollback()

    try:
        hatch_count = conn.execute(text("SELECT count(*) FROM curated_hatch_chart")).scalar()
        curated.append({
            "name": "Expert Hatch Chart",
            "table": "curated_hatch_chart",
            "records": hatch_count,
            "description": "Month-by-month aquatic insect emergence timing with fly pattern recommendations for 6 Pacific NW watersheds",
            "source": "Compiled from Western Hatches, The Caddis Fly Shop, Westfly.com, The Fly Fisher's Place",
        })
    except Exception:
        conn.rollback()

    return {
        "bronze": {
            "observations": bronze_obs,
            "time_series": bronze_ts,
            "interventions": bronze_int,
            "most_recent_sync": most_recent.isoformat() if most_recent else None,
            "oldest_pipeline_sync": oldest.isoformat() if oldest else None,
            "tables": bronze_tables,
        },
        "silver": {
            "views": next((r[1] for r in view_counts if r[0] == 'silver'), 0),
            "tables": silver_views,
        },
        "gold": {
            "views": next((r[1] for r in view_counts if r[0] == 'gold'), 0),
            "tables": gold_views,
        },
        "curated": curated,
        "pipelines": [
            {
                "source": r[0],
                "last_sync": r[1].isoformat() if r[1] else None,
                "total_jobs": r[2],
                "completed": r[3],
                "failed": r[4],
            }
            for r in pipelines
        ],
    }


def refresh_data_status_cache() -> dict:
    """Recompute the data-status payload and persist it as a single-row cache."""
    with engine.connect() as conn:
        payload = compute_data_status(conn)
        conn.execute(
            text("""
                INSERT INTO data_status_cache (id, payload, refreshed_at)
                VALUES (1, CAST(:payload AS jsonb), now())
                ON CONFLICT (id) DO UPDATE
                SET payload = EXCLUDED.payload,
                    refreshed_at = EXCLUDED.refreshed_at
            """),
            {"payload": json.dumps(payload)},
        )
        conn.commit()
    return payload


@router.get("/data-status")
def get_data_status():
    """Return cached pipeline sync status. Falls back to live compute on cold start."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT payload, refreshed_at FROM data_status_cache WHERE id = 1")
        ).fetchone()
        if row is not None:
            payload = row[0]
            payload["cache"] = {"refreshed_at": row[1].isoformat()}
            return payload

    payload = refresh_data_status_cache()
    payload["cache"] = {"refreshed_at": None, "cold_start": True}
    return payload


@router.post("/data-status/refresh")
def post_refresh_data_status():
    """Force-refresh the data-status cache."""
    payload = refresh_data_status_cache()
    return {"refreshed": True, "pipelines": len(payload.get("pipelines", []))}


@router.get("/data-status/freshness")
def get_freshness():
    """Lightweight per-source freshness map for UI status indicators.

    Returns one entry per ingested source with last_sync timestamp, age in
    hours, a status bucket (fresh/stale/very_stale/unknown), and a human label.
    Reads from the data_status_cache; falls back to live compute on cold start.
    """
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT payload FROM data_status_cache WHERE id = 1")
        ).fetchone()
        if row is not None:
            payload = row[0]
        else:
            payload = refresh_data_status_cache()

    now = datetime.now(timezone.utc)
    sources: dict[str, dict] = {}
    for entry in payload.get("pipelines", []) or []:
        src = entry.get("source")
        last_sync_iso = entry.get("last_sync")
        if not src:
            continue
        if last_sync_iso:
            try:
                ts = datetime.fromisoformat(last_sync_iso.replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
                hours_ago = (now - ts).total_seconds() / 3600.0
                sources[src] = {
                    "last_sync": last_sync_iso,
                    "hours_ago": round(hours_ago, 1),
                    "status": _status_for(src, hours_ago),
                    "label": _human_age(hours_ago),
                    "expected_cadence_hours": SOURCE_REFRESH_HOURS.get(src, 168),
                }
                continue
            except Exception:
                pass
        sources[src] = {
            "last_sync": None,
            "hours_ago": None,
            "status": "unknown",
            "label": "—",
            "expected_cadence_hours": SOURCE_REFRESH_HOURS.get(src, 168),
        }

    return {"sources": sources, "as_of": now.isoformat()}
