"""eBird observation ingestion adapter.

Uses the eBird API v2 to pull bird observation data. Much more comprehensive
than iNaturalist for birds -- includes structured checklist data, breeding
codes, and enables absence detection.

Requires EBIRD_API_KEY environment variable (free from https://ebird.org/api/keygen).
"""

import json
import os
import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

API_BASE = "https://api.ebird.org/v2"

UPSERT_SQL = text("""
    INSERT INTO observations (
        id, site_id, source_type, source_id, observed_at,
        taxon_name, taxon_rank, iconic_taxon,
        latitude, longitude,
        location,
        quality_grade, data_payload
    ) VALUES (
        gen_random_uuid(), :site_id, 'ebird', :source_id, :observed_at,
        :taxon_name, :taxon_rank, 'Aves',
        :latitude, :longitude,
        CASE WHEN :latitude IS NOT NULL AND :longitude IS NOT NULL
             THEN ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
             ELSE NULL END,
        :quality_grade, CAST(:data_payload AS jsonb)
    )
    ON CONFLICT (source_type, source_id) DO UPDATE SET
        taxon_name = EXCLUDED.taxon_name,
        data_payload = EXCLUDED.data_payload
""")


class EBirdAdapter(IngestionAdapter):
    source_type = "ebird"

    def ingest(self) -> tuple[int, int]:
        api_key = os.environ.get("EBIRD_API_KEY")
        if not api_key:
            console.print("    [yellow]EBIRD_API_KEY not set. Get a free key from https://ebird.org/api/keygen[/yellow]")
            return 0, 0

        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        last_sync = self.get_last_sync()

        headers = {"X-eBirdApiToken": api_key}
        created = 0

        # eBird API only returns recent observations (last 30 days) via the
        # geo endpoint. For historical data, we use the /data/obs endpoint
        # with back parameter (max 30 days back).
        #
        # Strategy: query a grid of points within the bbox to cover the
        # watershed area. eBird /obs/geo/recent returns observations within
        # a radius (max 50km) of a lat/lng point.

        # Create grid of query points
        lat_step = 0.3  # ~33km
        lng_step = 0.4  # ~33km at these latitudes
        points = []
        lat = bbox["south"]
        while lat <= bbox["north"]:
            lng = bbox["west"]
            while lng <= bbox["east"]:
                points.append((round(lat, 4), round(lng, 4)))
                lng += lng_step
            lat += lat_step

        console.print(f"    querying {len(points)} grid points (30-day window)...")

        with httpx.Client(timeout=30, headers=headers) as client, engine.connect() as conn:
            for i, (lat, lng) in enumerate(points):
                # Fetch recent observations near this point
                for attempt in range(3):
                    try:
                        resp = client.get(f"{API_BASE}/data/obs/geo/recent", params={
                            "lat": lat,
                            "lng": lng,
                            "dist": 25,  # km radius
                            "back": 30,  # days back
                            "cat": "species",  # species-level only
                            "includeProvisional": "true",
                            "maxResults": 10000,
                        })
                        if resp.status_code == 429:
                            time.sleep(5)
                            continue
                        resp.raise_for_status()
                        break
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        time.sleep(3)
                        continue
                else:
                    continue

                observations = resp.json()
                for obs in observations:
                    sub_id = obs.get("subId", "")
                    sp_code = obs.get("speciesCode", "")
                    source_id = f"eb_{sub_id}_{sp_code}"

                    obs_dt = obs.get("obsDt", "")
                    if len(obs_dt) == 10:
                        obs_dt = obs_dt  # date only
                    elif not obs_dt:
                        continue

                    obs_lat = obs.get("lat")
                    obs_lng = obs.get("lng")

                    # Skip observations outside our bbox
                    if obs_lat and obs_lng:
                        if not (bbox["south"] <= obs_lat <= bbox["north"] and
                                bbox["west"] <= obs_lng <= bbox["east"]):
                            continue

                    how_many = obs.get("howMany")

                    try:
                        conn.execute(UPSERT_SQL, {
                            "site_id": str(self.site_id),
                            "source_id": source_id,
                            "observed_at": obs_dt[:10],
                            "taxon_name": obs.get("sciName"),
                            "taxon_rank": "species",
                            "latitude": obs_lat,
                            "longitude": obs_lng,
                            "quality_grade": "ebird_reviewed" if obs.get("obsReviewed") else "ebird_unreviewed",
                            "data_payload": json.dumps({
                                "common_name": obs.get("comName"),
                                "species_code": sp_code,
                                "count": how_many,
                                "location_name": obs.get("locName"),
                                "checklist_id": sub_id,
                                "location_private": obs.get("locationPrivate", False),
                                "obs_valid": obs.get("obsValid"),
                            }),
                        })
                        created += 1
                    except Exception:
                        continue

                conn.commit()
                console.print(
                    f"    point {i+1}/{len(points)}: {len(observations)} obs, "
                    f"{created} total...",
                    end="\r",
                )
                time.sleep(0.5)  # Rate limit: ~100 req/hr for free tier

        console.print()
        return created, 0
