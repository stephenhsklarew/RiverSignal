"""Weather, real-time conditions, and snowpack endpoints."""

import time
from fastapi import APIRouter, HTTPException
import httpx
from sqlalchemy import text
from pipeline.db import engine

router = APIRouter(tags=["weather"])

# Watershed center coordinates
WS_COORDS = {
    "mckenzie": (44.08, -122.30),
    "deschutes": (44.33, -121.22),
    "metolius": (44.50, -121.57),
    "klamath": (42.65, -121.55),
    "johnday": (44.60, -119.15),
    "skagit": (48.45, -121.50),
    "green_river": (40.50, -109.50),  # Dinosaur National Monument area
}

# USGS gauge station IDs per watershed (primary stations)
WS_GAUGES = {
    "mckenzie": ["14159500", "14162500"],    # McKenzie River at Vida, near Coburg
    "deschutes": ["14070500", "14076500"],    # Deschutes at Bend, at Madras
    "metolius": ["14091500"],                  # Metolius River near Grandview
    "klamath": ["11502500", "11493500"],       # Williamson River, Sprague River
    "johnday": ["14048000", "14046000"],       # John Day at Service Creek, at Dayville
    "skagit": ["12189500", "12200500"],        # Skagit nr Concrete, nr Mount Vernon
    "green_river": ["09234500", "09315000"],   # Green River nr Greendale UT (Flaming Gorge tailwater), at Green River UT (Desolation/Gray)
}

# Simple in-memory cache: {key: (timestamp, data)}
_cache: dict[str, tuple[float, dict]] = {}
CACHE_TTL = 1800  # 30 minutes


def _cached(key: str, ttl: int = CACHE_TTL):
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < ttl:
        return entry[1]
    return None


def _set_cache(key: str, data: dict):
    _cache[key] = (time.time(), data)


@router.get("/sites/{watershed}/weather")
def get_weather(watershed: str):
    """7-day weather forecast from NWS API."""
    coords = WS_COORDS.get(watershed)
    if not coords:
        raise HTTPException(404, f"Watershed '{watershed}' not found")

    cache_key = f"weather:{watershed}"
    cached = _cached(cache_key)
    if cached:
        return cached

    lat, lon = coords
    headers = {"User-Agent": "RiverSignal/1.0 (watershed-monitoring)"}

    try:
        with httpx.Client(timeout=10, headers=headers) as client:
            # Step 1: Get forecast URL from NWS points API
            points = client.get(f"https://api.weather.gov/points/{lat},{lon}")
            points.raise_for_status()
            forecast_url = points.json()["properties"]["forecast"]

            # Step 2: Get forecast
            forecast = client.get(forecast_url)
            forecast.raise_for_status()
            periods = forecast.json()["properties"]["periods"]
    except Exception as e:
        raise HTTPException(502, f"NWS API error: {e}")

    result = {
        "watershed": watershed,
        "periods": [
            {
                "name": p["name"],
                "temperature": p["temperature"],
                "unit": p["temperatureUnit"],
                "forecast": p["shortForecast"],
                "detail": p["detailedForecast"],
                "wind_speed": p["windSpeed"],
                "wind_direction": p["windDirection"],
                "is_daytime": p["isDaytime"],
                "icon": p["icon"],
            }
            for p in periods[:8]  # 4 days (day + night)
        ],
    }
    _set_cache(cache_key, result)
    return result


@router.get("/sites/{watershed}/conditions/live")
def get_live_conditions(watershed: str):
    """Real-time stream gauge readings from USGS instantaneous values API."""
    gauges = WS_GAUGES.get(watershed)
    if not gauges:
        raise HTTPException(404, f"Watershed '{watershed}' not found")

    cache_key = f"live:{watershed}"
    cached = _cached(cache_key, ttl=900)  # 15 min cache
    if cached:
        return cached

    sites_param = ",".join(gauges)
    # Parameter codes: 00060=discharge, 00010=water temp, 00300=dissolved oxygen
    url = (
        f"https://waterservices.usgs.gov/nwis/iv/"
        f"?format=json&sites={sites_param}"
        f"&parameterCd=00060,00010,00300&siteStatus=active"
    )

    try:
        with httpx.Client(timeout=15) as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
    except Exception as e:
        raise HTTPException(502, f"USGS API error: {e}")

    time_series = data.get("value", {}).get("timeSeries", [])

    readings = []
    for ts in time_series:
        site_info = ts.get("sourceInfo", {})
        variable = ts.get("variable", {})
        values = ts.get("values", [{}])[0].get("value", [])
        if not values:
            continue

        latest = values[-1]
        param_code = variable.get("variableCode", [{}])[0].get("value", "")
        param_name = {
            "00060": "discharge_cfs",
            "00010": "water_temp_c",
            "00300": "dissolved_oxygen_mg_l",
        }.get(param_code, param_code)

        try:
            val = float(latest["value"])
        except (ValueError, TypeError):
            continue

        # Convert water temp to Fahrenheit for display
        display_val = val
        if param_name == "water_temp_c":
            display_val = round(val * 9 / 5 + 32, 1)

        readings.append({
            "station": site_info.get("siteName", ""),
            "station_id": site_info.get("siteCode", [{}])[0].get("value", ""),
            "parameter": param_name,
            "value": val,
            "display_value": display_val,
            "unit": "°F" if param_name == "water_temp_c" else variable.get("unit", {}).get("unitAbbreviation", ""),
            "timestamp": latest.get("dateTime", ""),
        })

    result = {
        "watershed": watershed,
        "readings": readings,
        "gauge_count": len(gauges),
    }
    _set_cache(cache_key, result)
    return result


# ── Snowpack ──

def _snowpack_insight(pct_normal, swe, swe_change, month):
    """Generate a fishing-relevant insight from snowpack conditions."""
    if swe is None or swe == 0:
        if month >= 6:
            return "Snowpack depleted — river flows now depend on springs and groundwater. Fish morning and evening when water is coolest."
        return "No snow at this station. Check higher-elevation stations for snowpack status."

    melting = swe_change is not None and swe_change < -0.3
    building = swe_change is not None and swe_change > 0.3

    if pct_normal is not None and pct_normal > 130:
        if melting:
            return "Big melt underway — rivers running high and cold. Fish pushed to bank edges and eddies. Use heavy nymphs and streamers."
        return "Heavy snowpack — expect high flows and late runoff. Spring fishing will be delayed but summer flows should be excellent."
    elif pct_normal is not None and pct_normal > 90:
        if melting:
            return "Steady melt — rivers should fish well as flows gradually drop. Good conditions for dry-dropper rigs."
        return "Normal snowpack — on track for a healthy summer flow season."
    elif pct_normal is not None and pct_normal > 50:
        return "Below-average snowpack — expect lower summer flows and warmer water earlier. Fish early season for best conditions."
    elif pct_normal is not None:
        return "Drought conditions — summer will bring low flows and thermal stress. Target cold-water refuges and fish early morning."
    elif melting:
        return "Snowpack melting — rising river flows expected. Nymph fishing should be productive as bugs get dislodged."
    elif building:
        return "Snow still accumulating — spring runoff hasn't peaked. Expect high water for several more weeks."
    return "Snowpack data available — check trends to plan your fishing season."


@router.get("/sites/{watershed}/snowpack")
def get_snowpack(watershed: str):
    """Current snowpack conditions from SNOTEL stations."""
    from datetime import datetime
    month = datetime.now().month

    with engine.connect() as conn:
        try:
            rows = conn.execute(text("""
                SELECT station_id, snow_depth_in, swe_in, precip_cumulative_in,
                       air_temp_f, latest_timestamp, swe_7day_change, pct_of_normal
                FROM gold.snowpack_current
                WHERE watershed = :ws
                ORDER BY swe_in DESC NULLS LAST
            """), {"ws": watershed}).fetchall()
        except Exception:
            return {"watershed": watershed, "stations": [], "insight": None}

    if not rows:
        return {"watershed": watershed, "stations": [], "insight": None}

    stations = []
    for r in rows:
        stations.append({
            "station_id": r[0],
            "snow_depth_in": r[1],
            "swe_in": r[2],
            "precip_cumulative_in": r[3],
            "air_temp_f": r[4],
            "latest_timestamp": str(r[5]) if r[5] else None,
            "swe_7day_change": round(r[6], 1) if r[6] is not None else None,
            "pct_of_normal": int(r[7]) if r[7] is not None else None,
        })

    # Generate insight from the station with most snow
    top = stations[0]
    insight = _snowpack_insight(top["pct_of_normal"], top["swe_in"], top["swe_7day_change"], month)

    # Summary stats
    active = [s for s in stations if s["swe_in"] and s["swe_in"] > 0]
    avg_swe = sum(s["swe_in"] for s in active) / len(active) if active else 0
    pcts = [s["pct_of_normal"] for s in active if s["pct_of_normal"]]
    avg_pct = sum(pcts) / len(pcts) if pcts else None

    return {
        "watershed": watershed,
        "stations": stations[:5],
        "station_count": len(rows),
        "stations_with_snow": len(active),
        "avg_swe_in": round(avg_swe, 1),
        "avg_pct_normal": int(avg_pct) if avg_pct else None,
        "insight": insight,
    }
