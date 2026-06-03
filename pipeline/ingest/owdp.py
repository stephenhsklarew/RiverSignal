"""Oregon Water Data Portal (OWRD) ingestion adapter.

Uses the Oregon Water Resources Department water quality data via their
WQP (Water Quality Portal) compatible endpoint.
"""

import time
import uuid
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
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

        # Self-heal: if last_sync is set but this site has NO WQ rows, last_sync
        # was poisoned by a prior run that advanced it without landing data
        # (e.g. a transient WQP outage before the raise-on-failure fix). Ignore
        # it and pull the full window so the back-fill actually happens — lets
        # prod recover on the next cron with no manual last_sync reset.
        # (RiverSignal-06b25aed)
        existing_rows = self.session.execute(
            select(func.count()).select_from(TimeSeries).where(
                TimeSeries.site_id == self.site_id,
                TimeSeries.source_type == "owdp",
            )
        ).scalar() or 0

        if last_sync and existing_rows > 0:
            start_date = last_sync.strftime("%m-%d-%Y")
        else:
            if last_sync and existing_rows == 0:
                console.print(
                    "    [yellow]owdp: last_sync set but 0 WQ rows — forcing full back-fill window[/yellow]"
                )
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

            # WQP is frequently overloaded and returns transient 5xx ("system
            # may be overloaded"); the wqx3 profile also 500s for narrowResult.
            # Retry each endpoint on 5xx / network errors before falling through
            # to the next. Without this, a transient blip lands 0 rows silently
            # (observed onboarding mad_river_oh — WQP had 187 OH stations but the
            # batch run caught an overload window). See verification report.
            resp = None
            for url in urls:
                got_ok = False
                for attempt in range(3):
                    try:
                        r = client.get(url, params=params)
                        if r.status_code == 200:
                            resp = r
                            got_ok = True
                            break
                        if r.status_code == 204:
                            console.print("    no water quality data found in this area")
                            return 0, 0
                        # 5xx → transient, back off and retry this url
                        if r.status_code >= 500:
                            time.sleep(3 * (attempt + 1))
                            continue
                        # other 4xx → don't retry this url, try the next
                        break
                    except httpx.HTTPError:
                        time.sleep(3 * (attempt + 1))
                        continue
                if got_ok:
                    break

            if resp is None or resp.status_code != 200:
                # RAISE (don't return 0,0) so run() marks the job failed and
                # last_sync is NOT advanced. Returning here let a transient WQP
                # outage advance last_sync to "now", so every later run did an
                # empty incremental window and never back-filled — the root
                # cause of the ipswich_river_ma wqp=0 bead (RiverSignal-06b25aed).
                raise RuntimeError("WQP API unavailable after retries; not advancing last_sync")

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

            data_lines = lines[1:]
            # Sample mode (local staging): cap how many WQP rows we parse.
            if self.sample_limit is not None:
                data_lines = data_lines[: self.sample_limit]

            for line in data_lines:
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
                self.session.execute(stmt)
                # rowcount is unreliable for ON CONFLICT upserts (the driver may
                # report -1), which made every run log "0 created" even when
                # thousands of rows landed. Count rows written instead.
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
