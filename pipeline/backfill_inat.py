"""Backfill enriched iNaturalist data: taxon metadata + photo URLs.

Enriches existing iNaturalist observations with:
- common_name, ancestry, conservation_status (from taxa API, batched)
- photo_url, photo_license (from observations API, batched by ID)
- positional_accuracy, captive, obscured, out_of_range (from observations API)

Resumes from where it left off -- safe to interrupt and restart.

Usage: python -m pipeline.backfill_inat [--photos-only] [--taxa-only]
"""

import json
import sys
import time

import httpx
from sqlalchemy import text

from pipeline.db import engine

API_BASE = "https://api.inaturalist.org/v1"


def backfill_taxa():
    """Fetch common names, ancestry, and conservation status for all taxa."""
    print("=== TAXON METADATA ENRICHMENT ===")

    with engine.connect() as conn:
        # Only fetch taxa that haven't been enriched yet
        rows = conn.execute(text("""
            SELECT DISTINCT taxon_id FROM observations
            WHERE source_type = 'inaturalist'
              AND taxon_id IS NOT NULL
              AND (data_payload->>'common_name') IS NULL
            ORDER BY taxon_id
        """)).fetchall()
        taxon_ids = [r[0] for r in rows]
        print(f"Taxa needing enrichment: {len(taxon_ids):,}")

    if not taxon_ids:
        print("All taxa already enriched.")
        return

    taxon_data = {}
    with httpx.Client(timeout=30) as client:
        for i in range(0, len(taxon_ids), 30):
            batch = taxon_ids[i:i + 30]
            ids_str = ",".join(str(t) for t in batch)

            for attempt in range(5):
                try:
                    resp = client.get(f"{API_BASE}/taxa/{ids_str}")
                    if resp.status_code == 429:
                        time.sleep(2 ** (attempt + 1))
                        continue
                    resp.raise_for_status()
                    break
                except (httpx.ConnectError, httpx.ReadTimeout):
                    time.sleep(3)
            else:
                continue

            for taxon in resp.json().get("results", []):
                cs = taxon.get("conservation_status") or {}
                taxon_data[taxon["id"]] = {
                    "common_name": taxon.get("preferred_common_name"),
                    "ancestry": taxon.get("ancestry"),
                    "wikipedia_url": taxon.get("wikipedia_url"),
                    "conservation_status": cs.get("status"),
                }

            if (i // 30) % 50 == 0:
                print(f"  fetched {i + len(batch):,}/{len(taxon_ids):,} taxa...", flush=True)
            time.sleep(0.5)

    print(f"Fetched {len(taxon_data):,} taxa. Backfilling...")

    updated = 0
    with engine.connect() as conn:
        for tid, meta in taxon_data.items():
            conn.execute(text("""
                UPDATE observations
                SET data_payload = data_payload || CAST(:meta AS jsonb)
                WHERE source_type = 'inaturalist' AND taxon_id = :tid
            """), {"tid": tid, "meta": json.dumps(meta)})
            updated += 1

            if updated % 500 == 0:
                conn.commit()
                print(f"  backfilled {updated:,}/{len(taxon_data):,} taxa...", flush=True)
        conn.commit()

    print(f"Done: {updated:,} taxa backfilled")


def backfill_photos():
    """Fetch photo URLs and observation-level fields for all observations."""
    print("\n=== PHOTO + OBSERVATION ENRICHMENT ===")

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT source_id FROM observations
            WHERE source_type = 'inaturalist'
              AND (data_payload->>'photo_url') IS NULL
            ORDER BY source_id::bigint
        """)).fetchall()
        obs_ids = [r[0] for r in rows]
        print(f"Observations needing photos: {len(obs_ids):,}")

    if not obs_ids:
        print("All observations already have photos.")
        return

    updated = 0
    with httpx.Client(timeout=30) as client:
        for i in range(0, len(obs_ids), 200):
            batch = obs_ids[i:i + 200]
            ids_str = ",".join(batch)

            for attempt in range(5):
                try:
                    resp = client.get(f"{API_BASE}/observations", params={
                        "id": ids_str,
                        "per_page": 200,
                    })
                    if resp.status_code == 429:
                        time.sleep(2 ** (attempt + 1))
                        continue
                    resp.raise_for_status()
                    break
                except (httpx.ConnectError, httpx.ReadTimeout):
                    time.sleep(3)
            else:
                continue

            with engine.connect() as conn:
                for obs in resp.json().get("results", []):
                    photos = obs.get("photos", [])
                    photo_url = photos[0].get("url", "").replace("square", "medium") if photos else None
                    photo_license = photos[0].get("license_code") if photos else None

                    meta = {
                        "photo_url": photo_url,
                        "photo_license": photo_license,
                        "photo_count": len(photos),
                        "positional_accuracy": obs.get("positional_accuracy"),
                        "captive": obs.get("captive", False),
                        "obscured": obs.get("obscured", False),
                        "out_of_range": obs.get("out_of_range", False),
                        "time_observed_at": obs.get("time_observed_at"),
                        "user": (obs.get("user") or {}).get("login"),
                    }

                    conn.execute(text("""
                        UPDATE observations
                        SET data_payload = data_payload || CAST(:meta AS jsonb)
                        WHERE source_type = 'inaturalist' AND source_id = :sid
                    """), {"sid": str(obs["id"]), "meta": json.dumps(meta)})
                    updated += 1

                conn.commit()

            if (i // 200) % 25 == 0:
                print(f"  {i + len(batch):,}/{len(obs_ids):,} processed...", flush=True)
            time.sleep(0.6)

    print(f"Done: {updated:,} observations enriched with photos")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--photos-only" in args:
        backfill_photos()
    elif "--taxa-only" in args:
        backfill_taxa()
    else:
        backfill_taxa()
        backfill_photos()
