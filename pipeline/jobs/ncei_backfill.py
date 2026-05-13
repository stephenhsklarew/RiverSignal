"""NCEI Climate Data Online 10-year backfill into bronze.weather_observations.

Plan §5 Phase C. One-shot Cloud Run job that pulls NOAA NCEI CDO
daily summaries for each watershed's closest GHCN-Daily station for
the past 10 years. Chunked by year, throttled to NCEI rate limits,
upserts with source_type='ncei'.

Requires NCEI_TOKEN env var. Without it, the job prints what it
*would* fetch and exits — useful for dev / dry-runs.

CDO API: https://www.ncei.noaa.gov/cdo-web/api/v2/data
Rate limits: 5 req/s, 10,000 req/day per token. We chunk by year
to stay well under both.
"""

from __future__ import annotations

import json
import os
import sys
import time
from datetime import date, datetime

import httpx
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.nws_observations import WS_COORDS


CDO_BASE = "https://www.ncei.noaa.gov/cdo-web/api/v2"
DATATYPES = ["TMAX", "TMIN", "PRCP", "AWND", "SNWD"]   # F, F, in, mph, in (after conversion)


def _nearest_ghcn_station(client: httpx.Client, token: str, lat: float, lon: float) -> str | None:
    """Find the nearest GHCN-Daily station via CDO's locations endpoint."""
    r = client.get(
        f"{CDO_BASE}/stations",
        headers={"token": token},
        params={
            "datasetid": "GHCND",
            "extent": f"{lat - 0.5},{lon - 0.5},{lat + 0.5},{lon + 0.5}",
            "limit": 25, "sortfield": "datacoverage", "sortorder": "desc",
        },
        timeout=20,
    )
    r.raise_for_status()
    rows = r.json().get("results", [])
    if not rows:
        return None
    # Highest data coverage wins
    return rows[0]["id"]


def _fetch_year(client: httpx.Client, token: str, station: str, year: int) -> list[dict]:
    """Fetch one year of daily GHCN summaries for a station."""
    r = client.get(
        f"{CDO_BASE}/data",
        headers={"token": token},
        params={
            "datasetid": "GHCND", "stationid": station,
            "startdate": f"{year}-01-01", "enddate": f"{year}-12-31",
            "datatypeid": DATATYPES, "limit": 1000, "units": "standard",
        },
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("results", [])


def _rollup_by_date(records: list[dict]) -> dict[date, dict]:
    """Collapse CDO records into one row per date."""
    by_date: dict[date, dict] = {}
    for rec in records:
        d = datetime.fromisoformat(rec["date"].replace("Z", "+00:00")).date()
        cur = by_date.setdefault(d, {})
        cur[rec["datatype"]] = rec["value"]
    return by_date


def _upsert(conn, watershed: str, station: str, d: date, vals: dict) -> None:
    conn.execute(text("""
        INSERT INTO bronze.weather_observations
            (watershed, date,
             temperature_max_f, temperature_min_f,
             precipitation_in, wind_speed_avg_mph, snow_depth_in,
             source_type, source_station_id, data_payload)
        VALUES (:ws, :d, :tmax, :tmin, :prcp, :wind, :snow, 'ncei', :st,
                CAST(:payload AS jsonb))
        ON CONFLICT (watershed, date, source_type) DO UPDATE
          SET temperature_max_f = EXCLUDED.temperature_max_f,
              temperature_min_f = EXCLUDED.temperature_min_f,
              precipitation_in = EXCLUDED.precipitation_in,
              wind_speed_avg_mph = EXCLUDED.wind_speed_avg_mph,
              snow_depth_in = EXCLUDED.snow_depth_in,
              data_payload = EXCLUDED.data_payload,
              fetched_at = now()
    """), {
        "ws": watershed, "d": d,
        "tmax": vals.get("TMAX"), "tmin": vals.get("TMIN"),
        "prcp": vals.get("PRCP"), "wind": vals.get("AWND"),
        "snow": vals.get("SNWD"),
        "st": station, "payload": json.dumps({"source": "ncei_ghcnd", "raw_datatypes": list(vals.keys())}),
    })


def run(years: int = 10, watersheds: list[str] | None = None) -> dict[str, int]:
    token = os.environ.get("NCEI_TOKEN")
    if not token:
        print("NCEI_TOKEN not set; dry-run only.")
        return {"would_backfill": years * len(watersheds or WS_COORDS), "wrote": 0}

    target_watersheds = watersheds or list(WS_COORDS.keys())
    end_year = datetime.now().year
    start_year = end_year - years
    summary: dict[str, int] = {}

    with httpx.Client(timeout=30.0) as client:
        for ws in target_watersheds:
            lat, lon = WS_COORDS[ws]
            station = _nearest_ghcn_station(client, token, lat, lon)
            if not station:
                summary[ws] = 0
                continue
            wrote = 0
            with engine.connect() as conn:
                for year in range(start_year, end_year + 1):
                    records = _fetch_year(client, token, station, year)
                    by_date = _rollup_by_date(records)
                    for d, vals in by_date.items():
                        _upsert(conn, ws, station, d, vals)
                        wrote += 1
                    conn.commit()
                    time.sleep(0.25)  # 4 req/s, well under 5 req/s limit
            summary[ws] = wrote
    return summary


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
    sys.exit(0)
