"""NRCS SNOTEL snowpack data ingestion adapter."""

import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

API_BASE = "https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1"
STATION_SEARCH_MARGIN = 0.3  # degrees beyond bbox to find nearby stations

ELEMENTS = {
    "WTEQ": ("snow_water_equivalent", "in"),
    "SNWD": ("snow_depth", "in"),
    "PREC": ("precipitation_cumulative", "in"),
    "TOBS": ("air_temperature", "degF"),
    "TAVG": ("air_temperature_avg", "degF"),
    "SMS": ("soil_moisture", "pct"),
    "STO": ("soil_temperature", "degF"),
}


class SNOTELAdapter(IngestionAdapter):
    source_type = "snotel"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox

        if self.from_date is not None:
            start_date = self.from_date.strftime("%Y-%m-%d")
        else:
            last_sync = self.get_last_sync()
            if last_sync:
                start_date = last_sync.strftime("%Y-%m-%d")
            else:
                start_date = (datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d")
        end_date = datetime.now().strftime("%Y-%m-%d")

        # Find SNOTEL stations near this watershed
        stations = self._find_stations(bbox)
        if not stations:
            console.print("    no SNOTEL stations found near this watershed")
            return 0, 0

        console.print(f"    found {len(stations)} SNOTEL stations")

        created = 0
        with httpx.Client(timeout=120) as client:
            # Fetch data for all stations at once
            triplets = ",".join(s["stationTriplet"] for s in stations)

            for elem_code, (param_name, unit) in ELEMENTS.items():
                try:
                    resp = client.get(f"{API_BASE}/data", params={
                        "stationTriplets": triplets,
                        "elements": elem_code,
                        "duration": "DAILY",
                        "beginDate": start_date,
                        "endDate": end_date,
                    })
                    if resp.status_code != 200:
                        continue
                    data = resp.json()
                except Exception:
                    continue

                with engine.connect() as conn:
                    for station_data in data:
                        station_id = station_data.get("stationTriplet", "unknown")
                        for series in station_data.get("data", []):
                            for v in series.get("values", []):
                                if v.get("value") is None:
                                    continue
                                try:
                                    val = float(v["value"])
                                except (ValueError, TypeError):
                                    continue

                                conn.execute(text("""
                                    INSERT INTO time_series (id, site_id, station_id, parameter, timestamp, value, unit, source_type)
                                    VALUES (gen_random_uuid(), :site_id, :station_id, :parameter, :timestamp, :value, :unit, 'snotel')
                                    ON CONFLICT (site_id, station_id, parameter, timestamp) DO UPDATE SET
                                        value = EXCLUDED.value
                                """), {
                                    "site_id": str(self.site_id),
                                    "station_id": station_id,
                                    "parameter": param_name,
                                    "timestamp": v["date"],
                                    "value": val,
                                    "unit": unit,
                                })
                                created += 1

                    conn.commit()
                    console.print(f"    {param_name}: {created} total records so far")

        return created, 0

    def _find_stations(self, bbox: dict) -> list[dict]:
        """Find SNOTEL stations near the watershed bbox."""
        # Determine state from bbox latitude (OR vs WA)
        state_codes = ["OR"]
        if bbox.get("north", 0) > 46:
            state_codes.append("WA")

        all_stations = []
        with httpx.Client(timeout=60) as client:
            for state in state_codes:
                try:
                    resp = client.get(f"{API_BASE}/stations", params={
                        "stateCode": state,
                        "networkCode": "SNTL",
                        "returnFields": "stationTriplet,name,latitude,longitude,elevation",
                    })
                    if resp.status_code == 200:
                        all_stations.extend(resp.json())
                except Exception:
                    pass

        m = STATION_SEARCH_MARGIN
        return [
            s for s in all_stations
            if "SNTL" in s.get("stationTriplet", "")
            and bbox["south"] - m <= s.get("latitude", 0) <= bbox["north"] + m
            and bbox["west"] - m <= s.get("longitude", 0) <= bbox["east"] + m
        ]
