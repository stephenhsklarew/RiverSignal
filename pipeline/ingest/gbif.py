"""GBIF fossil specimen ingestion adapter.

Fetches fossil specimen records from the Global Biodiversity Information
Facility (GBIF) occurrence API. Supplements PBDB and iDigBio data with
additional museum specimens and locality records.

API docs: https://www.gbif.org/developer/occurrence
"""

import json

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

GBIF_URL = "https://api.gbif.org/v1/occurrence/search"

# Map GBIF geological age strings to Ma ranges
PERIOD_AGES = {
    "Quaternary": (0, 2.58), "Holocene": (0, 0.012), "Pleistocene": (0.012, 2.58),
    "Neogene": (2.58, 23), "Pliocene": (2.58, 5.33), "Miocene": (5.33, 23),
    "Paleogene": (23, 66), "Oligocene": (23, 33.9), "Eocene": (33.9, 56),
    "Paleocene": (56, 66), "Cretaceous": (66, 145), "Jurassic": (145, 201),
    "Triassic": (201, 252), "Permian": (252, 299), "Carboniferous": (299, 359),
    "Devonian": (359, 419), "Silurian": (419, 444), "Ordovician": (444, 485),
    "Cambrian": (485, 541),
}

UPSERT_SQL = text("""
    INSERT INTO fossil_occurrences
        (id, source, source_id, taxon_name, taxon_id,
         common_name, phylum, class_name, order_name, family,
         age_min_ma, age_max_ma, period, formation,
         location, latitude, longitude,
         collector, reference, museum, data_payload, site_id)
    VALUES
        (gen_random_uuid(), 'gbif', :source_id, :taxon_name, :taxon_id,
         :common_name, :phylum, :class_name, :order_name, :family,
         :age_min, :age_max, :period, :formation,
         CASE WHEN :lat IS NOT NULL AND :lon IS NOT NULL
              THEN ST_SetSRID(ST_MakePoint(:lon, :lat), 4326) ELSE NULL END,
         :lat, :lon,
         :collector, :reference, :museum, CAST(:payload AS jsonb), :site_id)
    ON CONFLICT (source, source_id) DO UPDATE SET
        taxon_name = EXCLUDED.taxon_name,
        age_min_ma = EXCLUDED.age_min_ma,
        age_max_ma = EXCLUDED.age_max_ma,
        data_payload = EXCLUDED.data_payload,
        site_id = EXCLUDED.site_id
""")


class GBIFFossilAdapter(IngestionAdapter):
    """GBIF fossil specimen occurrences."""
    source_type = "gbif"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            return 0, 0

        bbox = site.bbox
        job = self.create_job()
        created = 0
        updated = 0

        try:
            console.print(f"    Fetching GBIF fossil specimens for {site.watershed}...")

            all_records = []
            offset = 0
            limit = 300

            with httpx.Client(timeout=30) as client:
                while True:
                    params = {
                        "decimalLatitude": f"{bbox['south']},{bbox['north']}",
                        "decimalLongitude": f"{bbox['west']},{bbox['east']}",
                        "basisOfRecord": "FOSSIL_SPECIMEN",
                        "limit": limit,
                        "offset": offset,
                    }
                    resp = client.get(GBIF_URL, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    results = data.get("results", [])
                    all_records.extend(results)

                    if data.get("endOfRecords", True) or len(results) < limit:
                        break
                    offset += limit
                    if offset > 5000:  # safety cap
                        break

            console.print(f"    {len(all_records)} GBIF fossil specimens")

            if not all_records:
                self.complete_job(job, 0, 0)
                return 0, 0

            with engine.connect() as conn:
                batch = 0
                for rec in all_records:
                    gbif_key = str(rec.get("key", ""))
                    if not gbif_key:
                        continue

                    lat = rec.get("decimalLatitude")
                    lon = rec.get("decimalLongitude")
                    taxon = rec.get("scientificName", "") or rec.get("species", "")
                    if not taxon:
                        continue

                    # Extract geological period from GBIF fields
                    period = rec.get("geologicalContext", {}).get("earliestPeriodOrLowestSystem") if isinstance(rec.get("geologicalContext"), dict) else None
                    formation = rec.get("geologicalContext", {}).get("formation") if isinstance(rec.get("geologicalContext"), dict) else None

                    # Try to infer period from verbatim locality or other fields
                    if not period:
                        locality = (rec.get("locality") or "").lower()
                        for p_name in PERIOD_AGES:
                            if p_name.lower() in locality:
                                period = p_name
                                break

                    # Age ranges from period
                    age_min, age_max = None, None
                    if period and period in PERIOD_AGES:
                        age_min, age_max = PERIOD_AGES[period]

                    # Institution as museum
                    inst = rec.get("institutionCode", "")
                    collection = rec.get("collectionCode", "")
                    museum = f"{inst} — {collection}" if collection else inst

                    # Extract image URL from media array
                    image_url = None
                    for media in (rec.get("media") or []):
                        if media.get("type") == "StillImage" and media.get("identifier"):
                            image_url = media["identifier"]
                            break

                    try:
                        conn.execute(UPSERT_SQL, {
                            "source_id": gbif_key,
                            "taxon_name": taxon[:255],
                            "taxon_id": str(rec.get("taxonKey", ""))[:100],
                            "common_name": (rec.get("vernacularName") or "")[:255],
                            "phylum": (rec.get("phylum") or "")[:100],
                            "class_name": (rec.get("class") or "")[:100],
                            "order_name": (rec.get("order") or "")[:100],
                            "family": (rec.get("family") or "")[:100],
                            "age_min": age_min,
                            "age_max": age_max,
                            "period": (period or "")[:100],
                            "formation": (formation or "")[:255],
                            "lat": lat,
                            "lon": lon,
                            "collector": (rec.get("recordedBy") or "")[:255],
                            "reference": (rec.get("bibliographicCitation") or "")[:500],
                            "museum": museum[:255],
                            "payload": json.dumps({
                                "gbifKey": gbif_key,
                                "datasetKey": rec.get("datasetKey"),
                                "institutionCode": inst,
                                "collectionCode": collection,
                                "catalogNumber": rec.get("catalogNumber"),
                                "locality": rec.get("locality"),
                                "year": rec.get("year"),
                                "typeStatus": rec.get("typeStatus"),
                                "basisOfRecord": rec.get("basisOfRecord"),
                                "image_url": image_url,
                            }),
                            "site_id": self.site_id,
                        })
                        created += 1
                    except Exception:
                        continue

                    batch += 1
                    if batch % 200 == 0:
                        conn.commit()
                        console.print(f"    ... {batch} records processed")

                conn.commit()

            # Second pass: fetch records with images to backfill image_url
            img_count = self._backfill_images(client, bbox)
            console.print(f"    [green]GBIF: {created} created, {img_count} images for {site.watershed}[/green]")
            self.complete_job(job, created, updated)

        except Exception as e:
            self.session.rollback()
            job.status = "failed"
            job.error_message = str(e)[:500]
            self.session.commit()
            console.print(f"    [red]GBIF ingestion failed: {e}[/red]")

        return created, updated

    def _backfill_images(self, client, bbox) -> int:
        """Fetch GBIF records that have images and update data_payload."""
        params = {
            "decimalLatitude": f"{bbox['south']},{bbox['north']}",
            "decimalLongitude": f"{bbox['west']},{bbox['east']}",
            "basisOfRecord": "FOSSIL_SPECIMEN",
            "mediaType": "StillImage",
            "limit": 300,
        }
        try:
            resp = client.get(GBIF_URL, params=params)
            resp.raise_for_status()
            records = resp.json().get("results", [])
        except Exception:
            return 0

        updated = 0
        with engine.connect() as conn:
            for rec in records:
                gbif_key = str(rec.get("key", ""))
                media = rec.get("media", [])
                image_url = None
                for m in media:
                    if m.get("type") == "StillImage" and m.get("identifier"):
                        image_url = m["identifier"]
                        break
                if not image_url:
                    continue

                try:
                    conn.execute(text("""
                        UPDATE fossil_occurrences
                        SET data_payload = jsonb_set(
                            COALESCE(data_payload, '{}'),
                            '{image_url}',
                            to_jsonb(CAST(:img AS text))
                        )
                        WHERE source = 'gbif' AND source_id = :sid
                    """), {"img": image_url, "sid": gbif_key})
                    updated += 1
                except Exception:
                    continue
            conn.commit()
        return updated
