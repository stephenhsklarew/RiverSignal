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

## Reference example: McKenzie watershed — what "fully loaded" looks like

McKenzie is the most-complete tracked watershed today. Every row count below was measured against
the local DB on 2026-05-15 and the prod `/data-status` endpoint; numbers will shift as new ingest
runs land, but the *shape* (which adapters write to which tables, what features end up lit up)
is the durable reference. When the agent finishes a new watershed and the verification grid in
§3.6 looks materially shorter than this table, something was skipped.

### Watershed config (the starting point)

```python
# pipeline/config/watersheds.py
"mckenzie": {
    "name": "McKenzie River",
    "description": (
        "McKenzie River watershed from headwaters to confluence with "
        "Willamette, including Blue River and South Fork"
    ),
    "bbox": { "north": 44.45, "south": 43.85, "east": -121.70, "west": -123.10 },
},
```

Headwaters: Clear Lake (~44.40°N). Mouth: Willamette confluence at Eugene (~44.08°N, -123.10°W).
Three curated reaches in `silver.river_reaches` (`mckenzie_upper`, `mckenzie_middle`,
`mckenzie_lower`) anchored on USGS gauges `14159200` / `14162200` / `14165500`.

### Adapters that touch McKenzie (every live ingest)

| CLI key | `ingestion_jobs.source_type` | Cadence | Source URL | License | Commercial-OK | Bronze table(s) written |
|---|---|---|---|---|---|---|
| `inaturalist` | `inaturalist` | daily | api.inaturalist.org/v1 | CC-BY-NC (mixed photo licenses; many CC-BY) | **false** for photo URLs; observation metadata true | `observations`, `time_series` |
| `usgs` | `usgs` | daily | waterservices.usgs.gov/nwis | Public Domain | true | `observations`, `time_series` |
| `snotel` | `snotel` | daily | wcc.sc.egov.usda.gov/awdbRestApi | Public Domain | true | `observations`, `time_series` |
| (job) | `nws` | daily | api.weather.gov | Public Domain | true | `bronze.weather_observations` |
| (job) | `nws_forecast` | daily | api.weather.gov | Public Domain | true | `bronze.weather_forecasts` |
| `fishing` | `fishing` | weekly | dfw.state.or.us (ODFW) | Public Records (OR) | true | `interventions` (stocking), `harvest_trends` (catch counts) |
| `wqp` | `owdp` *(divergence)* | weekly | waterqualitydata.us | Public Domain | true | `observations` (WQ measurements) |
| `washington` | `washington` | weekly | data.wa.gov + WDFW | Public Records (WA) | true | `interventions` (stocking) — currently scoped to Skagit only |
| `mtbs` | `mtbs` | quarterly | apps.fs.usda.gov/arcx (MTBS) | Public Domain | true | `fire_perimeters` |
| `nhdplus` | `nhdplus` | annual | hydro.nationalmap.gov | Public Domain | true | `stream_flowlines` |
| `wbd` | `wbd` | annual | hydro.nationalmap.gov | Public Domain | true | `watershed_boundaries` |
| `impaired` | `impaired` *(label `deq_303d`)* | quarterly | gispub.epa.gov ATTAINS | Public Domain | true | `impaired_waters` |
| `wetlands` | `wetlands` *(label `nwi`)* | annual | fwspublicservices.wim.usgs.gov | Public Domain | true | `wetlands` |
| `prism` | `prism` | monthly | data.prism.oregonstate.edu | Academic Free | true | `time_series` (PRISM climate) |
| `restoration` | `restoration` | monthly | OWRI / NOAA RC / PCSRF | Public Records | true | `interventions` |
| `recreation` | `recreation` | monthly | RIDB + OSMB + state parks | Public Domain / Public Records | true | `recreation_sites` |
| `biodata` | `biodata` | monthly | aquatic.biodata.usgs.gov | Public Domain | true | `observations`, `time_series` |
| `wqp_bugs` | `wqp_bugs` | monthly | waterqualitydata.us (macroinverts) | Public Domain | true | `observations` |
| `gbif` | `gbif` | monthly | gbif.org | CC-BY 4.0 | true | `observations`, `fossil_occurrences` |
| `idigbio` | `idigbio` | monthly | api.idigbio.org | CC0 / CC-BY (varies) | true | `fossil_occurrences` |
| `pbdb` | `pbdb` | monthly | paleobiodb.org | CC-BY 4.0 | true | `fossil_occurrences` |
| `streamnet` | `streamnet` | monthly | streamnet.org | Public Records (PNW co-op) | true | `observations` (fish counts) |
| `fish_passage` | `fish_passage` *(label `fish_barrier`)* | quarterly | streamnet + state passage feeds | Public Records | true | `interventions` (barrier rows) |
| `macrostrat` | `macrostrat` | annual | macrostrat.org/api/v2 | CC-BY 4.0 | true | `geologic_units` |
| `blm_sma` | `blm_sma` | annual | gis.blm.gov | Public Domain | true | `land_ownership` |
| `dogami` | `dogami` | annual | gis.dogami.oregon.gov (OR only) | Public Records (OR) | true | `geologic_units` |
| `mrds` | `mrds` | annual | mrdata.usgs.gov | Public Domain | true | `mineral_deposits` |

Note the three CLI-key vs source-type divergences flagged earlier (impaired/deq_303d,
wetlands/nwi, fish_passage/fish_barrier) plus the wqp→owdp source-type mismatch. New adapters
must not introduce more.

### Manually curated tables (no adapter — humans seed these)

| Table | McKenzie rows | What it holds | Where the curator edits |
|---|---|---|---|
| `silver.river_reaches` | 3 | Upper/Middle/Lower reach defs with gauge + species + bbox | alembic seed migration |
| `silver.flow_quality_bands` | 3 | cfs ideal/low/high band per reach | alembic seed migration |
| `silver.tqs_seasonal_modifiers` | 3 (cross-watershed) | Dry-fly summer / winter steelhead / spring runoff weight nudges | one seed migration, applies to all watersheds |
| `curated_hatch_chart` | 10 | Aquatic insect emergence windows per species | hand-curated; **entomologist-reviewed** |
| `fly_shops_guides` | 5 (where `'mckenzie' = ANY(watersheds)`) | Fly shop + guide service directory: name, type, city, address, lat/lon, phone, website | manual research per watershed |
| `mineral_shops` | 2 | Rock & mineral shop directory: name, city, address, lat/lon, phone, website | manual research per watershed |
| `rockhounding_sites` | 2 (via `watersheds text[]`) | Legal-collecting sites with land owner + collecting-rules + nearest town. Lean conservative — liability risk on bad entries | manual curation from BLM + USFS districts + published rockhound guides |
| `river_stories` | 3 | LLM-drafted river narrative at 3 reading levels (adult/kids/expert) | `python -m pipeline.generate_river_stories -w mckenzie` |
| `deep_time_stories` | 29 (cross-watershed) | LLM-drafted geology story per significant location | DeepTrail curator + LLM |
| `fly_tying_videos` | 47 (cross-watershed) | YouTube tutorial links per fly pattern | manually curated from named channels |
| `mineral_sites` photos | ~137 | Wikimedia-Commons photos matched per commodity | static lookup table |

### Bronze rows landed for McKenzie (sampled 2026-05-15)

| Table | Rows | Driven by |
|---|---|---|
| `time_series` | 403,493 | usgs + snotel + prism + biodata + wqp_bugs |
| `stream_flowlines` | 129,069 | nhdplus |
| `observations` | 76,306 | inaturalist + usgs + biodata + wqp + streamnet |
| `geologic_units` | 35,998 (cross-watershed) | macrostrat + dogami |
| `interventions` | 550 | fishing + washington + restoration + fish_passage + streamnet stocking |
| `wetlands` | 4,500 | wetlands (NWI) |
| `watershed_boundaries` | 320 | wbd |
| `impaired_waters` | 318 | impaired (EPA ATTAINS) |
| `recreation_sites` | 221 | recreation (RIDB + OSMB) |
| `mineral_deposits` | 137 | mrds |
| `fire_perimeters` | 63 | mtbs (Holiday Farm 2020 + smaller historic fires) |
| `fossil_occurrences` | 23 | pbdb + idigbio + gbif |

### Gold tables that surface McKenzie data

| MV / view | Rows (McKenzie) | Feeds which app/feature |
|---|---|---|
| `gold.water_quality_monthly` | 9,084 | RiverSignal trends + reports |
| `gold.river_miles` | 8,385 | river-mile lookup powering species-by-reach + reach selector |
| `gold.species_gallery` | 7,031 | RiverPath species cards + photo grid |
| `gold.hatch_chart` | 784 | RiverPath Hatch tab |
| `gold.swim_safety` | 638 | RiverPath swim-safety badge |
| `gold.river_story_timeline` | 517 | RiverPath River Story narrative timeline |
| `gold.stocking_schedule` | 274 | RiverPath stocking section |
| `gold.trip_quality_daily` | 273 (3 reaches × 91 days) | RiverPath Go Score + ranking |
| `gold.trip_quality_history` | 273 | Go Score trend slope + alert engine |
| `gold.post_fire_recovery` | 114 | RiverSignal restoration + RiverPath River Story |
| `gold.trip_quality_watershed_daily` | 91 (1 row/day) | Go Score watershed pill + `/path/where` ranking |
| `gold.species_by_reach` | 75 | RiverPath fish-present cards |
| `gold.fishing_conditions` | 65 | RiverSignal angling dashboard |
| `gold.cold_water_refuges` | 54 | RiverPath swim-safety + RiverSignal thermal refugia |
| `gold.stewardship_opportunities` | 34 | RiverPath Steward tab |
| `gold.river_health_score` | 27 | RiverSignal scorecard + RiverPath River Now |
| `gold.indicator_species_status` | 12 | RiverSignal indicator metrics |
| `gold.harvest_trends` | 8 | RiverPath catch-history sparkline |
| `gold.species_trends` | 8 | RiverSignal species-trend dashboards |
| `gold.site_ecological_summary` | 8 | RiverSignal site summary card |
| `gold.watershed_scorecard` | 1 | RiverSignal one-page scorecard |

### Pipelines (Cloud Run Jobs) and what they refresh for McKenzie

| Job | Schedule | Runs (in order) | Watershed-scoped touch for McKenzie |
|---|---|---|---|
| `riversignal-pipeline-daily` | 02:00 PT | `inaturalist -w all && snotel -w all && usgs -w all && nws && nws forecasts` | new observations + time-series + weather rows; ingestion_jobs entries for all 5 sources |
| `riversignal-pipeline-weekly` | Mon 04:00 PT | `fishing -w all && wqp -w all && washington -w all && utah -w green_river` | stocking + WQ updates; harvest_trends MV inputs |
| `riversignal-pipeline-monthly` | 1st @ 05:00 PT | `biodata && wqp_bugs && gbif && recreation && pbdb && restoration && prism && streamnet && idigbio` | climate + biodiversity + restoration refresh |
| `riversignal-refresh-views` | 10:00 PT daily | `pipeline.cli refresh --mode light` | silver layer + fast gold views |
| `riversignal-refresh-heavy` | Sun 03:00 PT | `pipeline.cli refresh --mode heavy` | slow gold views (species_gallery, river_miles, etc.) |
| `riversignal-tqs-daily-refresh` | 10:30 PT daily | `pipeline.jobs.tqs_daily_refresh` | recompute `gold.trip_quality_daily` for McKenzie's 3 reaches × 91 days + append `trip_quality_history` snapshot |
| `riversignal-migrate` | on deploy | `alembic upgrade head` | schema changes; not McKenzie-specific |

### Feature surfaces lit up for McKenzie (the success criterion)

| App | Feature | Lit up today? | Driven by |
|---|---|---|---|
| RiverSignal | Site dashboard | ✓ | `gold.site_ecological_summary` + `gold.river_health_score` + `gold.water_quality_monthly` |
| RiverSignal | Scorecard | ✓ | `gold.watershed_scorecard` |
| RiverSignal | Restoration tracking | ✓ | `interventions` (550 rows incl. Holiday Farm Fire restoration projects) |
| RiverSignal | Fire recovery | ✓ | `gold.post_fire_recovery` (114 rows incl. 2020 Holiday Farm) |
| RiverSignal | Predictions | ✓ | `predictions` (LLM-generated; refreshed monthly) |
| RiverPath | Go Score pill + ranking | ✓ | `gold.trip_quality_watershed_daily` + `gold.trip_quality_daily` |
| RiverPath | River Now hero | ✓ | live USGS instantaneous + NWS via `app/routers/weather.py` |
| RiverPath | Hatch tab | ✓ | `gold.hatch_chart` (10 curated species) |
| RiverPath | Steward tab | ✓ | `gold.stewardship_opportunities` (34 rows) |
| RiverPath | River Story | ✓ | `river_stories` (3 reading levels) + `gold.river_story_timeline` (517 events) |
| RiverPath | Species cards | ✓ | `gold.species_gallery` (7,031 rows w/ photos) |
| RiverPath | Stocking | ✓ | `gold.stocking_schedule` (274 rows from ODFW) |
| RiverPath | Swim safety | ✓ | `gold.swim_safety` |
| RiverPath | Snowpack | ✓ | snotel time-series → `gold.fishing_conditions` snowpack column |
| RiverPath | Photo observations | ✓ | inaturalist photos via `gold.species_gallery` |
| RiverPath | Fish passage | ✓ | `interventions` rows where `intervention_type='fish_passage'` |
| RiverPath | 14-day forecast | ✓ | `gold.trip_quality_daily` next 14 days |
| RiverPath | Fly shop directory | ✓ | `fly_shops_guides` (5 McKenzie rows; type='fly_shop' or 'guide') |
| RiverPath | Guide service directory | ✓ | `fly_shops_guides` (subset where type='guide') |
| RiverPath | Guide-availability divergence | ✗ | `bronze.guide_availability` empty — scaffolding only, no live guide adapters yet (cross-watershed gap) |
| DeepTrail | Geology units | ✓ | `geologic_units` (macrostrat + DOGAMI for OR) |
| DeepTrail | Fossil sites | ✓ | `fossil_occurrences` (23 rows: pbdb + idigbio + gbif) |
| DeepTrail | Rockhound sites | ⚠ | `rockhounding_sites` has 2 McKenzie rows — light coverage but legally-conservative; expand only with verified BLM/USFS confirmation |
| DeepTrail | Mineral deposits | ✓ | `mineral_deposits` (137 rows) |
| DeepTrail | Mineral & rock shop directory | ⚠ | `mineral_shops` has 2 McKenzie rows — light; expand via Google + AFMS club rolls |
| DeepTrail | Deep Time story | ⚠ | `deep_time_stories` is cross-watershed; specific McKenzie story coverage depends on `location_id` mapping (see RiverSignal `/trail/story` route) |

**"Fully loaded" means most rows in that table are ✓** — a new watershed won't match these counts
on day 1 (those grow with each weekly ingest), but the *check marks* should be present.
If a new watershed's verification grid in §3.6 has ⚠ or ✗ in a row that McKenzie shows ✓, the
agent missed an adapter or a curation seed — go back to §1.3 and look for the gap.

---

## STEP 0 — Pre-flight clarification (mandatory, before any code or ingest)

Before writing the inventory report, the agent **asks the user** the questions below. Defaults
are shown but the agent must echo the chosen answers back and get explicit acknowledgement. No
work begins until every question has an answer the user has confirmed.

| # | Question | Default | Why it matters |
|---|---|---|---|
| Q1 | **HUC boundary level for the bbox refinement** — HUC8, HUC10, or HUC12? | HUC8 with a 0.05° buffer | HUC10/HUC12 yield tighter bboxes but more excluded edge reaches; HUC8 is forgiving for v0 reach curation. |
| Q2 | **Paid-API tolerance** — if a required-for-v1 source needs a paid developer key (e.g., a commercial state-data API), should the agent stop, ask, and skip? Or skip silently with a documented gap? | Stop and ask | A paid commitment is a business decision, not a technical one. |
| Q3 | **License filter for B2B surfaces** — should the agent gate any non-`commercial:true` sources out of the data pipeline serving RiverSignal (the B2B paid product), even when those sources serve the B2C apps? | Yes — gate non-commercial sources out of RiverSignal queries | ADR-008 mandates this for paid features. iNat photos are the most-common offender. |
| Q4 | **Confluence into an existing tracked watershed** — if the new watershed's mouth flows into one of the seven already-tracked watersheds, may the agent **renumber or re-segment** the existing watershed's reaches to reflect the new tributary? | No — annotate only via `silver.river_reaches.notes`; do not restructure existing reaches | Reach IDs are referenced from `user_reach_watches`, `user_trip_feedback`, `user_trip_intentions`. Renaming silently drops user data. |
| Q5 | **Curation pace** — should the agent ship v0 reach names + flow bands + hatch chart now (all marked `needs_review=true`), or pause and wait for guide-reviewer + entomologist input before shipping any of those tables? | Ship v0, mark for review | Aligns with the runbook's "auto-draft v0" curation policy. Override only if a guide reviewer is already engaged and waiting. |
| Q6 | **Target ship date** — when does the watershed need to appear on prod? Drives whether terraform changes can wait a deploy cycle or need a same-session apply. | No deadline — ship at the next natural deploy cycle | Production deploys require explicit user approval per §2.8; tight deadlines force pre-confirmation. |

Output: a short transcript at the top of the §1 inventory report capturing each Q + answer + the
timestamp the user acknowledged it.

**Do not proceed to §1 without an answer in hand for every question above.**

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
| RiverPath | Fly shop directory | Manually curated business listings (name, address, lat/lon, phone, website) | `fly_shops_guides` table — **manual research per watershed** (Google/Maps + local fly-fishing forums) |
| RiverPath | Guide service directory | Same table as fly shops (rows have `type='guide'` vs `type='fly_shop'`) | `fly_shops_guides` table — **manual research per watershed** |
| RiverPath | Guide-availability divergence (TQS why-panel) | Scraped public booking calendars | `bronze.guide_availability` via `pipeline/ingest/guide_availability.py` — empty until per-guide adapters land (currently scaffolding) |
| RiverPath | Swim safety | USGS temp + flow, NLDAS-derived | derived view |
| RiverPath | Snowpack | NRCS SNOTEL | `snotel` |
| RiverPath | Recreation sites | RIDB (USFS, BLM, NPS, USACE, USBR) + state parks | `recreation` |
| **DeepTrail** | Geology units | Macrostrat, state geology (DOGAMI for OR; WSGS for WY; MBMG for MT; etc.) | `macrostrat`, `dogami` (OR only) — others NEW |
| DeepTrail | Fossil sites | PBDB, iDigBio, state paleo | `pbdb`, `idigbio`, `biodata` |
| DeepTrail | Rockhound sites | BLM PLSS + state rockhounding guides (Falcon, GemTrails) + national-forest district info | `rockhounding_sites` table — **manual curation per watershed**, ~3-10 rows expected |
| DeepTrail | Mineral & rock shop directory | Manually curated business listings | `mineral_shops` table — **manual research per watershed** |
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
5. **Stocking** — if no state stocking adapter exists yet, **do not insert placeholder rows**.
   `gold.stocking_schedule` is a materialized view assembled from state-adapter outputs
   (ODFW via `fishing.py`, WDFW via `washington.py`, UDWR via `utah.py`); it has no
   writable source table that accepts a "manual_pending" sentinel. The RiverPath stocking UI
   already handles the empty-state correctly (verified against Green River, which ships with
   only UDWR data). Instead: open a P2 follow-on bead — *"Author <STATE> stocking adapter for
   <WATERSHED_SLUG>"* — referencing this prompt's §1.3 gap-report line for the source.

6. **Fly shop + guide directory (`fly_shops_guides`)** — research and seed:
   - Source list: Google Maps search for *"fly shop near <nearest town to watershed>"*, ODFW
     guide license registry (or state equivalent), American Fly Fishing Trade Association directory,
     local Trout Unlimited chapter directory, fly-shop websites' "areas we cover" pages.
   - Schema: `(name, type, watersheds[], city, state, address, latitude, longitude, phone, website,
     description)`. `type` is `'fly_shop'` or `'guide'`. `watersheds` is a text[] — a single business
     can serve multiple watersheds (e.g., The Caddis Fly in Eugene serves McKenzie + Willamette).
   - Target: 3-10 rows per watershed. Mark `description` with `(needs_owner_verification — v0 auto-curation YYYY-MM-DD)`
     so a future curator can refresh contact details. Idempotent insert: check by (name, city) before insert.
   - Commit as: `v0 seed: <WATERSHED_SLUG> fly_shops_guides — needs_review=true`.

7. **Mineral & rock shops (`mineral_shops`)** — same pattern, scoped to DeepTrail:
   - Source list: Google Maps "rock shop"/"gem & mineral"/"lapidary" near nearest town; American
     Federation of Mineralogical Societies club directory; state geological society retail member
     lists.
   - Schema: `(name, city, address, latitude, longitude, phone, website, description, watersheds[])`.
   - Target: 1-5 rows per watershed (the table is sparser than fly shops by domain). v0 only —
     same `(needs_owner_verification)` marker.
   - Commit as: `v0 seed: <WATERSHED_SLUG> mineral_shops — needs_review=true`.

8. **Rockhounding sites (`rockhounding_sites`)** — high-care: legal-collecting locations carry
   liability risk if wrong. Required sources for each row:
   - **Land ownership** confirmed via BLM SMA layer (already in DB via `blm_sma`), USFS district
     office, or state DNR holdings. Federal wilderness, national parks, and most state parks
     prohibit collecting — exclude these.
   - **Collecting rules** from the specific managing district (BLM field office, USFS ranger
     district): commercial-collection bans, daily limits, casual-collection-only zones.
   - **Provenance**: cite a published rockhounding guide (Falcon's *Rockhounding Oregon*, etc.)
     or a state mineral society field-trip log. Don't invent sites from forum posts.
   - Schema includes `name, rock_type, latitude, longitude, land_owner, collecting_rules,
     nearest_town, description, watersheds[]`. v0 target: 2-5 rows per watershed; lean conservative.
   - Commit as: `v0 seed: <WATERSHED_SLUG> rockhounding_sites — needs_curator_review=true; legal-collecting verified <DATE>`.

9. **Expert hatch chart (`curated_hatch_chart`)** — already in step 3 above; mentioned here as a
   reminder that it lives alongside the other manually-curated tables and shares the same
   `needs_review` posture. Target: 8-15 species per watershed depending on aquatic-insect diversity.

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
| `frontend/src/pages/HomePage.tsx` | `WATERSHED_ORDER` (duplicated), **`PHOTOS`**, **`WATERSHED_META` (tagline + narrative)** — missed during the Shenandoah onboarding; resulted in a blank splash card |
| `frontend/src/pages/RiverNowPage.tsx` | `WATERSHED_ORDER` + local `WS_CENTERS` (for geology/fossils SWR keys), **`PHOTOS`**, **`TAGLINES`**, `WS_STATE_SOURCES` |
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

### 2.6.5 Pre-launch data seeds (mandatory before Step 3 verification)

Several surfaces are silently empty until their backing data is seeded. The Shenandoah onboarding
shipped with all of these missing and the user found them in the UI — bake them into the runbook
so they're never forgotten again.

For each watershed, write/run the following before Step 3:

| Data | Where | Why | Symptom if missing |
|---|---|---|---|
| `river_stories` rows for all 3 reading levels | Add the new watershed slug to `WATERSHEDS` dict in `pipeline/generate_river_stories.py`, run `python -m pipeline.generate_river_stories --watershed <slug>`, then ship the output as an alembic seed (commit the .txt files under `alembic/data/<slug>_river_stories/` and INSERT … ON CONFLICT in a new migration) so prod gets it on deploy | `/api/v1/sites/<slug>/river-story` 404s; SWR returns undefined; the River Story card on `/path/now/<slug>` either renders blank or (with stale cache from previous navigation) shows the prior watershed's prose | The "Deschutes content on Shenandoah" report |
| `sites.boundary` (MultiPolygon) | Alembic migration: `UPDATE sites SET boundary = (SELECT ST_Multi(ST_Union(geometry)) FROM watershed_boundaries WHERE site_id = sites.id) WHERE watershed = '<slug>'` — runs after the `wbd` adapter has populated `watershed_boundaries` for the slug | `/riversignal` homepage map renders no outline for the watershed; can appear "stuck loading" if the map awaits ALL boundaries | Yes |
| `stocking_locations` rows for state-stocking waterbodies | Alembic seed with (watershed, waterbody_exact_string, lat, lon, notes) — waterbody MUST match the exact string the state adapter writes to `interventions.description::jsonb ->> 'waterbody'`, including annotations like ` [Heritage Day Water]` | Fish Stocking "View map" toggle shows zero pins (rows surface in the list view with `latitude: null`) | Yes |
| `recreation_sites` rows | If RIDB has no coverage for the region (common for non-Western US), seed via alembic with `source_type='curated_<slug>_v0'` and the well-known state parks / NPS campgrounds / boat ramps / fishing access points / trailheads — at minimum 10 rows | `/path/explore` shows "No results" | Yes |
| `gold.species_by_reach` rows | Verify the MV's UNION branches don't filter out the new watershed. The MV historically (a) hardcoded `source='udwr'` on the stocking branch, hiding va_dwr/wv_dnr, and (b) excluded any watershed with `fish_stocking` interventions from the iNat fallback. Both fixed in migration `oo15j6k7l8m9_fix_species_by_reach_for_va_wv.py` (2026-05-15) | `/api/v1/sites/<slug>/catch-probability` returns a score but an empty `species: []`; UI shows the number but no fish list | Yes |
| `gold.species_gallery` photos for hatch-chart insects | Run `pipeline refresh --mode heavy` (or trigger the prod `riversignal-refresh-heavy` job) after the watershed's iNaturalist ingest completes. The hatch endpoint joins curated hatch rows to species_gallery by genus + watershed | "What Fish Are Eating Now" lists insects with no photos | Yes |

Each row above should map to an explicit subtask under Step 2 — don't ship without ticking all of
them.

### 2.6.6 Playwright UX smoke (mandatory before §2.8)

Run the cross-app smoke spec for the new watershed BEFORE crossing the production-deploy gates in
§2.8. The spec covers every surface a human would tap during a /path /riversignal /trail tour:

```
WATERSHED=<slug> BASE_URL=http://localhost:5173 \
  npx playwright test tests/watershed-smoke.spec.ts
```

After prod deploy, re-run against prod with `BASE_URL=https://riversignal-api-...run.app`.

What the spec asserts:
- /path splash card has an image + tagline + narrative (catches missing `PHOTOS` /
  `WATERSHED_META` entries)
- /path/now/<slug> river story is non-empty AND doesn't contain "deschutes" / "mckenzie" when the
  slug is something else (catches missing `river_stories` row + stale SWR fallback)
- Fish Stocking has at least one pinnable row (catches missing `stocking_locations` seed)
- Catch Probability returns species when overall_score is non-null (catches gold MV regressions)
- Hatch confidence returns insects with photos (catches missing species_gallery refresh)
- /path/explore returns non-empty recreation rows (catches missing curated seed)
- /path/saved empty-state heart icon is red (catches inline-style regressions)
- `/api/v1/sites/<slug>.boundary` is non-null (catches missing ST_Union update)
- /riversignal homepage map renders within 30s (catches "stuck loading" caused by NULL boundary)
- /trail picker lists the watershed (catches DeepTrailContext / DeepTrailPage misses)

The spec is parameterized by env vars (`WATERSHED`, `BASE_URL`, `API_BASE`) so it works for any
slug. **A clean pass here is a precondition for §2.8 Gate 1.**

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

### 2.8 Commit, push, deploy — **EXPLICIT USER APPROVAL REQUIRED AT EACH GATE**

Production state changes from here on. The agent **must pause and request explicit user
approval** at four gates. Each gate is a separate ask; bundling them together is not acceptable.

Discover the prod API URL fresh — do not hard-code it. The runbook used to embed
`https://riversignal-api-500769847975.us-west1.run.app`; that URL can change with terraform
or domain mapping. Read it once:

```
PROD_API_URL=$(gcloud run services describe riversignal-api --region us-west1 \
                --format='value(status.url)')
```

Then use `$PROD_API_URL` for every subsequent prod call.

**Gate 1 — push to main.** Show the full `git log --oneline <previous-head>..HEAD` since the
previous push, plus `git diff --stat`. Ask:

> Approve pushing the above N commits to main (triggers GitHub Actions deploy)?

Do not run `git push` until the user says yes. After approval:

```
git push origin main
LATEST_RUN_ID=$(gh run list --branch main --limit 1 --json databaseId --jq '.[0].databaseId')
gh run watch "$LATEST_RUN_ID" --exit-status
```

**Gate 2 — execute prod Cloud Run jobs.** After the deploy succeeds, list the jobs the agent
intends to invoke and the order. Ask:

> Approve manually executing these N Cloud Run jobs on prod so the new watershed has data today
> instead of waiting for tomorrow's cron?

After approval (and only after):

```
gcloud run jobs execute riversignal-pipeline-daily    --region us-west1 --wait
gcloud run jobs execute riversignal-pipeline-weekly   --region us-west1 --wait
gcloud run jobs execute riversignal-pipeline-monthly  --region us-west1 --wait
gcloud run jobs execute riversignal-tqs-daily-refresh --region us-west1 --wait
```

If any job fails, halt and show the failing job's last 50 log lines before proceeding.

**Gate 3 — bust the prod freshness cache.** Show that the `/data-status/freshness` cache is stale
(it caches for ~6h) and the POST is what makes the new watershed's freshness rows visible. Ask:

> Approve POST `$PROD_API_URL/api/v1/data-status/refresh` to rebuild the freshness cache?

After approval:

```
curl -s -X POST "$PROD_API_URL/api/v1/data-status/refresh"
```

**Gate 4 — any prod URL with side effects.** Beyond the explicitly-named POSTs above, every
write-side prod call requires the same per-call approval pattern. Read-only `curl -s` GETs
against prod are fine without approval (used by §3.4 verification).

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
SELECT 'fly_shops_guides',    count(*) FROM fly_shops_guides   WHERE :ws = ANY(watersheds)
UNION ALL
SELECT 'mineral_shops',       count(*) FROM mineral_shops      WHERE :ws = ANY(watersheds)
UNION ALL
SELECT 'rockhounding_sites',  count(*) FROM rockhounding_sites WHERE :ws = ANY(watersheds)
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

Same URLs as §3.3, but against `$PROD_API_URL/api/v1/...` (discovered in §2.8 — do not hard-code).
Read-only GETs, no approval needed. The force-refresh POST was already handled at Gate 3 of §2.8;
if that gate was deferred, surface the new watershed in the freshness payload here.

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
- [ ] Frontend dicts updated (`WATERSHED_LABELS`, `WATERSHED_ORDER`, `WS_COORDS`, `WS_GAUGES`, `PHOTOS`, `WATERSHED_META`, `TAGLINES` — see §2.6 table)
- [ ] Pre-launch data seeds applied (§2.6.5): river_stories, sites.boundary, stocking_locations, recreation_sites, species_by_reach MV verified, species_gallery refreshed
- [ ] Playwright UX smoke `tests/watershed-smoke.spec.ts` passes against local (§2.6.6)
- [ ] Terraform args updated for new adapter scheduling
- [ ] Commits pushed; CI deploy succeeded
- [ ] Manual one-shot ingest runs on prod completed
- [ ] `/data-status/refresh` POST'd to bust the cache
- [ ] Playwright UX smoke re-run against prod (`BASE_URL=https://riversignal-api-...run.app`)
- [ ] `docs/helix/06-iterate/watershed-add/<slug>-verification-<date>.md` (Step 3) with the
      feature-coverage grid
- [ ] Follow-on beads created for every `⚠` / `✗` from the verification grid

If any checkbox is unchecked at the end of the run, the report explains why and what's needed to
close it.
