"""Water Quality Portal — aquatic macroinvertebrate ingestion.

Fetches biological result data from WQP (waterqualitydata.us) filtered to
aquatic macroinvertebrate assemblages. Targets EPT taxa (Ephemeroptera,
Plecoptera, Trichoptera) plus Chironomidae and other aquatic Diptera.

This supplements the existing BioData adapter by:
  1. Including non-USGS sources (Oregon DEQ, BLM, EPA, tribal agencies)
  2. Better taxonomic classification for hatch chart use
  3. Filling coverage gaps for Metolius and John Day watersheds

WQP API docs: https://www.waterqualitydata.us/webservices_documentation/
"""

import csv as csvmod
import io
import json
import zipfile

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

WQP_BASE = "https://www.waterqualitydata.us"

# Aquatic insect families/orders for classification
AQUATIC_INSECT_TAXA = {
    # Ephemeroptera (mayflies)
    "ephemeroptera", "baetis", "baetidae", "ephemerella", "ephemerellidae",
    "drunella", "heptageniidae", "heptagenia", "rhithrogena", "epeorus",
    "cinygmula", "paraleptophlebia", "leptophlebiidae", "callibaetis",
    "hexagenia", "siphlonurus", "ameletus", "serratella", "tricorythodes",
    "timpanoga", "acentrella", "diphetor",
    # Trichoptera (caddisflies)
    "trichoptera", "hydropsyche", "hydropsychidae", "brachycentrus",
    "brachycentridae", "rhyacophila", "rhyacophilidae", "glossosoma",
    "glossosomatidae", "dicosmoecus", "limnephilidae", "limnephilus",
    "lepidostoma", "lepidostomatidae", "helicopsyche", "mystacides",
    "oecetis", "micrasema", "dolophilodes", "arctopsyche", "cheumatopsyche",
    # Plecoptera (stoneflies)
    "plecoptera", "pteronarcys", "pteronarcyidae", "hesperoperla",
    "acroneuria", "perlidae", "perlodidae", "sweltsa", "chloroperlidae",
    "skwala", "claassenia", "isoperla", "alloperla", "nemouridae",
    "zapada", "yoraperla", "malenka", "despaxia",
    # Diptera: aquatic families
    "chironomidae", "chironominae", "orthocladiinae", "tanytarsini",
    "simuliidae", "simulium", "tipulidae", "tipula", "athericidae",
    "ceratopogonidae", "empididae", "blephariceridae",
}

# Map taxon keywords to insect order
ORDER_MAP = {
    "ephemeroptera": "Ephemeroptera",
    "baetis": "Ephemeroptera", "baetidae": "Ephemeroptera",
    "ephemerella": "Ephemeroptera", "drunella": "Ephemeroptera",
    "heptageni": "Ephemeroptera", "rhithrogena": "Ephemeroptera",
    "callibaetis": "Ephemeroptera", "paraleptophlebia": "Ephemeroptera",
    "cinygmula": "Ephemeroptera", "epeorus": "Ephemeroptera",
    "hexagenia": "Ephemeroptera", "ameletus": "Ephemeroptera",
    "trichoptera": "Trichoptera",
    "hydropsyche": "Trichoptera", "brachycentrus": "Trichoptera",
    "rhyacophila": "Trichoptera", "glossosoma": "Trichoptera",
    "dicosmoecus": "Trichoptera", "limnephil": "Trichoptera",
    "lepidostoma": "Trichoptera", "helicopsyche": "Trichoptera",
    "plecoptera": "Plecoptera",
    "pteronarcys": "Plecoptera", "hesperoperla": "Plecoptera",
    "sweltsa": "Plecoptera", "skwala": "Plecoptera",
    "acroneuria": "Plecoptera", "isoperla": "Plecoptera",
    "zapada": "Plecoptera", "yoraperla": "Plecoptera",
    "chironomid": "Diptera", "simulii": "Diptera",
    "tipul": "Diptera", "ceratopogon": "Diptera",
}

UPSERT_SQL = text("""
    INSERT INTO observations (
        id, site_id, source_type, source_id, observed_at,
        taxon_name, iconic_taxon,
        latitude, longitude,
        location,
        quality_grade, data_payload
    ) VALUES (
        gen_random_uuid(), :site_id, 'wqp_bugs', :source_id, :observed_at,
        :taxon_name, 'Insecta',
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


class WQPBugsAdapter(IngestionAdapter):
    """Ingest aquatic macroinvertebrate data from the Water Quality Portal."""

    source_type = "wqp_bugs"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            return 0, 0

        bbox = site.bbox
        last_sync = self.get_last_sync()
        start_date = last_sync.strftime("%m-%d-%Y") if last_sync else "01-01-1990"

        job = self.create_job()
        created = 0
        updated = 0
        skipped = 0

        try:
            # Query WQP for biological results with assemblage filters
            params = {
                "bBox": f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
                "startDateLo": start_date,
                "sampleMedia": "Biological",
                "assemblage": "Benthic Macroinvertebrates",
                "mimeType": "csv",
                "zip": "yes",
                "sorted": "no",
                "dataProfile": "biological",
            }

            console.print(f"    Fetching WQP macroinvertebrate data for {site.watershed}...")

            with httpx.Client(timeout=600, follow_redirects=True) as client:
                resp = client.get(f"{WQP_BASE}/data/Result/search", params=params)

            if resp.status_code == 204:
                console.print("    No macroinvertebrate data found")
                self.complete_job(job, 0, 0)
                return 0, 0

            if resp.status_code != 200:
                console.print(f"    [yellow]WQP returned {resp.status_code}[/yellow]")
                self.complete_job(job, 0, 0)
                return 0, 0

            # Parse CSV (may be zipped)
            content_type = resp.headers.get("content-type", "")
            if "zip" in content_type or resp.content[:2] == b"PK":
                zf = zipfile.ZipFile(io.BytesIO(resp.content))
                csv_name = [n for n in zf.namelist() if n.endswith(".csv")][0]
                csv_text = zf.read(csv_name).decode("utf-8", errors="replace")
            else:
                csv_text = resp.text

            reader = csvmod.DictReader(io.StringIO(csv_text))
            rows_list = list(reader)
            console.print(f"    {len(rows_list)} raw biological records")

            with engine.connect() as conn:
                batch = 0
                for row in rows_list:
                    taxon = row.get("SubjectTaxonomicName", "").strip()
                    if not taxon:
                        skipped += 1
                        continue

                    # Filter to aquatic insect taxa only
                    taxon_lower = taxon.lower()
                    is_aquatic = any(t in taxon_lower for t in AQUATIC_INSECT_TAXA)
                    assemblage = (row.get("AssemblageSampledName", "") or "").lower()
                    if not is_aquatic and "macroinvertebrate" not in assemblage:
                        skipped += 1
                        continue

                    station = row.get("MonitoringLocationIdentifier", "")
                    activity_id = row.get("ActivityIdentifier", "")
                    date_str = row.get("ActivityStartDate", "")
                    if not date_str:
                        skipped += 1
                        continue

                    lat = row.get("ActivityLocation/LatitudeMeasure", "")
                    lon = row.get("ActivityLocation/LongitudeMeasure", "")
                    try:
                        lat_f = float(lat) if lat else None
                        lon_f = float(lon) if lon else None
                    except (ValueError, TypeError):
                        lat_f, lon_f = None, None

                    source_id = f"wqpbug_{station}_{activity_id}_{taxon}".replace(" ", "_")[:255]

                    # Determine insect order
                    insect_order = None
                    for keyword, order in ORDER_MAP.items():
                        if keyword in taxon_lower:
                            insect_order = order
                            break

                    payload = {
                        "station": station,
                        "activity_id": activity_id,
                        "assemblage": row.get("AssemblageSampledName", ""),
                        "characteristic": row.get("CharacteristicName", ""),
                        "value": row.get("ResultMeasureValue", ""),
                        "unit": row.get("ResultMeasure/MeasureUnitCode", ""),
                        "method": row.get("SampleCollectionMethod/MethodIdentifier", ""),
                        "subject_taxon": taxon,
                        "insect_order": insect_order,
                        "tolerance": row.get("TaxonomicPollutionTolerance", ""),
                        "feeding_group": row.get("FunctionalFeedingGroupName", ""),
                        "trophic_level": row.get("TrophicLevelName", ""),
                        "taxon_order": insect_order,
                        "provider": row.get("ProviderName", ""),
                        "org": row.get("OrganizationIdentifier", ""),
                    }

                    try:
                        result = conn.execute(UPSERT_SQL, {
                            "site_id": str(self.site_id),
                            "source_id": source_id,
                            "observed_at": date_str,
                            "taxon_name": taxon,
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
                        console.print(f"    ... {batch} records processed")

                conn.commit()

            console.print(f"    [green]WQP bugs: {created} created, {skipped} skipped (non-aquatic)[/green]")
            self.complete_job(job, created, updated)

        except Exception as e:
            self.session.rollback()
            job.status = "failed"
            job.error_message = str(e)[:500]
            self.session.commit()
            console.print(f"    [red]WQP bugs ingestion failed: {e}[/red]")

        return created, updated
