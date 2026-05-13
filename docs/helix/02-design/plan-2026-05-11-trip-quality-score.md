# Design Plan: Trip Quality Score (v1)

**Date**: 2026-05-11 (revised 2026-05-13 incorporating reviewer feedback)
**Status**: DRAFT — for review
**Governing artifacts**: `01-frame/features/FEAT-007-fishing-intelligence.md`, `01-frame/features/FEAT-017-predictive-intelligence.md`, `02-design/architecture.md`, `02-design/adr/ADR-002-medallion-warehouse.md`, `02-design/adr/ADR-007-ai-grounded-narrative.md`

## 1. Problem Statement and User Impact

The North-Star B2C question is:

> *"Where should I go fly fishing within X miles of my home tomorrow, next week, next month, or next season?"*

Today the user has to mentally combine four scattered RiverPath cards — Catch Probability, Hatch, water-conditions live values, Snowpack — and still wing it on weather and access. We need a single comparable number per `(reach, date)` that ranks rivers (and stretches within them) within the user's travel range, with a "why" panel for the curious user and a confidence band that decays with forecast horizon.

> **Why reach-level, not watershed-level**: the McKenzie is 90 miles long. The upper McKenzie (above Trail Bridge) and the lower McKenzie (near Eugene) are fundamentally different fishing trips — different water temperatures, different fish, different hatches at any given moment. Same story on the Deschutes (Upper / Middle / Lower / Crooked confluence), John Day (Mainstem / North Fork / South Fork), Klamath (Upper / Wood / Williamson), and others. A single watershed-level TQS would be a lie for these rivers. Reach is the modeling unit; watershed is just a rollup of its reaches' scores.

## 1.5 Two personas, one metric

The same TQS serves two distinct user modes. **Both ship in v1.**

| Persona | Mode | Surface | What they need |
|---------|------|---------|----------------|
| **Trip planner** | Pull | `/path/where` ranking page | "Given today/this weekend/next month, where within X miles is best?" |
| **Opportunist** | Push | Watchlist + alerts + weekly outlook digest | "I have a fixed set of in-range rivers and surplus drivable time — ping me when one crosses into 'go' territory or a trend is building." |

The metric and warehouse plumbing are shared. The surfaces differ:

- Pull: ranking, distance filter, "why" panel — see §6/§7.
- Push: per-user watchlist of reaches, per-reach alert thresholds (e.g., "ping me when Upper McKenzie ≥ 75"), trend detection on the materialized view (slope/band-crossing), AI narrative output via ADR-007, weekly digest cadence to mute high-frequency bad news.

### Trend detection

TQS as defined is point-in-time per `(reach, date)`. The push surface needs:

- **Slope**: TQS today vs TQS-for-target-date computed 3 days ago → "Lower McKenzie's Saturday forecast climbed from 60 to 78 over the past three days."
- **Band-crossing**: detect when a future-date TQS crosses an alert threshold (rising or falling).
- **Cadence**: negative alerts batched into a weekly outlook digest; positive band-crossings can be near-real-time (still rate-limited).

Implemented as deltas computed against a small `gold.trip_quality_history` snapshot (daily roll of the materialized view's previous day for the same target). No new model; just diff on existing data.

## 2. The Metric: Trip Quality Score (TQS)

A 0–100 score, computed per `(reach_id, target_date)`, with a confidence value 0–100 that decays with horizon. Watershed-level TQS is a rollup of its reaches (see §2.5).

```
if reach is hard-closed (regulation or active fire perimeter intersects):
    TQS = clamp(0, 29, internal weighted score)   # forced into Skip band
else:
    TQS = Σ wᵢ · sub_scoreᵢ                       # clamped 0–100
```

Where each `sub_scoreᵢ` is 0–100 and the v1 weights `wᵢ` are uniform per reach (with a seasonal modifier — see §2.7):

| Sub-metric         | Weight | Source today                            | Source for >7 days                  |
|--------------------|--------|------------------------------------------|--------------------------------------|
| Catch Probability  | 0.25   | `gold.predictions` (FEAT-017)            | Climatological catch by month        |
| Water Temperature  | 0.15   | USGS gauge temp via reach.primary_usgs_site_id | Climatological temp + seasonal norm |
| Flow Suitability   | 0.15   | USGS live + per-reach flow bands         | PRISM precip + snowmelt projection   |
| Weather Suitability| 0.15   | NWS forecast (live, 7-day)               | PRISM monthly normals + variance     |
| Hatch Alignment    | 0.15   | `gold.hatch_chart` + degree-days         | Hatch phenology by month             |
| Access Status      | 0.15   | Fish-passage, fires, closures, regulations | Same                                |

**Access rule (binary gate, not weighted cap)**: a reach is "hard-closed" if (a) a regulation closure is active for the target date, or (b) an active fire-perimeter geometry intersects `reach.bbox`. When hard-closed, TQS is forced into the Skip band (0–29) regardless of other sub-scores. **Partial-access issues** (a fish-passage barrier downstream that doesn't affect the fishable stretch, a closure on an adjacent reach, etc.) do not gate TQS; they surface as a separate badge next to the score ("⚠ partial passage downstream"). This avoids the "100 · Bluebird next to a closure badge" credibility-destroying screenshot.

**Water temperature is its own sub-score** (not folded into flow). Trout fishability is dominated by water temp:
- Above ~68–70°F: catch-and-release mortality risk spikes (ODFW issues hoot-owl closures on this basis). water_temp_score floors at 0 above 70°F so TQS lands in Marginal/Skip even with great flow.
- Below ~40°F: fish go dormant; water_temp_score floors at 0.
- Ideal 50–60°F for trout (varies by species; reach metadata flags warm-water reaches).
This is independent of flow — you can have ideal cfs at lethal temperature, and the score has to reflect that.

### Score bands (UI presentation)
Band copy is deliberately understated — anglers will test the score ruthlessly. We describe conditions, not promise outcomes.

| Range    | Label           | Copy                                                   |
|----------|-----------------|--------------------------------------------------------|
| 90–100   | Excellent       | "All indicators favorable"                              |
| 70–89    | Strong          | "Conditions look strong"                                |
| 50–69    | Mixed           | "Conditions are mixed — manage expectations"            |
| 30–49    | Marginal        | "Several indicators weak — better options likely nearby" |
| 0–29     | Unfavorable     | "Conditions unfavorable" (closures get their own badge) |

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
Tap a score → show all six sub-scores with a sparkline of the last 30 days, and call out the **primary factor** — but use weight-adjusted contribution to the gap from 100, not just "lowest sub-score":

```
primary_factor = argmax(wᵢ × (100 − sub_scoreᵢ))
```

Why: if catch=60 (normal for that reach in May) and weather=65 (the real delta), the lowest-sub-score rule names "catch" and obscures what's actually moving the score. The weighted-contribution rule names "weather" — what the user can actually act on.

### 2.7 Seasonal weight modifier

Uniform weights miss season-driven shifts:

- **Dry-fly summer** (Jun–Sep): hatch matters more than catch baseline → bump `w_hatch += 0.05`, drop `w_catch -= 0.05`.
- **Winter steelhead** (Dec–Feb on coastal reaches): catch baseline matters more, hatch is irrelevant → bump `w_catch += 0.10`, drop `w_hatch -= 0.10`.
- **Spring runoff** (Apr–May): flow matters more, catch model less reliable → bump `w_flow += 0.05`, drop `w_catch -= 0.05`.

Modifiers are reach-aware (winter-steelhead bump only applies to reaches whose `typical_species` include steelhead). Live in a `silver.tqs_seasonal_modifiers` table — cheap data, easy to tune.

### 2.5 Sub-metric × reach matrix

| Sub-metric | Granularity | Why |
|------------|-------------|-----|
| Catch Probability | Reach | Cutthroat upper, steelhead lower — same river, different scores |
| Water Temperature | Reach | 10–15°F difference between upper (cold) and lower (warm) reaches is routine |
| Flow Suitability | Reach | Each reach has its own primary USGS gauge and ideal cfs band |
| Hatch Alignment | Reach | Cooler upper = later hatches than warm lower |
| Access Status | Reach | Closures, fires, and barriers happen to specific stretches |
| Weather Suitability | Watershed (wind: reach-aware) | NWS forecast is watershed-level, but wind impact depends on reach orientation (see §4 — wind direction vs `reach.general_flow_bearing`) |

So five of the six sub-scores need reach-level data; weather is watershed-level except for the wind sub-component which uses each reach's bearing.

### 2.6 Watershed rollup

For surfaces that show a single number per river (the home page river cards, the `/path/where` ranking page):

```
watershed_tqs        = MAX(reach.tqs)  across all reaches in the watershed
watershed_best_reach = argmax(reach.tqs)
reach_spread         = COUNT(reaches with tqs < 50) / COUNT(all reaches in watershed)
```

Rationale for MAX (not AVG): "what's the best part of this river right now" matches the user intent better than an average dragged down by stretches you don't care about. UI shows e.g. *"Deschutes — 82 · Lower stretch · Strong"* so the user knows immediately which reach to head for.

**The "1 of N good" affordance**: when `reach_spread ≥ 0.5` (half or more of the reaches are Marginal/Unfavorable), the watershed card shows a small caveat next to the score: *"Upper only — 2 of 3 reaches are unfavorable"*. Prevents the misleading screenshot when a fire or closure has knocked out two of three stretches but the watershed pill still reads 92.

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
    general_flow_bearing        int,             -- compass bearing 0–359° (river flow direction) for wind-vs-flow scoring; nullable when reach is too sinuous to characterize
    is_warm_water               boolean DEFAULT false,  -- bass / smallmouth / panfish reaches use different temp thresholds
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

### 3.0b `user_reach_watches` + `user_alert_thresholds` (new — push-product watchlist)

The opportunist persona needs a per-user set of watched reaches with personalized alert thresholds. Authenticated users only — anonymous users see the pull surfaces.

```sql
CREATE TABLE IF NOT EXISTS user_reach_watches (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reach_id        varchar(80) NOT NULL REFERENCES silver.river_reaches(id),
    alert_threshold int NOT NULL DEFAULT 70,     -- ping when TQS ≥ this
    alert_trend     boolean NOT NULL DEFAULT true, -- ping on positive band-crossing
    muted_until     timestamptz,                  -- soft mute (user is on a trip, etc.)
    created_at      timestamptz DEFAULT now(),
    UNIQUE (user_id, reach_id)
);
CREATE INDEX idx_uw_user ON user_reach_watches (user_id);
CREATE INDEX idx_uw_reach ON user_reach_watches (reach_id);

CREATE TABLE IF NOT EXISTS user_alert_deliveries (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    reach_id        varchar(80) NOT NULL,
    alert_type      varchar(40) NOT NULL,         -- 'band_cross_up' | 'trend_rising' | 'weekly_digest'
    target_date     date NOT NULL,                -- the day the alert is about
    tqs_at_alert    int NOT NULL,
    channel         varchar(20) NOT NULL,         -- 'in_app' | 'email' (v1: in_app only)
    delivered_at    timestamptz DEFAULT now(),
    seen_at         timestamptz
);
CREATE INDEX idx_uad_user_unseen ON user_alert_deliveries (user_id) WHERE seen_at IS NULL;
```

Alert thresholds per-reach. Defaults to 70 (Strong band). User can set per-reach (e.g., A-river at 80, B-river at 65). `muted_until` supports a "I'm fishing, don't ping me about other rivers" toggle. `user_alert_deliveries` is the audit log + dedupe key so we don't spam.

### 3.0c `user_trip_feedback` (new — feedback loop ground truth)

Earlier than originally planned. The one-tap "How was it?" prompt and the implied feedback are essential for any calibration.

```sql
CREATE TABLE IF NOT EXISTS user_trip_feedback (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         uuid REFERENCES users(id) ON DELETE SET NULL,
    reach_id        varchar(80) NOT NULL REFERENCES silver.river_reaches(id),
    trip_date       date NOT NULL,                -- the day the user actually fished
    tqs_at_view     int,                          -- the score we showed when they planned
    rating          smallint NOT NULL,            -- 1–5, "how was it really?"
    notes           text,
    submitted_at    timestamptz DEFAULT now()
);
CREATE INDEX idx_utf_reach_date ON user_trip_feedback (reach_id, trip_date);
```

Anonymous users can submit feedback too (user_id nullable). Used for the calibration analysis in Phase E.

### 3.0d `bronze.guide_availability` (new — async ground-truth from guide booking calendars)

```sql
CREATE TABLE IF NOT EXISTS bronze.guide_availability (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    guide_id        varchar(80) NOT NULL,        -- stable id for the guide / shop
    reach_id        varchar(80) REFERENCES silver.river_reaches(id),
    target_date     date NOT NULL,
    availability_pct double precision,           -- 0–100, what % of slots are open
    source_url      text,
    fetched_at      timestamptz DEFAULT now(),
    UNIQUE (guide_id, reach_id, target_date, fetched_at::date)
);
```

Scrape public guide booking calendars (Worldcast, Patagonia Guides, Fly Water Travel, etc.) on a weekly cadence. **Use as validation, not direct input**: surface high-divergence cases in the "why" panel ("TQS says 85 but local guides have unusual availability") as a credibility lever. Don't let guide signal score the metric — chicken-and-egg risk is real (if TQS gets influential it moves bookings).

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
    is_hard_closed                 ::boolean,  -- regulation or active fire closure on this reach
    catch_score                    ::int,
    water_temp_score               ::int,
    flow_score                     ::int,
    weather_score                  ::int,
    hatch_score                    ::int,
    access_score                   ::int,
    primary_factor                 ::text,     -- weighted-contribution argmax
    partial_access_flag            ::boolean,  -- non-blocking access concerns ("⚠ partial passage downstream")
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
WITH ranked AS (
    SELECT *,
           ROW_NUMBER() OVER (PARTITION BY watershed, target_date ORDER BY tqs DESC) AS rn,
           COUNT(*) FILTER (WHERE tqs < 50) OVER (PARTITION BY watershed, target_date) AS unfavorable_count,
           COUNT(*)                          OVER (PARTITION BY watershed, target_date) AS total_reaches
    FROM gold.trip_quality_daily
)
SELECT
    watershed,
    target_date,
    tqs                                  AS watershed_tqs,
    reach_id                             AS best_reach_id,
    confidence,
    primary_factor,
    unfavorable_count,                   -- for "2 of 3 reaches unfavorable" affordance
    total_reaches,
    (unfavorable_count::float / NULLIF(total_reaches, 0)) AS reach_spread,
    horizon_days,
    forecast_source,
    computed_at
FROM ranked
WHERE rn = 1;

CREATE UNIQUE INDEX IF NOT EXISTS idx_tqs_ws_rollup
    ON gold.trip_quality_watershed_daily(watershed, target_date);
```

### 3.4c `gold.trip_quality_history` (rollup view — supports push trend detection)

Daily snapshot of the previous day's `gold.trip_quality_daily` per `(reach_id, target_date)`, so we can compute slopes for the push surface.

```sql
CREATE TABLE IF NOT EXISTS gold.trip_quality_history (
    reach_id        varchar(80) NOT NULL,
    target_date     date NOT NULL,
    snapshot_date   date NOT NULL,           -- the day the snapshot was taken
    tqs             int NOT NULL,
    confidence      int,
    PRIMARY KEY (reach_id, target_date, snapshot_date)
);
CREATE INDEX idx_tqs_hist_recent ON gold.trip_quality_history (reach_id, target_date, snapshot_date DESC);
```

Daily job appends today's `gold.trip_quality_daily` rows into this table. Trend = `today.tqs - previous_n_days.tqs`. Used by the alert engine to detect band-crossings and rising trends without re-computing from scratch.

### 3.5 Algorithm — `compute_trip_quality_daily(start_date, end_date)`

Lives in `pipeline/predictions/trip_quality.py`. For each `(reach_id, target_date)` in the cross-product of `silver.river_reaches` × the date range:

1. **horizon_days** = `target_date - today()`.
2. **source layer** based on horizon:
   - `0–1`   → live (USGS instantaneous on reach.primary_usgs_site_id, NWS current observations for watershed)
   - `2–7`   → NWS forecast from `bronze.weather_forecasts` for watershed
   - `8–30`  → PRISM monthly normals + recent trend
   - `31–90` → pure climatology (PRISM normals + NCEI historical)
3. **Compute each sub-score** (functions described below) — five are reach-aware, weather is watershed-level with reach-aware wind component.
4. **Hard-closure check**: if reach is regulation-closed for `target_date` OR an active fire perimeter intersects `reach.bbox`, set `is_hard_closed=true` and force TQS into 0–29.
5. **Otherwise compute TQS** = `Σ wᵢ · sub_scoreᵢ` using reach-aware weights (with seasonal modifier per §2.7).
6. **Compute confidence** = `max(20, 100 - horizon * 1.7)`.
7. **primary_factor** = `argmax(wᵢ × (100 − sub_scoreᵢ))` (weighted contribution to gap, not lowest raw sub-score).
8. **partial_access_flag** = true when there's an access concern that didn't hard-close (e.g., downstream barrier, adjacent-reach closure).

#### sub-score functions

```
catch_score(reach, date)      = filter gold.predictions to species typical of this reach + date, then blend
water_temp_score(reach, date) = piecewise-linear curve over expected water temp at reach.primary_usgs_site_id;
                                hard floor 0 above 70°F (trout, cold-water reaches) or below 40°F;
                                ideal band 50–60°F; warm-water reaches use a 60–75°F ideal band instead
flow_score(reach, date)       = piecewise-linear from silver.flow_quality_bands keyed by reach_id,
                                using gauge reading from reach.primary_usgs_site_id
weather_score(ws, reach, date)= temp/precip/storm penalty from watershed NWS (see §4) MINUS
                                wind_penalty computed against reach.general_flow_bearing
hatch_score(reach, date)      = gold.hatch_chart strength × degree-day alignment, computed against
                                reach.primary_usgs_site_id temperature history (so upper-reach hatches
                                lag lower-reach hatches by weeks in spring)
access_score(reach, date)     = 100 minus penalties — only count fire perimeters, closures, and barriers
                                whose geometry intersects reach.bbox (or river-mile range); also drives
                                is_hard_closed flag in step 4
```

### 3.6 Alert engine — `compute_alerts_for_user(user_id)`

Runs hourly. For each `user_reach_watches` row, query `gold.trip_quality_daily` and `gold.trip_quality_history`:

1. **Band-cross detection** — for each upcoming target_date (today, +1, +3, +7, +14, +21):
   - Today's TQS for that target ≥ watch.alert_threshold AND
   - Most recent prior snapshot's TQS for the same target was < threshold
   → fire `band_cross_up` alert (one row in `user_alert_deliveries`).
2. **Rising trend** — slope over last 5 daily snapshots ≥ +4 TQS/day for a future target → fire `trend_rising` alert (rate-limited per reach to once per 5 days).
3. **Weekly digest** — Friday morning batch: every watched reach + the next 14 days' TQS plotted, with band-crossings highlighted. One delivery per user per week.
4. **Negative alerts are mute-by-default** — falling TQS doesn't ping; it surfaces in the weekly digest only.
5. **Respect `muted_until`** — drop all alert deliveries while muted.

Delivery channel v1: in-app notification list at `/path/alerts` (see §7). Email channel v2.

### 3.7 Narrative output for push alerts (ADR-007)

Each alert includes a short LLM-generated narrative grounded in the warehouse, not raw boilerplate. Example:

> "Lower McKenzie's Saturday score climbed from 64 to 81 over the last three days. Warmer afternoons (forecast 72°F vs 60°F earlier in the week) bumped both the hatch window and catch probability. Flow holding steady at 1,400 cfs — within the lower stretch's ideal band."

Cached per `(alert_id)` — never regenerated. Uses same retrieval pattern as `gold.deep_time_story` (ADR-007).

## 4. Weather-Suitability Sub-Score (worth its own section)

Fly fishing weather isn't generic "nice weather" — anglers tolerate (and sometimes prefer) overcast, light rain, mild wind. The v1 weather sub-score:

```
weather_score = 100
  − temp_penalty           (air temp: too hot OR too cold)
  − precip_penalty         (heavy rain blowing out flows in next 24h)
  − wind_speed_penalty     (sustained wind > 15 mph degrades casting)
  − wind_direction_penalty (forecast wind bearing vs reach.general_flow_bearing — see below)
  − thunderstorm_penalty   (severe storm flag → −40)
```

Thresholds (PNW defaults):
- Temp ideal: 50–75°F. Score drops 1pt/°F outside that band; cap at −30.
- Precip: 0–0.25" ideal, 0.25–0.75" mild penalty, > 0.75" heavy penalty.
- Wind speed: < 10 mph ideal, 10–15 mild, > 15 heavy.
- Thunderstorm: hard −40 (lightning + fly rod is bad news).

### Wind direction (reach-aware)

Wind speed alone misses what anglers actually feel. The direction relative to river flow matters more than the speed:

```
delta = ((wind_bearing - reach.general_flow_bearing) + 360) mod 360
# 0°    = wind blowing downstream (favorable — at your back)
# 180°  = wind blowing upstream (in your face — penalize hard)
# 90/270= cross-river (penalize moderate — kills mending)
```

Penalty curve at wind ≥ 10 mph:
- 0° ± 30° (downstream): no extra penalty
- 60° ± 30° / 300° ± 30° (quartering): −0.5 × wind_mph
- 90° ± 30° / 270° ± 30° (cross): −1.0 × wind_mph
- 180° ± 30° (upstream-in-face): −2.0 × wind_mph

NWS forecasts already include direction. `reach.general_flow_bearing` is in the seed inventory (§3.0). Reaches with very sinuous flow (no characteristic bearing) skip the direction penalty entirely.

These are scalar formulas, not ML — calibratable once we have historical weather + quality ground truth (`user_trip_feedback` per §3.0c) or correlated catch reports.

## 4.5 Water-Temperature Sub-Score (its own section because of stakes)

Trout fishability is gated by water temperature in ways that no other sub-metric captures:

- **> 70°F**: catch-and-release mortality risk spikes. ODFW issues hoot-owl closures on this basis. **Hard floor 0** — water_temp_score = 0 in this band even with ideal flow.
- **65–70°F**: stressed fish, marginal trip. Penalty 1pt/°F.
- **50–60°F**: ideal for most trout species. water_temp_score = 100.
- **40–50°F**: cool, fish slower but feeding. Penalty 1pt/°F below 50°F.
- **< 40°F**: fish dormant. **Hard floor 0**.

Reaches flagged `is_warm_water = true` (bass / smallmouth / panfish) use a shifted band: ideal 60–75°F, hard floors at 32°F (icing) and 85°F (heat-kill).

Source: USGS gauge temperature reading at `reach.primary_usgs_site_id`. When the gauge doesn't report temperature, use the climatological monthly mean for that gauge's lat/lon (PRISM-derived) with a wider confidence band (already handled in §confidence).

## 5. Phasing

| Phase | Scope | Unblocks |
|-------|-------|----------|
| **A0** (~3 days) | **Reach curation** — define ~25 reaches with a guide-reviewer per watershed; assign primary USGS gauge + SNOTEL station + `general_flow_bearing` + `typical_species` + `is_warm_water` per reach; populate `silver.river_reaches` seed migration. Document reach boundaries in an angler-readable spec. | Modeling unit exists |
| **A** (1–2 weeks) | Schema migrations for §3.0–3.4 (river_reaches, weather_observations, watchlist tables, feedback table, guide-availability table, flow_quality_bands, trip_quality_daily, rollup view, history snapshot); daily weather-observation ingest job; seed flow bands; basic `compute_trip_quality_daily` using catch + water_temp + flow + hatch + access (skip weather sub-score in this phase) | Reach-level pull score visible in UI for 0–7 day horizon |
| **A.5** (~3 days) | **Hallway test** — clickable prototype of the pull surface with band labels, reach selector, "why" panel. 5 anglers in person. Capture friction; iterate band copy, reach naming, info hierarchy before any UI ships to production. | De-risks v1 surface |
| **B** (2 weeks) | Add `bronze.weather_forecasts` capture; wire full weather sub-score (incl. wind direction); surface confidence band. **Plus the feedback loop**: ship one-tap "How was it?" prompt and the `user_trip_feedback` write path; weekly guide-availability scrape job into `bronze.guide_availability`; surface divergence callouts in the "why" panel ("TQS says 85; local guides have unusual availability") | Full v1 pull score with calibration signal collecting |
| **B.5** (1 week) | **Push surface v1**: watchlist UI (`/path/alerts` page), per-reach alert threshold settings, in-app notification delivery, alert engine cron, weekly digest renderer, ADR-007 narrative pipeline for each alert | Opportunist persona served; both v1 personas live |
| **C** (1 week) | NCEI historical-weather backfill (10 years, full PNW + Utah); 30–90 day climatological projections; trend snapshots populated daily into `gold.trip_quality_history` | Next-month / next-season horizons usable; long-horizon trends feed weekly digest |
| **D** (later) | "Why" panel polish, distance filter on `/path/where`, ranking page UX iteration based on Phase A.5 + B feedback; email channel for alerts; user-curated reach feedback ("report this is wrong") | Self-improvement loop |
| **E** (later) | Tune per-reach weights using `user_trip_feedback` and guide-availability divergence as ground truth; switch from hand-tuned to learned weights; expand reach inventory based on usage | Better accuracy |

## 6. API surface (sketch)

### Pull (trip planner)

```
GET /api/v1/reaches?watershed=mckenzie
   → [ { id, name, short_label, river_mile_start, river_mile_end, centroid_lat, centroid_lon,
         primary_usgs_site_id, general_flow_bearing, typical_species, is_warm_water }, ... ]

GET /api/v1/trip-quality?date=2026-05-15&reach_id=mckenzie_upper
   → { reach_id, watershed, score, confidence, is_hard_closed,
       catch_score, water_temp_score, flow_score, weather_score, hatch_score, access_score,
       primary_factor, partial_access_flag, horizon_days, forecast_source }

GET /api/v1/trip-quality?date=2026-05-15&watershed=mckenzie
   → { watershed, best_reach_id, score, confidence, primary_factor,
       reach_spread, unfavorable_count, total_reaches,
       reaches: [ ... per-reach scores ... ] }

GET /api/v1/trip-quality/ranking?date=2026-05-15&user_lat=44.05&user_lon=-123.09&max_miles=150
   → [ { watershed, best_reach_id, best_reach_name, score, confidence,
         miles_from_user, primary_factor, reach_spread }, ... ]   # sorted desc by score
```

### Push (opportunist)

```
GET /api/v1/watchlist                              # current user's watched reaches
   → [ { reach_id, name, alert_threshold, alert_trend, muted_until, current_tqs, trend_7d }, ... ]

POST /api/v1/watchlist
   body: { reach_id, alert_threshold?, alert_trend? }
   → { reach_id, alert_threshold, alert_trend }

PATCH /api/v1/watchlist/{reach_id}
   body: { alert_threshold?, alert_trend?, muted_until? }

DELETE /api/v1/watchlist/{reach_id}

GET /api/v1/alerts?seen=false                      # in-app notification list
   → [ { id, reach_id, reach_name, alert_type, target_date, tqs_at_alert,
         narrative, delivered_at }, ... ]

POST /api/v1/alerts/{id}/seen                      # mark as read

GET /api/v1/digest/weekly                          # this user's weekly outlook
   → { issued_at, watershed_summaries: [ { reach_id, name,
         daily: [ { date, tqs, band_crossing? }, ... 14 entries ], narrative } ] }
```

### Feedback

```
POST /api/v1/trip-feedback
   body: { reach_id, trip_date, rating, notes?, tqs_at_view? }
   → 201
```

## 7. UI surface (sketch)

### Pull (trip planner)

On `/path/now/<watershed>`:
- A "Trip Quality" pill above the existing hero metrics shows the watershed-rollup number — e.g. `Trip Quality: 82 · Strong · Lower stretch`. The "Lower stretch" label is the `best_reach_id`.
- When `reach_spread ≥ 0.5`, a small caveat shows: *"Upper only — 2 of 3 reaches unfavorable"*.
- When `is_hard_closed = true` on the best reach, the pill is replaced by a clear closed badge — never a numeric score for a closed reach.
- Below the hero, a reach selector (chips: *Upper · Middle · Lower*) lets the user view per-reach TQS. Selecting a reach updates the pill, the "why" panel, and the page's sub-cards.
- **Default reach selection**: if the user arrived from the ranking page, default to the best-scoring reach; if they navigated directly to the watershed URL, default to last-viewed reach (from localStorage); else default to best-scoring.
- The "why" panel shows the six sub-scores with weight-adjusted contribution highlighted on the primary factor.

`/path/where` ranking page:
- User enters home zip / location and max miles.
- Ranked list of **watersheds** (not reaches), each showing best-reach name + score + drive distance + primary factor + a small reach_spread indicator.
- Tapping a watershed expands to show all of its reaches' scores.
- Filter chip "Only reaches with score ≥ 70" hides marginal stretches.

### Push (opportunist)

New page `/path/alerts`:
- **Watchlist tab**: every reach the user is watching, with current TQS, 7-day trend sparkline, alert threshold (editable), and a mute toggle. Add-to-watchlist button on any reach detail page.
- **Notifications tab**: chronological list of band-cross-up and trend-rising alerts. Each card shows the alert narrative (ADR-007), the reach + target date + score, and a "Plan this trip" button that deep-links to that reach's detail view.
- **Digest tab**: most recent weekly outlook (or "issued every Friday" placeholder until the first one).

Tab badge on the bottom-nav `Saved` icon → repurpose or add an Alerts icon. To be decided in Phase A.5 hallway testing.

### Band copy guard rails

Per the soften-copy reframe: no copy promises a result. "All indicators favorable" / "Conditions look strong" / "Conditions are mixed" / "Several indicators weak" / "Conditions unfavorable". Closures get their own explicit badge separate from the score band.

## 8. Explicitly deferred in v1

Everything below was considered and consciously punted. Listed here so reviewers can see what's been examined vs. missed.

| # | Item | Why deferred | Reconsider when |
|---|------|--------------|-----------------|
| 1 | Per-reach regulation closures (open seasons, special-tackle regs) from ODFW eRegulations | No structured data source today; manual transcription is curator-grade work | Phase E or when ODFW publishes structured eRegs data |
| 2 | Crowd / use estimate (Strava heatmaps, recreation.gov bookings) | Multiple third-party integrations, each with friction; iNat density was rejected as too weak | After v1 ships and user research shows crowding is in the top 3 unmet asks |
| 3 | Daily climatology (vs PRISM monthly) | PRISM monthly mean used as the day-proxy in v1; daily NOAA climatologies are a larger ingestion | Phase E if Phase B feedback shows climatology accuracy is the binding constraint |
| 4 | Reach-level weather resolution (NWS gridpoint per reach centroid vs watershed-uniform) | Watershed-uniform is a simplification; very large watersheds (Deschutes north-south) may diverge in practice | v2 — likely combined with reach-specific microclimate notes |
| 5 | Reach-boundary self-service editing | UI complexity; we ship a "report this is wrong" link in v1 instead, then triage manually | Phase E |
| 6 | Email channel for push alerts | In-app notifications only in v1; email adds deliverability + opt-in compliance | Phase D |
| 7 | Direct guide-availability scoring (using empty calendars as a *signal* in TQS) | Chicken-and-egg risk — if TQS gets influential it moves bookings, which feeds back into TQS. v1 uses guide signal as **validation only**, not direct input | v2 only after we have ground truth to detangle correlation from causation |
| 8 | Catch-data ground truth at a date level | ODFW publishes annual counts; we lack per-day. v1 backs off to `user_trip_feedback` from Phase B as the proxy | When user-feedback volume crosses a threshold (~1000 ratings/quarter) |
| 9 | Reach-specific microclimate notes (e.g., Lower Deschutes canyon afternoon thermals) | Curator-grade content; v1 ships generic NWS data per watershed | v2 — write up as reach metadata once we have guide reviewers engaged |
| 10 | Multi-language UI for international anglers | English-only in v1 | Out-of-scope; if/when geographic expansion warrants |

## 9. Risks and Counter-Plans

| Risk | Likelihood | Impact | Counter |
|------|-----------|--------|---------|
| Sub-score weights wrong → score doesn't track reality | High | Med | Ship with curator-defined defaults + seasonal modifier; `user_trip_feedback` from Phase B starts collecting ground truth immediately; tune in Phase E |
| Reach boundaries don't match how anglers actually think about a river | Med | High | Recruit one local guide per watershed to review the seed reach inventory before Phase A0 closes; ship a "report this is wrong" link in the "why" panel |
| Too many reaches clutters the UI and confuses users on small rivers | Low | Med | Cap at 3–5 reaches per watershed in v1; only show reach selector when watershed has ≥2 reaches |
| NCEI backfill is large and slow | Med | Low | Chunk by year; one-time job; throttle; 10-year window (not 20) |
| Weather sub-score over-penalizes typical PNW conditions (overcast, light rain) | High | Med | Tune thresholds with a fishing-guide reviewer; Phase A.5 hallway test catches the worst cases before code ships |
| Users compare scores across reaches with very different flow regimes and feel the score is unfair (e.g., Skagit always lower than Metolius) | Med | Med | Per-reach weights in Phase E; document that the score is *relative to that reach's good days* |
| Adding TQS to the hero pushes more API/DB load on first paint | Low | Low | `gold.trip_quality_daily` is pre-materialized; one keyed lookup; same SWR cache pattern as the rest |
| **Push alerts feel spammy → users mute or churn** | High | High | Negative alerts muted by default (weekly digest only); positive band-crossings rate-limited per reach; user-configurable thresholds default conservatively (≥ 70); `muted_until` for trip-mode silencing |
| **TQS gets screenshotted next to a closure** | Med | Critical | Hard binary access gate (TQS forced 0–29 when reach is closed); closures get their own badge separate from the score band; band copy never promises a result |
| **Guide-availability scrape becomes a TOS / legal issue** | Med | Med | Use only public booking-page data; document robots.txt compliance; named guides as sources are crediting, not exploiting; pull immediately on any opt-out request |
| **Feedback loop too sparse to calibrate** | Med | Med | One-tap "How was it?" prompt placement matters — show on Saved trips that the user returned from; combine with guide-availability divergence as a secondary signal |
| **Chicken-and-egg with guide bookings** (TQS moves bookings → bookings feed TQS) | Low (v1) | High | Use guide signal as validation only in v1; flag in monitoring once we have data to detect the feedback loop forming |

## 10. Decision points — resolved 2026-05-13

The reviewer-feedback pass folded in the following decisions. Each one is now baked into the plan above:

| # | Decision | Resolution |
|---|----------|------------|
| 1 | Composite vs per-timeframe scores | **Composite**, one score with horizon parameter |
| 2 | Initial sub-score weights | **0.25 / 0.15 × 5** (catch slightly higher; water_temp added as 6th); seasonal modifier per §2.7 |
| 3 | Access cap vs binary gate | **Hard binary gate** — closures force TQS into 0–29 with explicit badge; partial-access issues surface as a separate badge, not weighted |
| 4 | NCEI backfill scope | **10 years**, full PNW + Utah |
| 5 | `/path/where` in v1 | **Yes — plus push surfaces too**. Both personas live in v1 (Phase A pull, Phase B.5 push) |
| 6 | Reach inventory review | **Guide-reviewer per watershed** in Phase A0; "report this is wrong" link in v1 UI |
| 7 | Watershed rollup rule | **MAX**, with reach_spread affordance ("2 of 3 reaches unfavorable") |
| 8 | Default reach selection | **Best-scoring** when arriving from ranking; **last-viewed** (localStorage) when navigating directly to watershed URL |
| 9 | Water temperature as a sub-score | **Yes** — its own sub-score with hard floors at 70°F (trout reaches) and 40°F |
| 10 | Wind direction in weather sub-score | **Yes** — uses `reach.general_flow_bearing` |
| 11 | Feedback loop timing | **Phase B**, not Phase D — one-tap "How was it?" + guide-availability scraping |
| 12 | Guide-availability use | **Validation only** in v1; surface divergence as credibility lever; defer direct scoring use to v2 |
| 13 | Hallway test | **Yes** — Phase A.5, 5 anglers before code ships to production |
| 14 | Band copy tone | **Soften** — describe conditions, never promise outcomes (see §2 score-bands table) |
| 15 | 90-day horizon | **Retained** in v1; NCEI backfill funds it in Phase C |

Implementation order: A0 reach curation → A schema + v0.5 score → A.5 hallway test → B full score + feedback loop + guide-availability scrape → B.5 push surfaces (watchlist + alerts + digest) → C NCEI backfill + 90-day horizons → D polish → E learned weights.

## 11. Competitive wedge

| Player | Strength | Where we differ |
|--------|----------|-----------------|
| Troutroutes | Hyperlocal trail + stream-access maps, paid app, strong angler community | We're broader (water + species + access + weather + geology + restoration) and free at the use surface. They're a map; we're a decision. |
| OnX Fish | Premium polish, multi-state coverage, hunt-app cross-sell | Same map-product critique. We're not trying to be a navigator. |
| FishBrain | Catch logs + community + weather | Crowd-sourced data quality is uneven; no real warehouse. We have scientific data integration they don't. |
| Reddit / forums | Free, hyperlocal, current intel | Inconsistent signal, requires patience and trust-building. TQS is the "give me a number" answer for the user who doesn't have time to read 40 posts. |
| Local fly shops (online + phone) | Authoritative when reached | Not scalable, not 24/7, geographically limited. Guide-availability validation lets us *complement* shop reports rather than compete. |

**The wedge**: integration of public scientific data + reach-level granularity + push (watchlist + trend alerts) + AI narrative grounded in real data. For the angler who wants a quick directional answer ("should I drive to the Deschutes or the Mckenzie this Saturday, or wait until next weekend?"), we beat both manually combining four cards and reading three Reddit threads.

**What we don't beat**: the experienced angler who already knows three rivers deeply and has guide relationships. They're not our target — they're already optimizing without us. We're aimed at the angler with broad in-range options, limited time, and unevenly-distributed expertise across those rivers.
