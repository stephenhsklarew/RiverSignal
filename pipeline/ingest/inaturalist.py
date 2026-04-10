"""iNaturalist observation ingestion adapter."""

import time
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

API_BASE = "https://api.inaturalist.org/v1"
PAGE_SIZE = 200
RATE_LIMIT_DELAY = 0.6  # seconds between requests (100 req/min limit)

UPSERT_SQL = text("""
    INSERT INTO observations (
        id, site_id, source_type, source_id, observed_at,
        taxon_name, taxon_id, taxon_rank, iconic_taxon,
        location, latitude, longitude, quality_grade, data_payload
    ) VALUES (
        gen_random_uuid(), :site_id, 'inaturalist', :source_id, :observed_at,
        :taxon_name, :taxon_id, :taxon_rank, :iconic_taxon,
        CASE WHEN :latitude IS NOT NULL AND :longitude IS NOT NULL
             THEN ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
             ELSE NULL END,
        :latitude, :longitude, :quality_grade, CAST(:data_payload AS jsonb)
    )
    ON CONFLICT (source_type, source_id) DO UPDATE SET
        taxon_name = EXCLUDED.taxon_name,
        taxon_id = EXCLUDED.taxon_id,
        taxon_rank = EXCLUDED.taxon_rank,
        quality_grade = EXCLUDED.quality_grade,
        data_payload = EXCLUDED.data_payload
""")


class INaturalistAdapter(IngestionAdapter):
    source_type = "inaturalist"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        last_sync = self.get_last_sync()

        params = {
            "nelat": bbox["north"],
            "nelng": bbox["east"],
            "swlat": bbox["south"],
            "swlng": bbox["west"],
            "quality_grade": "research,needs_id",
            "per_page": PAGE_SIZE,
            "order": "asc",
            "order_by": "id",
        }

        if last_sync:
            params["d1"] = last_sync.strftime("%Y-%m-%d")

        created = 0
        total_fetched = 0
        last_id = 0

        with httpx.Client(timeout=30) as client, engine.connect() as conn:
            while True:
                if last_id > 0:
                    params["id_above"] = last_id

                for attempt in range(5):
                    resp = client.get(f"{API_BASE}/observations", params=params)
                    if resp.status_code == 429:
                        wait = 2 ** (attempt + 1)
                        console.print(f"    [yellow]rate limited, waiting {wait}s...[/yellow]")
                        time.sleep(wait)
                        continue
                    resp.raise_for_status()
                    break
                else:
                    resp.raise_for_status()
                data = resp.json()

                results = data.get("results", [])
                if not results:
                    break

                for obs in results:
                    row = self._parse_observation(obs)
                    conn.execute(UPSERT_SQL, row)
                    last_id = obs["id"]

                conn.commit()
                created += len(results)
                total_fetched += len(results)
                console.print(
                    f"    fetched {total_fetched}/{data.get('total_results', '?')} "
                    f"observations...",
                    end="\r",
                )

                if len(results) < PAGE_SIZE:
                    break

                time.sleep(RATE_LIMIT_DELAY)

        console.print()
        return created, 0

    def _parse_observation(self, obs: dict) -> dict:
        import json

        source_id = str(obs["id"])
        lat = obs.get("geojson", {}).get("coordinates", [None, None])[1] if obs.get("geojson") else None
        lon = obs.get("geojson", {}).get("coordinates", [None, None])[0] if obs.get("geojson") else None

        taxon = obs.get("taxon") or {}
        observed_at = obs.get("observed_on_details", {}).get("date")
        if not observed_at:
            observed_at = obs.get("created_at", "")

        try:
            observed_dt = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            observed_dt = datetime.now(timezone.utc)

        return {
            "site_id": str(self.site_id),
            "source_id": source_id,
            "observed_at": observed_dt,
            "taxon_name": taxon.get("name"),
            "taxon_id": taxon.get("id"),
            "taxon_rank": taxon.get("rank"),
            "iconic_taxon": taxon.get("iconic_taxon_name"),
            "latitude": lat,
            "longitude": lon,
            "quality_grade": obs.get("quality_grade"),
            "data_payload": json.dumps({
                "species_guess": obs.get("species_guess"),
                "place_guess": obs.get("place_guess"),
                "uri": obs.get("uri"),
                "photos": len(obs.get("photos", [])),
                "num_identification_agreements": obs.get(
                    "num_identification_agreements", 0
                ),
            }),
        }
