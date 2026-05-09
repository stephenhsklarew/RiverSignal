# Alignment Review: Full Platform — 2026-05-08

## 1. Review Metadata

| Field | Value |
|-------|-------|
| Date | 2026-05-08 |
| Scope | Full platform — RiverSignal (B2B) + RiverPath (B2C) + DeepTrail (B2C) + DeepSignal (B2B) |
| Reviewer | HELIX alignment review |
| Prior Reviews | AR-2026-04-10 (data-only), AR-2026-04-13-riverpath-mvp, AR-2026-04-13-full-platform |
| Governing Bead | RiverSignal-main (f87514e) |

## 2. Scope and Governing Artifacts

### Artifacts Reviewed (Authority Order)

| # | Artifact | Path | Role |
|---|----------|------|------|
| 1 | Product Vision | `docs/helix/00-discover/product-vision.md` | Platform strategy, RiverSignal positioning |
| 2 | RiverPath Vision | `docs/helix/00-discover/riverpath-vision.md` | B2C watershed product definition |
| 3 | DeepTrail Vision | `docs/helix/00-discover/deeptrail-vision.md` | B2C geology product definition |
| 4 | PRD | `docs/helix/01-frame/prd.md` | Requirements authority |
| 5 | FEAT-001 | `docs/helix/01-frame/features/FEAT-001-observation-interpretation.md` | Ecological reasoning |
| 6 | FEAT-002 | `docs/helix/01-frame/features/FEAT-002-restoration-forecasting.md` | Restoration predictions |
| 7 | FEAT-003 | `docs/helix/01-frame/features/FEAT-003-management-recommendations.md` | Field action recommendations |
| 8 | FEAT-004 | `docs/helix/01-frame/features/FEAT-004-funder-report-generation.md` | OWEB report generation |
| 9 | FEAT-005 | `docs/helix/01-frame/features/FEAT-005-data-ingestion-pipeline.md` | Data platform |
| 10 | FEAT-006 | `docs/helix/01-frame/features/FEAT-006-map-workspace.md` | Map-first workspace |
| 11 | FEAT-007 | `docs/helix/01-frame/features/FEAT-007-fishing-intelligence.md` | Fishing layer |
| 12 | FEAT-008 | `docs/helix/01-frame/features/FEAT-008-geologic-context.md` | Geologic data layer |
| 13 | FEAT-009 | `docs/helix/01-frame/features/FEAT-009-fossil-discovery.md` | Fossil + legal collecting |
| 14 | FEAT-010 | `docs/helix/01-frame/features/FEAT-010-deep-time-storytelling.md` | Deep time narratives |
| 15 | FEAT-011 | `docs/helix/01-frame/features/FEAT-011-four-product-ui.md` | Four-product UI architecture |
| 16 | FEAT-012 | `docs/helix/01-frame/features/FEAT-012-riverpath-b2c.md` | RiverPath B2C (52 FRs) |
| 17 | FEAT-013 | `docs/helix/01-frame/features/FEAT-013-deeptrail-b2c.md` | DeepTrail B2C (25 FRs) |
| 18 | FEAT-014 | `docs/helix/01-frame/features/FEAT-014-mobile-navigation.md` | Bottom nav architecture |
| 19 | FEAT-015 | `docs/helix/01-frame/features/FEAT-015-explore-recreation.md` | Recreation discovery |
| 20 | FEAT-016 | `docs/helix/01-frame/features/FEAT-016-saved-favorites.md` | Client-side favorites |
| 21 | User Stories | `docs/helix/01-frame/user-stories/riversignal-stories.md` | 23 B2B stories |
| 22 | User Stories | `docs/helix/01-frame/user-stories/riverpath-stories.md` | 19 B2C watershed stories |
| 23 | User Stories | `docs/helix/01-frame/user-stories/deeptrail-stories.md` | 12 B2C geology stories |
| 24 | Design Plans (8) | `docs/helix/02-design/plan-*.md` | Architecture decisions |
| 25 | Parking Lot | `docs/helix/parking-lot.md` | Deferred items |

### New Design Plans Since April 13

| Plan | Date | Scope |
|------|------|-------|
| `plan-2026-05-05-gcp-terraform-migration.md` | 2026-05-05 | GCP production deployment (Cloud Run, Cloud SQL, Terraform) |
| `plan-2026-05-05-posthog-analytics.md` | 2026-05-05 | PostHog event tracking (33 events) |
| `plan-2026-05-08-predictive-intelligence.md` | 2026-05-08 | 5 ML prediction models |

## 3. Intent Summary

### RiverSignal (B2B)
AI-powered watershed intelligence copilot for restoration professionals. Core value: reduce monitoring interpretation time by 40%, auto-generate funder reports, provide restoration forecasts with confidence scores, and deliver management recommendations. Map-first desktop workspace with LLM-powered ecological reasoning.

### RiverPath (B2C)
Mobile-first river field companion for families, anglers, and educators. Core value: turn every river visit into an ecological adventure with living river stories, species galleries, fishing intelligence (hatch confidence, cold-water refuges, stocking), stewardship connection, and seasonal trip planning. Bottom-nav mobile architecture with 5 tabs (River Now / Explore / Hatch / Steward / Saved).

### DeepTrail (B2C)
Mobile-first geology and fossil exploration companion. Core value: answer "What ancient world am I standing in?", show legal collecting sites, fossil galleries, mineral sites, and deep time narratives at three reading levels. Dark-themed adventure UI with bottom nav (Story / Explore / Collect / Learn / Saved).

### DeepSignal (B2B)
Professional geologic intelligence platform. Core value: correlate geologic units with watershed ecology for researchers and land managers. Currently the lowest-priority product with a minimal UI.

### Shared Data Platform
PostgreSQL + PostGIS data lake with medallion architecture (7 silver + 30+ gold materialized views), 22+ ingestion adapters, and a FastAPI backend serving all four products. The data platform is the strategic asset.

## 4. Planning Stack Findings

### New Traceability Gaps Since April 13

| Finding | Type | Evidence | Impact |
|---------|------|----------|--------|
| 5 predictive models built without feature spec | UNDERSPECIFIED | `pipeline/predictions/*.py` (5 models), `app/routers/intelligence.py`, `app/routers/predictions.py` — design plan exists (`plan-2026-05-08`) but no FEAT spec | HIGH — substantial new capability with no governing feature spec or acceptance criteria |
| GCP Terraform infrastructure not in any FEAT spec | UNDERSPECIFIED | 14 `.tf` files in `terraform/`, Dockerfile, `deploy.yml` — design plan exists (`plan-2026-05-05`) | MEDIUM — infrastructure is operational but no acceptance criteria for deployment |
| PostHog analytics planned but not implemented | STALE_PLAN | `plan-2026-05-05-posthog-analytics.md` defines 33 events — no `useAnalytics.ts` hook or PostHog provider found in codebase | MEDIUM — plan written, zero code exists |
| Washington state adapters (6 sources) not in any spec | UNDERSPECIFIED | `pipeline/ingest/washington.py` (492 lines): WDFW SalmonScape, WDFW Stocking, WA DNR Geology, SRFB, WA Parks, WDFW Water Access | HIGH — expands geographic scope beyond Oregon without updated vision/PRD |
| Utah adapter (5 sources) not in any spec | UNDERSPECIFIED | `pipeline/ingest/utah.py` (408 lines): boat ramps, DWQ assessment, trailheads, BOR HydroData, UDWR stocking | HIGH — expands geographic scope to Utah without updated vision/PRD |
| Skagit + Green River watersheds not in PRD | UNDERSPECIFIED | `DeepTrailContext.tsx` WATERSHEDS includes `skagit` and `green_river` | HIGH — PRD lists 5 Oregon watersheds; 2 out-of-state watersheds added |
| Auth system (Google + Apple OAuth) not in feature spec | UNDERSPECIFIED | `app/routers/auth.py`, `frontend/src/components/AuthContext.tsx`, `LoginModal.tsx`, `UserMenu.tsx`, `UsernameSetupPage.tsx` | HIGH — complete auth system built without governing spec |
| Photo observation with GCS storage not in spec | UNDERSPECIFIED | `app/routers/user_observations.py` with rate limiting, image validation, GCS upload | MEDIUM — user-generated content feature with security hardening |
| Audio stories (OpenAI TTS) not in FEAT-010 | UNDERSPECIFIED | DeepTrail story pages have "Listen" button, audio playback via OpenAI `gpt-4o-audio-preview` | MEDIUM — FEAT-010 explicitly listed audio narration as Out of Scope |
| DeepTrail bottom nav + 5-tab architecture not in FEAT-013 | UNDERSPECIFIED | `DeepTrailBottomNav.tsx` with Story/Explore/Collect/Learn/Saved tabs, `DeepTrailHeader.tsx` with location picker | MEDIUM — full navigation rebuild without spec update |
| `predictions` table and prediction tracking system not in schema | UNDERSPECIFIED | `app/routers/predictions.py` manages a `predictions` table with generate/list/score/resolve lifecycle | MEDIUM — new table + full CRUD not in Alembic or design |
| CardSettings (customizable card visibility) not specced | UNDERSPECIFIED | `frontend/src/components/CardSettings.tsx` used on TrailStoryPage, TrailExplorePage | LOW — UX enhancement |
| GitHub Actions CI/CD not specced | UNDERSPECIFIED | `.github/workflows/deploy.yml` — builds Docker, runs migrations, deploys to Cloud Run | LOW — operational concern, design plan covers it |

### Findings from Prior Reviews Still Open

| Prior Finding | Status | Notes |
|---------------|--------|-------|
| FEAT-012 FR-12 reading mode toggle (no UI) | STILL INCOMPLETE | Backend param exists; no frontend toggle on RiverPath. DeepTrail has a working toggle. |
| FEAT-012 FR-26 cold-water refuge MapLibre overlay | STILL INCOMPLETE | FishRefugePage uses thermal station grid, not a MapLibre map overlay |
| PRD lists "Multi-state regulatory compliance" as non-goal | DIVERGENT | Implementation now includes WA and UT data; PRD scope is Oregon-only |
| Spec docs not updated per AR-2026-04-13 recommendations | STILL OPEN | Issues #1-#8 from prior review (spec updates for weather, USGS real-time, snowpack, etc.) not visibly resolved |

## 5. Implementation Map

### Frontend Pages (22 files)

| Page | Route | Product | In Spec? |
|------|-------|---------|----------|
| LandingPage | `/` | Shared | FEAT-011 |
| HomePage | `/path` | RiverPath | FEAT-012 |
| RiverNowPage | `/path/now` | RiverPath | FEAT-012/014 |
| ExplorePage | `/path/explore` | RiverPath | FEAT-015 |
| ExploreMapPage | `/path/explore-map/:ws` | RiverPath | Not in spec |
| HatchPage | `/path/hatch` | RiverPath | FEAT-012 |
| FishRefugePage | `/path/fish/:ws` | RiverPath | FEAT-012 |
| StewardPage | `/path/steward` | RiverPath | FEAT-012 |
| SavedPage | `/path/saved` | RiverPath | FEAT-016 |
| SpeciesMapPage | `/path/map/:ws` | RiverPath | Not in spec |
| MapPage | `/riversignal` | RiverSignal | FEAT-006 |
| ReportsPage | `/riversignal/reports` | RiverSignal | FEAT-004 |
| StatusPage | `/status` | Shared | Not in spec |
| DeepSignalPage | `/deepsignal` | DeepSignal | FEAT-011 |
| DeepTrailPickPage | `/trail` | DeepTrail | FEAT-013 |
| DeepTrailPage | `/trail/:loc` (legacy) | DeepTrail | FEAT-013 |
| TrailStoryPage | `/trail/story/:loc` | DeepTrail | Not in spec |
| TrailExplorePage | `/trail/explore/:loc` | DeepTrail | Not in spec |
| TrailCollectPage | `/trail/collect/:loc` | DeepTrail | Not in spec |
| TrailLearnPage | `/trail/learn/:loc` | DeepTrail | Not in spec |
| TrailSavedPage | `/trail/saved` | DeepTrail | Not in spec |
| UsernameSetupPage | `/setup-username` | Shared | Not in spec |

### API Routers (15 files)

| Router | Endpoints | In Spec? |
|--------|-----------|----------|
| `sites.py` | /sites/nearest, /sites/{ws}/recreation, /sites/{ws} details | FEAT-005, FEAT-015 |
| `fishing.py` | /sites/{ws}/fishing/* (brief, species, harvest, stocking, conditions, hatch, barriers, alerts, fly-recommendations, swim-safety, hatch-confidence) | FEAT-007 |
| `weather.py` | /weather, /conditions/live, /snowpack | Not in spec |
| `geology.py` | /geology/at, /fossils/near, /land/at, /minerals/near, /deep-time/* | FEAT-008/009/010 |
| `reasoning.py` | /sites/{ws}/chat, /sites/{ws}/recommendations, /sites/{ws}/story | FEAT-001/003 |
| `reports.py` | /sites/{ws}/report | FEAT-004 |
| `intelligence.py` | /sites/{ws}/hatch-forecast, /catch-forecast, /health-anomaly, /species-shifts, /restoration-forecast | Not in spec (plan only) |
| `predictions.py` | /sites/{ws}/predictions, /predictions/{id} (generate, score, resolve) | Not in spec |
| `auth.py` | /auth/google/*, /auth/apple/*, /auth/me, /auth/logout | Not in spec |
| `user_observations.py` | /observations/submit, /observations/mine, /species/typeahead | Not in spec |
| `ai_features.py` | AI-powered features | Partial (FEAT-001) |
| `deeptrail_ai.py` | DeepTrail-specific AI endpoints | FEAT-010/013 |
| `data_status.py` | /data-status | Not in spec |
| `health.py` | /health | Infrastructure |

### Pipeline Ingest Adapters (22 files)

| Adapter | Data Source | In Spec? |
|---------|-----------|----------|
| `inaturalist.py` | iNaturalist observations | FEAT-005 |
| `usgs.py` | USGS stream gauges | FEAT-005 |
| `owdp.py` | Oregon Water Data Portal | FEAT-005 |
| `nhdplus.py` | NHDPlus HR stream flowlines | FEAT-005 |
| `spatial.py` | WBD, NWI, EPA ATTAINS | FEAT-005 |
| `mtbs.py` | MTBS burn severity | FEAT-005 |
| `restoration.py` | OWRI/NOAA/PCSRF | FEAT-005 |
| `fishing.py` | ODFW sport catch + stocking | FEAT-007 |
| `fish_passage.py` | ODFW fish barriers | FEAT-007 |
| `prism.py` | PRISM climate data | Design plan |
| `streamnet.py` | StreamNet fish habitat | Design plan |
| `biodata.py` | USGS BioData | Design plan |
| `snotel.py` | SNOTEL snowpack | Not in spec |
| `geology.py` | DOGAMI + Macrostrat + PBDB + iDigBio + BLM SMA + MRDS | FEAT-008/009 |
| `gbif.py` | GBIF fossil specimens | Not in spec |
| `wqp_bugs.py` | WQP macroinvertebrates | Not in spec |
| `recreation.py` | OSMB + USFS Recreation | FEAT-015 (partial) |
| `fossil_images.py` | Fossil image backfill | Not in spec |
| **`washington.py`** | **6 WA state sources** | **Not in spec** |
| **`utah.py`** | **5 UT state sources** | **Not in spec** |

### Predictive Models (5 files) — ALL NEW since April 13

| Model | File | Output Table | In Spec? |
|-------|------|-------------|----------|
| Hatch Emergence | `hatch_forecast.py` | `gold_hatch_emergence_forecast` | Design plan only |
| Catch Probability | `catch_forecast.py` | `gold_catch_forecast` | Design plan only |
| Health Anomaly | `health_anomaly.py` | `gold_health_anomaly` | Design plan only |
| Species Distribution | `species_distribution.py` | `gold_species_distribution_shifts` | Design plan only |
| Restoration Impact | `restoration_impact.py` | `gold_restoration_forecast` | Design plan only |

### Infrastructure (14 Terraform files + CI/CD) — ALL NEW since April 13

| File | Purpose | In Spec? |
|------|---------|----------|
| `main.tf` | GCP provider, APIs | Design plan only |
| `cloud_sql.tf` | PostgreSQL 17 + PostGIS | Design plan only |
| `cloud_run.tf` | FastAPI on Cloud Run (2 vCPU, 2GB) | Design plan only |
| `cloud_run_jobs.tf` | Pipeline batch jobs | Design plan only |
| `cloud_storage.tf` | Assets + backups buckets | Design plan only |
| `cloud_scheduler.tf` | Cron triggers | Design plan only |
| `secrets.tf` | Secret Manager (11 secrets) | Design plan only |
| `networking.tf` | VPC, serverless connector | Design plan only |
| `iam.tf` | 3 service accounts | Design plan only |
| `artifact_registry.tf` | Docker image repo | Design plan only |
| `cloud_build.tf` | Cloud Build + Workload Identity Federation for GitHub Actions | Design plan only |
| `notifications.tf` | Essential Contacts | Not in spec |
| `variables.tf` | Configurable inputs | Design plan only |
| `outputs.tf` | Deployment outputs | Design plan only |
| `.github/workflows/deploy.yml` | CI/CD: build, migrate, deploy | Design plan only |
| `Dockerfile` | Single image for API + pipeline | Design plan only |

### Medallion Architecture

**Silver views (7)**: species_observations, water_conditions, interventions_enriched, geologic_context, fossil_records, land_access, mineral_sites

**Gold views (30)**: site_ecological_summary, species_trends, invasive_detections, watershed_scorecard, indicator_species_status, harvest_trends, whats_alive_now, stewardship_opportunities, legal_collecting_sites, stocking_schedule, cold_water_refuges, fishing_conditions, seasonal_observation_patterns, post_fire_recovery, geology_watershed_link, anomaly_flags, water_quality_monthly, species_by_reach, river_miles, species_gallery, species_by_river_mile, river_health_score, hatch_chart, river_story_timeline, swim_safety, restoration_outcomes, geologic_age_at_location, fossils_nearby, deep_time_story, formation_species_history, mineral_sites_nearby, hatch_fly_recommendations

**Total: 37 materialized views** (PRD states 41; difference likely from prediction tables stored outside the medallion system)

### Watersheds Configured (7 total)

| Watershed | State | In PRD? | New Since April 13? |
|-----------|-------|---------|---------------------|
| Deschutes | OR | Yes | No |
| McKenzie | OR | Yes | No |
| Metolius | OR | Yes | No |
| Klamath | OR | Yes | No |
| John Day | OR | Yes | No |
| **Skagit** | **WA** | **No** | **Yes** |
| **Green River** | **UT** | **No** | **Yes** |

## 6. Gap Register

| Area | Classification | Planning Evidence | Implementation Evidence | Resolution Direction |
|------|----------------|-------------------|------------------------|----------------------|
| **FEAT-001 Observation Interpretation** | INCOMPLETE | P0-1: structured ecological summary endpoint | Chat endpoint exists (`/sites/{ws}/chat`), no dedicated `POST /sites/{id}/summary`. No HITL review queue. | code-to-plan |
| **FEAT-002 Restoration Forecasting** | DIVERGENT (richer) | P0-2: species-return predictions with confidence | `pipeline/predictions/restoration_impact.py` builds trained model from historical outcomes. `app/routers/predictions.py` has full prediction lifecycle (generate/list/score/resolve). Exceeds spec intent. | plan-to-code |
| **FEAT-003 Management Recommendations** | INCOMPLETE | P0-3: ranked actions with reasoning, accept/defer/dismiss | `/sites/{ws}/recommendations` exists. No field crew assignment workflow. No dismiss-with-feedback loop. | code-to-plan |
| **FEAT-004 Funder Report Generation** | INCOMPLETE | P0-4: OWEB reports with PDF export, auto maps | `/sites/{ws}/report` generates markdown. ReportsPage.tsx exists. No PDF export. No OWEB-specific format. No auto-generated maps. | code-to-plan |
| **FEAT-005 Data Ingestion Pipeline** | DIVERGENT (richer) | P0-6: 3 data sources (iNat, USGS, OWDP) | 22 adapters covering 30+ data sources across 3 states. Nightly automation via Cloud Scheduler. Far exceeds spec. | plan-to-code |
| **FEAT-006 Map Workspace** | ALIGNED | P0-5: map-first workspace with chat | MapPage.tsx with MapLibre, boundaries, observations, barriers, KPIs, SitePanel with tabs | -- |
| **FEAT-007 Fishing Intelligence** | ALIGNED | P1-5: species by reach, harvest, stocking, conditions | 10+ fishing endpoints, curated hatch chart, hatch confidence scoring, fly recommendations | -- |
| **FEAT-008 Geologic Context** | ALIGNED | P1-6: geologic units, geology-ecology link | `/geology/at`, gold views, LLM tool functions | -- |
| **FEAT-009 Fossil Discovery** | DIVERGENT (richer) | P1-7/8: PBDB fossils + BLM legal status | 3,673 fossils from 3 sources (PBDB + iDigBio + GBIF), image backfill, source-specific links | plan-to-code |
| **FEAT-010 Deep Time Storytelling** | DIVERGENT (richer) | P1-9: AI narratives, 3 reading levels | LLM narratives + audio playback (OpenAI TTS) + story caching. Audio was explicitly out of scope. | plan-to-code |
| **FEAT-011 Four-Product UI** | ALIGNED | Route-based 4-product architecture | LandingPage, 4 product routes, dynamic favicons, product themes | -- |
| **FEAT-012 RiverPath B2C** | INCOMPLETE | 52 FRs across 8 areas | ~48 of 52 FRs built. Missing: FR-12 reading mode toggle UI (backend only), FR-26 cold-water refuge MapLibre overlay (grid only) | code-to-plan |
| **FEAT-013 DeepTrail B2C** | DIVERGENT (richer) | 25 FRs + location picker | Full 5-tab bottom nav rebuild (Story/Explore/Collect/Learn/Saved), watershed header with location picker, card settings, quiz, rarity scoring, mineral shop lookup, rockhounding sites. Significantly exceeds spec. | plan-to-code |
| **FEAT-014 Mobile Navigation** | ALIGNED | Bottom nav, GPS lookup | BottomNav.tsx, DeepTrailBottomNav.tsx, 5 tabs each product, GPS resolve | -- |
| **FEAT-015 Explore & Recreation** | DIVERGENT (richer) | RIDB primary, 200 sites | OSMB + USFS primary (566 sites), explore map page with type filters, WA/UT recreation data | plan-to-code |
| **FEAT-016 Saved & Favorites** | ALIGNED | localStorage, SavedContext | SaveButton.tsx, SavedContext.tsx, SavedPage.tsx, TrailSavedPage.tsx, badge count | -- |
| **Predictive Intelligence (5 models)** | UNDERSPECIFIED | Design plan only (plan-2026-05-08) | 5 models implemented, 2 API routers (`intelligence.py`, `predictions.py`), gold tables | Create FEAT-017 |
| **GCP Production Deployment** | UNDERSPECIFIED | Design plan only (plan-2026-05-05) | 14 Terraform files, Dockerfile, GitHub Actions CI/CD, Cloud Run + Cloud SQL + GCS | Create FEAT-018 or infra spec |
| **PostHog Analytics** | STALE_PLAN | Design plan defines 33 events | Zero implementation. No PostHog provider, no useAnalytics hook, no event tracking. | code-to-plan |
| **Authentication (Google + Apple OAuth)** | UNDERSPECIFIED | PRD FR-19/20/21 mention auth abstractly | Full OAuth2 implementation: `auth.py`, `AuthContext.tsx`, `LoginModal.tsx`, `UserMenu.tsx`, JWT cookies, `users` table | Create spec or update PRD |
| **Photo Observations** | UNDERSPECIFIED | Not in any spec | `user_observations.py` with rate limiting, image validation (magic bytes), GCS upload, EXIF parsing, species typeahead, `PhotoObservation.tsx` | Create spec |
| **Audio Stories (OpenAI TTS)** | DIVERGENT | FEAT-010 explicitly lists audio as Out of Scope | DeepTrail + RiverPath have "Listen" buttons, OpenAI `gpt-4o-audio-preview` TTS integration | plan-to-code (update FEAT-010 out-of-scope) |
| **Washington State Expansion** | UNDERSPECIFIED | PRD scope = Oregon only | 6 WA adapters (WDFW SalmonScape, stocking, WA DNR geology, SRFB, WA Parks, water access), Skagit watershed | Create expansion spec |
| **Utah State Expansion** | UNDERSPECIFIED | PRD scope = Oregon only | 5 UT adapters (boat ramps, DWQ assessment, trailheads, BOR HydroData, UDWR stocking), Green River watershed | Create expansion spec |
| **Security Hardening** | UNDERSPECIFIED | Not in any spec | Rate limiting (IP-based, 10/5min), image validation (magic byte check), input sanitization (HTML stripping, null byte removal) in `user_observations.py` | Document in security spec |
| **DeepTrail Rebuild (5-tab)** | UNDERSPECIFIED | FEAT-013 describes single-page DeepTrail | Full 5-page rebuild: TrailStoryPage, TrailExplorePage, TrailCollectPage, TrailLearnPage, TrailSavedPage with DeepTrailBottomNav, DeepTrailHeader, CardSettings | plan-to-code |
| **RiverSignal SitePanel Overhaul** | UNDERSPECIFIED | FEAT-006 describes tabbed SitePanel | SitePanel now has Overview/Species/Rocks/Story/Predict/Ask tabs. Fishing and Recs tabs hidden. Story merged into overview context. | plan-to-code |

## 7. Traceability Matrix

| Feature | Vision | PRD Req | User Stories | Design Plan | Code | Status |
|---------|--------|---------|-------------|-------------|------|--------|
| FEAT-001 Observation Interpretation | Ecological reasoning | P0-1 | US-001/002/003 | plan-2026-04-10 | Chat endpoint + gold views | INCOMPLETE |
| FEAT-002 Restoration Forecasting | Restoration forecasts | P0-2 | US-004/005/006 | plan-2026-04-10 | predictions pipeline + API | DIVERGENT (richer) |
| FEAT-003 Management Recommendations | Prioritized actions | P0-3 | US-007/008/009 | plan-2026-04-10 | /recommendations endpoint | INCOMPLETE |
| FEAT-004 Funder Report Generation | Auto reports | P0-4 | US-010/011/012 | plan-2026-04-10 | Markdown reports, ReportsPage | INCOMPLETE |
| FEAT-005 Data Ingestion Pipeline | Unified data | P0-6 | US-013/014/015 | plan-2026-04-10 | 22 adapters, 30+ sources | ALIGNED+ |
| FEAT-006 Map Workspace | Map-first | P0-5 | US-016/017/018/019 | plan-2026-04-10 | MapPage + SitePanel | ALIGNED |
| FEAT-007 Fishing Intelligence | Angler support | P1-5 | US-020/021/022/023 | plan-2026-04-12 | 10+ endpoints, curated hatch | ALIGNED |
| FEAT-008 Geologic Context | Geology layer | P1-6 | US-030/031/032 | plan-2026-04-10-4p | geology endpoints + gold | ALIGNED |
| FEAT-009 Fossil Discovery | Fossil + legal | P1-7, P1-8 | US-033/034/035 | plan-2026-04-10-4p | 3 data sources, legal badges | DIVERGENT (richer) |
| FEAT-010 Deep Time Storytelling | Ancient worlds | P1-9 | US-036/037 | plan-2026-04-11 | LLM stories + audio TTS | DIVERGENT (richer) |
| FEAT-011 Four-Product UI | 4 products | -- | US-038/039/040 | plan-2026-04-10-4p | LandingPage + routes | ALIGNED |
| FEAT-012 RiverPath B2C | River companion | P1-10 thru P1-16 | US-040 thru US-058 | plan-2026-04-12 | 9 pages, full mobile UX | INCOMPLETE (2 of 52 FRs) |
| FEAT-013 DeepTrail B2C | Geology explorer | -- | US-046 thru US-053 | plan-2026-04-11 | 5-tab rebuild, far exceeds spec | DIVERGENT (richer) |
| FEAT-014 Mobile Navigation | Bottom nav | P2-7 | US-040, US-042 | plan-2026-04-12 | BottomNav + DeepTrailBottomNav | ALIGNED |
| FEAT-015 Explore & Recreation | Recreation | -- | US-050/051/052 | plan-2026-04-12 | 566+ sites, explore map | DIVERGENT (richer) |
| FEAT-016 Saved & Favorites | Bookmarks | -- | US-053/054/055 | plan-2026-04-12 | SavedContext, both products | ALIGNED |
| Predictive Intelligence | -- | -- | -- | plan-2026-05-08 | 5 models, 2 routers | UNDERSPECIFIED |
| GCP Deployment | -- | -- | -- | plan-2026-05-05 | 14 TF files, CI/CD | UNDERSPECIFIED |
| PostHog Analytics | -- | -- | -- | plan-2026-05-05 | None | STALE_PLAN |
| Authentication | -- | FR-19/20/21 | -- | -- | Full OAuth2 + JWT | UNDERSPECIFIED |
| Photo Observations | -- | -- | -- | -- | UGC with security | UNDERSPECIFIED |
| WA/UT Expansion | -- | -- | -- | -- | 11 adapters, 2 watersheds | UNDERSPECIFIED |

## 8. Key Findings Since Last Review (April 13)

### Major Additions

**1. Multi-State Geographic Expansion**
The platform has expanded beyond its Oregon-only scope to include Washington (Skagit River watershed, 6 state data adapters) and Utah (Green River watershed, 5 state data adapters). This is a strategic shift: the PRD, vision documents, and all feature specs scope the platform to Oregon. The implementation now covers 3 states and 7 watersheds. The Washington adapter covers WDFW SalmonScape, fish stocking, WA DNR surface geology, SRFB salmon recovery projects, WA State Parks, and WDFW water access. The Utah adapter covers AGRC boat ramps, DWQ assessment units, AGRC trailheads, Bureau of Reclamation Flaming Gorge HydroData, and UDWR fish stocking.

**2. Five Predictive Intelligence Models**
A complete predictive analytics pipeline has been built, replacing hardcoded scoring rules with trained models:
- **Hatch Emergence**: Degree-day logistic regression replaces static month lookup
- **Catch Probability**: Multi-factor model (water temp, flow, stocking, hatch activity, weather) replaces fixed formula
- **Health Anomaly Detection**: Z-score anomaly detection against historical baselines replaces 3-line if/else
- **Species Distribution Shifts**: Centroid tracking, new arrival detection, range contraction estimation
- **Restoration Impact Prediction**: Regression model predicting species gain by intervention type

These models are served via `app/routers/intelligence.py` (read endpoints) and `app/routers/predictions.py` (full prediction lifecycle with generate/list/score/resolve). A design plan exists but no feature spec.

**3. GCP Production Deployment**
Full infrastructure-as-code deployment to Google Cloud Platform:
- Cloud Run (FastAPI, 2 vCPU, 2GB RAM)
- Cloud SQL (PostgreSQL 17 + PostGIS, db-g1-small, 20GB SSD)
- Cloud Storage (assets CDN for images/audio)
- Cloud Run Jobs (pipeline batch execution)
- Cloud Scheduler (cron triggers for daily/weekly/monthly pipeline runs)
- Secret Manager (11 secrets)
- VPC with serverless connector (private Cloud SQL access)
- Artifact Registry (Docker images)
- Workload Identity Federation for GitHub Actions (no stored credentials)
- GitHub Actions CI/CD (`deploy.yml`): build Docker image, run migrations, deploy to Cloud Run on push to main

**4. Authentication System**
Complete OAuth2 authentication with Google and Apple providers:
- JWT tokens in httpOnly cookies (30-day expiry)
- Anonymous-first architecture (all read endpoints work without auth)
- User table with `users` schema
- Username setup flow (`UsernameSetupPage.tsx`)
- `AuthContext.tsx` with React context, `LoginModal.tsx`, `UserMenu.tsx`

**5. Photo Observation System**
User-generated content capability with security hardening:
- Photo upload with base64 encoding and GCS storage in production
- Image validation via magic byte checking (JPEG/PNG only)
- Input sanitization (HTML tag stripping, null byte removal, length limits)
- Rate limiting (10 submissions per 5 minutes per IP)
- EXIF GPS and DateTime extraction from uploaded photos
- Species typeahead for classification
- Thumbnail generation

**6. Audio Stories (OpenAI TTS)**
DeepTrail and RiverPath now have "Listen to Story" functionality using OpenAI's `gpt-4o-audio-preview` model. This was explicitly listed as Out of Scope in FEAT-010 ("Audio narration / podcast-style tours") but has been implemented and is a prominent UI feature with a styled Listen button.

**7. DeepTrail 5-Tab Rebuild**
DeepTrail has been completely restructured from a single-page experience to a 5-tab bottom-nav architecture mirroring RiverPath's navigation pattern:
- TrailStoryPage (deep time narratives, timeline, era comparison)
- TrailExplorePage (fossils, minerals with maps and filters)
- TrailCollectPage (legal collecting, rockhounding sites, mineral shops)
- TrailLearnPage (quizzes, educational content)
- TrailSavedPage (bookmarked fossils, minerals, sites)

Each page has a `DeepTrailHeader` with location picker modal and `DeepTrailBottomNav`. The `DeepTrailContext` provides shared state (location, fossils, minerals, story, quiz, rarity scores, etc.).

**8. RiverSignal SitePanel Overhaul**
The SitePanel tab structure has been reorganized. The `predict` tab has been added for the prediction lifecycle. The Fishing and Recs tabs have been hidden (functionality moved to dedicated pages). A Rocks tab was added for geologic data. The Story tab's content has been merged into the overview context.

**9. PostHog Analytics Plan (Not Implemented)**
A detailed analytics plan (`plan-2026-05-05-posthog-analytics.md`) was written defining 33 events across all 3 apps, a `useAnalytics()` hook, `PostHogPageView` and `PostHogIdentify` components, and a multi-app segmentation strategy. However, zero code has been written. No PostHog package installed, no provider in `main.tsx`, no analytics hook. This is the only design plan with no corresponding implementation.

## 9. Open Decisions

| Decision | Why Open | Impact | Recommended Owner |
|----------|----------|--------|-------------------|
| Should the PRD/vision be updated to reflect multi-state scope (WA, UT)? | Platform has expanded beyond Oregon without updated strategy docs. Current PRD says "Oregon's Living Rivers Loop." | HIGH — fundamental scope change | Product |
| Should predictive models have their own feature spec (FEAT-017)? | 5 models are live with no acceptance criteria, no success metrics, no error handling spec | HIGH — critical new capability | Product + Engineering |
| Should PostHog analytics be implemented or plan discarded? | Plan written 3 days ago with no implementation | MEDIUM — analytics is needed for PRD success metrics | Product |
| Should the auth system be specced retroactively or governed by PRD FR-19/20/21? | Auth is built but PRD's FR-19/20/21 describe a different multi-tenancy model | MEDIUM — implementation diverges from PRD auth vision | Product |
| Should photo observations have a feature spec? | UGC is a significant new surface area (security, storage, moderation) | MEDIUM — security implications | Product + Security |
| How should the prediction lifecycle (generate/score/resolve) integrate with FEAT-002 Restoration Forecasting? | `predictions.py` is a generic prediction system; FEAT-002 specifies restoration-specific forecasting | MEDIUM — overlapping capabilities | Engineering |
| Should FEAT-010 Out of Scope be updated now that audio stories are shipped? | FEAT-010 says "Audio narration / podcast-style tours" is out of scope | LOW — spec hygiene | Engineering |
| When should cold-water refuge MapLibre overlay (FEAT-012 FR-26) be built? | Two reviews have flagged this; thermal grid works but doesn't match spec | LOW — cosmetic gap | Engineering |
| Should the DeepTrail 5-tab architecture be specced in a new FEAT or appended to FEAT-013? | FEAT-013 describes a fundamentally different single-page architecture | MEDIUM — spec no longer matches reality | Product |

## 10. Recommendations

### Priority 1: Spec Reconciliation (Planning Debt)

The platform has grown significantly beyond its specs. The ratio of UNDERSPECIFIED items in this review is the highest of any review — 12 major capabilities exist in code with no governing feature spec. This creates risk: no acceptance criteria means no way to verify correctness, and new contributors cannot understand intent.

1. **Create FEAT-017: Predictive Intelligence** — Spec the 5 models with acceptance criteria, error handling, accuracy targets, and refresh schedules. The design plan (`plan-2026-05-08`) provides the skeleton.

2. **Update PRD geographic scope** — The PRD states "Oregon's Living Rivers Loop" as MVP geography. The platform now spans 3 states. Either update the PRD to reflect multi-state ambition or clarify that WA/UT are experimental extensions.

3. **Create geographic expansion spec** — Document the WA adapter (6 sources), UT adapter (5 sources), and the corresponding Skagit and Green River watershed configurations. Define which gold views and features apply to out-of-state watersheds.

4. **Update FEAT-013 for 5-tab architecture** — The current FEAT-013 describes a single-page DeepTrail. The implementation is a 5-tab bottom-nav app with Story/Explore/Collect/Learn/Saved pages, DeepTrailHeader, location picker, quiz, rarity scoring, and card customization. This is a fundamentally different product shape.

5. **Spec auth and photo observations** — These are significant new capabilities with security implications. Auth affects the multi-tenancy model described in PRD FR-19/20/21. Photo observations introduce UGC, rate limiting, and image validation that should be documented.

### Priority 2: Close Implementation Gaps

6. **FEAT-001: Build structured ecological summary endpoint** — The chat endpoint works for Q&A but doesn't match the spec's intent of a structured summary with species richness deltas, invasive flags, indicator status, and citations. This is a P0 requirement.

7. **FEAT-004: Add PDF export** — The report endpoint generates markdown but the spec requires PDF export for funder submission. This is a P0 requirement and "first killer feature" per the seed strategy.

8. **FEAT-012 FR-12: Build reading mode toggle UI** — This has been flagged in two prior reviews. The backend supports `reading_level` parameter. DeepTrail has a working toggle. RiverPath does not.

9. **FEAT-012 FR-26: Cold-water refuge MapLibre overlay** — Also flagged in two prior reviews. FishRefugePage uses a thermal station grid rather than a MapLibre map overlay. Lower priority but spec gap remains open.

### Priority 3: Operational

10. **Implement PostHog analytics** — The plan is detailed and ready. Zero implementation exists. The PRD's success metrics (10,000 MAU families, 500 daily active guides, NPS surveys) all require analytics infrastructure that doesn't exist.

11. **Resolve spec update backlog from AR-2026-04-13** — The prior review generated 8 issues for spec updates (weather, USGS real-time, snowpack, species map, cross-product cards, data sources, FEAT-015 source divergence, FEAT-016 grouping). These appear unresolved.

### Summary

The platform has advanced dramatically since April 13: 5 predictive models, GCP production deployment, authentication, photo observations, multi-state expansion, audio stories, and a DeepTrail rebuild. The implementation consistently outpaces the specs — 12 major capabilities have no feature spec. The core P0 requirements (FEAT-001 structured summary, FEAT-004 PDF export) remain incomplete. The most urgent action is spec reconciliation for the predictive intelligence models and geographic expansion, followed by closing the remaining P0 implementation gaps.
