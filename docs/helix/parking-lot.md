# Parking Lot

Deferred items that are explicitly out of scope for the current MVP but tracked for future consideration.

## Resolved (moved out of parking lot)

| Item | Resolution |
|------|-----------|
| Macroinvertebrate index scoring | RESOLVED: BioData pipeline loaded 292K professional survey records including macroinvertebrate data |
| eBird integration | DROPPED: eBird license is non-commercial only; bird data available through iNaturalist (19K+ bird observations loaded) |
| Climate-downscaled forecasting | PARTIALLY RESOLVED: PRISM 800m gridded climate data pipeline operational; full downscaling still deferred |
| Cross-watershed comparative analytics | RESOLVED: 4 watersheds loaded with comparison queries operational |

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
| Hourly hatch forecasts (now / +4h / tomorrow) | Wireframe Screen 3 descope | Gold layer has monthly observation counts, not hourly phenology models; would require building a phenology model keyed to water temp + time of day. MVP uses "this month / next month" seasonal intelligence |
| Holding water cards (pool/riffle/run) | Wireframe Screen 4 descope | No pool/riffle/run habitat classification data in any ingested source; would require NHDPlus reach characterization or ODFW habitat survey ingestion |
| Before/after restoration photo slider | Wireframe Screen 5 descope | gold.restoration_outcomes has numeric before/after species counts but no curated imagery; photo slider needs content sourcing effort (watershed council archives, OWRI project photos) |
| Trip journal with photos and notes | Wireframe Screen 6 descope | Wireframe implied user-generated content (hatch photos, field notes, trip timeline) — this is a UGC platform feature requiring backend user model, media storage, and moderation. MVP Saved = bookmarks via localStorage |
| Oregon State Parks recreation adapter | FEAT-015 Phase 2 | RIDB covers federal lands first (USFS, BLM) where the 5 MVP watersheds sit; Oregon State Parks ArcGIS FeatureServer adds state-managed access points as incremental coverage |

## Phase 3 Candidates

| Item | Source | Notes |
|------|--------|-------|
| Insurance nature-risk underwriting scores | Seed strategy | Enterprise expansion after public-sector validation |
| TNFD biodiversity disclosure reporting | Seed strategy | Regulatory-driven; market still maturing |
| Carbon + biodiversity co-optimization | Seed strategy | High value but requires additional data sources and modeling |
| Private land portfolio scoring | Seed strategy | PE/agriculture expansion market |
| Multi-state regulatory compliance | PRD Non-Goal | Per-state template expansion |
| Guided trip booking / marketplace | FEAT-007 Out of Scope | Fishing community feature if angler adoption is strong |
