# Prompt: Onboard a new US watershed end-to-end

| | |
|---|---|
| **Date** | 2026-05-15 |
| **Status** | Active — verified against codebase 2026-05-15 |
| **Audience** | Claude Code agent (or equivalent) with full repo read + shell + edit access |
| **Related artifacts** | `02-design/adr/ADR-001-anonymous-first-access.md`, `02-design/adr/ADR-008-source-license-tagging.md`, `02-design/plan-2026-05-11-trip-quality-score.md`, `pipeline/config/watersheds.py` |
| **Last verified against** | commit at HEAD on 2026-05-15. Codepaths cited here drift; re-verify the §"Operating context" file inventory if `git log --since="2 weeks"` shows non-trivial pipeline/adapter changes. |

**Goal:** ingest, verify, and ship a brand-new US watershed across the full stack (bronze → silver →
gold → API → UI → prod), in three explicit steps.
**Curation policy:** auto-draft v0 for every editorial gate (reach naming, flow bands, river story,
species lists) with `needs_review=true` flags. Never block on human input — flag and continue.
**Pause policy:** the agent stops only when (a) a brand-new state agency requires a developer key it
cannot obtain, (b) a destructive infra action would be required, or (c) any of the explicit
production-deployment gates in §2.8 are reached. Anything softer is a flag-and-continue.

---

## Required arguments

Before running, supply these values:

| Var | Example | Notes |
|---|---|---|
| `WATERSHED_SLUG` | `yellowstone_upper` | snake_case; used in DB rows, file paths, route params |
| `WATERSHED_DISPLAY` | `Upper Yellowstone River` | shown in UI |
| `WATERSHED_STATES` | `MT,WY` | comma-separated USPS codes |
| `HEADWATERS_DESCRIPTION` | `Yellowstone Lake outflow in Yellowstone NP` | one sentence |
| `MOUTH_DESCRIPTION` | `Confluence with Missouri at Buford, ND` | one sentence; if confluence is into another tracked watershed, name the existing slug |
| `BBOX_HINT` | `north=46.05, south=44.50, east=-108.30, west=-110.95` | rough box; agent will refine after inspecting NHDPlus + reach centroids |

If any of the above are unknown, the agent's first move is to look them up from authoritative sources
(USGS Water Resources, NHDPlus, USFS GeoData, NPS) and confirm before proceeding.

---

## Operating context the agent must read first

Spend the first 5 minutes establishing context — do not skip:

1. `pipeline/config/watersheds.py` — the canonical watershed-config dict; note the bbox conventions
   ("full drainage with small buffer beyond extreme reach centroid").
2. `pipeline/ingest/` — every adapter that exists today (`*.py`). Note which are state-bound
   (`washington.py`, `utah.py`, `dogami.py`) vs federal/universal (`usgs`, `nws_observations`,
   `inaturalist`, `snotel`, `prism`, `mtbs`).
3. `pipeline/ingest/base.py` — `IngestionAdapter` base class. Any new state-agency adapter follows
   this pattern (writes to `ingestion_jobs` for the freshness endpoint, exposes `source_type`).
4. `pipeline/cli.py` — the entry point. Adapters are invoked as
   `python -m pipeline.cli ingest <source> -w <watershed>`.
5. `app/routers/data_status.py` — `SOURCE_REFRESH_HOURS` registers every source's expected cadence.
   Any new adapter needs an entry here, plus a label in `frontend/src/hooks/useFreshness.ts`.
6. `frontend/src/components/WatershedHeader.tsx` — `WATERSHED_ORDER` and `WATERSHED_LABELS` for the
   picker; new watersheds must be added in both spots.
7. `app/routers/weather.py` (`WS_COORDS`, `WS_GAUGES`), `app/routers/fishing.py`, and any other
   router with a hard-coded watershed dict. Grep for the new slug to find every place it must land.
8. `terraform/cloud_run_jobs.tf` — `pipeline_daily`, `pipeline_weekly`, `pipeline_monthly` args.
   New state adapters get appended here per the existing pattern (at the END of the chain so
   failures don't short-circuit upstream ingest).
9. `docs/helix/02-design/plan-2026-05-11-trip-quality-score.md` §3.0 — reach inventory expectations
   for TQS (3-5 named reaches per watershed; flow-quality bands; warm-water flag).
10. Recent watershed-onboarding commits — `git log --oneline --grep="watershed\\|johnday\\|green_river"`
    — to mirror established patterns.

After this read-pass, the agent should be able to predict every place a watershed slug appears.

---

## STEP 1 — Source identification & gap report

**Output:** `docs/helix/06-iterate/watershed-add/<WATERSHED_SLUG>-source-inventory-<YYYY-MM-DD>.md`

The agent enumerates every live data feed required by **all three apps** for this specific watershed,
checks availability, and flags gaps with recommended fills. No code changes yet — pure investigation.

### 1.1 Inventory required feeds, per app

Use the table below as the canonical feature → source map. For each row, the agent answers:
*does an existing adapter cover this watershed, does a new adapter need authoring, or is the data
unavailable / manual?*

| App | Feature surface | Required data | Existing adapter (if any) |
|---|---|---|---|
| **RiverSignal** | Site dashboards | USGS gauges, NWIS time series | `usgs` |
| RiverSignal | Restoration tracking | OWRI / NOAA RC / PCSRF | `restoration` |
| RiverSignal | Fire recovery | MTBS perimeters, BAER severity | `mtbs` |
| RiverSignal | Water quality | EPA WQP, state 303(d) | `wqp`, `deq_303d` |
| RiverSignal | Land ownership / access | BLM SMA, USFS, state parks | `blm_sma`, `recreation` |
| RiverSignal | Watershed geometry | USGS WBD (HUC8/10/12), NHDPlus | `wbd`, `nhdplus` |
| RiverSignal | Wetlands | USFWS NWI | `nwi` |
| RiverSignal | Predictions / reports | All of the above feeding `gold.predictions` | derived |
| **RiverPath** | Go Score (TQS) sub-scores | USGS flow + temp; NWS obs + forecast; PRISM normals; ODFW-equivalent harvest; MTBS access; hatch chart | `usgs`, `nws_observations`, `prism`, `fishing`, `mtbs` + `curated_hatch_chart` (manual) |
| RiverPath | River Now hero | USGS instantaneous; NWS current obs | live API (no adapter — `app/routers/weather.py`) |
| RiverPath | Hatch panel | `curated_hatch_chart` + degree-day calc | manual seed |
| RiverPath | River Story (LLM) | All of the above as context | derived; `pipeline/generate_river_stories.py` |
| RiverPath | Photo observations | iNaturalist (CC-licensed) | `inaturalist` |
| RiverPath | Stocking schedule | State hatchery feeds (ODFW, WDFW, UDWR, ID F&G, MT FWP, CDFW, NMDGF, etc.) | `fishing` (Oregon only), `washington`, `utah` — others NEW |
| RiverPath | Fish passage | USGS / state passage barriers | `fish_barrier` |
| RiverPath | Swim safety | USGS temp + flow, NLDAS-derived | derived view |
| RiverPath | Snowpack | NRCS SNOTEL | `snotel` |
| RiverPath | Recreation sites | RIDB (USFS, BLM, NPS, USACE, USBR) + state parks | `recreation` |
| **DeepTrail** | Geology units | Macrostrat, state geology (DOGAMI for OR; WSGS for WY; MBMG for MT; etc.) | `macrostrat`, `dogami` (OR only) — others NEW |
| DeepTrail | Fossil sites | PBDB, iDigBio, state paleo | `pbdb`, `idigbio`, `biodata` |
| DeepTrail | Rockhound sites | BLM PLSS, state rockhounding lists, manual curation | `blm_sma` + manual `rockhounding_sites` |
| DeepTrail | Mineral deposits | USGS MRDS | `mrds` |
| DeepTrail | Deep Time stories | All of the above feeding `gold.deep_time_story` | derived |

The agent expands this table with concrete answers for the target watershed. For any **NEW** adapter,
it identifies:

- Authoritative source URL + API doc URL
- `robots.txt` status (HTML scrapers only) and the User-Agent the agent will identify as
- Rate limits / quota
- API key requirement — **stop and ask the user before proceeding** if a paid key is required
  (see §"Pause / escalation triggers")
- **License (per ADR-008):** one of `Public Domain`, `CC0`, `CC BY 4.0`, `CC BY-NC`,
  `Public Records`, `Varies`, `Academic Free`, `All rights reserved`, or the exact license string
  the source asserts
- **`commercial: true|false`** — whether the license permits use behind a paid B2B feature.
  iNaturalist CC-BY-NC photos are `commercial: false`; all USGS / NWS / NOAA / EPA federal data is
  `commercial: true`; state-agency data is usually `Public Records` + `commercial: true` but verify
  the state's open-records statute
- Attribution requirement (text to render, link target)
- Redistribution restrictions (some agencies forbid republishing raw rows; in those cases the
  adapter must store the data internally but never expose unaggregated rows via the public API)

### 1.2 Watershed geometry & topology

- Pull HUC8 / HUC10 boundaries from USGS WBD via `wbd` adapter or one-shot query.
- Pull NHDPlus flowlines for the watershed → identify primary stream, major tributaries, headwater
  reaches, mouth.
- Identify the **confluence** target (existing watershed or external). If it joins an existing
  tracked watershed, note that the existing watershed's downstream-segment graph may need
  updating (`silver.river_reaches.notes` annotation, not a structural change).
- Refine the `BBOX_HINT` to a tight bounding box that includes:
  - All headwater segments (above any major confluence)
  - The full main stem
  - All named tributaries the project should reach-curate
  - A 0.05° buffer beyond the most-extreme reach centroid

### 1.3 Per-source check matrix

For every row in §1.1, produce a check line that includes the **license + commercial-use**
assessment per ADR-008:

```
✓ usgs           — 14 gauges in bbox (NWIS site list verified) — Public Domain, commercial:true
✓ snotel         — 6 SNOTEL stations in HUC8 / HUC10           — Public Domain, commercial:true
✓ nws            — forecast office BYZ (Billings); gridpoint 102,87 — Public Domain, commercial:true
✓ mtbs           — 3 perimeters intersecting bbox 1984-2023    — Public Domain, commercial:true
✓ inaturalist    — ~2,400 research-grade observations in bbox  — CC-BY-NC (mixed), commercial:false
                   (B2B paid surfaces must filter to commercial:true sources only — RiverSignal
                    reports should not embed iNat photos unless we add CC-BY-only filtering)
✓ wqp            — 412 monitoring stations in bbox             — Public Domain, commercial:true
⚠ fishing        — state is MT (not OR); existing adapter is ODFW-only → NEW adapter required
                   (target source: MT FWP fishing reports + stocking schedule)
                   — anticipated license: Public Records, commercial:true
⚠ state_geology  — state is MT; no MBMG adapter exists → NEW adapter required
                   (target source: Montana Bureau of Mines and Geology web services)
                   — license depends on dataset; verify per-feed before authoring
✗ deq_303d       — Montana DEQ 303(d) list is PDF-only, no structured feed
                   → manual JSON import + scheduled re-check
                   — license: Public Records (statute permits republishing)
✗ curated_hatch_chart — entomologist input required; auto-seed from nearest existing watershed
                       (mckenzie hatch chart) with `needs_entomologist_review=true`
                       — license: this project's hand-curated content, commercial:true
```

The license + commercial column lands in the §1.4 gap-report table as a column, and in the
§2.2 new-adapter checklist as step 5.

### 1.4 Gap report + recommendations

A markdown table at the end of the inventory listing every `⚠` or `✗` from §1.3 with:

| Gap | Recommended fill | Cost / effort | License + commercial | Blocker for v1? |
|---|---|---|---|---|
| MT FWP stocking | New adapter (~1d) following `fishing.py` pattern | dev time | Public Records, commercial:true | no — auto-draft v0 with empty schedule |
| MBMG geology | New adapter; check ArcGIS REST service availability | dev time + API discovery | varies — verify per dataset | no — DeepTrail can ship with macrostrat-only for v1 |
| MT DEQ 303(d) | Manual JSON import; quarterly recheck | curator | Public Records, commercial:true | no — RiverSignal view degrades gracefully |

**Stop conditions for Step 1:** if the agent finds a required-for-v1 source that requires an
unobtainable API key, halt and report. Otherwise: proceed to Step 2 with all `⚠` items listed as
follow-on beads and all `✗` items as deferred (documented in the inventory).

---

## STEP 2 — Pipeline implementation

For each phase, **commit on green** (lint + type-check + tests pass) and reference the inventory
report path in the commit message. Use `ddx bead` if HELIX tracking is active.

### 2.1 Watershed config

Add an entry to `pipeline/config/watersheds.py`:

```python
"<WATERSHED_SLUG>": {
    "name": "<WATERSHED_DISPLAY>",
    "description": "<headwaters>...<mouth confluence sentence>",
    "bbox": { "north": ..., "south": ..., "east": ..., "west": ... },
}
```

Bbox must be the refined value from §1.2, not the user-supplied `BBOX_HINT`.

### 2.2 New state-agency adapters (only when §1.3 flagged `NEW adapter required`)

**ADR-008 requirement.** Every new adapter MUST declare a license + commercial-use flag, per
`docs/helix/02-design/adr/ADR-008-source-license-tagging.md`. The ADR specifies a
`SOURCE_META` dict, which **is not implemented in the codebase yet** as of this runbook's
verification date — until it lands, declare the license in two places:

1. The §1.3 inventory check line for the source
2. The adapter file's module docstring (top of the new `.py`), in this form:

   ```python
   """<Adapter name> — <one-line purpose>.

   Source: <upstream-url>
   License: <CC0 | Public Domain | CC BY 4.0 | CC BY-NC | Public Records | ...>
   commercial: <true|false>  # whether OK for B2B paid surfaces
   Attribution: "<exact text and link target the UI must render>"
   """
   ```

When ADR-008's `SOURCE_META` runtime structure lands, the docstring metadata moves into it. Until
then, the docstring is the canonical source of truth.

For each new adapter:

1. **Adapter file** — either a new `pipeline/ingest/<name>.py` (one adapter per file is the most
   common pattern: `usgs.py`, `snotel.py`, `washington.py`, `utah.py`) OR add a class to an
   existing domain file when a related adapter already lives there (e.g., DOGAMI, BLM-SMA, MRDS,
   macrostrat, PBDB, iDigBio all live inside `pipeline/ingest/geology.py`). Prefer the existing-file
   pattern when the new adapter is the same data domain as something already there.
2. Inherit `IngestionAdapter` (from `pipeline.ingest.base`) and define `source_type = "<name>"`
   (e.g., `"mt_fwp"`, `"mbmg"`). **Use the same string as the CLI key in step 7 and the
   `SOURCE_REFRESH_HOURS` / `SOURCE_LABELS` keys in steps 5–6** — don't introduce another
   naming divergence (see §2.3 caveat).
3. Implement `ingest()` returning `(records_created, records_updated)`; write to existing bronze
   tables where shape matches (`observations`, `time_series`, `interventions`, `mineral_deposits`,
   etc.). Create new bronze tables only when the shape genuinely doesn't fit.
4. Log to `ingestion_jobs` via `self.create_job()` / `self.complete_job()` — the freshness
   endpoint depends on this. `create_job()` uses `self.site_id` from the constructor, so the
   adapter receives a site via `pipeline/cli.py`'s per-site loop — no extra wiring needed.
5. **License + commercial-use declaration (ADR-008).** Module docstring per the template above.
   Once ADR-008's `SOURCE_META` runtime dict lands, add an entry there too — until then, the
   docstring is canonical.
6. Add the new source to `app/routers/data_status.py:SOURCE_REFRESH_HOURS` with the appropriate
   cadence (daily/weekly/monthly).
7. Add the human label to `frontend/src/hooks/useFreshness.ts:SOURCE_LABELS`.
8. Register the adapter in `pipeline/cli.py`'s `adapters` dict inside the `ingest()` function so
   `python -m pipeline.cli ingest <source> -w all` works.
9. **Watershed-scoping caveat.** Existing state adapters hard-code which watersheds they cover
   inside the adapter body. Examples:
   - `pipeline/ingest/washington.py`: `if site.watershed not in ("skagit",): skip`
   - `pipeline/ingest/utah.py`:       `if site.watershed not in ("green_river",): skip`
   - `pipeline/ingest/fishing.py` (ODFW): includes a `("skagit", "green_river")` allowlist
   When adding a watershed to a state whose adapter already exists, the agent **MUST also update
   the existing adapter's scoping tuple** to include the new watershed slug — otherwise the
   `python -m pipeline.cli ingest <state> -w <new_watershed>` invocation silently does nothing
   for the new watershed.
10. Write a unit test in `tests/test_ingest_<source>.py` with a recorded HTTP fixture (use the
    `httpx` recorder pattern from existing adapter tests if present, otherwise vcrpy or a static
    JSON fixture).

Each adapter ships as its own commit.

### 2.3 Run all applicable existing adapters scoped to the new watershed

In this order (each command is one commit-worthy log entry; failures are captured but don't halt):

```
python -m pipeline.cli ingest wbd          -w <WATERSHED_SLUG>
python -m pipeline.cli ingest nhdplus      -w <WATERSHED_SLUG>
python -m pipeline.cli ingest usgs         -w <WATERSHED_SLUG>
python -m pipeline.cli ingest snotel       -w <WATERSHED_SLUG>
python -m pipeline.cli ingest prism        -w <WATERSHED_SLUG>
python -m pipeline.cli ingest mtbs         -w <WATERSHED_SLUG>
python -m pipeline.cli ingest inaturalist  -w <WATERSHED_SLUG>
python -m pipeline.cli ingest wqp          -w <WATERSHED_SLUG>
python -m pipeline.cli ingest wqp_bugs     -w <WATERSHED_SLUG>
python -m pipeline.cli ingest gbif         -w <WATERSHED_SLUG>
python -m pipeline.cli ingest biodata      -w <WATERSHED_SLUG>
python -m pipeline.cli ingest recreation   -w <WATERSHED_SLUG>
python -m pipeline.cli ingest blm_sma      -w <WATERSHED_SLUG>
python -m pipeline.cli ingest macrostrat   -w <WATERSHED_SLUG>
python -m pipeline.cli ingest pbdb         -w <WATERSHED_SLUG>
python -m pipeline.cli ingest idigbio      -w <WATERSHED_SLUG>
python -m pipeline.cli ingest mrds         -w <WATERSHED_SLUG>
python -m pipeline.cli ingest restoration  -w <WATERSHED_SLUG>
python -m pipeline.cli ingest wetlands     -w <WATERSHED_SLUG>   # NWI; freshness key is 'nwi' — see naming-divergence note below
python -m pipeline.cli ingest impaired     -w <WATERSHED_SLUG>   # OR/WA only (EPA 303(d)); freshness key is 'deq_303d'
python -m pipeline.cli ingest fish_passage -w <WATERSHED_SLUG>   # freshness key is 'fish_barrier'
python -m pipeline.cli ingest streamnet    -w <WATERSHED_SLUG>   # PNW only — skip if outside
python -m pipeline.cli ingest dogami       -w <WATERSHED_SLUG>   # OR only — skip if outside
python -m pipeline.cli ingest washington   -w <WATERSHED_SLUG>   # WA only — skip if outside (see scoping caveat in §2.2)
python -m pipeline.cli ingest utah         -w <WATERSHED_SLUG>   # UT only — skip if outside
python -m pipeline.cli ingest fishing      -w <WATERSHED_SLUG>   # ODFW; OR + (currently) skagit + green_river — see scoping caveat in §2.2
python -m pipeline.cli ingest <new-state-adapters from §2.2>
python -m pipeline.ingest.nws_observations              # whole-platform; new watershed picked up via WS_COORDS
python -m pipeline.ingest.nws_observations forecasts
```

Skip-conditions for state-bound adapters are inferred from `WATERSHED_STATES`.

**Naming-divergence caveat.** Four existing CLI keys differ from the source IDs the adapters
actually write to `ingestion_jobs.source_type` and/or from the keys registered in
`app/routers/data_status.py:SOURCE_REFRESH_HOURS` / `frontend/src/hooks/useFreshness.ts:SOURCE_LABELS`:

| CLI key (pipeline/cli.py adapters dict) | Adapter `source_type` written to ingestion_jobs | Freshness key (SOURCE_REFRESH_HOURS / SOURCE_LABELS) |
|---|---|---|
| `fish_passage` | `fish_passage` (matches CLI) | `fish_barrier` (label only) |
| `impaired`     | `impaired` (matches CLI)     | `deq_303d`   (label only) |
| `wetlands`     | `wetlands` (matches CLI)     | `nwi`        (label only) |
| `wqp`          | **`owdp`** (does NOT match)  | `wqp` (registered) — no `owdp` entry, so OWDP rows silently fall through to default cadence and render literally as "owdp" in the freshness UI |

When authoring a new state-agency adapter (§2.2), pick **one** name and use it in all three places
(CLI key, `source_type` written to `ingestion_jobs`, `SOURCE_REFRESH_HOURS` / `SOURCE_LABELS` key).
The wqp/owdp row above is a pre-existing freshness-reporting bug — flag it in the verification
report (§3.6) if the new watershed touches the WQP adapter. Don't replicate this pattern.

### 2.4 v0 curation drafts (auto-write, mark `needs_review=true`)

1. **`silver.river_reaches` seed migration** — author 3-5 reaches per the rules below; write a new
   alembic revision named `<rev>_seed_<WATERSHED_SLUG>_reaches.py`.
   - Reach boundaries derived from: USGS gauge locations, dams/reservoirs, named confluences,
     state regulation boundaries when available.
   - For each reach populate: `id` (snake_case like `<slug>_upper`), `watershed`, `name`,
     `short_label`, `centroid_lat`, `centroid_lon`, `river_mile_start/end` (NULL if NHDPlus
     unclear), `bbox`, `primary_usgs_site_id`, `primary_snotel_station_id`,
     `general_flow_bearing` (degrees compass; NULL if reach is too sinuous),
     `typical_species` (varchar[]; copy from nearest analogous reach in an existing watershed),
     `is_warm_water` (true for bass/panfish-dominated lower reaches), `notes='needs_guide_review=true; auto-seeded <date>'`,
     `source='v0 auto-seed — needs guide review'`.
   - Idempotent: `ON CONFLICT (id) DO NOTHING`.
2. **`silver.flow_quality_bands` seed migration** — for each reach, compute cfs band from USGS
   daily-value medians for the reach's primary gauge:
   - `cfs_ideal_low = 30th percentile`
   - `cfs_ideal_high = 70th percentile`
   - `cfs_low = 10th percentile`
   - `cfs_high = 90th percentile`
   - `source='derived from USGS daily-value medians, needs angler review'`.
3. **`curated_hatch_chart` seed** — copy the nearest-analogous existing watershed's hatch chart
   (by ecoregion / dominant fishery type — e.g., for a Rocky Mountain trout river, copy
   `metolius`; for a desert Southwest river, copy nothing and leave empty) with the new
   watershed slug and `source='v0 — needs entomologist review'`.
4. **River story draft** — `pipeline/generate_river_stories.py <WATERSHED_SLUG>` produces an
   LLM-grounded narrative; mark `is_draft=true` in metadata so the UI can show a "draft" badge
   if it wants to.
5. **Stocking** — if no state stocking adapter exists yet, insert an empty placeholder row in
   `stocking_schedule` derived view's source table with `source='manual_pending'` so the UI
   renders an "Updates coming" empty state rather than crashing.

Each draft seed = one commit, message format:
`v0 seed: <WATERSHED_SLUG> <artifact> — needs_review=true`.

### 2.5 Refresh medallion layers

```
python -m pipeline.cli refresh --mode light   # silver + fast gold views
python -m pipeline.cli refresh --mode heavy   # slow gold views
python -m pipeline.jobs.tqs_daily_refresh     # TQS compute for the new watershed
```

After refresh, smoke-check that `gold.trip_quality_daily` has rows for the new watershed and that
`gold.trip_quality_watershed_daily` (the MAX rollup view) reports a best reach.

### 2.6 Wire frontend

Grep first to find every dict that needs the new entry, then edit each. The slug-string is the
load-bearing thing — both `WATERSHED_ORDER` lists (alphabetized) and `WATERSHED_LABELS` /
`WS_COORDS` / `WS_GAUGES` dicts are duplicated across multiple files. Update them all in one pass:

```
rg -n '"mckenzie"' --type ts --type py --type tsx app/ frontend/src/ pipeline/
```

Expected hits at minimum (as of 2026-05-15):

| File | Symbol(s) |
|---|---|
| `app/routers/weather.py` | `WS_COORDS`, `WS_GAUGES` |
| `pipeline/ingest/nws_observations.py` | `WS_COORDS` (kept in sync with weather.py) |
| `pipeline/jobs/ncei_backfill.py` | imports `WS_COORDS` from `nws_observations` |
| `frontend/src/components/WatershedHeader.tsx` | `WATERSHED_ORDER`, `WATERSHED_LABELS` |
| `frontend/src/pages/HomePage.tsx` | `WATERSHED_ORDER` (duplicated) |
| `frontend/src/pages/RiverNowPage.tsx` | `WATERSHED_ORDER` + local `WS_CENTERS` (for geology/fossils SWR keys) |
| `frontend/src/pages/SavedPage.tsx` | `WATERSHED_LABELS` (duplicated) |
| `frontend/src/pages/SpeciesMapPage.tsx` | per-watershed centroid map |
| `frontend/src/pages/ExploreMapPage.tsx` | per-watershed centroid map |
| `frontend/src/pages/MyObsMapPage.tsx` | per-watershed centroid map |
| `frontend/src/pages/StockingMapPage.tsx` | per-watershed centroid map |
| `frontend/src/components/PhotoObservation.tsx` | per-watershed centroid map |
| `frontend/tests/*.spec.ts` | fixture watersheds in Playwright specs |
| `tests/*.py` | any test fixturing watershed lists |

The grep is the source of truth — if it returns more files than the table lists, update all of
them. Skipping one usually shows up as a watershed-picker missing the option or a map page
defaulting back to McKenzie.

Run `npx tsc -p tsconfig.app.json --noEmit` and `npx vite build` after the frontend edits.

### 2.7 Terraform — append new adapter args to Cloud Run Jobs

For every new adapter authored in §2.2, append to the appropriate job's args in
`terraform/cloud_run_jobs.tf` (at the END of the `&&` chain — failures don't short-circuit upstream).

Plan with targeted apply:

```
cd terraform
terraform plan -target=google_cloud_run_v2_job.pipeline_daily  \
               -target=google_cloud_run_v2_job.pipeline_weekly \
               -target=google_cloud_run_v2_job.pipeline_monthly
```

Apply only after the user reviews. Take a Cloud SQL backup first if any change touches the SQL
instance (look for `google_sql_database_instance.db` in the plan — should NOT appear for arg-only
changes).

### 2.8 Commit, push, deploy

```
git add -p   # commit per artifact category
git push origin main
gh run watch <latest-run-id>
```

After the deploy completes, manually trigger one ingest run so the new watershed has data on prod
*today* instead of waiting for tomorrow's cron:

```
gcloud run jobs execute riversignal-pipeline-daily   --region us-west1 --wait
gcloud run jobs execute riversignal-pipeline-weekly  --region us-west1 --wait
gcloud run jobs execute riversignal-pipeline-monthly --region us-west1 --wait
gcloud run jobs execute riversignal-tqs-daily-refresh --region us-west1 --wait
curl -s -X POST "https://riversignal-api-500769847975.us-west1.run.app/api/v1/data-status/refresh"
```

---

## STEP 3 — Testing & verification

**Output:** `docs/helix/06-iterate/watershed-add/<WATERSHED_SLUG>-verification-<YYYY-MM-DD>.md`

### 3.1 Schema-level checks (local DB)

For each bronze table that *should* now hold data for this watershed, verify row counts > 0:

```sql
SELECT 'observations'   AS tbl, count(*) FROM observations            WHERE site_id IN (SELECT id FROM sites WHERE watershed = :ws)
UNION ALL
SELECT 'time_series',         count(*) FROM time_series      ts JOIN sites s ON s.id = ts.site_id WHERE s.watershed = :ws
UNION ALL
SELECT 'fire_perimeters',     count(*) FROM fire_perimeters  fp JOIN sites s ON s.id = fp.site_id WHERE s.watershed = :ws
UNION ALL
SELECT 'curated_hatch_chart', count(*) FROM curated_hatch_chart WHERE watershed = :ws
UNION ALL
SELECT 'river_reaches',       count(*) FROM silver.river_reaches    WHERE watershed = :ws
UNION ALL
SELECT 'flow_quality_bands',  count(*) FROM silver.flow_quality_bands WHERE reach_id IN (SELECT id FROM silver.river_reaches WHERE watershed = :ws)
UNION ALL
SELECT 'trip_quality_daily',  count(*) FROM gold.trip_quality_daily   WHERE watershed = :ws;
```

Report each row; zero counts are flagged with the gap-report cross-reference (§1.4 entry that
predicted the zero).

### 3.2 Data integrity invariants

- Every reach centroid is inside the watershed bbox.
- Every reach's `primary_usgs_site_id` resolves to a real NWIS gauge (HEAD request to
  `https://waterservices.usgs.gov/nwis/iv/?sites=<id>&format=json`).
- Every flow band satisfies `cfs_low ≤ cfs_ideal_low ≤ cfs_ideal_high ≤ cfs_high`.
- `gold.trip_quality_daily.tqs` rows are all in [0, 100]; `is_hard_closed = true` rows are all
  in [0, 29].
- No orphaned foreign keys (every `reach_id` reference resolves to `silver.river_reaches.id`).

### 3.3 API smoke (local)

Hit each watershed-scoped endpoint and confirm a non-empty response:

Local API listens on `:8001` per `frontend/src/config.ts` default. Each `jq` filter below has
been verified against the actual response shape — don't paraphrase or guess:

```
curl -s "http://localhost:8001/api/v1/sites/<WATERSHED_SLUG>"             | jq '.name, .watershed'
curl -s "http://localhost:8001/api/v1/reaches?watershed=<WATERSHED_SLUG>" | jq '.reaches | length'
curl -s "http://localhost:8001/api/v1/trip-quality?date=$(date -I)&watershed=<WATERSHED_SLUG>" | jq '.watershed_tqs, .best_reach_id'
curl -s "http://localhost:8001/api/v1/sites/<WATERSHED_SLUG>/conditions/live" | jq '.gauge_count, (.readings | length)'
curl -s "http://localhost:8001/api/v1/sites/<WATERSHED_SLUG>/weather"     | jq '.periods | length'   # NWS 7-day forecast (endpoint is /weather, not /forecast)
curl -s "http://localhost:8001/api/v1/sites/<WATERSHED_SLUG>/snowpack"    | jq '.stations | length'
curl -s "http://localhost:8001/api/v1/sites/<WATERSHED_SLUG>/recreation"  | jq 'length'             # endpoint returns the array directly
curl -s "http://localhost:8001/api/v1/sites/<WATERSHED_SLUG>/story"       | jq '.events | length'   # timeline payload — no .narrative key
curl -s "http://localhost:8001/api/v1/sites/<WATERSHED_SLUG>/species"     | jq 'length'             # endpoint returns the array directly
curl -s "http://localhost:8001/api/v1/data-status/freshness" | jq --arg w <state-adapter-source> '.sources[$w]'
```

Each should return a non-error payload with watershed-specific values.

### 3.4 API smoke (prod, after deploy)

Same URLs, but against
`https://riversignal-api-500769847975.us-west1.run.app/api/v1/...`. Plus a force-refresh:

```
curl -s -X POST "https://riversignal-api-500769847975.us-west1.run.app/api/v1/data-status/refresh"
```

If any prod endpoint returns 404 or empty where local returned data, the most likely cause is a
deploy lag or terraform args drift — diagnose before declaring done.

### 3.5 UI smoke

Playwright specs live in `frontend/tests/` (e.g., `riverpath-mvp.spec.ts`, `species-map.spec.ts`).
Run with:

```
cd frontend && npx playwright test --grep <WATERSHED_SLUG>
```

If no spec matches the new slug, copy the structure of `frontend/tests/riverpath-mvp.spec.ts`
and parameterize it for the new watershed.

Otherwise, manual smoke against `npm run dev`:

- Navigate to `/path/now/<WATERSHED_SLUG>` — page renders without console errors, Go Score pill
  shows a number, hero shows live values, River Story has draft narrative.
- Open the watershed picker — new watershed is in the list, alphabetized.
- Tap the Go Score pill — why-panel opens with all 6 sub-scores (weather may be 50 if NWS hasn't
  ingested yet — that's expected on day 0).
- Open the 14-day forecast modal — shows ≥ 7 day cards with valid scores.
- `/path/where?lat=&lon=&max_miles=` returns the new watershed in ranking if within distance.
- DeepTrail surfaces: `/trail/story/<location>` etc render geology + fossil counts > 0.

### 3.6 Feature-coverage report

Final section of the verification doc — a checkbox grid mapping every feature row from §1.1 to
its actual status on prod:

```
| App         | Feature                | Has data? | Notes                                              |
|-------------|------------------------|-----------|----------------------------------------------------|
| RiverSignal | Site dashboard         | ✓         | 14 gauges, 8.2k time-series rows                   |
| RiverSignal | Restoration tracking   | ✓         | 18 OWRI projects in bbox                            |
| RiverSignal | Fire recovery          | ✓         | 3 MTBS perimeters; 1 (2021) ≥ "high severity"      |
| RiverPath   | Go Score               | ✓         | 5 reaches, weather still 50 until tomorrow's cron  |
| RiverPath   | River Story            | ⚠         | draft only, marked is_draft=true                   |
| RiverPath   | Stocking               | ✗         | MT FWP adapter pending — placeholder row only       |
| DeepTrail   | Geology units          | ⚠         | macrostrat only — MBMG adapter pending             |
| DeepTrail   | Fossil sites           | ✓         | 22 PBDB + 47 iDigBio records                       |
| ...         | ...                    | ...       | ...                                                 |
```

Every `⚠` or `✗` corresponds to a §1.4 gap. The verification doc closes by listing the follow-on
beads created during the work, with priority hints (P1 = blocks RiverPath ship, P2 = degraded
feature, P3 = nice-to-have).

---

## Cross-cutting requirements (apply throughout)

- **Never destroy data.** Backup before any infra change. Idempotent inserts only.
- **Migrations are append-only.** New alembic revisions, never edit shipped revisions.
- **Commit per artifact.** A single sprawling commit hides intent. Per-adapter, per-seed, per-wiring.
- **HELIX authority order.** When sources disagree with curated data, curated wins. When data
  disagrees with code, fix the code.
- **No silent failure.** Every ingest failure logs to `ingestion_jobs` with `status='failed'` so
  the freshness endpoint surfaces it.
- **Anonymous-first.** Nothing in the watershed-onboarding flow can require auth — adapters write
  watershed-scoped public data.
- **Cost discipline.** LLM calls (river story, narrative) cached per-watershed and reused.
- **Curation flags are load-bearing.** Anything `needs_review=true` must be visible in a follow-up
  inventory query — don't bury it in a notes field that nobody greps.

## Pause / escalation triggers (stop and ask)

1. A required-for-v1 state adapter needs a developer key or paid API access the agent can't
   obtain. → Halt, open a bead, ask the user.
2. Terraform plan shows any change to `google_sql_database_instance.db` settings, network, or
   IAM bindings. → Stop, take a backup, present the plan, ask before applying.
3. A bbox refinement would force resizing of an *existing* watershed's bbox (overlap conflict).
   → Stop and ask which boundary wins.
4. Migrations conflict with the current head revision (someone else's branch is in flight).
   → Stop, rebase, present the resolution plan, ask before applying.

Everything else is flag-and-continue.

---

## Deliverables checklist

By the end of a successful run:

- [ ] `docs/helix/06-iterate/watershed-add/<slug>-source-inventory-<date>.md` (Step 1)
- [ ] Watershed entry in `pipeline/config/watersheds.py`
- [ ] All applicable existing adapters run; rows landed in bronze
- [ ] New state adapters (if any) merged with tests
- [ ] Alembic seed migrations: river_reaches, flow_quality_bands, hatch_chart, stocking placeholder
- [ ] `gold.trip_quality_daily` populated for the new watershed
- [ ] Frontend dicts updated (`WATERSHED_LABELS`, `WATERSHED_ORDER`, `WS_COORDS`, `WS_GAUGES`, etc.)
- [ ] Terraform args updated for new adapter scheduling
- [ ] Commits pushed; CI deploy succeeded
- [ ] Manual one-shot ingest runs on prod completed
- [ ] `/data-status/refresh` POST'd to bust the cache
- [ ] `docs/helix/06-iterate/watershed-add/<slug>-verification-<date>.md` (Step 3) with the
      feature-coverage grid
- [ ] Follow-on beads created for every `⚠` / `✗` from the verification grid

If any checkbox is unchecked at the end of the run, the report explains why and what's needed to
close it.
