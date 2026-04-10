"""USGS BioData ingestion via Water Quality Portal biological results endpoint.

BioData macroinvertebrate and fish community survey data is accessible through
the WQP biological result profile. This captures professional sampling data
(EPT indices, community composition) that is higher quality than citizen science.
"""

import json
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

WQP_BASE = "https://www.waterqualitydata.us"

UPSERT_SQL = text("""
    INSERT INTO observations (
        id, site_id, source_type, source_id, observed_at,
        taxon_name, iconic_taxon,
        latitude, longitude,
        location,
        quality_grade, data_payload
    ) VALUES (
        gen_random_uuid(), :site_id, 'biodata', :source_id, :observed_at,
        :taxon_name, :iconic_taxon,
        :latitude, :longitude,
        CASE WHEN :latitude IS NOT NULL AND :longitude IS NOT NULL
             THEN ST_SetSRID(ST_MakePoint(:longitude, :latitude), 4326)
             ELSE NULL END,
        'professional', CAST(:data_payload AS jsonb)
    )
    ON CONFLICT (source_type, source_id) DO UPDATE SET
        taxon_name = EXCLUDED.taxon_name,
        data_payload = EXCLUDED.data_payload
""")


class BioDataAdapter(IngestionAdapter):
    source_type = "biodata"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        last_sync = self.get_last_sync()

        if last_sync:
            start_date = last_sync.strftime("%m-%d-%Y")
        else:
            start_date = "01-01-2000"

        created = 0

        # Fetch biological results from WQP
        params = {
            "bBox": f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
            "startDateLo": start_date,
            "sampleMedia": "Biological",
            "dataProfile": "biological",
            "mimeType": "csv",
            "zip": "no",
            "sorted": "no",
        }

        with httpx.Client(timeout=600, follow_redirects=True) as client:
            console.print("    fetching WQP biological data (may be large)...")

            url = f"{WQP_BASE}/data/Result/search"
            resp = None
            try:
                resp = client.get(url, params=params)
            except httpx.HTTPError as e:
                console.print(f"    [yellow]WQP error: {e}[/yellow]")
                return 0, 0

            if resp is None or resp.status_code not in (200, 204):
                console.print(f"    [yellow]WQP returned {resp.status_code if resp else 'no response'}[/yellow]")
                return 0, 0
            if resp.status_code == 204:
                console.print("    no biological data found")
                return 0, 0

            # Handle zip response
            content_type = resp.headers.get("content-type", "")
            if "zip" in content_type or resp.content[:2] == b"PK":
                import io, zipfile
                zf = zipfile.ZipFile(io.BytesIO(resp.content))
                csv_name = [n for n in zf.namelist() if n.endswith(".csv")][0]
                csv_text = zf.read(csv_name).decode("utf-8", errors="replace")
            else:
                csv_text = resp.text

            import csv as csvmod
            import io

            reader = csvmod.DictReader(io.StringIO(csv_text))
            rows_list = list(reader)
            if not rows_list:
                console.print("    no biological records")
                return 0, 0

            console.print(f"    parsing {len(rows_list)} biological records...")

            with engine.connect() as conn:
                batch = 0
                for row in rows_list:
                    station = row.get("MonitoringLocationIdentifier", "")
                    activity_id = row.get("ActivityIdentifier", "")
                    date_str = row.get("ActivityStartDate", "")
                    taxon = row.get("SubjectTaxonomicName", "")
                    char_name = row.get("CharacteristicName", "")
                    result_val = row.get("ResultMeasureValue", "")
                    result_unit = row.get("ResultMeasure/MeasureUnitCode", "")
                    sample_method = row.get("SampleCollectionMethod/MethodIdentifier", "")
                    assemblage = row.get("AssemblageSampledName", "")
                    lat = row.get("ActivityLocation/LatitudeMeasure", "")
                    lon = row.get("ActivityLocation/LongitudeMeasure", "")

                    if not date_str:
                        continue

                    source_id = f"bio_{station}_{activity_id}_{taxon or char_name}".replace(" ", "_")[:255]

                    try:
                        lat_f = float(lat) if lat else None
                        lon_f = float(lon) if lon else None
                    except (ValueError, TypeError):
                        lat_f, lon_f = None, None

                    iconic = _classify_taxon(taxon, char_name, assemblage)

                    payload = {
                        "station": station,
                        "activity_id": activity_id,
                        "assemblage": assemblage,
                        "characteristic": char_name,
                        "value": result_val,
                        "unit": result_unit,
                        "method": sample_method,
                        "subject_taxon": taxon,
                        "group_count": row.get("GroupSummaryCountWeight/MeasureValue", ""),
                        "tolerance": row.get("TaxonomicPollutionTolerance", ""),
                        "feeding_group": row.get("FunctionalFeedingGroupName", ""),
                        "trophic_level": row.get("TrophicLevelName", ""),
                    }

                    try:
                        conn.execute(UPSERT_SQL, {
                            "site_id": str(self.site_id),
                            "source_id": source_id,
                            "observed_at": date_str,
                            "taxon_name": taxon,
                            "iconic_taxon": iconic,
                            "latitude": lat_f,
                            "longitude": lon_f,
                            "data_payload": json.dumps(payload),
                        })
                        created += 1
                    except Exception:
                        continue

                    batch += 1
                    if batch % 500 == 0:
                        conn.commit()

                conn.commit()

        return created, 0


def _get(fields: list, col: dict, name: str) -> str | None:
    idx = col.get(name, -1)
    if idx < 0 or idx >= len(fields):
        return None
    val = fields[idx].strip()
    return val if val else None


def _classify_taxon(taxon: str | None, char_name: str | None, assemblage: str | None = None) -> str | None:
    if not taxon and not char_name and not assemblage:
        return None
    text = (taxon or "") + " " + (char_name or "") + " " + (assemblage or "")
    text_lower = text.lower()
    if any(w in text_lower for w in ["ephemeroptera", "plecoptera", "trichoptera", "chironomidae", "macroinvertebrate", "benthic"]):
        return "Insecta"
    if any(w in text_lower for w in ["fish", "salmo", "oncorhynchus", "cottus", "rhinichthys"]):
        return "Actinopterygii"
    if any(w in text_lower for w in ["amphibia", "rana", "frog", "salamander"]):
        return "Amphibia"
    if any(w in text_lower for w in ["mollusc", "gastropod", "bivalv"]):
        return "Mollusca"
    return None


def _parse_csv_line(line: str) -> list[str]:
    fields = []
    current = []
    in_quotes = False
    for char in line:
        if char == '"':
            in_quotes = not in_quotes
        elif char == "," and not in_quotes:
            fields.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    fields.append("".join(current).strip())
    return fields
