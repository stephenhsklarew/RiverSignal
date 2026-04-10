"""USGS Water Services ingestion adapter."""

import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.dialects.postgresql import insert

from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site, TimeSeries

API_BASE = "https://waterservices.usgs.gov/nwis"

# USGS parameter codes
PARAM_CODES = {
    "00060": ("discharge", "ft3/s"),
    "00010": ("temperature", "degC"),
    "00300": ("dissolved_oxygen", "mg/L"),
    "00065": ("gage_height", "ft"),
    "00400": ("ph", "std_units"),
    "00095": ("specific_conductance", "uS/cm"),
}


class USGSAdapter(IngestionAdapter):
    source_type = "usgs"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        last_sync = self.get_last_sync()

        # Default to last 30 days for initial sync, or since last sync
        if last_sync:
            start_date = last_sync.strftime("%Y-%m-%d")
        else:
            start_date = (datetime.now() - timedelta(days=365 * 2)).strftime("%Y-%m-%d")

        end_date = datetime.now().strftime("%Y-%m-%d")

        created = 0
        updated = 0

        # Fetch daily values (more complete historical data than instantaneous)
        params = {
            "format": "json",
            "bBox": f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
            "startDT": start_date,
            "endDT": end_date,
            "siteType": "ST",
            "siteStatus": "all",
            "parameterCd": ",".join(PARAM_CODES.keys()),
        }

        with httpx.Client(timeout=120) as client:
            console.print("    fetching USGS daily values...")
            resp = client.get(f"{API_BASE}/dv/", params=params)
            resp.raise_for_status()
            data = resp.json()

            time_series_list = data.get("value", {}).get("timeSeries", [])
            console.print(
                f"    found {len(time_series_list)} time series from USGS"
            )

            for ts in time_series_list:
                source_info = ts.get("sourceInfo", {})
                station_id = source_info.get("siteCode", [{}])[0].get("value", "unknown")
                variable = ts.get("variable", {})
                param_code = variable.get("variableCode", [{}])[0].get("value", "")
                param_name, unit = PARAM_CODES.get(
                    param_code, (param_code, "unknown")
                )

                values_list = ts.get("values", [{}])[0].get("value", [])

                for v in values_list:
                    try:
                        val = float(v.get("value", ""))
                    except (ValueError, TypeError):
                        continue

                    # Skip nodata values (USGS uses -999999)
                    if val <= -999999:
                        continue

                    ts_dt = datetime.fromisoformat(
                        v["dateTime"].replace("Z", "+00:00")
                    )
                    qualifier = v.get("qualifiers", [""])[0] if v.get("qualifiers") else None

                    values = {
                        "site_id": self.site_id,
                        "station_id": station_id,
                        "parameter": param_name,
                        "timestamp": ts_dt,
                        "value": val,
                        "unit": unit,
                        "source_type": "usgs",
                        "quality_flag": qualifier,
                    }

                    stmt = insert(TimeSeries).values(**values)
                    stmt = stmt.on_conflict_do_update(
                        index_elements=[
                            "site_id", "station_id", "parameter", "timestamp"
                        ],
                        set_={
                            "value": stmt.excluded.value,
                            "quality_flag": stmt.excluded.quality_flag,
                        },
                    )
                    self.session.execute(stmt)
                    created += 1

                # Flush per station to avoid large pending sets
                self.session.flush()

        return created, updated
