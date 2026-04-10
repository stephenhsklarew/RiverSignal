"""PRISM climate data ingestion adapter.

Downloads gridded climate data (800m resolution) from Oregon State's
PRISM Climate Group. Extracts daily values at watershed grid points
for precipitation, temperature, and vapor pressure deficit.

Data source: https://data.prism.oregonstate.edu/time_series/
"""

import io
import os
import tempfile
import zipfile
from datetime import datetime, timedelta, timezone

import httpx
import rasterio
from sqlalchemy import text

from pipeline.db import engine
from pipeline.ingest.base import IngestionAdapter, console
from pipeline.models import Site

PRISM_BASE = "https://data.prism.oregonstate.edu/time_series/us/an/800m"

# Variables to fetch
VARIABLES = {
    "ppt": ("precipitation", "mm"),
    "tmax": ("temperature_max", "degC"),
    "tmin": ("temperature_min", "degC"),
    "tmean": ("temperature_mean", "degC"),
}

UPSERT_SQL = text("""
    INSERT INTO time_series (id, site_id, station_id, parameter, timestamp, value, unit, source_type)
    VALUES (gen_random_uuid(), :site_id, :station_id, :parameter, :timestamp, :value, :unit, 'prism')
    ON CONFLICT (site_id, station_id, parameter, timestamp) DO UPDATE SET value = EXCLUDED.value
""")


class PRISMAdapter(IngestionAdapter):
    source_type = "prism"

    def ingest(self) -> tuple[int, int]:
        site = self.session.get(Site, self.site_id)
        if not site or not site.bbox:
            raise ValueError(f"Site {self.site_id} has no bounding box configured")

        bbox = site.bbox
        last_sync = self.get_last_sync()

        # Date range: last 2 years for initial, or since last sync
        if last_sync:
            start = last_sync.date()
        else:
            start = (datetime.now() - timedelta(days=365 * 2)).date()

        end = (datetime.now() - timedelta(days=2)).date()  # PRISM has ~1 day lag

        # Generate grid of sample points within the bbox (every ~0.05 degrees = ~5km)
        points = []
        step = 0.05
        lat = bbox["south"]
        while lat <= bbox["north"]:
            lon = bbox["west"]
            while lon <= bbox["east"]:
                station_id = f"prism_{lat:.2f}_{lon:.2f}"
                points.append((lat, lon, station_id))
                lon += step
            lat += step

        console.print(f"    {len(points)} grid points, {(end - start).days} days, {len(VARIABLES)} variables")

        created = 0
        current = start

        with httpx.Client(timeout=120) as client:
            while current <= end:
                date_str = current.strftime("%Y%m%d")
                year = current.strftime("%Y")

                for var_code, (param_name, unit) in VARIABLES.items():
                    filename = f"prism_{var_code}_us_30s_{date_str}.zip"
                    url = f"{PRISM_BASE}/{var_code}/daily/{year}/{filename}"

                    try:
                        resp = client.get(url, timeout=120)
                        if resp.status_code != 200:
                            continue
                    except (httpx.ConnectError, httpx.ReadTimeout):
                        continue

                    # Extract and sample the raster
                    try:
                        values = self._sample_raster(resp.content, points)
                    except Exception:
                        continue

                    with engine.connect() as conn:
                        for (lat, lon, station_id), val in zip(points, values):
                            if val is None or val < -900:  # nodata
                                continue
                            conn.execute(UPSERT_SQL, {
                                "site_id": str(self.site_id),
                                "station_id": station_id,
                                "parameter": param_name,
                                "timestamp": current.isoformat(),
                                "value": round(val, 2),
                                "unit": unit,
                            })
                            created += 1
                        conn.commit()

                console.print(
                    f"    {current} ({created:,} records)...",
                    end="\r",
                )
                current += timedelta(days=1)

        console.print()
        return created, 0

    def _sample_raster(self, zip_content: bytes, points: list) -> list:
        """Extract values from a PRISM zip at the given lat/lon points."""
        with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
            tif_name = [n for n in zf.namelist() if n.endswith(".tif")][0]

            with tempfile.TemporaryDirectory() as tmpdir:
                zf.extractall(tmpdir)
                tif_path = os.path.join(tmpdir, tif_name)

                with rasterio.open(tif_path) as src:
                    coords = [(lon, lat) for lat, lon, _ in points]
                    return [v[0] for v in src.sample(coords)]
