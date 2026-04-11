"""ODFW fishing data: sport catch harvest, fish habitat distribution, stocking schedule.

Three data sources for recreational fishing use cases:
1. Sport catch CSVs -- monthly salmon/steelhead harvest by waterbody (2019-2025)
2. Fish habitat distribution -- 150 species layers from ODFW ArcGIS
3. Stocking schedule -- weekly trout stocking (HTML scrape)
"""

import csv
import io
import json
import re
import time
from datetime import datetime

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

SPORTCATCH_BASE = "https://www.dfw.state.or.us/resources/fishing/docs/sportcatch"

SPORTCATCH_FILES = {
    "Chinook": "ChinookSalmonByMonthAndWaterbodyCode",
    "Steelhead": "SteelheadByMonthAndWaterbodyCode",
    "Coho": "CohoSalmonByMonthAndWaterbodyCode",
    "Sturgeon": "SturgeonByMonthAndWaterbodyCode",
}

# Location codes for our watersheds (from the CSV data)
WATERSHED_LOCATION_CODES = {
    "klamath": [],  # Not in sport catch data
    "mckenzie": ["155", "158", "223"],  # Below/above Leaburg Dam, Blue R
    "deschutes": ["131", "203"],  # Below/above Sherars Falls
    "metolius": [],  # Not in sport catch data (wild fishery)
}

FHD_BASE = "https://nrimp.dfw.state.or.us/arcgis/rest/services/FHD/OregonFishHabitatDistribution2/FeatureServer"

# Sport fish layers to query
SPORT_FISH_LAYERS = {
    1: "Bull Trout",
    2: "Fall Chinook",
    4: "Spring Chinook",
    7: "Coho",
    11: "Summer Steelhead",
    13: "Winter Steelhead",
    15: "Redband Trout",
    17: "Rainbow Trout",
    19: "Coastal Cutthroat Trout",
    23: "Mountain Whitefish",
    25: "Brook Trout",
    27: "Brown Trout",
}

STOCKING_URL = "https://myodfw.com/fishing/species/trout/stocking-schedule-print"

# Stream name patterns for each watershed
WATERSHED_STREAMS = {
    "klamath": ["Klamath", "Williamson", "Sprague", "Wood R", "Upper Klamath"],
    "mckenzie": ["McKenzie", "Blue R", "Horse Cr", "South Fork McKenzie"],
    "deschutes": ["Deschutes", "Crooked R", "Tumalo", "Fall R"],
    "metolius": ["Metolius", "Lake Cr", "Spring Cr", "Canyon Cr"],
    "johnday": ["John Day", "North Fork John Day", "Middle Fork John Day", "South Fork John Day"],
}


class FishingDataAdapter(IngestionAdapter):
    """Combined adapter for all fishing-related data."""
    source_type = "fishing"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} not found or no bbox")

        created = 0

        c1 = self._ingest_sport_catch(site)
        created += c1

        c2 = self._ingest_fish_habitat(site)
        created += c2

        c3 = self._ingest_stocking(site)
        created += c3

        return created, 0

    def _ingest_sport_catch(self, site: Site) -> int:
        """Download ODFW sport catch CSVs for salmon/steelhead/sturgeon."""
        location_codes = WATERSHED_LOCATION_CODES.get(site.watershed, [])
        if not location_codes:
            console.print(f"    sport catch: no location codes for {site.watershed}")
            return 0

        created = 0
        with httpx.Client(timeout=30, follow_redirects=True) as client:
            console.print("    fetching ODFW sport catch data...")

            for species, file_prefix in SPORTCATCH_FILES.items():
                for year in range(2019, 2026):
                    url = f"{SPORTCATCH_BASE}/{file_prefix}{year}.csv"
                    try:
                        resp = client.get(url)
                        if resp.status_code != 200:
                            continue
                    except httpx.HTTPError:
                        continue

                    reader = csv.DictReader(io.StringIO(resp.text))
                    with engine.connect() as conn:
                        for row in reader:
                            loc_code = str(row.get("Location Code", "")).strip()
                            if loc_code not in location_codes:
                                continue

                            location = row.get("Location", "")
                            total = row.get("Total", "0")
                            try:
                                total_int = int(total.replace(",", ""))
                            except (ValueError, AttributeError):
                                total_int = 0

                            if total_int == 0:
                                continue

                            # Store monthly data as time series
                            months = ["January", "February", "March", "April", "May", "June",
                                      "July", "August", "September", "October", "November", "December"]
                            for i, month in enumerate(months):
                                val = row.get(month, "0")
                                try:
                                    val_int = int(val.replace(",", ""))
                                except (ValueError, AttributeError):
                                    val_int = 0

                                if val_int == 0:
                                    continue

                                ts = f"{year}-{i+1:02d}-15"
                                param = f"sport_catch_{species.lower()}"
                                station = f"odfw_{loc_code}_{location[:30]}".replace(" ", "_")

                                conn.execute(text("""
                                    INSERT INTO time_series (id, site_id, station_id, parameter, timestamp, value, unit, source_type)
                                    VALUES (gen_random_uuid(), :site_id, :station_id, :parameter, :timestamp, :value, 'fish', 'sport_catch')
                                    ON CONFLICT (site_id, station_id, parameter, timestamp) DO UPDATE SET value = EXCLUDED.value
                                """), {
                                    "site_id": str(self.site_id),
                                    "station_id": station,
                                    "parameter": param,
                                    "timestamp": ts,
                                    "value": val_int,
                                })
                                created += 1
                        conn.commit()

            console.print(f"    sport catch: {created} monthly records")

        return created

    def _ingest_fish_habitat(self, site: Site) -> int:
        """Query ODFW Fish Habitat Distribution for sport fish species."""
        streams = WATERSHED_STREAMS.get(site.watershed, [])
        if not streams:
            return 0

        where_clause = " OR ".join(f"fhdStNm LIKE '%{s}%'" for s in streams)
        created = 0

        with httpx.Client(timeout=60) as client:
            console.print("    fetching ODFW fish habitat distribution...")

            for layer_id, species_name in SPORT_FISH_LAYERS.items():
                url = f"{FHD_BASE}/{layer_id}/query"

                for attempt in range(3):
                    try:
                        resp = client.get(url, params={
                            "where": where_clause,
                            "outFields": "fhdStNm,fhdSpNm,fhdRun,fhdUseTy,fhdOrig,fhdLifeHst,fhdBasis,fhdComment",
                            "f": "json",
                            "resultRecordCount": "500",
                        })
                        if resp.status_code == 200:
                            break
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        time.sleep(3)
                else:
                    continue

                features = resp.json().get("features", [])
                if not features:
                    continue

                with engine.connect() as conn:
                    for feat in features:
                        attrs = feat.get("attributes", {})
                        stream = attrs.get("fhdStNm", "")
                        use_type = attrs.get("fhdUseTy", "")
                        origin = attrs.get("fhdOrig", "")
                        life_hist = attrs.get("fhdLifeHst", "")
                        run = attrs.get("fhdRun", "")

                        source_id = f"fhd_{layer_id}_{stream}_{use_type}".replace(" ", "_")[:255]

                        conn.execute(text("""
                            INSERT INTO observations (id, site_id, source_type, source_id, observed_at,
                                taxon_name, iconic_taxon, quality_grade, data_payload)
                            VALUES (gen_random_uuid(), :site_id, 'fish_habitat', :source_id, '2024-01-01',
                                :taxon_name, 'Actinopterygii', 'odfw_official',
                                CAST(:payload AS jsonb))
                            ON CONFLICT (source_type, source_id) DO UPDATE SET
                                data_payload = EXCLUDED.data_payload
                        """), {
                            "site_id": str(self.site_id),
                            "source_id": source_id,
                            "taxon_name": attrs.get("fhdSpNm", species_name),
                            "payload": json.dumps({
                                "stream": stream,
                                "species": species_name,
                                "scientific_name": attrs.get("fhdSpNm", ""),
                                "run": run,
                                "use_type": use_type,
                                "origin": origin,
                                "life_history": life_hist,
                                "basis": attrs.get("fhdBasis", ""),
                                "comment": attrs.get("fhdComment", ""),
                            }),
                        })
                        created += 1
                    conn.commit()

            console.print(f"    fish habitat: {created} distribution records")

        return created

    def _ingest_stocking(self, site: Site) -> int:
        """Scrape ODFW trout stocking schedule."""
        created = 0

        with httpx.Client(timeout=30, follow_redirects=True) as client:
            console.print("    fetching ODFW stocking schedule...")

            try:
                resp = client.get(STOCKING_URL)
                if resp.status_code != 200:
                    console.print("    [yellow]stocking schedule unavailable[/yellow]")
                    return 0
            except httpx.HTTPError:
                return 0

            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', resp.text, re.DOTALL)

            # Match waterbodies in our watershed area by zone
            zone_map = {
                "klamath": "Southeast",
                "mckenzie": "Willamette",
                "deschutes": "Central",
                "metolius": "Central",
            }
            target_zone = zone_map.get(site.watershed, "")

            with engine.connect() as conn:
                for row in rows[1:]:
                    cells = re.findall(r'<td[^>]*>(.*?)</td>', row, re.DOTALL)
                    cells = [re.sub(r'<[^>]+>', '', c).strip() for c in cells]
                    if len(cells) < 8:
                        continue

                    week = cells[0]
                    waterbody = cells[1]
                    zone = cells[2]

                    if target_zone and target_zone.lower() not in zone.lower():
                        continue

                    legals = cells[3].replace(",", "")
                    trophy = cells[4].replace(",", "")
                    brood = cells[5].replace(",", "")
                    fingerling = cells[6].replace(",", "")
                    total = cells[7].replace(",", "")

                    try:
                        total_int = int(total)
                    except ValueError:
                        continue

                    if total_int == 0:
                        continue

                    # Parse week start date
                    date_match = re.search(r'(\w+)\.\s+(\d+),\s+(\d+)', week)
                    if date_match:
                        try:
                            month_str = date_match.group(1)
                            day = date_match.group(2)
                            year = date_match.group(3)
                            month_map = {"Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
                                         "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
                                         "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"}
                            month = month_map.get(month_str, "01")
                            ts = f"{year}-{month}-{day}"
                        except (ValueError, KeyError):
                            ts = "2026-01-01"
                    else:
                        ts = "2026-01-01"

                    station = f"stocking_{waterbody}".replace(" ", "_")[:50]
                    conn.execute(text("""
                        INSERT INTO time_series (id, site_id, station_id, parameter, timestamp, value, unit, source_type)
                        VALUES (gen_random_uuid(), :site_id, :station_id, 'trout_stocked', :timestamp, :value, 'fish', 'stocking')
                        ON CONFLICT (site_id, station_id, parameter, timestamp) DO UPDATE SET value = EXCLUDED.value
                    """), {
                        "site_id": str(self.site_id),
                        "station_id": station,
                        "timestamp": ts,
                        "value": total_int,
                    })
                    created += 1
                conn.commit()

            console.print(f"    stocking: {created} records")

        return created
