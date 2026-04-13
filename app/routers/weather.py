"""Weather and real-time conditions endpoints.

NWS 7-day forecast and USGS instantaneous gauge readings — both are
pass-through API calls (no database storage), cached briefly.
"""

import time
from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter(tags=["weather"])

# Watershed center coordinates
WS_COORDS = {
    "mckenzie": (44.08, -122.30),
    "deschutes": (44.33, -121.22),
    "metolius": (44.50, -121.57),
    "klamath": (42.65, -121.55),
    "johnday": (44.60, -119.15),
}

# USGS gauge station IDs per watershed (primary stations)
WS_GAUGES = {
    "mckenzie": ["14159500", "14162500"],    # McKenzie River at Vida, near Coburg
    "deschutes": ["14070500", "14076500"],    # Deschutes at Bend, at Madras
    "metolius": ["14091500"],                  # Metolius River near Grandview
    "klamath": ["11502500", "11493500"],       # Williamson River, Sprague River
    "johnday": ["14048000", "14046000"],       # John Day at Service Creek, at Dayville
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
