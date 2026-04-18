"""StreamNet salmon data ingestion adapter.

Uses the public ArcGIS REST services at gis.psmfc.org (no authentication
required) for fish monitoring time series data (spawner counts, redd counts,
abundance estimates) and GBIF for occurrence records from museum collections.
"""

import json
import uuid
from datetime import datetime, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

# Public ArcGIS REST services -- no auth required
ARCGIS_BASE = "https://gis.psmfc.org/server/rest/services/StreamNet"
# Table 5 = Trends4GIS_Escdata (escapement detail with counts)
ESCDATA_URL = f"{ARCGIS_BASE}/Fish_Monitoring_Time_Series_Data/MapServer/5/query"
# Table 4 = Trends4GIS (monitoring locations and metadata)
TRENDS_URL = f"{ARCGIS_BASE}/Fish_Monitoring_Time_Series_Data/MapServer/4/query"
# Layer 0 = point locations
POINTS_URL = f"{ARCGIS_BASE}/Fish_Monitoring_Time_Series_Data/MapServer/0/query"

GBIF_API = "https://api.gbif.org/v1/occurrence/search"

SALMON_SPECIES = [
    "Chinook salmon", "Coho salmon", "Steelhead",
    "Sockeye salmon", "Bull trout", "Pacific lamprey",
]

UPSERT_OBS_SQL = text("""
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

UPSERT_TS_SQL = text("""
    INSERT INTO time_series (
        id, site_id, station_id, parameter, timestamp, value, unit, source_type
    ) VALUES (
        gen_random_uuid(), :site_id, :station_id, :parameter, :timestamp,
        :value, :unit, 'streamnet'
    )
    ON CONFLICT (site_id, station_id, parameter, timestamp) DO UPDATE SET
        value = EXCLUDED.value
""")


class StreamNetAdapter(IngestionAdapter):
    source_type = "streamnet"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        created = 0

        # 1. Fetch fish monitoring time series from ArcGIS (public, no auth)
        c1 = self._ingest_arcgis_monitoring(site)
        created += c1

        # 2. Fetch GBIF fish occurrence records (non-iNaturalist)
        c2 = self._ingest_gbif(site)
        created += c2

        return created, 0

    def _ingest_arcgis_monitoring(self, site: Site) -> int:
        """Fetch spawner counts, redd counts, abundance from StreamNet ArcGIS."""
        bbox = site.bbox
        created = 0

        # Build stream name queries based on watershed
        stream_queries = {
            "klamath": "StreamName LIKE '%Klamath%' OR StreamName LIKE '%Williamson%' OR StreamName LIKE '%Sprague%'",
            "mckenzie": "StreamName LIKE '%McKenzie%'",
            "deschutes": "StreamName LIKE '%Deschutes%' OR StreamName LIKE '%Crooked%'",
            "metolius": "StreamName LIKE '%Metolius%'",
            "skagit": "StreamName LIKE '%Skagit%' OR StreamName LIKE '%Sauk%' OR StreamName LIKE '%Baker%' OR StreamName LIKE '%Suiattle%'",
        }

        where = stream_queries.get(site.watershed, f"StreamName LIKE '%{site.name.split()[0]}%'")

        import time

        with httpx.Client(timeout=120, verify=True) as client:
            console.print("    fetching StreamNet fish monitoring data...")

            offset = 0
            while True:
                resp = None
                for attempt in range(3):
                    try:
                        resp = client.get(TRENDS_URL, params={
                            "where": where,
                            "outFields": "*",
                            "f": "json",
                            "resultRecordCount": 2000,
                            "resultOffset": offset,
                        })
                        break
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        wait = 5 * (attempt + 1)
                        console.print(f"    [yellow]connection error, retrying in {wait}s...[/yellow]")
                        time.sleep(wait)

                if resp is None or resp.status_code != 200:
                    status = resp.status_code if resp else "no response"
                    console.print(f"    [yellow]ArcGIS unavailable ({status}), skipping monitoring data[/yellow]")
                    break

                data = resp.json()
                features = data.get("features", [])
                if not features:
                    break

                console.print(f"    found {len(features)} monitoring records (offset {offset})")

                with engine.connect() as conn:
                    for feat in features:
                        attrs = feat.get("attributes", {})
                        geom = feat.get("geometry", {})

                        species = attrs.get("Species", "")
                        run = attrs.get("Run", "")
                        stream = attrs.get("StreamName", "")
                        data_cat = attrs.get("DataCategory", "")
                        trend_id = attrs.get("TrendsID") or attrs.get("OBJECTID")
                        pop_name = attrs.get("PopulationName", "")

                        lat = geom.get("y")
                        lon = geom.get("x")

                        # Get associated count data from escapement table
                        esc_resp = client.get(ESCDATA_URL, params={
                            "where": f"TrendsID = {trend_id}" if trend_id else "1=0",
                            "outFields": "CountYear,CountValue,CountCILowLim,CountCIUpLim,SampleMethod,MilesSurveyed,TimesSurveyed",
                            "f": "json",
                            "resultRecordCount": 500,
                        })

                        if esc_resp.status_code == 200:
                            esc_data = esc_resp.json()
                            for esc_feat in esc_data.get("features", []):
                                esc = esc_feat.get("attributes", {})
                                year = esc.get("CountYear")
                                count_val = esc.get("CountValue")

                                if not year or count_val is None:
                                    continue

                                # Insert as time series (spawner/redd count per year)
                                param = f"{data_cat}_{species}_{run}".strip("_").replace(" ", "_").lower()
                                station_id = f"sn_{stream}_{pop_name}".replace(" ", "_")[:50]

                                try:
                                    conn.execute(UPSERT_TS_SQL, {
                                        "site_id": str(self.site_id),
                                        "station_id": station_id,
                                        "parameter": param,
                                        "timestamp": f"{int(year)}-01-01",
                                        "value": float(count_val),
                                        "unit": "count",
                                    })
                                    created += 1
                                except Exception:
                                    continue

                    conn.commit()

                if not data.get("exceededTransferLimit"):
                    break
                offset += 2000

        console.print(f"    StreamNet ArcGIS: {created} records")
        return created

    def _ingest_gbif(self, site: Site) -> int:
        """Fetch non-iNaturalist fish occurrence records from GBIF."""
        bbox = site.bbox
        created = 0

        salmon_species = [
            ("Oncorhynchus tshawytscha", "Chinook salmon"),
            ("Oncorhynchus kisutch", "Coho salmon"),
            ("Oncorhynchus mykiss", "Steelhead/Rainbow trout"),
            ("Oncorhynchus nerka", "Sockeye/Kokanee"),
            ("Oncorhynchus clarkii", "Cutthroat trout"),
            ("Salvelinus confluentus", "Bull trout"),
            ("Salvelinus fontinalis", "Brook trout"),
            ("Prosopium williamsoni", "Mountain whitefish"),
            ("Lampetra tridentata", "Pacific lamprey"),
        ]

        with httpx.Client(timeout=30) as client, engine.connect() as conn:
            for sci_name, common_name in salmon_species:
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
                        if rec.get("datasetName", "").startswith("iNaturalist"):
                            continue

                        source_id = f"gbif_{rec.get('key', '')}"
                        event_date = rec.get("eventDate", "")
                        if not event_date:
                            year = rec.get("year")
                            event_date = f"{year}-01-01" if year else "2020-01-01"
                        if len(event_date) == 4 and event_date.isdigit():
                            event_date = f"{event_date}-01-01"

                        try:
                            conn.execute(UPSERT_OBS_SQL, {
                                "site_id": str(self.site_id),
                                "source_type": "gbif_fish",
                                "source_id": source_id,
                                "observed_at": event_date[:10],
                                "taxon_name": rec.get("scientificName", sci_name),
                                "latitude": rec.get("decimalLatitude"),
                                "longitude": rec.get("decimalLongitude"),
                                "quality_grade": "museum_specimen",
                                "data_payload": json.dumps({
                                    "common_name": common_name,
                                    "dataset": rec.get("datasetName"),
                                    "institution": rec.get("institutionCode"),
                                    "basis_of_record": rec.get("basisOfRecord"),
                                }),
                            })
                            created += 1
                        except Exception:
                            continue

                    conn.commit()

                    if data.get("endOfRecords", True):
                        break
                    offset += 300

        if created > 0:
            console.print(f"    GBIF fish records: {created}")
        return created
