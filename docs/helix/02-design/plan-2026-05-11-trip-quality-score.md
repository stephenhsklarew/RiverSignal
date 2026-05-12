# Design Plan: Trip Quality Score (v1)

**Date**: 2026-05-11
**Status**: DRAFT — for review
**Governing artifacts**: `01-frame/features/FEAT-007-fishing-intelligence.md`, `01-frame/features/FEAT-017-predictive-intelligence.md`, `02-design/architecture.md`, `02-design/adr/ADR-002-medallion-warehouse.md`, `02-design/adr/ADR-007-ai-grounded-narrative.md`

## 1. Problem Statement and User Impact

The North-Star B2C question is:

> *"Where should I go fly fishing within X miles of my home tomorrow, next week, next month, or next season?"*

Today the user has to mentally combine four scattered RiverPath cards — Catch Probability, Hatch, water-conditions live values, Snowpack — and still wing it on weather and access. We need a single comparable number per `(reach, date)` that ranks rivers (and stretches within them) within the user's travel range, with a "why" panel for the curious user and a confidence band that decays with forecast horizon.

> **Why reach-level, not watershed-level**: the McKenzie is 90 miles long. The upper McKenzie (above Trail Bridge) and the lower McKenzie (near Eugene) are fundamentally different fishing trips — different water temperatures, different fish, different hatches at any given moment. Same story on the Deschutes (Upper / Middle / Lower / Crooked confluence), John Day (Mainstem / North Fork / South Fork), Klamath (Upper / Wood / Williamson), and others. A single watershed-level TQS would be a lie for these rivers. Reach is the modeling unit; watershed is just a rollup of its reaches' scores.

## 2. The Metric: Trip Quality Score (TQS)

A 0–100 score, computed per `(reach_id, target_date)`, with a confidence value 0–100 that decays with horizon. Watershed-level TQS is a rollup of its reaches (see §2.5).

```
TQS = Σ wᵢ · sub_scoreᵢ          (clamped 0–100)
    └─ but capped at 30 if access_score < 30
```

Where each `sub_scoreᵢ` is 0–100 and the v1 weights `wᵢ` are uniform per watershed:

| Sub-metric        | Weight | Source today                            | Source for >7 days                  |
|-------------------|--------|------------------------------------------|--------------------------------------|
| Catch Probability | 0.30   | `gold.predictions` (FEAT-017)            | Climatological catch by month        |
| Flow Suitability  | 0.20   | USGS live + per-watershed flow bands     | PRISM precip + snowmelt projection   |
| Weather Suitability | 0.20 | NWS forecast (live, 7-day)               | PRISM monthly normals + variance     |
| Hatch Alignment   | 0.20   | `gold.hatch_chart` + degree-days         | Hatch phenology by month             |
| Access Status     | 0.10   | Fish-passage, fires, closures            | Same                                  |

**Why the access hard cap**: a river that's currently closed by wildfire smoke or seasonal regulations should never read as "good" no matter how favorable the other inputs.

### Score bands (UI presentation)
| Range    | Label           | Example copy                            |
|----------|-----------------|------------------------------------------|
| 90–100   | Bluebird        | "Ideal conditions — clear your calendar" |
| 70–89    | Solid           | "Strong trip, expect good fishing"       |
| 50–69    | Workable        | "Decent. Manage expectations on …"       |
| 30–49    | Marginal        | "Risky — consider an alternate"          |
| 0–29     | Skip            | "Don't go — closed or hostile conditions"|

### Confidence
```
confidence = max(20, 100 - horizon_days * 1.7)
```
- Tomorrow      → ~98
- 7 days out    → ~88
- 30 days out   → ~49
- 90 days out   → ~20 (floor)

Shown as a small `±` band on the score: `78 ± 12`.

### The "why" panel
Tap a score → show all five sub-scores with a sparkline of the last 30 days, and call out the **primary factor** (the lowest contributing sub-score that's pulling the total down).

### 2.5 Sub-metric × reach matrix

| Sub-metric | Granularity | Why |
|------------|-------------|-----|
| Catch Probability | Reach | Cutthroat upper, steelhead lower — same river, different scores |
| Flow Suitability | Reach | Each reach has its own primary USGS gauge and ideal cfs band |
| Hatch Alignment | Reach | Cooler upper = later hatches than warm lower |
| Access Status | Reach | Closures, fires, and barriers happen to specific stretches |
| Weather Suitability | Watershed | NWS forecast resolution + reach proximity → marginal reach-vs-watershed variation; shared across reaches in v1 |

So four of the five sub-scores need reach-level data; weather rolls up from the watershed's single NWS station.

### 2.6 Watershed rollup

For surfaces that show a single number per river (the home page river cards, the `/path/where` ranking page):

```
watershed_tqs       = MAX(reach.tqs)  across all reaches in the watershed
watershed_best_reach= argmax(reach.tqs)            (the reach driving that number)
```

Rationale for MAX (not AVG): "what's the best part of this river right now" matches the user intent of "should I go fishing here?" better than an average that's dragged down by stretches you don't care about. UI shows e.g. *"Deschutes — 82 · Lower stretch · Solid"* so the user knows immediately which reach to head for.

## 3. Schema Additions

### 3.0 `silver.river_reaches` (new — the modeling unit)

A curated table of named stretches within each watershed. 3–5 reaches per watershed; ~25 total across the 7 currently-supported watersheds.

```sql
CREATE TABLE IF NOT EXISTS silver.river_reaches (
    id              varchar(80) PRIMARY KEY,    -- e.g. 'mckenzie_upper'
    watershed       varchar(50) NOT NULL,        -- 'mckenzie'
    name            varchar(120) NOT NULL,       -- 'Upper McKenzie'
    short_label     varchar(40),                 -- 'Upper' for compact UI
    description     text,                        -- one-line angler-friendly
    -- Spatial extent
    river_mile_start    double precision,        -- nullable when not on NHDPlus
    river_mile_end      double precision,
    bbox            geometry(POLYGON, 4326),     -- for spatial joins
    centroid_lat    double precision NOT NULL,
    centroid_lon    double precision NOT NULL,
    -- Sub-score anchors
    primary_usgs_site_id        varchar(40),     -- the gauge that defines flow + temp for this reach
    primary_snotel_station_id   varchar(40),     -- the SNOTEL station whose snowpack drives this reach's runoff timing
    -- Curation
    typical_species varchar[],                   -- e.g. {'cutthroat','rainbow_trout'}
    notes           text,
    source          text,                        -- 'expert curated', 'ODFW reach definitions', etc.
    is_active       boolean NOT NULL DEFAULT true,
    created_at      timestamptz DEFAULT now(),
    updated_at      timestamptz DEFAULT now()
);
CREATE INDEX idx_reaches_watershed ON silver.river_reaches (watershed);
CREATE INDEX idx_reaches_bbox      ON silver.river_reaches USING GIST (bbox);
```

**Seed data**: hand-curated CSV / seed-migration with ~25 rows. Initial reaches per watershed (approximate, requires angler review):

| Watershed | Reaches |
|-----------|---------|
| McKenzie | Upper (above Trail Bridge), Middle (Blue River–Leaburg), Lower (Leaburg–confluence) |
| Deschutes | Upper (above Wickiup), Middle (Wickiup–Bend), Lower (Bend–Maupin), Lower Canyon (Maupin–mouth) |
| Metolius | Headwaters–Camp Sherman, Camp Sherman–Lake Billy Chinook |
| John Day | Mainstem, North Fork, South Fork |
| Klamath | Upper Klamath Lake tribs, Wood River, Williamson River |
| Skagit | Upper (above Marblemount), Middle (Marblemount–Concrete), Lower (Concrete–mouth) |
| Green River | Flaming Gorge Dam–Little Hole, Little Hole–Brown's Park, Brown's Park–Canyonlands |

**Why curation, not derivation**: anglers think in named reaches that align with access points, fly-shop conventions, and ODFW regulation boundaries — not in NHDPlus segments or grid cells. A derived definition would group stretches that locals consider distinct. Initial table is opinionated; future refinements come from guide / curator feedback.

### 3.1 `bronze.weather_observations` (new — fills the historical-weather gap)

```sql
CREATE TABLE IF NOT EXISTS bronze.weather_observations (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    watershed       varchar(50) NOT NULL,
    date            date NOT NULL,
    temperature_max_f         double precision,
    temperature_min_f         double precision,
    temperature_avg_f         double precision,
    precipitation_in          double precision,
    wind_speed_avg_mph        double precision,
    wind_gust_max_mph         double precision,
    relative_humidity_pct     double precision,
    cloud_cover_avg_pct       double precision,
    snow_depth_in             double precision,
    pressure_avg_mb           double precision,
    source_type     varchar(30) NOT NULL DEFAULT 'nws',
    source_station_id text,
    data_payload    jsonb,
    fetched_at      timestamptz DEFAULT now(),
    UNIQUE (watershed, date, source_type)
);
CREATE INDEX idx_weather_obs_ws_date ON bronze.weather_observations (watershed, date DESC);
```

**Ingestion**: a new daily Cloud Run job (`pipeline-daily` chain or its own job) calls NWS's hourly observations API for the closest station to each watershed centroid, rolls up to daily, writes one row per `(watershed, date)`. Backfill via NCEI Climate Data Online for prior years (one-shot job, ~1 GB raw).

### 3.2 `bronze.weather_forecasts` (optional but cheap — enables accuracy tracking)

```sql
CREATE TABLE IF NOT EXISTS bronze.weather_forecasts (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    watershed       varchar(50) NOT NULL,
    issued_date     date NOT NULL,       -- the day the forecast was made
    target_date     date NOT NULL,       -- the day being predicted
    horizon_days    int GENERATED ALWAYS AS (target_date - issued_date) STORED,
    temperature_max_f         double precision,
    temperature_min_f         double precision,
    precipitation_in          double precision,
    wind_speed_avg_mph        double precision,
    cloud_cover_avg_pct       double precision,
    data_payload    jsonb,
    fetched_at      timestamptz DEFAULT now(),
    UNIQUE (watershed, issued_date, target_date)
);
CREATE INDEX idx_weather_fc_target ON bronze.weather_forecasts (watershed, target_date DESC);
```

**Ingestion**: piggyback on the existing live NWS fetch — when we hit the API for the 7-day forecast, also write a row per `target_date` to this table. Cheap because we're already making the request.

### 3.3 `silver.flow_quality_bands` (new — encodes "what flow is good for this reach")

Curated table, not derived. Per reach × species (optional), the cfs ranges that map to flow-score bands. Flow varies enormously between upper and lower reaches of the same river, so this MUST be reach-keyed.

```sql
CREATE TABLE IF NOT EXISTS silver.flow_quality_bands (
    reach_id    varchar(80) NOT NULL REFERENCES silver.river_reaches(id),
    species     varchar(80),         -- nullable = applies to all
    cfs_low     int NOT NULL,        -- below this: too low
    cfs_ideal_low   int NOT NULL,    -- start of ideal band
    cfs_ideal_high  int NOT NULL,    -- end of ideal band
    cfs_high    int NOT NULL,        -- above this: blown out
    season_start_month  int,         -- nullable = year-round
    season_end_month    int,
    source      text,                -- "ODFW manual", "expert curator", etc.
    PRIMARY KEY (reach_id, COALESCE(species, ''), COALESCE(season_start_month, 0))
);
```

**Seed data**: hand-curated for each of the ~25 reaches. Same approach as `silver.insect_fly_patterns` — spreadsheet → CSV → seed migration. Anglers report meaningfully different ideal-flow ranges across reaches even on the same river: e.g., the upper Deschutes fishes well at 200–400 cfs but the lower Deschutes (much wider channel) is ideal at 4,000–6,000 cfs. Future enhancement: derive from catch ↔ flow correlation once we have user-reported catch data.

### 3.4 `gold.trip_quality_daily` (new — the serving table, per reach)

```sql
CREATE MATERIALIZED VIEW gold.trip_quality_daily AS
SELECT
    reach_id,
    watershed,                                  -- denormalized for convenience
    target_date,
    score                          ::int       AS tqs,
    confidence                     ::int,
    catch_score                    ::int,
    flow_score                     ::int,
    weather_score                  ::int,
    hatch_score                    ::int,
    access_score                   ::int,
    primary_factor                 ::text,     -- 'catch' | 'flow' | 'weather' | 'hatch' | 'access'
    horizon_days                   ::int,
    forecast_source                ::text,     -- 'live'|'nws_forecast'|'climatology'
    computed_at                    ::timestamptz
FROM compute_trip_quality_daily(now()::date, now()::date + INTERVAL '90 days');

CREATE UNIQUE INDEX IF NOT EXISTS idx_tqs_reach_date
    ON gold.trip_quality_daily(reach_id, target_date);
CREATE INDEX IF NOT EXISTS idx_tqs_ws_date
    ON gold.trip_quality_daily(watershed, target_date);
```

**Refresh cadence**: daily (light tier — fast computation, ~25 reaches × 90 days ≈ 2,250 rows).

### 3.4b `gold.trip_quality_watershed_daily` (rollup view)

For surfaces that need a single number per river — the home-page river cards and the `/path/where` ranking page.

```sql
CREATE MATERIALIZED VIEW gold.trip_quality_watershed_daily AS
SELECT DISTINCT ON (watershed, target_date)
    watershed,
    target_date,
    tqs                            AS watershed_tqs,
    reach_id                       AS best_reach_id,
    confidence,
    primary_factor,
    horizon_days,
    forecast_source,
    computed_at
FROM gold.trip_quality_daily
ORDER BY watershed, target_date, tqs DESC;

CREATE UNIQUE INDEX IF NOT EXISTS idx_tqs_ws_rollup
    ON gold.trip_quality_watershed_daily(watershed, target_date);
```

### 3.5 Algorithm — `compute_trip_quality_daily(start_date, end_date)`

Lives in `pipeline/predictions/trip_quality.py`. For each `(reach_id, target_date)` in the cross-product of `silver.river_reaches` × the date range:

1. **horizon_days** = `target_date - today()`.
2. **source layer** based on horizon:
   - `0–1`   → live (USGS instantaneous on reach.primary_usgs_site_id, NWS current observations for watershed)
   - `2–7`   → NWS forecast from `bronze.weather_forecasts` for watershed
   - `8–30`  → PRISM monthly normals + recent trend
   - `31–90` → pure climatology (PRISM normals)
3. **Compute each sub-score** (functions described below) — four are reach-aware, weather rolls up from watershed.
4. **Compute TQS** = weighted average; apply access hard cap.
5. **Compute confidence** = `max(20, 100 - horizon * 1.7)`.
6. **primary_factor** = name of the lowest sub-score.

#### sub-score functions

```
catch_score(reach, date)   = filter gold.predictions to species typical of this reach + date, then blend
flow_score(reach, date)    = piecewise-linear from silver.flow_quality_bands keyed by reach_id,
                             using gauge reading from reach.primary_usgs_site_id
weather_score(ws, date)    = scalar from temp/precip/wind via watershed-level NWS data (see §4) —
                             shared across all reaches in the watershed
hatch_score(reach, date)   = gold.hatch_chart strength × degree-day alignment, computed against
                             reach.primary_usgs_site_id temperature history (so upper-reach hatches
                             lag lower-reach hatches by weeks in spring)
access_score(reach, date)  = 100 minus penalties — only count fire perimeters, closures, and barriers
                             whose geometry intersects reach.bbox (or river-mile range)
```

## 4. Weather-Suitability Sub-Score (worth its own section)

Fly fishing weather isn't generic "nice weather" — anglers tolerate (and sometimes prefer) overcast, light rain, mild wind. The v1 weather sub-score:

```
weather_score = 100
  − temp_penalty       (too hot OR too cold, see thresholds below)
  − precip_penalty     (heavy rain blowing out flows in next 24h)
  − wind_penalty       (sustained wind > 15 mph degrades casting)
  − thunderstorm_penalty (severe storm flag → −40)
```

Thresholds tuned per region. Pacific Northwest defaults:
- Temp ideal: 50–75°F. Score drops 1pt/°F outside that band; cap at −30.
- Precip: 0–0.25" ideal, 0.25–0.75" mild penalty, > 0.75" heavy penalty.
- Wind: < 10 mph ideal, 10–15 mild, > 15 heavy.
- Thunderstorm: hard −40 (lightning + fly rod is bad news).

These are scalar formulas, not ML — but they're calibratable once we have historical weather + a quality ground truth (user-reported "good day / bad day" feedback or correlated catch reports).

## 5. Phasing

| Phase | Scope | Unblocks |
|-------|-------|----------|
| A0 (~3 days) | Reach curation: define ~25 reaches across 7 watersheds with an angler reviewer; assign primary USGS gauge + primary SNOTEL station per reach; populate `silver.river_reaches` seed migration | Modeling unit exists; everything downstream keys on it |
| A (1–2 weeks) | Schema migrations for §3.0–3.4 (incl. river_reaches, weather_observations, flow_quality_bands keyed by reach, trip_quality_daily, watershed rollup view); daily weather-observation ingest job; seed flow bands for the ~25 reaches; basic `compute_trip_quality_daily` using catch + flow + hatch + access (skip weather sub-score) | Reach-level score visible in UI for tomorrow / next 7 days |
| B (1 week) | Add `bronze.weather_forecasts` capture on the existing NWS live fetch; wire weather sub-score; surface confidence band | Full v1 score |
| C (1 week) | NCEI historical-weather backfill (one-shot); 30–90 day climatological projections | Next-month / next-season horizons |
| D (later) | UI: "why" panel, distance filter, ranking across reaches, user feedback "was this right?" with reach selection | Calibration loop |
| E (later) | Tune per-reach weights using D's feedback; switch to learned weights; expand reach inventory based on usage | Better accuracy |

## 6. API surface (sketch)

```
GET /api/v1/reaches?watershed=mckenzie
   → [ { id, name, short_label, river_mile_start, river_mile_end, centroid_lat, centroid_lon,
         primary_usgs_site_id, typical_species }, ... ]

GET /api/v1/trip-quality?date=2026-05-15&reach_id=mckenzie_upper
   → { reach_id, watershed, score, confidence, catch_score, flow_score, weather_score,
       hatch_score, access_score, primary_factor, horizon_days, forecast_source }

GET /api/v1/trip-quality?date=2026-05-15&watershed=mckenzie
   → { watershed, best_reach_id, score, confidence, primary_factor, reaches: [ ... per-reach scores ... ] }
   # Convenience rollup using gold.trip_quality_watershed_daily plus per-reach drilldown.

GET /api/v1/trip-quality/ranking?date=2026-05-15&user_lat=44.05&user_lon=-123.09&max_miles=150
   → [ { watershed, best_reach_id, best_reach_name, score, confidence,
         miles_from_user, primary_factor }, ... ]   # sorted desc by score
   # Ranking is over watershed-rollups (one row per watershed) so the user
   # doesn't see five "McKenzie Upper / Middle / Lower" entries dominating;
   # tapping a watershed reveals its reach breakdown.
```

## 7. UI surface (sketch)

On `/path/now/<watershed>`:
- A "Trip Quality" pill above the existing hero metrics shows the watershed-rollup number — e.g. `Trip Quality: 82 · Solid · Lower stretch`. The "Lower stretch" label is the `best_reach_id` so the user knows immediately which part of the river is driving that score.
- Below the hero, a reach selector (chips: *Upper · Middle · Lower*) lets the user view per-reach TQS. Selecting a reach updates the score pill, the "why" panel, and (if practical) the rest of the page's sub-cards to that reach.
- The "why" panel shows the five sub-scores for the *currently selected reach*, plus a small note when the watershed-level pill differs from the selected reach (e.g., *"Lower stretch scores 82; you're viewing Upper at 64"*).

New page `/path/where` (or `/path/now` "find a good river" entry):
- User enters home zip / location and max miles.
- See a ranked list of **watersheds** (not reaches) for the selected date, each showing its best-reach name + score + drive distance + primary factor.
- Tapping a watershed expands to show all of its reaches' scores.
- Filter chip "Only reaches with score ≥ 70" hides marginal stretches.

## 8. Gaps still open after v1

1. **Ground-truth feedback loop** — no per-day catch reports from users yet. We can ship without it but won't be able to backtest accuracy until we have it. Could add a one-tap "How was it?" prompt after a saved trip; tag feedback to the specific reach the user fished.
2. **Crowd / use estimate** — still unsourced. Out of scope for v1. Could approximate from iNat observation density as a Phase-E signal.
3. **Per-reach flow-quality curves are curator-dependent** — initial bands are expert guesses. Quality of TQS = quality of these curves × correctness of reach boundaries. Plan: expose a curator workflow as v2; allow guide / shop feedback to fork bands per reach.
4. **PRISM is monthly** — not daily. For 30–90 day climatology we use the monthly mean as a proxy for that day. Acceptable v1 simplification; can refine with NOAA daily climatologies later.
5. **No legal restrictions baked in** — closed seasons, regulated stretches, special-tackle regs. These deserve their own data source (ODFW eRegulations) and aren't in TQS v1. Per-reach regulation flags would slot naturally into the access sub-score in v2.
6. **Reach boundaries are static** — anglers may disagree with our cut points. Expose a "report this reach is wrong" link in the "why" panel so we can curate based on real usage.
7. **Weather is watershed-uniform** — for very large watersheds (e.g., Deschutes north-south span) the same NWS forecast may not represent the lower canyon and upper basin equally well. Acceptable simplification for v1; future v2 could resolve weather to the nearest NWS gridpoint per reach centroid.

## 9. Risks and Counter-Plans

| Risk | Likelihood | Impact | Counter |
|------|-----------|--------|---------|
| Sub-score weights wrong → score doesn't track reality | High | Med | Ship with curator-defined defaults; expose feedback; tune in Phase E |
| Reach boundaries don't match how anglers actually think about a river | Med | High | Recruit one local guide per watershed to review the seed reach inventory before Phase A0 closes; ship a "report this is wrong" link in the "why" panel |
| Too many reaches clutters the UI and confuses users on small rivers | Low | Med | Cap at 3–5 reaches per watershed in v1; only show reach selector when watershed has ≥2 reaches |
| NCEI backfill is large and slow | Med | Low | Chunk by year; one-time job; throttle |
| Weather sub-score over-penalizes typical PNW conditions (overcast, light rain) | High | Med | Tune thresholds with a fishing-guide reviewer; ship Phase B behind a quick on/off so we can iterate |
| Users compare scores across reaches with very different flow regimes and feel the score is unfair (e.g., Skagit always lower than Metolius) | Med | Med | Per-reach weights in Phase E; until then, document that the score is *relative to that reach's good days*, not an absolute fishability scale |
| Adding TQS to the hero pushes more API/DB load on first paint | Low | Low | `gold.trip_quality_daily` is pre-materialized; one keyed lookup; same SWR cache pattern as the rest |

## 10. Decision points for review

Before any code lands, please confirm:

1. **Single composite vs separate scores per timeframe** — this plan uses one score with a horizon parameter. Alternative: 4 distinct scores (tomorrow / week / month / season) each with their own model. The single-score path is simpler and reads better in the UI; the separate-scores path is more honest about what's actually being predicted.
2. **Initial weights** — 0.30 / 0.20 / 0.20 / 0.20 / 0.10. OK as a starting point, or do you want a guide to weigh in first?
3. **Hard-cap rule on access** — TQS capped at 30 if `access_score < 30`. Reasonable, or should access be a hard binary "go / don't go" filter outside the score?
4. **NCEI backfill scope** — full PNW + Utah for last 20 years (≈ heavy but one-shot), or shorter window (5 years) for v1?
5. **`/path/where` ranking page** — is that scoped in for the v1 ship, or just `/path/now` integration?
6. **Reach inventory & boundaries** — initial cut is in §3.0 (~25 reaches across 7 watersheds). Do you want to review and edit that list now, or trust me to recruit a guide-reviewer to validate before Phase A code starts?
7. **Watershed rollup = MAX(reach)** — gives users the "best stretch of this river right now" view, which matches the user intent. Alternative is AVG (more representative of the river as a whole, but worse for a "where should I go" tool). MAX is the v1 choice; do you agree?
8. **Reach selector default** — when a user lands on `/path/now/<watershed>`, do we default to showing the best-scoring reach, the most-popular reach (would need usage data we don't have), or no reach selected (watershed-rollup only)? V1 default in this plan is best-scoring reach.

Once you've signed off, the implementation order will be 3.0 → 3.4 in Phase A (gated by Phase A0 reach curation), then 3.2 + weather sub-score in B, then backfill in C.
