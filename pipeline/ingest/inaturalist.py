"""iNaturalist observation ingestion adapter."""

import time
import uuid
from datetime import datetime, timezone

import httpx
from geoalchemy2 import WKTElement
from sqlalchemy.dialects.postgresql import insert

from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Observation, Site

API_BASE = "https://api.inaturalist.org/v1"
PAGE_SIZE = 200
RATE_LIMIT_DELAY = 0.6  # seconds between requests (100 req/min limit)


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
        updated = 0
        total_fetched = 0
        last_id = 0

        with httpx.Client(timeout=30) as client:
            while True:
                if last_id > 0:
                    params["id_above"] = last_id

                resp = client.get(f"{API_BASE}/observations", params=params)
                resp.raise_for_status()
                data = resp.json()

                results = data.get("results", [])
                if not results:
                    break

                for obs in results:
                    c, u = self._upsert_observation(obs)
                    created += c
                    updated += u
                    last_id = obs["id"]

                total_fetched += len(results)
                console.print(
                    f"    fetched {total_fetched}/{data.get('total_results', '?')} "
                    f"observations...",
                    end="\r",
                )

                if len(results) < PAGE_SIZE:
                    break

                # Commit in batches
                if total_fetched % 1000 == 0:
                    self.session.flush()

                time.sleep(RATE_LIMIT_DELAY)

        console.print()  # newline after progress
        self.session.flush()
        return created, updated

    def _upsert_observation(self, obs: dict) -> tuple[int, int]:
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

        location = None
        if lat is not None and lon is not None:
            location = WKTElement(f"POINT({lon} {lat})", srid=4326)

        values = {
            "site_id": self.site_id,
            "source_type": "inaturalist",
            "source_id": source_id,
            "observed_at": observed_dt,
            "taxon_name": taxon.get("name"),
            "taxon_id": taxon.get("id"),
            "taxon_rank": taxon.get("rank"),
            "iconic_taxon": taxon.get("iconic_taxon_name"),
            "location": location,
            "latitude": lat,
            "longitude": lon,
            "quality_grade": obs.get("quality_grade"),
            "data_payload": {
                "species_guess": obs.get("species_guess"),
                "place_guess": obs.get("place_guess"),
                "uri": obs.get("uri"),
                "photos": len(obs.get("photos", [])),
                "num_identification_agreements": obs.get(
                    "num_identification_agreements", 0
                ),
            },
        }

        stmt = insert(Observation).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_type", "source_id"],
            set_={
                "taxon_name": stmt.excluded.taxon_name,
                "taxon_id": stmt.excluded.taxon_id,
                "taxon_rank": stmt.excluded.taxon_rank,
                "quality_grade": stmt.excluded.quality_grade,
                "data_payload": stmt.excluded.data_payload,
            },
        )

        self.session.execute(stmt)
        return 1, 0
