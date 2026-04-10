"""Oregon Water Data Portal (OWRD) ingestion adapter.

Uses the Oregon Water Resources Department water quality data via their
WQP (Water Quality Portal) compatible endpoint.
"""

import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy.dialects.postgresql import insert

from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site, TimeSeries

# Water Quality Portal API (EPA/USGS/NWQMC partnership, includes Oregon data)
WQP_BASE = "https://www.waterqualitydata.us"

# Common water quality parameters
CHARACTERISTIC_NAMES = [
    "Dissolved oxygen (DO)",
    "Temperature, water",
    "pH",
    "Phosphorus",
    "Chlorophyll a",
    "Turbidity",
    "Specific conductance",
    "Nitrogen, total",
]


class OWDPAdapter(IngestionAdapter):
    source_type = "owdp"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        last_sync = self.get_last_sync()

        if last_sync:
            start_date = last_sync.strftime("%m-%d-%Y")
        else:
            start_date = (datetime.now() - timedelta(days=365 * 5)).strftime(
                "%m-%d-%Y"
            )

        created = 0
        updated = 0

        params = {
            "bBox": f"{bbox['west']},{bbox['south']},{bbox['east']},{bbox['north']}",
            "startDateLo": start_date,
            "mimeType": "csv",
            "dataProfile": "narrowResult",
            "zip": "no",
        }

        with httpx.Client(timeout=300, follow_redirects=True) as client:
            console.print("    fetching Water Quality Portal data...")

            # Try WQP v3 API first, fall back to legacy
            urls = [
                f"{WQP_BASE}/wqx3/Result/search",
                f"{WQP_BASE}/data/Result/search",
            ]

            resp = None
            for url in urls:
                try:
                    resp = client.get(url, params=params)
                    if resp.status_code == 200:
                        break
                    if resp.status_code == 204:
                        console.print("    no water quality data found in this area")
                        return 0, 0
                except httpx.HTTPError:
                    continue

            if resp is None or resp.status_code != 200:
                console.print("    [yellow]WQP API unavailable, skipping[/yellow]")
                return 0, 0

            lines = resp.text.strip().split("\n")
            if len(lines) < 2:
                console.print("    no water quality records returned")
                return 0, 0

            # Parse CSV header
            header = lines[0].split(",")
            header = [h.strip('"') for h in header]

            # Find column indices
            col_map = {}
            for i, h in enumerate(header):
                col_map[h] = i

            station_col = col_map.get("MonitoringLocationIdentifier", -1)
            char_col = col_map.get("CharacteristicName", -1)
            value_col = col_map.get("ResultMeasureValue", -1)
            unit_col = col_map.get("ResultMeasure/MeasureUnitCode", -1)
            date_col = col_map.get("ActivityStartDate", -1)
            time_col = col_map.get("ActivityStartTime/Time", -1)

            if any(c == -1 for c in [station_col, char_col, value_col, date_col]):
                console.print(
                    "    [yellow]warning: unexpected CSV format from WQP[/yellow]"
                )
                return 0, 0

            console.print(f"    parsing {len(lines) - 1} water quality records...")

            for line in lines[1:]:
                fields = _parse_csv_line(line)
                if len(fields) <= max(station_col, char_col, value_col, date_col):
                    continue

                station_id = fields[station_col]
                char_name = fields[char_col]
                raw_value = fields[value_col]
                unit = fields[unit_col] if unit_col < len(fields) else "unknown"
                date_str = fields[date_col]
                time_str = fields[time_col] if time_col >= 0 and time_col < len(fields) else ""

                try:
                    val = float(raw_value)
                except (ValueError, TypeError):
                    continue

                try:
                    if time_str:
                        ts_dt = datetime.fromisoformat(f"{date_str}T{time_str}")
                    else:
                        ts_dt = datetime.fromisoformat(date_str)
                    if ts_dt.tzinfo is None:
                        ts_dt = ts_dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue

                # Normalize parameter name
                param = _normalize_param(char_name)

                values = {
                    "site_id": self.site_id,
                    "station_id": station_id,
                    "parameter": param,
                    "timestamp": ts_dt,
                    "value": val,
                    "unit": unit,
                    "source_type": "owdp",
                    "quality_flag": None,
                }

                stmt = insert(TimeSeries).values(**values)
                stmt = stmt.on_conflict_do_update(
                    index_elements=[
                        "site_id", "station_id", "parameter", "timestamp"
                    ],
                    set_={
                        "value": stmt.excluded.value,
                        "unit": stmt.excluded.unit,
                    },
                )
                result = self.session.execute(stmt)
                if result.rowcount > 0:
                    created += 1

            self.session.flush()

        return created, updated


def _normalize_param(char_name: str) -> str:
    """Normalize WQP characteristic names to shorter parameter names."""
    mapping = {
        "Dissolved oxygen (DO)": "dissolved_oxygen",
        "Dissolved oxygen": "dissolved_oxygen",
        "Temperature, water": "temperature",
        "pH": "ph",
        "Phosphorus": "phosphorus",
        "Total Phosphorus, mixed forms": "phosphorus",
        "Chlorophyll a": "chlorophyll_a",
        "Chlorophyll a, corrected for pheophytin": "chlorophyll_a",
        "Turbidity": "turbidity",
        "Specific conductance": "specific_conductance",
        "Specific Conductance": "specific_conductance",
        "Nitrogen": "nitrogen",
        "Nitrogen, total": "nitrogen",
    }
    return mapping.get(char_name, char_name.lower().replace(" ", "_").replace(",", ""))


def _parse_csv_line(line: str) -> list[str]:
    """Simple CSV line parser handling quoted fields."""
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
