# Alignment Review: Full Platform (RiverSignal + RiverPath + DeepTrail)

**Review Date**: 2026-04-13
**Scope**: All 4 products (RiverSignal, RiverPath, DeepSignal, DeepTrail)
**Status**: complete

## RiverSignal (B2B) — FEAT-001 through FEAT-007

| FEAT | Name | Status | What's Built | What's Missing |
|------|------|--------|-------------|----------------|
| FEAT-001 | Observation Interpretation | INCOMPLETE | Chat endpoint (`/sites/{ws}/chat`) uses LLM for ecological Q&A. Gold views provide species richness, trends, anomalies. SitePanel Ask tab. | No structured ecological summary endpoint (POST /sites/{id}/summary). No HITL review queue. No citation linking to specific observation IDs in responses. |
| FEAT-002 | Restoration Forecasting | NOT_STARTED | `gold.restoration_outcomes` has before/after data. No prediction engine. | No forecast endpoint. No confidence scores. No species-return predictions. Tracker bead open. |
| FEAT-003 | Management Recommendations | INCOMPLETE | `/sites/{ws}/recommendations` endpoint exists, returns LLM-generated recommendations. | No ranked action list with reasoning. No seasonal context integration. No field crew assignment. |
| FEAT-004 | Funder Report Generation | INCOMPLETE | `/sites/{ws}/report` endpoint generates markdown reports. ReportsPage.tsx with watershed selector, date range, download. | No PDF export (Playwright rendering). No OWEB-specific format. No auto-generated maps in reports. |
| FEAT-005 | Data Ingestion Pipeline | ALIGNED | 22 adapters, 550K observations, 1.7M time series, CLI with per-source and per-watershed commands. | Pipeline is solid. All 5 watersheds loaded. Nightly automation not configured (manual runs). |
| FEAT-006 | Map Workspace | ALIGNED | MapPage.tsx with MapLibre GL, watershed boundaries, observation overlays, fish passage barriers, KPI chips, watershed tabs, SitePanel with 6 tabs (Overview, Species, Fishing, Story, Recs, Ask). | Desktop-first as specced. Working well. |
| FEAT-007 | Fishing Intelligence | ALIGNED | 10 fishing endpoints (brief, species, harvest, stocking, conditions, hatch, barriers, alerts, fly-recommendations, swim-safety). FlyRecommendations component, hatch chart, seasonal planner. | All core FRs implemented. Curated hatch chart and hatch confidence built beyond spec. |

## DeepTrail (B2C Geology) — FEAT-008 through FEAT-010, FEAT-013

| FEAT | Name | Status | What's Built | What's Missing |
|------|------|--------|-------------|----------------|
| FEAT-008 | Geologic Context | ALIGNED | `/geology/at/{lat}/{lon}` returns geologic units. `gold.geologic_age_at_location`, `gold.geology_watershed_link`. DeepTrailPage geologic context section. | Working as specced. |
| FEAT-009 | Fossil Discovery | DIVERGENT (richer) | 3,673 fossils from PBDB + iDigBio + GBIF (spec only mentioned PBDB). Image URLs from GBIF. `/fossils/near` endpoint with image prioritization. Period/phylum filters. Source-specific links (PBDB/GBIF/iDigBio). | GBIF and image backfill not in spec. |
| FEAT-010 | Deep Time Storytelling | ALIGNED | LLM-generated deep time narratives with 3 reading levels (adult/kid_friendly/expert). Audio playback (TTS). Story caching in `deep_time_stories` table. | Working well. |
| FEAT-013 | DeepTrail B2C | DIVERGENT (richer) | Full DeepTrailPage: location picker (GPS/coords/watersheds), deep time story with reading levels + audio, geologic context, legal collecting with color badges, deep time timeline, fossil list with filters + map + images, mineral sites with filters + map, Living River cross-sell card to RiverPath. | FEAT-013 doesn't mention: Living River cross-sell card, GBIF fossil images, source-specific links on fossils. Mineral site commodity filter built but not in spec. |

## Four-Product UI — FEAT-011

| FEAT | Name | Status | What's Built | What's Missing |
|------|------|--------|-------------|----------------|
| FEAT-011 | Four-Product UI Architecture | ALIGNED | LandingPage with 4 product cards, route-based code splitting (/riversignal, /path, /deepsignal, /trail), DynamicFavicon, product-specific CSS themes, cross-product navigation. | DeepSignal page is minimal (data tables only). PWA manifest and service worker working. |

## Data Sources — Not Specced

These were built during this session without governing specs:

| Source | Records | Used By | Needs Spec |
|--------|---------|---------|------------|
| NWS Weather API | Live (cached 30min) | RiverPath River Now | Yes |
| USGS Real-Time Gauges | Live (cached 15min) | RiverPath River Now LIVE badge | Yes |
| SNOTEL → gold.snowpack_current | 650K time_series, 66 station view rows | RiverPath snowpack card | Yes |
| GBIF Fossil Specimens | 965 records, 18 with images | DeepTrail fossil list | Yes |
| WQP Macroinvertebrates | 14,876 records | Hatch chart (via aquatic_hatch_chart) | Yes |
| OSMB Boating Access | 160 boat ramps | RiverPath Explore | Yes (update FEAT-015) |
| Curated Hatch Chart | 50 expert entries | RiverPath Hatch tab | Yes |
| gold.aquatic_hatch_chart | 134 rows | Hatch confidence API | Yes |
