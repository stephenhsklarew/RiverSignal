"""StreamNet salmon data ingestion adapter.

StreamNet (streamnet.org) provides coordinated salmon and steelhead
population data for the Pacific Northwest. Their API requires a free
API key from https://api.streamnet.org.

Set STREAMNET_API_KEY environment variable to enable this adapter.
Without a key, it falls back to GBIF salmon occurrence records.
"""

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

STREAMNET_API = "https://api.streamnet.org/api/v1/ca.json"
GBIF_API = "https://api.gbif.org/v1/occurrence/search"

SALMON_SPECIES = [
    ("Oncorhynchus tshawytscha", "Chinook salmon"),
    ("Oncorhynchus kisutch", "Coho salmon"),
    ("Oncorhynchus mykiss", "Steelhead/Rainbow trout"),
    ("Oncorhynchus nerka", "Sockeye/Kokanee"),
    ("Oncorhynchus clarkii", "Cutthroat trout"),
    ("Salvelinus confluentus", "Bull trout"),
    ("Salvelinus fontinalis", "Brook trout"),
    ("Salmo trutta", "Brown trout"),
    ("Prosopium williamsoni", "Mountain whitefish"),
    ("Lampetra tridentata", "Pacific lamprey"),
]

UPSERT_SQL = text("""
    INSERT INTO observations (
        id, site_id, source_type, source_id, observed_at,
        taxon_name, iconic_taxon,
        latitude, longitude,
        location,
        quality_grade, data_payload
    ) VALUES (
        gen_random_uuid(), :site_id, :source_type, :source_id, :observed_at,
        :taxon_name, 'Actinopterygii',
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


class StreamNetAdapter(IngestionAdapter):
    source_type = "streamnet"

    def ingest(self) -> tuple[int, int]:
        api_key = os.environ.get("STREAMNET_API_KEY")
        if api_key:
            return self._ingest_streamnet(api_key)
        else:
            console.print("    [yellow]STREAMNET_API_KEY not set, using GBIF fallback[/yellow]")
            return self._ingest_gbif()

    def _ingest_streamnet(self, api_key: str) -> tuple[int, int]:
        """Ingest from StreamNet Coordinated Assessments API."""
        site = self.session.get(Site, self.site_id)
        if not site:
            raise ValueError(f"Site {self.site_id} not found")

        created = 0
        with httpx.Client(timeout=60) as client:
            # Fetch NOSA (Natural Origin Spawner Abundance) data
            for table_id in ["NOSA", "SAR", "RperS"]:
                page = 1
                while True:
                    resp = client.get(STREAMNET_API, params={
                        "table_id": table_id,
                        "XLoc_State": "OR",
                        "api_key": api_key,
                        "per_page": 500,
                        "page": page,
                    })
                    if resp.status_code != 200:
                        break

                    records = resp.json()
                    if not records:
                        break

                    with engine.connect() as conn:
                        for rec in records:
                            lat = rec.get("Latitude")
                            lon = rec.get("Longitude")
                            bbox = site.bbox
                            if lat and lon:
                                if not (bbox["south"] <= float(lat) <= bbox["north"] and
                                        bbox["west"] <= float(lon) <= bbox["east"]):
                                    continue

                            source_id = f"sn_{table_id}_{rec.get('id', page)}"
                            year = rec.get("SpawningYear") or rec.get("OutmigrationYear") or "2020"

                            conn.execute(UPSERT_SQL, {
                                "site_id": str(self.site_id),
                                "source_type": "streamnet",
                                "source_id": source_id,
                                "observed_at": f"{year}-01-01",
                                "taxon_name": rec.get("CommonName") or rec.get("Species"),
                                "latitude": float(lat) if lat else None,
                                "longitude": float(lon) if lon else None,
                                "quality_grade": "professional",
                                "data_payload": json.dumps({
                                    "table": table_id,
                                    "population": rec.get("CommonPopName"),
                                    "run": rec.get("Run"),
                                    "abundance": rec.get("NOSAij"),
                                    "method": rec.get("MethodNumber"),
                                }),
                            })
                            created += 1

                        conn.commit()

                    console.print(f"    {table_id}: page {page}, {created} total")
                    if len(records) < 500:
                        break
                    page += 1

        return created, 0

    def _ingest_gbif(self) -> tuple[int, int]:
        """Fallback: ingest salmon occurrence records from GBIF."""
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        created = 0

        with httpx.Client(timeout=30) as client, engine.connect() as conn:
            for sci_name, common_name in SALMON_SPECIES:
                offset = 0
                while True:
                    resp = client.get(GBIF_API, params={
                        "scientificName": sci_name,
                        "decimalLatitude": f"{bbox['south']},{bbox['north']}",
                        "decimalLongitude": f"{bbox['west']},{bbox['east']}",
                        "hasCoordinate": "true",
                        "limit": 300,
                        "offset": offset,
                    })
                    if resp.status_code != 200:
                        break

                    data = resp.json()
                    results = data.get("results", [])
                    if not results:
                        break

                    for rec in results:
                        # Skip iNaturalist records (we already have them)
                        if rec.get("datasetName", "").startswith("iNaturalist"):
                            continue

                        source_id = f"gbif_{rec.get('key', '')}"
                        lat = rec.get("decimalLatitude")
                        lon = rec.get("decimalLongitude")
                        event_date = rec.get("eventDate", "")
                        if not event_date:
                            year = rec.get("year")
                            event_date = f"{year}-01-01" if year else "2020-01-01"
                        # Normalize year-only dates
                        if len(event_date) == 4 and event_date.isdigit():
                            event_date = f"{event_date}-01-01"

                        conn.execute(UPSERT_SQL, {
                            "site_id": str(self.site_id),
                            "source_type": "gbif_fish",
                            "source_id": source_id,
                            "observed_at": event_date[:10],
                            "taxon_name": rec.get("scientificName", sci_name),
                            "latitude": lat,
                            "longitude": lon,
                            "quality_grade": rec.get("issues", [""])[0] if rec.get("issues") else "accepted",
                            "data_payload": json.dumps({
                                "common_name": common_name,
                                "dataset": rec.get("datasetName"),
                                "institution": rec.get("institutionCode"),
                                "basis_of_record": rec.get("basisOfRecord"),
                                "catalog_number": rec.get("catalogNumber"),
                            }),
                        })
                        created += 1

                    conn.commit()

                    if data.get("endOfRecords", True):
                        break
                    offset += 300

                if created > 0:
                    console.print(f"    {common_name}: {created} total records")

        return created, 0
