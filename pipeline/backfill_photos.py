"""Backfill photo URLs for existing iNaturalist observations.

Fetches photo URLs from iNaturalist API by observation ID and updates
data_payload with photo_url, photo_license, and photo_count.

Usage: python -m pipeline.backfill_photos
"""

import json
import time

import httpx
from sqlalchemy import text

from pipeline.db import engine

API_BASE = "https://api.inaturalist.org/v1"


def backfill():
    with engine.connect() as conn:
        # Get all iNaturalist source_ids (observation IDs) that lack photo_url
        rows = conn.execute(text("""
            SELECT source_id FROM observations
            WHERE source_type = 'inaturalist'
              AND (data_payload->>'photo_url' IS NULL
                   OR data_payload->>'photo_url' = '')
            ORDER BY source_id::int
        """)).fetchall()
        obs_ids = [r[0] for r in rows]
        print(f"Observations needing photo URLs: {len(obs_ids):,}")

    # Fetch in batches of 200 (iNaturalist max per_page)
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
                        "fields": "id,photos",
                    })
                    if resp.status_code == 429:
                        wait = 2 ** (attempt + 1)
                        print(f"  rate limited, waiting {wait}s...")
                        time.sleep(wait)
                        continue
                    resp.raise_for_status()
                    break
                except (httpx.ConnectError, httpx.ReadTimeout):
                    time.sleep(3)
            else:
                continue

            results = resp.json().get("results", [])

            with engine.connect() as conn:
                for obs in results:
                    obs_id = str(obs["id"])
                    photos = obs.get("photos", [])
                    if not photos:
                        continue

                    photo_url = photos[0].get("url", "").replace("square", "medium")
                    photo_license = photos[0].get("license_code")

                    photo_meta = json.dumps({
                        "photo_url": photo_url,
                        "photo_license": photo_license,
                        "photo_count": len(photos),
                    })

                    conn.execute(text("""
                        UPDATE observations
                        SET data_payload = data_payload || CAST(:meta AS jsonb)
                        WHERE source_type = 'inaturalist' AND source_id = :sid
                    """), {"sid": obs_id, "meta": photo_meta})
                    updated += 1

                conn.commit()

            if (i // 200) % 50 == 0:
                print(f"  {i + len(batch):,}/{len(obs_ids):,} processed, {updated:,} updated...", flush=True)
            time.sleep(0.6)

    print(f"\nDone: {updated:,} observations updated with photo URLs")


if __name__ == "__main__":
    backfill()
