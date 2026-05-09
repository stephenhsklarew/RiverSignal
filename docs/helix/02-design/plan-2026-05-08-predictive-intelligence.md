# Predictive Intelligence Plan

## Context

All gold views are currently deterministic SQL aggregations with hardcoded scoring rules. There's an opportunity to add real predictive models that learn from the 1.3M observations, 8.4M time series readings, and 14K interventions to generate genuinely intelligent insights.

## Recommended Models (Priority Order)

### 1. Hatch Emergence Prediction
**Impact: HIGH** — This is the #1 thing anglers want to know

**Current state:** Static lookup table — if current month is in `peak_months`, show HIGH confidence.

**What a model could do:**
- Predict emergence timing based on **accumulated degree days** (water temperature sum), not calendar month
- Use historical observation data: correlate water temp trends with actual insect observation spikes
- Factor in snowmelt timing, flow rate, and air temperature
- Output: "Blue-Winged Olives likely emerging in 3-5 days based on current water temps" vs today's "BWOs are active this month"

**Data available:**
- 8.4M time series (daily water temp from USGS + SNOTEL)
- 4,453 hatch chart observations with dates
- 63 curated hatch entries with month ranges
- Species observations with timestamps

**Approach:** Logistic regression or gradient boosted trees. Features: 7-day avg water temp, cumulative degree days since Jan 1, day of year, flow rate. Target: binary (species observed that day yes/no). Train per species per watershed.

**Gold table:** `gold.hatch_emergence_forecast` — species, watershed, probability, expected_date, confidence_interval, driving_factors

---

### 2. Catch Probability Model
**Impact: HIGH** — Currently a fake score from hardcoded rules

**Current state:** Fixed formula: base 50 + temp match bonus + hatch bonus. Same score whether it's a bluebird day or a storm front.

**What a model could do:**
- Train on actual catch/harvest data (ODFW sport catch, WDFW stocking returns)
- Factor in: water temp, flow, weather forecast, barometric pressure trend, moon phase, time of year, hatch activity, stocking events within last 30 days
- Per-species probability: "Chinook: 72% (high flow + recent stocking), Rainbow: 45% (water temp rising above preferred range)"

**Data available:**
- `gold.harvest_trends` — annual catch by species
- `gold.fishing_conditions` — monthly water temp and flow
- `gold.stocking_schedule` — 2,311 stocking events with dates
- `gold.hatch_fly_recommendations` — 1,445 insect-fly matches
- NWS weather forecast (live API)
- USGS real-time flow and temp (live API)

**Approach:** Gradient boosted trees (XGBoost/LightGBM). Features: water temp, flow, temp delta (3-day trend), day of year, days since last stocking, hatch activity score, weather. Target: harvest count or presence/absence. Train on historical monthly catch data, predict daily.

**Gold table:** `gold.catch_forecast` — species, watershed, date, probability, confidence, top_factors, recommended_flies

---

### 3. River Health Anomaly Detection
**Impact: MEDIUM** — Early warning for ecological problems

**Current state:** Health score is `30 + temp_bonus + DO_bonus`. Doesn't detect trends or anomalies.

**What a model could do:**
- Detect **unusual patterns**: "Water temperature is 2.5 standard deviations above the 10-year mean for this date"
- Predict water quality exceedances 3-7 days out based on weather forecast + upstream flow
- Identify **regime shifts**: "Species richness has declined 3 consecutive months — this hasn't happened since the 2020 fire"
- Correlate across signals: dropping DO + rising temp + low flow = thermal stress event incoming

**Data available:**
- 8.4M time series readings (temp, DO, flow, precipitation)
- `gold.anomaly_flags` — 24,374 existing threshold-based flags
- Historical baselines per station per month
- Weather forecast (7-day NWS)

**Approach:** 
- Anomaly detection: Isolation Forest or simple z-score against historical monthly distributions
- Forecasting: ARIMA or Prophet for 7-day water temp prediction
- Regime shift: CUSUM or change-point detection on species richness time series

**Gold table:** `gold.health_forecast` — watershed, date, predicted_temp, predicted_do, anomaly_score, alert_level, explanation

---

### 4. Species Distribution Shift Tracking
**Impact: MEDIUM** — Climate change signal detection

**Current state:** `gold.species_trends` shows year-over-year count changes. No spatial analysis.

**What a model could do:**
- Track which species are **moving upstream** (cold-water species retreating to higher elevation)
- Detect **new arrivals**: species appearing in a watershed for the first time
- Predict **range contractions** based on temperature trends: "Bull trout habitat in the McKenzie is projected to shrink 30% by 2030 based on current warming rate"

**Data available:**
- 1.3M observations with lat/lon and dates spanning 15+ years
- `gold.cold_water_refuges` — thermal classification by station
- PRISM climate data (354K records, monthly temp/precip)

**Approach:** Species distribution modeling (MaxEnt or random forest). Features: elevation, water temp, distance from refuge, flow, canopy cover. Compare current vs historical distributions. No deep learning needed.

**Gold table:** `gold.species_range_forecast` — species, watershed, direction (expanding/contracting), rate_km_per_year, projected_range_2030, confidence

---

### 5. Restoration Impact Prediction
**Impact: MEDIUM** — Justify conservation spending

**Current state:** `gold.restoration_outcomes` shows species before/after intervention. No prediction of which interventions work best.

**What a model could do:**
- Predict **expected species gain** for a proposed restoration type at a specific location
- Rank intervention types by ROI: "Riparian replanting yields 2.3x more species recovery per dollar than fish screening in this watershed"
- Estimate **recovery timeline**: "Based on similar sites, expect 80% of pre-disturbance species richness within 4.2 years"

**Data available:**
- `gold.restoration_outcomes` — 300 interventions with before/after species counts
- `gold.post_fire_recovery` — 459 fire recovery trajectories
- `gold.stewardship_opportunities` — 136 project categories
- WA SRFB projects with funding amounts

**Approach:** Linear regression or random forest. Features: intervention type, watershed, pre-intervention species count, distance to nearest refuge, upstream land use, years since last fire. Target: species delta.

**Gold table:** `gold.restoration_forecast` — intervention_type, watershed, predicted_species_gain, confidence_interval, estimated_recovery_years, cost_effectiveness_rank

---

## Implementation Architecture

### Option A: In-Database (simplest)
- Use PostgreSQL's `pg_ml` extension or compute predictions in Python during the pipeline refresh
- Store predictions in gold tables alongside existing views
- Refresh predictions on the same schedule as data ingestion

### Option B: Lightweight ML Service
- Train models offline (notebook or script), export as pickle/ONNX
- Load models in the FastAPI backend, compute predictions on-demand
- Cache predictions in gold tables, refresh daily

### Option C: Cloud ML (most scalable)
- Vertex AI for training and serving
- Cloud Run calls Vertex AI endpoints
- Most expensive, only needed if models are large

**Recommendation:** Start with **Option A** for models 1-3 (simple statistical models that run in Python during pipeline refresh). Move to Option B if latency matters.

## Phased Rollout

**Phase 1** (highest value, simplest): Hatch Emergence Prediction + Catch Probability
- Both use existing data, simple models (logistic regression, gradient boosted trees)
- Directly replace the hardcoded scoring rules
- Users see immediate improvement in the quality of predictions

**Phase 2**: River Health Anomaly Detection
- Adds early warning capability
- Uses statistical methods (z-scores, CUSUM), not heavy ML

**Phase 3**: Species Distribution + Restoration Impact
- More complex models, need more training data validation
- Higher scientific rigor required (peer-reviewable methodology)
