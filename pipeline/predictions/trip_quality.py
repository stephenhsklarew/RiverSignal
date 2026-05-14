"""Trip Quality Score (TQS) v0.5 compute.

Produces one TQS row per (reach_id, target_date) in the requested date
range. v0.5 implements 5 of the 6 sub-scores (skips weather — added in
Phase B per plan §5). Weather weight is redistributed across the other 5
in this phase (0.20 each).

See docs/helix/02-design/plan-2026-05-11-trip-quality-score.md §3.5.

Sub-score functions are scalar / piecewise linear and pure Python — they
take primitive inputs so they can be unit-tested without a database.
The orchestrator (compute_trip_quality_daily) handles DB lookups.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Iterable

from sqlalchemy import text

from pipeline.db import engine


# ── v0.5 weights (weather is skipped, its 0.15 redistributed) ──────────────
W_V05 = {
    "catch":       0.30,   # 0.25 + ~half of weather slice
    "water_temp":  0.175,
    "flow":        0.175,
    "hatch":       0.175,
    "access":      0.175,
}
# v1 weights (with weather) — kept here for the Phase B switch
W_V1 = {
    "catch":       0.25,
    "water_temp":  0.15,
    "flow":        0.15,
    "weather":     0.15,
    "hatch":       0.15,
    "access":      0.15,
}


# ── Pure sub-score functions (unit-testable) ────────────────────────────────

def water_temp_score(temp_f: float | None, is_warm_water: bool = False) -> int:
    """Piecewise water-temp suitability for trout (default) or warm-water reaches.

    Trout: ideal 50-60°F; hard floor 0 above 70°F or below 40°F.
    Warm-water: ideal 60-75°F; hard floor 0 above 85°F or below 32°F.
    """
    if temp_f is None:
        return 50  # neutral when unknown
    if is_warm_water:
        if temp_f >= 85 or temp_f <= 32:
            return 0
        if 60 <= temp_f <= 75:
            return 100
        if temp_f < 60:
            return max(0, int(100 - (60 - temp_f) * 4))
        return max(0, int(100 - (temp_f - 75) * 8))
    # Trout / cold-water default
    if temp_f >= 70 or temp_f <= 40:
        return 0
    if 50 <= temp_f <= 60:
        return 100
    if temp_f < 50:
        return max(0, int(100 - (50 - temp_f) * 10))
    return max(0, int(100 - (temp_f - 60) * 10))


def flow_score(cfs: float | None, low: int, ideal_low: int, ideal_high: int, high: int) -> int:
    """Piecewise flow suitability; 100 inside [ideal_low, ideal_high]."""
    if cfs is None:
        return 50
    if cfs < low or cfs > high:
        return 0
    if ideal_low <= cfs <= ideal_high:
        return 100
    if cfs < ideal_low:
        return int(100 * (cfs - low) / max(1, ideal_low - low))
    return int(100 * (high - cfs) / max(1, high - ideal_high))


def hatch_score(target_date: date, hatch_windows: list[tuple[int, int]]) -> int:
    """Score is 100 if target month falls inside any (start_month, end_month)
    window; otherwise scales with proximity to the nearest window edge."""
    m = target_date.month
    if not hatch_windows:
        return 30  # baseline: no hatches in catalogue for this reach/watershed
    for start, end in hatch_windows:
        if start <= end:
            if start <= m <= end:
                return 100
        else:  # wraps year
            if m >= start or m <= end:
                return 100
    # Outside any window: pick the nearest edge and decay
    best = 30
    for start, end in hatch_windows:
        d_start = min(abs(m - start), 12 - abs(m - start))
        d_end   = min(abs(m - end),   12 - abs(m - end))
        d = min(d_start, d_end)
        best = max(best, max(0, 70 - d * 20))
    return int(best)


def weather_score(temp_f: float | None, precip_in: float | None,
                  wind_mph: float | None, wind_bearing: int | None,
                  reach_flow_bearing: int | None, thunderstorm: bool = False) -> int:
    """Full weather sub-score per plan §4.

    weather = 100 − temp_penalty − precip_penalty − wind_speed_penalty
              − wind_direction_penalty − thunderstorm_penalty
    """
    if temp_f is None and precip_in is None and wind_mph is None:
        # No forecast / observation data → neutral score
        return 50
    if thunderstorm:
        # Lightning + fly rod is bad news; the rest of the score is moot.
        return max(0, 100 - 40)

    score = 100.0

    # Temperature: ideal 50-75°F; 1pt/°F outside that band, cap −30
    if temp_f is not None:
        if temp_f < 50:
            penalty = min(30, 50 - temp_f)
        elif temp_f > 75:
            penalty = min(30, temp_f - 75)
        else:
            penalty = 0
        score -= penalty

    # Precipitation: 0-0.25 ideal, 0.25-0.75 mild, > 0.75 heavy
    if precip_in is not None:
        if precip_in > 0.75:
            score -= 25
        elif precip_in > 0.25:
            score -= 10

    # Wind speed: < 10 ideal, 10-15 mild, > 15 heavy
    if wind_mph is not None:
        if wind_mph > 15:
            score -= 15
        elif wind_mph >= 10:
            score -= 5

        # Wind direction penalty only meaningful at wind ≥ 10 mph
        if wind_mph >= 10 and wind_bearing is not None and reach_flow_bearing is not None:
            delta = ((wind_bearing - reach_flow_bearing) + 360) % 360
            # Penalty curve from §4 wind-direction subsection
            if 30 <= delta <= 90 or 270 <= delta <= 330:  # quartering
                score -= 0.5 * wind_mph
            elif 90 < delta <= 150 or 210 <= delta < 270:  # cross
                score -= 1.0 * wind_mph
            elif 150 < delta < 210:  # upstream-in-face
                score -= 2.0 * wind_mph
            # 0 ± 30° (downstream) gets no extra penalty

    return max(0, min(100, int(round(score))))


def access_score(active_fire_intersects: bool, regulation_closed: bool,
                 partial_access: bool = False) -> tuple[int, bool, bool]:
    """Returns (score, is_hard_closed, partial_access_flag)."""
    if active_fire_intersects or regulation_closed:
        return (0, True, partial_access)
    if partial_access:
        return (80, False, True)
    return (100, False, False)


def catch_score(species_predicted: bool, base: int = 60) -> int:
    """v0.5 stub. Real implementation queries gold.predictions for the
    species typical of this reach + a window around target_date. For now,
    return a base score boosted when a prediction exists for the watershed."""
    return min(100, base + (15 if species_predicted else 0))


# ── Climatological water temperature proxy (until USGS gauge integration) ──
# Monthly average water temp in °F by latitude bin. Crude but produces sane
# values in the right ranges. To be replaced with USGS gauge readings in a
# follow-up bead.
def proxy_water_temp_f(target_date: date, lat: float) -> float:
    """Estimate water temperature from latitude + month (climatology stub)."""
    m = target_date.month
    # Seasonal amplitude (warmer in summer); higher latitudes = colder year-round
    annual_mean_f = 52.0 - max(0, (lat - 40)) * 1.5
    seasonal_offset = 18 * (1 - abs(m - 7) / 6)  # peak at month 7
    return annual_mean_f + seasonal_offset


def confidence(target_date: date, today: date | None = None) -> int:
    """confidence = max(20, 100 - horizon_days * 1.7)"""
    if today is None:
        today = date.today()
    horizon = max(0, (target_date - today).days)
    return max(20, int(100 - horizon * 1.7))


# ── Seasonal modifier application ───────────────────────────────────────────

def apply_seasonal_modifier(weights: dict[str, float], target_date: date,
                            modifiers: list[dict],
                            typical_species: list[str]) -> dict[str, float]:
    """Apply any matching seasonal modifier to the baseline weights."""
    m = target_date.month
    out = dict(weights)
    for mod in modifiers:
        start, end = mod["month_start"], mod["month_end"]
        in_window = (start <= end and start <= m <= end) or \
                    (start > end and (m >= start or m <= end))
        if not in_window:
            continue
        applies_to = mod.get("applies_to_species")
        if applies_to and not any(s in typical_species for s in applies_to):
            continue
        out["catch"]      += mod.get("w_catch_delta", 0)
        out["water_temp"] += mod.get("w_water_temp_delta", 0)
        out["flow"]       += mod.get("w_flow_delta", 0)
        out["hatch"]      += mod.get("w_hatch_delta", 0)
        out["access"]     += mod.get("w_access_delta", 0)
        if "weather" in out:
            out["weather"] += mod.get("w_weather_delta", 0)
    return out


# ── Primary factor — argmax(w_i * (100 - score_i)) ─────────────────────────

def primary_factor(weights: dict[str, float], scores: dict[str, int]) -> str:
    return max(scores.keys(), key=lambda k: weights.get(k, 0) * (100 - scores[k]))


# ── DB orchestrator ────────────────────────────────────────────────────────

@dataclass
class TQSRow:
    reach_id: str
    watershed: str
    target_date: date
    tqs: int
    confidence: int
    is_hard_closed: bool
    catch_score: int
    water_temp_score: int
    flow_score: int
    weather_score: int        # 0 in v0.5
    hatch_score: int
    access_score: int
    primary_factor: str
    partial_access_flag: bool
    horizon_days: int
    forecast_source: str
    computed_at: datetime
    # Snapshot of the inputs actually consumed during scoring. Persisted so
    # future ML feature engineering has access to "what we saw at decision
    # time" — NWS forecasts aren't archived elsewhere. See plan
    # plan-2026-05-14-tqs-forecast-history.md AD-2 / forecast_inputs_payload.
    forecast_inputs_payload: dict | None = None


def _load_reaches(conn):
    rows = conn.execute(text("""
        SELECT id, watershed, name, centroid_lat, centroid_lon,
               primary_usgs_site_id, is_warm_water, typical_species,
               COALESCE(bbox, ST_GeomFromText('POLYGON EMPTY', 4326)) AS bbox,
               general_flow_bearing
        FROM silver.river_reaches
        WHERE is_active = true
    """)).fetchall()
    return rows


def _load_flow_band(conn, reach_id: str):
    row = conn.execute(text("""
        SELECT cfs_low, cfs_ideal_low, cfs_ideal_high, cfs_high
        FROM silver.flow_quality_bands
        WHERE reach_id = :rid
        ORDER BY species, season_start_month
        LIMIT 1
    """), {"rid": reach_id}).fetchone()
    return row


def _load_hatch_windows(conn, watershed: str) -> list[tuple[int, int]]:
    rows = conn.execute(text("""
        SELECT start_month, end_month
        FROM curated_hatch_chart
        WHERE watershed = :ws
    """), {"ws": watershed}).fetchall()
    return [(int(r[0]), int(r[1])) for r in rows]


def _load_seasonal_modifiers(conn) -> list[dict]:
    rows = conn.execute(text("""
        SELECT season_label, month_start, month_end, applies_to_species,
               w_catch_delta, w_water_temp_delta, w_flow_delta,
               w_weather_delta, w_hatch_delta, w_access_delta
        FROM silver.tqs_seasonal_modifiers
    """)).fetchall()
    return [
        {
            "season_label": r[0], "month_start": r[1], "month_end": r[2],
            "applies_to_species": list(r[3]) if r[3] else None,
            "w_catch_delta": r[4], "w_water_temp_delta": r[5],
            "w_flow_delta": r[6], "w_weather_delta": r[7],
            "w_hatch_delta": r[8], "w_access_delta": r[9],
        }
        for r in rows
    ]


def _active_fire_intersects(conn, reach_bbox_geom, target_date: date) -> bool:
    """v0.5: a fire is 'active' if its ig_date is within target_date ± 30 days
    AND its perimeter intersects the reach bbox. Real implementation will use
    a live fire feed; this approximates with MTBS data."""
    if reach_bbox_geom is None:
        return False
    row = conn.execute(text("""
        SELECT 1
        FROM fire_perimeters
        WHERE ig_date BETWEEN :d - INTERVAL '30 days' AND :d
          AND ST_Intersects(perimeter, :bbox)
        LIMIT 1
    """), {"d": target_date, "bbox": reach_bbox_geom}).fetchone()
    return bool(row)


def _weather_inputs(conn, watershed: str, target_date: date) -> tuple[float | None, float | None, float | None, int | None]:
    """Pull (temp_f, precip_in, wind_mph, wind_bearing) for a watershed × date.

    Source order:
      - horizon ≤ 1d: live observation for that date
      - horizon ≤ 7d: most recent forecast for that target_date
      - horizon 8-30d: monthly climatology + 14-day recent trend (C_2)
      - horizon > 30d: pure monthly climatology (C_3 will refine with NCEI)
    Returns Nones if no rows are available at any tier.
    """
    today = date.today()
    horizon = (target_date - today).days
    if horizon <= 1:
        row = conn.execute(text("""
            SELECT temperature_avg_f, precipitation_in, wind_speed_avg_mph
            FROM bronze.weather_observations
            WHERE watershed = :ws AND date = :d
            ORDER BY fetched_at DESC LIMIT 1
        """), {"ws": watershed, "d": target_date}).fetchone()
        if row:
            return (
                float(row[0]) if row[0] is not None else None,
                float(row[1]) if row[1] is not None else None,
                float(row[2]) if row[2] is not None else None,
                None,
            )
    if horizon <= 7:
        row = conn.execute(text("""
            SELECT temperature_max_f, precipitation_in, wind_speed_avg_mph
            FROM bronze.weather_forecasts
            WHERE watershed = :ws AND target_date = :d
            ORDER BY issued_date DESC LIMIT 1
        """), {"ws": watershed, "d": target_date}).fetchone()
        if row:
            return (
                float(row[0]) if row[0] is not None else None,
                float(row[1]) if row[1] is not None else None,
                float(row[2]) if row[2] is not None else None,
                None,
            )
    # Climatological fallback (C_2 for 8-30d; C_3 will refine for > 30d).
    return _climatology_weather(conn, watershed, target_date, horizon)


def _climatology_weather(conn, watershed: str, target_date: date, horizon: int) -> tuple[float | None, float | None, float | None, int | None]:
    """Monthly mean from bronze.weather_observations (NCEI/NWS history)
    blended with a 14-day recent-trend signal for the 8-30d horizon."""
    monthly = conn.execute(text("""
        SELECT AVG(temperature_avg_f), AVG(precipitation_in), AVG(wind_speed_avg_mph)
        FROM bronze.weather_observations
        WHERE watershed = :ws
          AND EXTRACT(MONTH FROM date) = :m
    """), {"ws": watershed, "m": target_date.month}).fetchone()
    base_temp = float(monthly[0]) if monthly and monthly[0] is not None else None
    base_precip = float(monthly[1]) if monthly and monthly[1] is not None else None
    base_wind = float(monthly[2]) if monthly and monthly[2] is not None else None

    if 8 <= horizon <= 30:
        # Blend in the 14-day recent trend (delta from current month's running mean)
        trend = conn.execute(text("""
            SELECT AVG(temperature_avg_f), AVG(precipitation_in), AVG(wind_speed_avg_mph)
            FROM bronze.weather_observations
            WHERE watershed = :ws AND date >= CURRENT_DATE - INTERVAL '14 days'
        """), {"ws": watershed}).fetchone()
        if trend and trend[0] is not None and base_temp is not None:
            base_temp = (base_temp + float(trend[0])) / 2.0
        if trend and trend[1] is not None and base_precip is not None:
            base_precip = (base_precip + float(trend[1])) / 2.0
        if trend and trend[2] is not None and base_wind is not None:
            base_wind = (base_wind + float(trend[2])) / 2.0

    return base_temp, base_precip, base_wind, None


def _watershed_has_prediction(conn, watershed: str, target_date: date) -> bool:
    row = conn.execute(text("""
        SELECT 1 FROM predictions
        WHERE watershed = :ws
          AND status = 'active'
          AND generated_at >= :d - INTERVAL '30 days'
        LIMIT 1
    """), {"ws": watershed, "d": target_date}).fetchone()
    return bool(row)


def compute_trip_quality_daily(start_date: date, end_date: date) -> list[TQSRow]:
    """Compute TQS for each (active reach × target_date) in the range."""
    today = date.today()
    out: list[TQSRow] = []

    with engine.connect() as conn:
        reaches = _load_reaches(conn)
        modifiers = _load_seasonal_modifiers(conn)

        # Precompute per-reach static lookups
        flow_bands = {r[0]: _load_flow_band(conn, r[0]) for r in reaches}
        hatch_by_ws: dict[str, list[tuple[int, int]]] = {}

        d = start_date
        while d <= end_date:
            horizon = max(0, (d - today).days)
            forecast_source = (
                "live" if horizon <= 1
                else "nws_forecast" if horizon <= 7
                else "climatology+trend" if horizon <= 30
                else "climatology"
            )
            for r in reaches:
                rid, ws = r[0], r[1]
                lat = float(r[3])
                is_warm = bool(r[6])
                typical_species = list(r[7] or [])
                bbox = r[8]

                if ws not in hatch_by_ws:
                    hatch_by_ws[ws] = _load_hatch_windows(conn, ws)

                # Sub-scores
                wt_f = proxy_water_temp_f(d, lat)
                wt = water_temp_score(wt_f, is_warm)

                band = flow_bands.get(rid)
                proxy_cfs: float | None = None
                if band:
                    # Mid-of-ideal as a proxy until USGS time-series integration
                    proxy_cfs = (band[1] + band[2]) / 2.0
                    fl = flow_score(proxy_cfs, *band)
                else:
                    fl = 50

                ht = hatch_score(d, hatch_by_ws[ws])
                pred = _watershed_has_prediction(conn, ws, d)
                ct = catch_score(species_predicted=pred)

                fire = _active_fire_intersects(conn, bbox, d)
                acc, is_hard_closed, partial = access_score(
                    active_fire_intersects=fire,
                    regulation_closed=False,  # plumbed in a follow-up bead
                    partial_access=False,
                )

                reach_flow_bearing = int(r[9]) if r[9] is not None else None
                temp_f, precip_in, wind_mph, wind_bearing = _weather_inputs(conn, ws, d)
                ws_score = weather_score(
                    temp_f, precip_in, wind_mph, wind_bearing, reach_flow_bearing,
                )

                # Weighted sum + seasonal modifier (full §2 weights now that weather has data)
                w = apply_seasonal_modifier(W_V1, d, modifiers, typical_species)
                weighted_sum = (
                    w["catch"]      * ct +
                    w["water_temp"] * wt +
                    w["flow"]       * fl +
                    w["weather"]    * ws_score +
                    w["hatch"]      * ht +
                    w["access"]     * acc
                )
                tqs = int(round(weighted_sum))
                if is_hard_closed:
                    tqs = min(29, tqs)

                scores = {
                    "catch": ct, "water_temp": wt, "flow": fl,
                    "weather": ws_score, "hatch": ht, "access": acc,
                }
                pf = primary_factor(w, scores)

                # Capture the inputs actually consumed at scoring time. NWS
                # doesn't archive forecasts, so without this snapshot the
                # inputs that drove a past score would be lost.
                inputs_payload = {
                    "nws": {
                        "temp_f":         temp_f,
                        "precip_in":      precip_in,
                        "wind_mph":       wind_mph,
                        "wind_bearing":   wind_bearing,
                        "forecast_source": forecast_source,
                    },
                    "water": {
                        "temp_f": wt_f,
                        "source": "proxy_seasonal",
                    },
                    "flow": (
                        {"cfs": proxy_cfs, "source": "ideal_band_midpoint"}
                        if band else
                        {"cfs": None, "source": "no_band"}
                    ),
                    "fire_intersects": fire,
                    "computed_at": datetime.now(timezone.utc).isoformat(),
                }

                out.append(TQSRow(
                    reach_id=rid, watershed=ws, target_date=d,
                    tqs=max(0, min(100, tqs)),
                    confidence=confidence(d, today),
                    is_hard_closed=is_hard_closed,
                    catch_score=ct, water_temp_score=wt, flow_score=fl,
                    weather_score=ws_score,
                    hatch_score=ht, access_score=acc,
                    primary_factor=pf,
                    partial_access_flag=partial,
                    horizon_days=horizon,
                    forecast_source=forecast_source,
                    computed_at=datetime.now(timezone.utc),
                    forecast_inputs_payload=inputs_payload,
                ))
            d += timedelta(days=1)
    return out


def snapshot_history(snapshot_day: date | None = None) -> int:
    """Append today's gold.trip_quality_daily into gold.trip_quality_history.

    Carries the full sub-score decomposition + forecast metadata + the
    inputs payload, enabling future forecast-accuracy analysis and ML
    feature engineering off the history table alone.

    Idempotent for the same snapshot_day via the composite PK
    (reach_id, target_date, snapshot_date) — ON CONFLICT DO NOTHING.
    Returns the number of rows appended.
    """
    if snapshot_day is None:
        snapshot_day = date.today()
    with engine.connect() as conn:
        with conn.begin():
            result = conn.execute(text("""
                INSERT INTO gold.trip_quality_history
                    (reach_id, target_date, snapshot_date, tqs, confidence,
                     catch_score, water_temp_score, flow_score, weather_score,
                     hatch_score, access_score, forecast_source, horizon_days,
                     primary_factor, forecast_inputs_payload)
                SELECT reach_id, target_date, :s, tqs, confidence,
                       catch_score, water_temp_score, flow_score, weather_score,
                       hatch_score, access_score, forecast_source, horizon_days,
                       primary_factor, forecast_inputs_payload
                FROM gold.trip_quality_daily
                ON CONFLICT (reach_id, target_date, snapshot_date) DO NOTHING
            """), {"s": snapshot_day})
            return result.rowcount or 0


def refresh_trip_quality_daily(start_date: date | None = None,
                                end_date: date | None = None) -> int:
    """Recompute and replace gold.trip_quality_daily for the given range.

    Functional equivalent of `REFRESH MATERIALIZED VIEW` but in Python.
    Default range: today through today+90 (matches plan §3.4 refresh scope).
    Returns the number of rows written. Wraps the write in a single
    transaction so the table never contains a half-refresh state.
    """
    if start_date is None:
        start_date = date.today()
    if end_date is None:
        end_date = start_date + timedelta(days=90)

    rows = compute_trip_quality_daily(start_date, end_date)

    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(
                "DELETE FROM gold.trip_quality_daily WHERE target_date BETWEEN :s AND :e"
            ), {"s": start_date, "e": end_date})
            if rows:
                conn.execute(
                    text("""
                        INSERT INTO gold.trip_quality_daily
                            (reach_id, watershed, target_date, tqs, confidence,
                             is_hard_closed, catch_score, water_temp_score,
                             flow_score, weather_score, hatch_score, access_score,
                             primary_factor, partial_access_flag, horizon_days,
                             forecast_source, computed_at, forecast_inputs_payload)
                        VALUES
                            (:reach_id, :watershed, :target_date, :tqs, :confidence,
                             :is_hard_closed, :catch_score, :water_temp_score,
                             :flow_score, :weather_score, :hatch_score, :access_score,
                             :primary_factor, :partial_access_flag, :horizon_days,
                             :forecast_source, :computed_at,
                             CAST(:forecast_inputs_payload AS jsonb))
                    """),
                    [
                        {
                            "reach_id": r.reach_id, "watershed": r.watershed,
                            "target_date": r.target_date, "tqs": r.tqs,
                            "confidence": r.confidence, "is_hard_closed": r.is_hard_closed,
                            "catch_score": r.catch_score, "water_temp_score": r.water_temp_score,
                            "flow_score": r.flow_score, "weather_score": r.weather_score,
                            "hatch_score": r.hatch_score, "access_score": r.access_score,
                            "primary_factor": r.primary_factor,
                            "partial_access_flag": r.partial_access_flag,
                            "horizon_days": r.horizon_days,
                            "forecast_source": r.forecast_source,
                            "computed_at": r.computed_at,
                            "forecast_inputs_payload": (
                                json.dumps(r.forecast_inputs_payload)
                                if r.forecast_inputs_payload is not None else None
                            ),
                        }
                        for r in rows
                    ],
                )
    return len(rows)


if __name__ == "__main__":
    from datetime import date as _d
    rows = compute_trip_quality_daily(_d.today(), _d.today())
    for r in rows[:5]:
        print(f"{r.reach_id} {r.target_date}: tqs={r.tqs} pf={r.primary_factor} "
              f"closed={r.is_hard_closed} ct={r.catch_score} wt={r.water_temp_score} "
              f"fl={r.flow_score} ht={r.hatch_score} acc={r.access_score}")
    print(f"... total rows: {len(rows)}")
