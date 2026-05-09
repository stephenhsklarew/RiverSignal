# Parking Lot

Deferred items that are explicitly out of scope for the current MVP but tracked for future consideration.

## Resolved (moved out of parking lot)

| Item | Resolution | Date |
|------|-----------|------|
| Macroinvertebrate index scoring | RESOLVED: BioData pipeline loaded 292K professional survey records including macroinvertebrate data | 2026-04 |
| eBird integration | DROPPED: eBird license is non-commercial only; bird data available through iNaturalist (19K+ bird observations loaded) | 2026-04 |
| Climate-downscaled forecasting | PARTIALLY RESOLVED: PRISM 800m gridded climate data pipeline operational; full downscaling still deferred | 2026-04 |
| Cross-watershed comparative analytics | RESOLVED: 7 watersheds loaded across 3 states with comparison queries operational | 2026-05 |
| Trip journal with photos and notes | PARTIALLY RESOLVED: Photo observations implemented (FEAT-020) with camera FAB, EXIF extraction, species typeahead, GCS storage. Full trip journal (timeline, notes, multi-photo) still deferred. | 2026-05 |
| Oregon State Parks recreation adapter | STILL DEFERRED: Remains Phase 2 candidate — USFS + OSMB cover MVP watersheds | 2026-05 |
| Audio narration for DeepTrail | RESOLVED: OpenAI gpt-4o-audio-preview TTS implemented with "Listen to Story" button. Was listed as out of scope in FEAT-010/013. | 2026-05 |
| Multi-state regulatory compliance | PARTIALLY RESOLVED: Multi-state data adapters built (WA: 6 sources, UT: 5 sources). Funder report templates remain Oregon-only (OWEB). | 2026-05 |

## Phase 2 Candidates

| Item | Source | Rationale for Deferral |
|------|--------|----------------------|
| Real-time IoT sensor streaming | PRD Non-Goal | MVP uses batch API polling; real-time requires edge infrastructure not justified until pilot validates core value |
| Species identification from photos | PRD Non-Goal | iNaturalist handles upstream; building competing CV adds complexity without differentiation |
| Drone/satellite imagery ingestion | PRD Non-Goal | Requires specialized image processing pipeline; ground observations sufficient for MVP validation |
| Collaborative annotation/overrides | PRD P2-1 | Valuable for reasoning quality feedback loop; not required for initial pilot |
| Custom report templates (NOAA, BPA, tribal) | PRD P2-2 | OWEB format sufficient for Oregon pilot; additional formats per customer demand |
| Historical multi-year trend visualization | PRD P2-3 | Useful and now feasible with 6+ years of data; prioritize after core reasoning validated |
| GIS desktop integration (ArcGIS/QGIS plugins) | FEAT-006 Out of Scope | Many users have existing GIS workflows; assess adoption barrier during pilot |
| Acoustic sensor (BirdNET) integration | PRD P1-4 | Strong biodiversity signal; depends on BirdNET API availability |
| Deschutes River Alliance real-time data | Research finding | DRA has 3 water quality stations (temp, DO, pH, turbidity) but no public API; requires contacting sarah@deschutesriveralliance.org |
| StreamNet spawning abundance time series | Research finding | StreamNet CAX API requires free API key registration; ArcGIS service at gis.psmfc.org intermittently available |
| Fishing regulation structured data | FEAT-007 Out of Scope | eRegulations.com has consistent HTML but no API; scraping feasible but maintenance-heavy |
| Creel survey data | Research finding | ODFW does not publish publicly; available only by direct request |
| Landsat/Sentinel NDVI vegetation trends | Design plan | Requires Google Earth Engine or large raster infrastructure |
| USGS BioData portal direct access | Research finding | BioData web portal retired; data partially available through WQP biological profile |
| Hourly hatch forecasts (now / +4h / tomorrow) | Wireframe Screen 3 descope | Degree-day hatch emergence model (FEAT-017) predicts emergence timing but not intraday windows. Would require building a phenology model keyed to water temp + time of day + light conditions. MVP uses "this month / next month" with emergence predictions. |
| Holding water cards (pool/riffle/run) | Wireframe Screen 4 descope | No pool/riffle/run habitat classification data in any ingested source; would require NHDPlus reach characterization or ODFW habitat survey ingestion |
| Before/after restoration photo slider | Wireframe Screen 5 descope | gold.restoration_outcomes has numeric before/after species counts but no curated imagery; photo slider needs content sourcing effort (watershed council archives, OWRI project photos) |
| Trip journal with photos and notes (full version) | Wireframe Screen 6 descope | Photo observations (FEAT-020) handle single-photo submissions with species ID. Full trip journal (multi-photo timeline, field notes, trip sharing) requires additional UGC features and moderation workflow |
| Oregon State Parks recreation adapter | FEAT-015 Phase 2 | USFS + OSMB cover the 7 MVP watersheds; Oregon State Parks ArcGIS FeatureServer adds 422 state-managed park parcels as incremental coverage |
| PostHog analytics implementation | plan-2026-05-05-posthog-analytics.md | Detailed plan with 33 events exists; zero implementation. Required for PRD success metrics (MAU, DAU, NPS). |
| FEAT-012 FR-12 reading mode toggle UI | FEAT-012 | Backend `reading_level` parameter exists; DeepTrail has a working toggle. RiverPath frontend toggle not built. |
| FEAT-012 FR-26 cold-water refuge MapLibre overlay | FEAT-012 | FishRefugePage uses thermal station grid, not MapLibre map overlay as specced. Functional but doesn't match spec. |
| Observation moderation workflow | FEAT-020 | User photo submissions currently auto-accepted; no review queue or spam detection |
| WA/UT-specific funder report templates | PRD expansion | Multi-state data exists but report generation targets Oregon OWEB format only |

## Phase 3 Candidates

| Item | Source | Notes |
|------|--------|-------|
| Insurance nature-risk underwriting scores | Seed strategy | Enterprise expansion after public-sector validation |
| TNFD biodiversity disclosure reporting | Seed strategy | Regulatory-driven; market still maturing |
| Carbon + biodiversity co-optimization | Seed strategy | High value but requires additional data sources and modeling |
| Private land portfolio scoring | Seed strategy | PE/agriculture expansion market |
| Multi-state regulatory compliance (full) | PRD Non-Goal | WA/UT data adapters built; per-state funder report templates remain expansion scope |
| Guided trip booking / marketplace | FEAT-007 Out of Scope | Fishing community feature if angler adoption is strong |
