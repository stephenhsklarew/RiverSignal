# Parking Lot

Deferred items that are explicitly out of scope for the current MVP but tracked for future consideration.

## Phase 2 Candidates

| Item | Source | Rationale for Deferral |
|------|--------|----------------------|
| Real-time IoT sensor streaming | PRD Non-Goal | MVP uses batch API polling; real-time requires edge infrastructure not justified until pilot validates core value |
| Species identification from photos | PRD Non-Goal | iNaturalist handles upstream; building competing CV adds complexity without differentiation |
| Drone/satellite imagery ingestion | PRD Non-Goal | Requires specialized image processing pipeline; ground observations sufficient for MVP validation |
| Macroinvertebrate index scoring | FEAT-001 Out of Scope | Strong ecological signal but public dataset availability varies by watershed; assess during pilot |
| eBird integration | PRD P2-4 | Supplements iNaturalist bird data; not blocking for initial ecological reasoning |
| Collaborative annotation/overrides | PRD P2-1 | Valuable for reasoning quality feedback loop; not required for initial pilot |
| Custom report templates (NOAA, BPA, tribal) | PRD P2-2 | OWEB format sufficient for Oregon pilot; additional formats per customer demand |
| Historical multi-year trend visualization | PRD P2-3 | Useful but not critical for first-season pilot with limited historical data |
| GIS desktop integration (ArcGIS/QGIS plugins) | FEAT-006 Out of Scope | Many users have existing GIS workflows; assess adoption barrier during pilot |
| Climate-downscaled forecasting | FEAT-002 Out of Scope | Adds precision to forecasts but requires climate model integration |
| Acoustic sensor (BirdNET) integration | PRD P1-4 | Strong biodiversity signal; depends on BirdNET API availability |
| Cross-watershed comparative analytics | PRD P1-3 | Requires multiple active watersheds; build after second watershed onboards |

## Phase 3 Candidates

| Item | Source | Notes |
|------|--------|-------|
| Insurance nature-risk underwriting scores | Seed strategy | Enterprise expansion after public-sector validation |
| TNFD biodiversity disclosure reporting | Seed strategy | Regulatory-driven; market still maturing |
| Carbon + biodiversity co-optimization | Seed strategy | High value but requires additional data sources and modeling |
| Private land portfolio scoring | Seed strategy | PE/agriculture expansion market |
| Multi-state regulatory compliance | PRD Non-Goal | Per-state template expansion |
