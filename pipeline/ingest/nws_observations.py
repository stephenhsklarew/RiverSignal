"""Daily NWS observations ingest into bronze.weather_observations.

For each watershed, finds the nearest NWS observation station to the
watershed centroid (one-time lookup, cached in this module), pulls
yesterday's hourly observations, rolls up to daily aggregates, and
upserts one row keyed on (watershed, date, source_type='nws').

Idempotent: re-running on the same day is a no-op via ON CONFLICT
DO NOTHING.
"""

from __future__ import annotations

import json
import os
from datetime import date, datetime, timedelta, timezone

import httpx
from sqlalchemy import text

from pipeline.db import engine

NWS_BASE = "https://api.weather.gov"
USER_AGENT = "RiverSignal/1.0 (weather-ingest; contact@liquidmarble.com)"

# Watershed centroids — mirrors app/routers/weather.py WS_COORDS.
WS_COORDS: dict[str, tuple[float, float]] = {
    "mckenzie":   (44.08, -122.30),
    "deschutes":  (44.33, -121.22),
    "metolius":   (44.50, -121.57),
    "klamath":    (42.65, -121.55),
    "johnday":    (44.60, -119.15),
    "skagit":     (48.45, -121.50),
    "green_river":(40.50, -109.50),
}


def _nearest_station(client: httpx.Client, lat: float, lon: float) -> str | None:
    """Resolve nearest NWS observation station id for a coordinate."""
    pts = client.get(f"{NWS_BASE}/points/{lat},{lon}")
    pts.raise_for_status()
    stations_url = pts.json()["properties"]["observationStations"]
    sts = client.get(stations_url)
    sts.raise_for_status()
    features = sts.json().get("features", [])
    if not features:
        return None
    # First feature is the nearest by NWS convention
    return features[0]["properties"]["stationIdentifier"]


def _fetch_day_observations(client: httpx.Client, station: str, day: date) -> list[dict]:
    """Fetch hourly observations for `station` on the given UTC date."""
    start = datetime.combine(day, datetime.min.time(), tzinfo=timezone.utc).isoformat()
    end = datetime.combine(day + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc).isoformat()
    resp = client.get(
        f"{NWS_BASE}/stations/{station}/observations",
        params={"start": start, "end": end},
    )
    resp.raise_for_status()
    return resp.json().get("features", [])


def _c_to_f(c: float | None) -> float | None:
    return None if c is None else c * 9.0 / 5.0 + 32.0


def _mm_to_in(mm: float | None) -> float | None:
    return None if mm is None else mm / 25.4


def _kmh_to_mph(k: float | None) -> float | None:
    return None if k is None else k * 0.621371


def _avg(xs: list[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _max(xs: list[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return max(xs) if xs else None


def _min(xs: list[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return min(xs) if xs else None


def _rollup(features: list[dict]) -> dict:
    temps_f, precips_in, winds_mph, gusts_mph, rh, cloud, pressure = [], [], [], [], [], [], []
    for f in features:
        p = f.get("properties", {})
        temps_f.append(_c_to_f((p.get("temperature") or {}).get("value")))
        precips_in.append(_mm_to_in((p.get("precipitationLastHour") or {}).get("value")))
        winds_mph.append(_kmh_to_mph((p.get("windSpeed") or {}).get("value")))
        gusts_mph.append(_kmh_to_mph((p.get("windGust") or {}).get("value")))
        rh.append((p.get("relativeHumidity") or {}).get("value"))
        sky = (p.get("cloudLayers") or [])
        cloud.append(len(sky) * 25.0 if sky else None)  # crude proxy
        pressure.append((p.get("barometricPressure") or {}).get("value"))
    return {
        "temperature_max_f": _max(temps_f),
        "temperature_min_f": _min(temps_f),
        "temperature_avg_f": _avg(temps_f),
        "precipitation_in":  sum([p for p in precips_in if p is not None]) or None,
        "wind_speed_avg_mph": _avg(winds_mph),
        "wind_gust_max_mph":  _max(gusts_mph),
        "relative_humidity_pct": _avg(rh),
        "cloud_cover_avg_pct":  _avg(cloud),
        "pressure_avg_mb": _avg([p / 100.0 if p else None for p in pressure]),  # Pa → mb
    }


def ingest_day(target_day: date | None = None) -> dict[str, int]:
    """Ingest one day per watershed. Returns {watershed: rows_inserted}."""
    if target_day is None:
        target_day = (datetime.now(timezone.utc) - timedelta(days=1)).date()

    results: dict[str, int] = {}
    with httpx.Client(timeout=20.0, headers={"User-Agent": USER_AGENT}) as client:
        for ws, (lat, lon) in WS_COORDS.items():
            try:
                station = _nearest_station(client, lat, lon)
                if not station:
                    results[ws] = 0
                    continue
                features = _fetch_day_observations(client, station, target_day)
                agg = _rollup(features)
                with engine.connect() as conn:
                    conn.execute(
                        text("""
                            INSERT INTO bronze.weather_observations
                                (watershed, date, temperature_max_f, temperature_min_f,
                                 temperature_avg_f, precipitation_in, wind_speed_avg_mph,
                                 wind_gust_max_mph, relative_humidity_pct,
                                 cloud_cover_avg_pct, pressure_avg_mb,
                                 source_type, source_station_id, data_payload)
                            VALUES (:ws, :d, :tmax, :tmin, :tavg, :precip, :wind, :gust,
                                    :rh, :cloud, :pressure, 'nws', :station,
                                    CAST(:payload AS jsonb))
                            ON CONFLICT (watershed, date, source_type) DO NOTHING
                        """),
                        {
                            "ws": ws, "d": target_day, **{
                                "tmax": agg["temperature_max_f"],
                                "tmin": agg["temperature_min_f"],
                                "tavg": agg["temperature_avg_f"],
                                "precip": agg["precipitation_in"],
                                "wind": agg["wind_speed_avg_mph"],
                                "gust": agg["wind_gust_max_mph"],
                                "rh": agg["relative_humidity_pct"],
                                "cloud": agg["cloud_cover_avg_pct"],
                                "pressure": agg["pressure_avg_mb"],
                            },
                            "station": station,
                            "payload": json.dumps({"feature_count": len(features)}),
                        },
                    )
                    conn.commit()
                results[ws] = 1
            except Exception as e:
                # Don't let one watershed kill the whole run
                print(f"[nws] {ws} ingest failed: {e}")
                results[ws] = 0
    return results


if __name__ == "__main__":
    target = None
    if len(os.sys.argv) > 1:
        target = date.fromisoformat(os.sys.argv[1])
    summary = ingest_day(target)
    print(json.dumps(summary, indent=2))
