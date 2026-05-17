# Design Plan: Pollution & Watershed-Stressor Data Feeds (Water, Land, Air, Development)

**Date**: 2026-05-16
**Status**: RESEARCH — not yet committed
**Phase**: 02-design — companion to [`data-sources-roadmap.md`](./data-sources-roadmap.md)
**Scope**: Catalog publicly available data feeds covering Oregon, Washington, Utah, and Virginia that bear on watershed health, with recommendations for how each feed enhances RiverSignal product surfaces. Four signal channels are in scope: **water** (direct measurement), **land** (contamination source attribution), **air** (atmospheric deposition + smoke chemistry), and **development pressure** (housing, commercial growth, impervious-surface expansion).

> **Status legend**: 🟢 implemented | 🟡 partially implemented | ⚪ not yet implemented
> **Effort legend**: L = ≤1 day adapter, M = 1–3 day adapter (auth, joins, schema work), H = >3 day (rasters, time-series infra, or scraping)

---

## Problem Statement

RiverSignal today ingests biological signal (iNat, ODFW/WDFW, stocking), hydrological signal (USGS gauges, SNOTEL, PRISM), and a thin slice of water chemistry (Water Quality Portal — source #3, ~66K time series). Four product surfaces are blocked or weakened by missing pollution + watershed-stressor context:

1. **Path Now / River Now hero card** lacks swim-safety, fishing-safety, and HAB warnings; "is this water safe right now?" is the most common unanswered user question logged from the 2026-04 user-testing sessions on the Shenandoah and Skagit pilots. Also lacks "active construction upstream" sediment-pulse warnings.
2. **Steward** (watershed health trends) can show flow, snowpack, and fish observation trends but cannot tell the *story of why a watershed is healthy or degraded* without nutrient loadings, point-source discharges, mining/Superfund context, atmospheric N/Hg deposition, *or development pressure* (housing growth, impervious-surface expansion, urban-growth-boundary status).
3. **Catch-Probability** (hatch reliability, species temp optima) ignores pollution-driven stressors: HAB-induced fish kills, mercury advisories for striped bass/catfish/walleye, post-wildfire ash + sediment events, and CAFO-driven nutrient pulses.
4. **DeepTrail / Explore** (place-based context) has no way to anchor "what is this place" stories to actual structures, urban-growth boundaries, or development history — features that would make local browsing feel grounded.

This document catalogs feeds across water/land/air pollution **and land-use change & development pressure** categories that fix those gaps. It complements `data-sources-roadmap.md`, which is the canonical inventory of *all* data sources; this plan focuses specifically on watershed-stressor signals and ties each feed to concrete RiverSignal product value.

---

## 1. Water Pollution Feeds

### 1.1 Federal — cover all 4 states uniformly

| Status | Feed | Carries | Access | Effort | Notes |
|---|---|---|---|---|---|
| 🟢 | **EPA / USGS Water Quality Portal (WQP)** | ~430M results aggregating EPA WQX + USGS NWIS + 400+ state/tribal/local agencies. Chemistry, biology, sediment, fish-tissue, algal taxa. | REST `https://www.waterqualitydata.us/` (CSV/JSON), filter by state, HUC, organization, characteristic. WQX 3.0 is current schema. | — | Already shipped as source #3 but filter is narrow (nutrient/turb/pH/EC). Expand to pull mercury, PFAS, pesticide residues, total dissolved solids, fecal indicators. |
| 🟢 | **USGS NWIS / Water Data for the Nation** | Continuous + discrete water quality, real-time gauges, nutrient + turbidity + DO sensors. | REST `https://api.waterdata.usgs.gov/`, OpenAPI `https://nwis.waterservices.usgs.gov/openapi/`, `dataretrieval` Python/R. | — | Already shipped as source #28 for flow/temp. Expand to pull instantaneous turbidity and conductance where available. |
| ⚪ | **EPA ECHO — ICIS-NPDES DMR** | Discharge Monitoring Reports for every NPDES facility: effluent loadings, permit limits, exceedances, by month. | Annual CSV national files (`npdes_dmr_fyXXXX.zip`), per-facility XLSX/CSV via UI. REST web services (Effluent Charts, Loading Tool) at `https://echo.epa.gov/tools/web-services`. | M | The pollution-source ledger. Tied to NPDES permits — every regulated wastewater/stormwater discharger. Snapshot monthly. |
| ⚪ | **EPA Envirofacts / TRI** | Toxic Release Inventory: industrial water releases (lb/yr) by chemical, facility, state. | REST `https://data.epa.gov/efservice/tri_facility/state_abbr/<ST>/...` (CSV/XML/Excel). TRI Explorer for interactive. | L | Annual, lagged ~12 months. Useful for prioritization, not real-time. |
| ⚪ | **EPA / CDC OHHABS + EPA CyAN** | Algal-bloom event records (OHHABS) and near-real-time satellite cyanobacteria abundance for lakes/reservoirs ≥1 km² (CyAN, Sentinel-3 based, weekly composites). | OHHABS state CSVs at CDC; CyAN app + tile downloads. | M | OR has CyAN coverage; VDH dashboard for VA. Critical for swim/fishing safety on lakes & reservoirs. |
| ⚪ | **EPA SDWIS (drinking water)** | Public water system violations and contaminant exceedances (lead, nitrate, DBPs). UCMR 5 PFAS layer is the current emerging-contaminant slice (2023–2025). | Envirofacts REST (same shape as TRI). | M | Indirect watershed signal — exceedances often trace to source-water contamination. |
| ⚪ | **EPA ATTAINS (CWA 303(d) / 305(b))** | Per-segment impaired-waters listings, TMDLs, designated uses, attainment status. | ATTAINS REST services at `https://www.epa.gov/waterdata/attains`. | M | Required to drive a "what's wrong with this water" narrative in Steward. |
| ⚪ | **EPA Beach Advisory & Closing Notification (BEACON)** | Coastal & large-lake recreational closures. | Envirofacts + downloadable lists. | L | Highest direct user safety value for OR/WA coasts and VA tidal sites. |

### 1.2 State-specific water quality

#### Oregon
| Status | Feed | Access | Effort |
|---|---|---|---|
| 🟡 | **OR DEQ AWQMS** — rivers, streams, lakes, estuaries, beaches, groundwater. Public portal off `https://www.oregon.gov/deq/wq/pages/wqdata.aspx`. Submits to WQP as `OREGONDEQ`. | Easiest path is WQP filtered to org. | L when piggybacking on WQP. |
| ⚪ | **Your DEQ Online (Public Records Portal)** — replaced ECSI April 2024. Cleanup sites, contamination, spill records. | Portal search only, no API. Use bulk pulls or selective HTML scrape. | M |
| ⚪ | **OregonExplorer Hub** — GIS shapefiles for AWQMS station locations. | Shapefile download. | L |
| ⚪ | **Oregon HABs ArcGIS** | Already on roadmap as "retry — URL needs fixing". | L |

#### Washington
| Status | Feed | Access | Effort |
|---|---|---|---|
| 🟡 | **Ecology EIM** — water/sediment/biota/air/soil. UI at `https://apps.ecology.wa.gov/eim/search/`. Submits to WQP as `WAECY`. | No public REST API — use WQP for the WQX subset; EIM bulk UI for fields not in WQX. | M (WQP path), H (EIM scrape for proprietary fields). |
| ⚪ | **Ecology River & Stream WQ Monitoring program** — long-term ambient stations. | Same EIM backing store. | M |
| ⚪ | **Ecology 303(d) / WA WQ Assessment** — impaired waters lists, GIS layers. | GIS Data page. | L |
| ⚪ | **WDOH Shellfish Beach closures** — fecal/biotoxin closures for marine watersheds. | Public dashboard, no API documented; consider scrape. | M |

#### Utah
| Status | Feed | Access | Effort |
|---|---|---|---|
| 🟡 | **Utah DWQ AWQMS** — portal entry at `https://deq.utah.gov/water-quality/databases-and-information`. R package `utah-dwq/wqTools::readAWQMS()`. Submits to WQP as `UTAHDWQ_WQX`. | Easiest path is WQP filtered to org. | L when piggybacking on WQP. |
| ⚪ | **Utah DEQ Interactive Map** — each layer downloadable as shapefile or table. | Shapefile / CSV download. | L |
| ⚪ | **Utah DOGM AWQMS** — separate AWQMS instance for coal-mining-related water quality at `https://ogm.utah.gov/awqms-access/`. | UI download; relevant for Price River / Emery County. | M |
| ⚪ | **Utah Integrated Report** — 303(d)/305(b) impaired waters. | Cross-walked with EPA ATTAINS. | L |

#### Virginia
| Status | Feed | Access | Effort |
|---|---|---|---|
| 🟡 | **VA DEQ CEDS WQM** — ~1,000+ ambient stations, backing store. Submits to WQP as `21VASWCB_WQX` / `VADEQ`. | WQP filter, plus Virginia Environmental Data Hub (`https://geohub-vadeq.hub.arcgis.com/`) for ArcGIS REST feature services. | M |
| ⚪ | **Annual Water Quality Monitoring Plan** — interactive map of upcoming stations/parameters/frequencies. | ArcGIS feature service. | L |
| ⚪ | **VA Integrated Report (305(b)/303(d))** — impaired waters, TMDLs. | Cross-walked with EPA ATTAINS. | L |
| ⚪ | **VDH HAB Dashboard** — `https://www.vdh.virginia.gov/waterborne-hazards-control/algal-bloom-surveillance-map/` (the strongest near-real-time state HAB feed of the four). | Public dashboard, scrape or feature-service. | M |
| ⚪ | **VA DEQ Volunteer Monitoring** — citizen-submitted data lands in CEDS. | Already in WQP. | L |

---

## 2. Land Pollution Feeds

Land pollution feeds answer "where is the pollution *coming from*?" — they are source-attribution layers for the water-quality measurements above.

### 2.1 Federal — cover all 4 states uniformly

| Status | Feed | Carries | Access | Effort |
|---|---|---|---|---|
| ⚪ | **EPA Facility Registry Service (FRS)** | Integrated air/water/waste facility registry — cross-references TRI, NPDES, SEMS, RCRA, Brownfields, Air. | REST `https://www.epa.gov/frs/frs-rest-services`; FRS Facilities & Linkages bulk file via ECHO. | M |
| ⚪ | **EPA Superfund — SEMS** | Active + archived hazardous waste sites under CERCLA. Replaced CERCLIS in 2013. | Via FRS REST and ECHO downloads. Filter by state/zip/coord radius. | M |
| ⚪ | **EPA RCRAInfo** | Hazardous waste generators, transporters, TSD facilities. Inspections + enforcement actions. | Envirofacts REST + ECHO downloads. | M |
| ⚪ | **EPA Brownfields (ACRES)** | Brownfield assessment, cleanup, redevelopment grants. | Envirofacts REST. | L |
| ⚪ | **EPA TRI on-site land releases** | Industrial land disposal (landfills, surface impoundments) by chemical. | Same REST as water-side TRI; filter on `LAND_RELEASES` columns. | L |
| ⚪ | **USDA NASS Agricultural Chemical Use Survey** | On-farm pesticide and fertilizer application rates by commodity (rotating: corn/soy/cotton/potatoes/wheat/fruits/vegetables). | Quick Stats API at `https://www.nass.usda.gov/developer/`. | M |
| ⚪ | **USDA NASS Cropland Data Layer (CDL)** | 30 m annual raster of crop type, 2008–present nationally. | CroplandCROS GeoTIFF + WMS. | H (raster ETL into HUC summaries). |
| 🟡 | **USGS MRLC / NLCD** | National Land Cover Database — impervious surface, canopy, urbanization. | GeoTIFF download, WMS. | H (raster ETL). Existing geology and SSURGO patterns from `pipeline/ingest/streamnet.py` would help. |
| ⚪ | **USDA SSURGO soils** | High-resolution soil polygons, erodibility (K-factor), runoff class. | Web Soil Survey + Soil Data Access REST. | H |
| ⚪ | **EPA NPDES CAFO permitted facilities** | Concentrated Animal Feeding Operations — nutrient point sources, runoff risk. | Via ECHO + FRS, filtered to SIC/NAICS. | M |
| ⚪ | **USGS Mineral Resources Data System (MRDS)** | Active + historic mines, tailings, mineral deposits. | REST + shapefile. | L |
| ⚪ | **USGS Abandoned Mine Lands inventory** | Inventoried abandoned mines, acid drainage risk. | Shapefile + WMS. | L |
| ⚪ | **PHMSA Pipeline Incident Reports** | Hazardous-liquid and gas pipeline accidents 1986–present, with lat/lon and commodity. | ZIP CSV downloads at `https://www.phmsa.dot.gov/data-and-statistics/pipeline/source-data`. | L |
| ⚪ | **NIFC WFIGS Wildfire Perimeters** | Best-available perimeters for all known wildland fires, current + historical. | NIFC Open Data ArcGIS REST at `https://data-nifc.opendata.arcgis.com/`. | L (geometry only); H if joining with USGS post-fire sediment/Hg risk. |
| ⚪ | **USGS Post-Fire Sediment & Mercury Risk** | Wildfire-driven sediment yield and Hg mobilization models for western US through 2050. | USGS publication-grade GeoTIFF / shapefile. | H |

### 2.2 State-specific land pollution

#### Oregon
- **Your DEQ Online (Public Records Portal)** — also the cleanup/contamination repository (ECSI successor as of April 2024). Spill reports phoned to OERS (800-452-0311) end up here. No public API; portal search only.
- **DOGAMI mining permits** — Oregon Dept of Geology and Mineral Industries. Aggregate, hard-rock, and oil/gas via ArcGIS.
- **ODF Forest Practices** — timber harvest notification system; relevant to sediment events.

#### Washington
- **Ecology Toxics Cleanup Program (TCP) — CLARC + Confirmed Contaminated Sites** — state CERCLA-equivalent registry. ArcGIS layers available.
- **WA DNR mining permits** — surface and reclamation permits. ArcGIS feature services.
- **DNR Forest Practices** — timber harvest applications, road-density indicators.
- **Ecology Spill incidents** — reportable spills via ERTS. Search UI only.

#### Utah
- **Utah Division of Oil, Gas & Mining (DOGM)** — Permit, plug, spill records. Includes the DOGM AWQMS for coal-mining water (listed above under Water).
- **Utah DEQ Environmental Incidents Database** — spills, releases, complaints.
- **DAQ + DERR cleanup sites** — UST/LUST, Voluntary Cleanup.

#### Virginia
- **VA DEQ Petroleum Storage Tank Program** — UST/LUST records, cleanup status.
- **VA DEQ CEDS (Solid/Hazardous Waste module)** — landfill, transfer station data.
- **Virginia DMME (now DEE)** — mining and energy permits, especially coal in Southwest VA.
- **VA DEQ Spill / PReP database** — reportable releases.

---

## 3. Land-Use Change & Development Pressure Feeds

Housing growth, commercial development, and the transition from forest/agricultural land cover to impervious surface is one of the strongest non-point-source drivers of watershed degradation: more rooftops + roads + parking lots → flashier hydrology, higher peak flows, elevated water temperature, thermal pollution, nutrient pulses from lawns and pet waste, road-salt loading, and construction-phase sediment slugs. These feeds answer "where is the watershed *changing*, and how fast?" — context that turns Steward from a snapshot into a trend story and powers an "encroachment risk" tile on Path Now / DeepTrail.

### 3.1 Federal — cover all 4 states uniformly

| Status | Feed | Carries | Access | Effort |
|---|---|---|---|---|
| ⚪ | **U.S. Census Bureau Building Permits Survey (BPS)** | Monthly + annual residential permits authorized by structure type. Reported at national, region, division, state, CBSA, county, and permit-issuing-place level. Coverage since 1959. | Web CSV at `https://www.census.gov/permits` + Census Economic Indicators API (monthly/quarterly). ~12 working days after reference month for preliminary, ~17 days for state/county detail. | L |
| ⚪ | **U.S. Census American Community Survey (ACS)** | Housing characteristics (units, year built, occupancy, value, gross rent), commute mode, population density. 5-year tract-level estimates. | Census Data API. | L |
| ⚪ | **U.S. Census Population Estimates Program (PEP)** | Annual population estimates by state/county/place — the most reliable growth-pressure signal. | Census Data API. | L |
| ⚪ | **EPA Smart Location Database (SLD) v3.0** | 90+ built-environment indicators at the 2019 Census Block Group level: development density, land-use diversity, street-network design, destination accessibility, employment + transit metrics. | ArcGIS REST `https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer`; downloads at the Smart Location Mapping page. | M |
| ⚪ | **USA Structures (FEMA + ORNL + USGS)** | National point/footprint inventory of every structure >450 sq ft, used for flood-insurance + emergency response. | ArcGIS Hub (`gis-fema.hub.arcgis.com`), HIFLD, Data.gov. CSV/KML/GeoJSON/GeoTIFF. | M (large files; ~125M structures.) |
| ⚪ | **Microsoft US Building Footprints + Global ML Building Footprints** | ~130M US polygons, periodically re-released. Global set is 1.4B buildings from 2014–2024 imagery. ODbL license. | GitHub `microsoft/USBuildingFootprints`, `microsoft/GlobalMLBuildingFootprints`. GeoJSON `.csv.gz` partitioned by quadkey. | M–H |
| 🟡 | **USGS NLCD impervious surface + canopy** | National annual + epoch impervious-surface raster, 30 m, 1985–present. The single best long-trend impervious-surface dataset. | MRLC viewer + GeoTIFF + WMS. | H — already noted in §2 Land. Same raster ETL applies. |
| ⚪ | **USGS LCMAP** | 10 annual science products covering land cover + change for CONUS 1985–2021 (Collection 1.3, Aug 2022). Goes deeper on *change* than NLCD: change date, magnitude, time-since-change. | GeoTIFF mosaics at `https://eros.usgs.gov/lcmap/apps/data-downloads`. WMS + EarthExplorer. | H (raster ETL). |
| ⚪ | **NOAA C-CAP (Coastal Change Analysis Program)** | Coastal land cover + change at 1 m + 30 m, 5-year cadence. Relevant for OR, WA, VA tidal watersheds. | Bulk download + WMS. | H |
| ⚪ | **EPA NPDES MS4 Permitted Municipalities + Notices of Intent** | Phase I + Phase II MS4 (Municipal Separate Storm Sewer System) operators — the regulated urban stormwater universe. Every MS4 has TMDL load allocations. | Via ECHO Water Facility Search + ICIS-NPDES exports. eReporting NeT for current NOIs. | M |
| ⚪ | **EPA NPDES Construction General Permit (CGP) NOIs** | Every construction site >1 acre disturbance covered under federal CGP. New filings = leading indicator of imminent sediment-pulse risk. | EPA Permit Lookup tool + NeT NOI search. | L–M |
| ⚪ | **USACE Section 404 wetland permits** | Wetland fill / dredge permits — every commercial or residential development that touches a wetland or stream. | USACE Regulatory Request System (RRS) + ORM2 data; some state-level via state portals. | M |
| ⚪ | **USFS FIA (Forest Inventory and Analysis)** | Plot-level forest condition; FIA's `MORTYR` and removals fields track forest loss including to development. | EVALIDator + FIA datamart CSV. | M |
| ⚪ | **HUD CHAS + AHS + LIHTC / Section 8** | Housing affordability, age, condition — useful for "is this a build-out-saturated watershed or a greenfield-development one?" | HUD User datasets, mostly CSV. | M |
| ⚪ | **USDA ERS Rural-Urban Continuum + Urban Influence Codes** | County-level urbanization classification. | CSV download. | L |
| ⚪ | **EPA ICLUS (Integrated Climate and Land-Use Scenarios)** | Projected housing density 2010–2100 under multiple SSP scenarios — *forward-looking* development pressure. | GeoTIFF + report. | H |
| ⚪ | **BLS QCEW (Quarterly Census of Employment and Wages)** | Commercial activity proxy by NAICS and county/zip. | BLS REST API. | M |

### 3.2 State-specific development & permitting feeds

#### Oregon
- **Oregon DLCD (Dept of Land Conservation and Development)** — Urban Growth Boundaries (UGBs), Goal 14 (urbanization) implementation, statewide planning goals. ArcGIS feature services for UGBs. The UGB layer alone is high-value: every parcel inside is permitted to develop; every parcel outside is statutorily protected.
- **Oregon Office of Economic Analysis** — county population forecasts.
- **OR DEQ MS4 + 1200-C construction stormwater** — state-administered NPDES; permits searchable in Your DEQ Online.
- **Oregon Spatial Data Library + Metro RLIS** (Portland metro) — parcel + zoning layers.
- **Oregon Department of Forestry (ODF) Forest Practices** — Notifications of Operation (timber harvest); already noted in §2 Land but is also a development-adjacent feed in areas where harvest is followed by conversion.

#### Washington
- **WA Office of Financial Management (OFM)** — county population forecasts and projections; the Growth Management Act planning anchor.
- **WA Dept of Commerce GMA Comprehensive Plans + UGAs** — every GMA-planning county/city's adopted Urban Growth Area boundary; mid-cycle 8-year refresh.
- **WA Ecology MS4 (Western + Eastern Phase I/II) + Construction Stormwater General Permit** — state-administered NPDES; permits searchable in ECY's WPLCS / PARIS.
- **WA OFM Building Permits** — state-aggregated complement to Census BPS.
- **King County, Pierce County, Snohomish County, Whatcom County open data portals** — parcel + permit feeds with reasonable API coverage (Socrata-shaped or ArcGIS).

#### Utah
- **Utah AGRC (Automated Geographic Reference Center) — gis.utah.gov** — statewide parcels (SGID Cadastre), zoning where available, building footprints.
- **Utah Governor's Office of Planning and Budget (GOPB) demographics** — county population projections.
- **Utah DEQ MS4 + Utah Pollutant Discharge Elimination System (UPDES) construction permits** — state-administered.
- **Wasatch Front Regional Council + Mountainland AOG** — MPO transportation models with land-use inputs (TAZ-level).
- **Salt Lake County, Utah County, Davis County, Washington County GIS** — parcel + permit feeds.

#### Virginia
- **VA DEQ Virginia Stormwater Management Program (VSMP)** — state-administered MS4 + construction general permit (VPDES-equivalent). Searchable via VA DEQ CEDS.
- **Virginia Geographic Information Network (VGIN)** — statewide parcel layer, building footprints.
- **Virginia Employment Commission Population Estimates** — county-level.
- **Chesapeake Bay Program Phase 6 Watershed Model land-use inputs** — high-fidelity land-use change for the Bay watershed (covers all of VA's eastern + central drainages); a published 30 m product calibrated for Bay TMDL.
- **Northern Virginia Regional Commission + Hampton Roads PDC + Richmond Regional PDC** — MPO/PDC parcel + zoning + permit feeds for the three biggest VA growth corridors.

---

## 4. Air Pollution Feeds (Watershed-Relevant)

Air pollution affects watersheds three ways: **wet/dry atmospheric deposition** (N, S, Hg, PFAS) drives nutrient and toxin loading directly; **wildfire smoke** carries Hg and ash that settle into snowpack and surface waters; **ambient AQI** is an ecological-stress and recreational-safety signal.

### 4.1 Federal — cover all 4 states uniformly

| Status | Feed | Carries | Access | Effort | Watershed relevance |
|---|---|---|---|---|---|
| ⚪ | **NADP NTN** (National Trends Network) | Wet deposition: H⁺, SO₄²⁻, NO₃⁻, NH₄⁺, Ca, Cl, etc. ~250 sites. | Free CSV at `https://nadp.slh.wisc.edu/`. | L | Atmospheric N is a major driver of nitrate in headwaters and HAB risk in nutrient-limited systems. |
| ⚪ | **NADP MDN** (Mercury Deposition Network) | Wet total + methyl mercury in precip. | Same NADP portal. | L | Methyl-Hg in fish (especially walleye, striped bass, catfish) — directly informs consumption advisories. |
| ⚪ | **NADP AMoN** (Ammonia) | Atmospheric NH₃ gas concentrations, ~100 sites. | Same NADP portal. | L | Cropping + CAFO airshed → downwind ammonia → wet N deposition. |
| ⚪ | **NADP AMNet / CASTNET** | Atmospheric Hg speciation; dry deposition of N, S, O₃. | EPA CASTNET portal. | L | Pairs with MDN for total Hg loading; pairs with NTN for total N. |
| ⚪ | **EPA AirNow** | Real-time AQI from 2,500+ monitors: O₃, PM₂.₅, PM₁₀. | REST + FTP at `https://docs.airnowapi.org/`; requires free key. | L | Smoke-event detection; user-facing recreational safety. |
| ⚪ | **EPA AQS** | Authoritative ambient air sample archive from state/local/tribal agencies. | JSON REST at `https://aqs.epa.gov/aqsweb/documents/data_api.html`; ~6-month lag; requires free key. | M | Backfill / trend analysis; pairs with NEI for source attribution. |
| ⚪ | **EPA NEI** (National Emissions Inventory) | Triennial inventory of criteria + HAP emissions by facility, county, mobile. | Bulk CSV at EPA NEI page. | M | Source attribution behind NADP and AirNow signals. |
| ⚪ | **NOAA HMS Smoke Product** | Daily satellite-detected smoke plumes (light/medium/heavy). | Shapefile / KML from NESDIS. | L | Pair with NIFC WFIGS to detect smoke-impacted watershed days. |
| ⚪ | **NOAA HYSPLIT** | Air-parcel trajectory + dispersion model. | Web tool + REST runs. | H | Source attribution: "did the Hg load in this watershed event come from upwind coal generation?" |
| ⚪ | **IMPROVE network** | Visibility / aerosol speciation (organic carbon, sulfate, nitrate, dust). | CSV downloads. | L | Aerosol context for deposition modeling. |
| ⚪ | **PurpleAir** | Dense community PM₂.₅ network. | REST, requires registration. | L | Hyper-local smoke + dust; user-facing trust value. |

### 4.2 State-specific air pollution

The big four state agencies do air quality through their own networks, but virtually all of it flows to AQS within the 6-month lag window, and AirNow carries the live feed. Pull federal first; reach for state portals only if filling gaps.

- **OR DEQ Air Toxics** — periodic monitoring studies, especially Portland-area.
- **WA Ecology Air Quality** — Eastern WA agricultural-burn permits, ECY ambient stations.
- **Utah DAQ** — winter inversion PM₂.₅ (Wasatch Front); ozone in Uinta Basin.
- **VA DEQ Air Quality** — Chesapeake airshed N deposition is a federally-recognized watershed driver.
- **Tribal air monitoring** — Yakama, CTUIR, Confederated Tribes of Warm Springs, Ute, Eastern Band of Cherokee — varies; many submit to AQS.

---

## 5. Recommendations: how each feed enhances RiverSignal

Each feed below is annotated with the **product surface** it lights up, what the **user-facing feature** would look like, and **integration shape** (does it slot into existing `observations` / `gold` tables, or need new infra?).

### 5.1 Direct user-safety wins (Path Now / River Now hero card)

| Feed | Product feature | Integration shape |
|---|---|---|
| **EPA CyAN + state HAB dashboards** (VDH, OR ArcGIS, WA shellfish biotoxin) | "🟡 Cyanobacteria advisory active — avoid contact" badge on hero card; explicit toggle on swim-safety modal. | Polygons + advisory status; new `gold.water_safety_advisories` MV joining HAB polygons to watershed sites. Daily refresh. |
| **EPA BEACON beach closures** | "🔴 Beach closed — fecal bacteria" badge for tidal/coastal sites in OR, WA, VA. | Daily polling; same advisory MV. |
| **AirNow** (AQI for O₃/PM₂.₅) | "Smoke advisory — PM₂.₅ unhealthy" badge; downgrade fishing/hike recommendations on Code Orange+ days. | Already adjacent to existing weather card; new `gold.air_now_current` row per site. |
| **NIFC WFIGS active perimeters + NOAA HMS smoke** | "Wildfire X mi upwind — heavy smoke today" hero copy; auto-flag post-fire watersheds for 2 years (ash + sediment risk on Catch Probability). | Polygon overlap with `sites.watershed`; flag in `gold.watershed_health_score`. |
| **VA DEQ + VDH HAB** | Shenandoah-specific HAB badge with attribution to VDH. | Same advisory MV. |

### 5.2 Steward (watershed-health storytelling)

| Feed | Product feature | Integration shape |
|---|---|---|
| **EPA ECHO ICIS-NPDES DMR** | "12 permitted dischargers in this HUC; 2 had effluent exceedances in 2026 Q1" tile. Click → list of facilities with effluent trends. | Monthly snapshot; new `silver.npdes_discharges` table joined to HUC. |
| **EPA TRI water + land releases** | "143,000 lb toxics released to water in 2024 from facilities in this watershed". Top-N chemicals callout. | Annual snapshot; new `silver.tri_releases`. |
| **EPA ATTAINS 303(d)** | "🟡 8 stream miles in this watershed are listed impaired for: nutrients, sediment, bacteria." | One-time + annual refresh; new `silver.attains_listings`. |
| **NADP NTN + MDN + AMoN** | Trend tile: "Atmospheric N deposition: 6.8 kg/ha/yr, ↓12% since 2010"; methyl-Hg deposition for fish-advisory context. | Annual; new `silver.atm_deposition` table keyed to NADP site → nearest watershed. |
| **USGS post-fire sediment / Hg risk model** | "Post-fire sediment yield 1st year forecast: 3.2× normal" callout for fire-impacted watersheds. | One-time raster ETL into `silver.post_fire_risk` polygons. |
| **EPA RCRAInfo + SEMS** | "2 Superfund sites within 5 km of watershed; status: in remediation". | One-time + quarterly; new `silver.contaminated_sites`. |
| **USGS Abandoned Mine Lands** | "47 abandoned mines in this HUC, 9 with documented acid drainage". Targets UT (Bingham/Tintic), OR (Eastern OR), WA (Cascade gold belt), VA (SW VA coal). | One-time; `silver.abandoned_mines`. |
| **Census Building Permits Survey (BPS) + ACS + PEP** | Trend tile: "Housing units in this watershed: 12,400, +18% since 2015" with sparkline. "Build-out velocity" ranking among RiverSignal watersheds. | Monthly + annual; new `silver.development_pressure` table keyed to HUC via county apportionment. |
| **USGS NLCD impervious + LCMAP land-change** | Trend tile: "Impervious surface: 8.4% of watershed, +1.2 pp since 2010". Map overlay: red-shaded "developed since 2015" polygons. | Raster ETL → `silver.land_cover_change` (uses the §5.5 raster stack). |
| **EPA Smart Location Database** | Walkability + transit-accessibility context for urbanized portions of the watershed; informs urban-stormwater risk modeling. | ArcGIS REST → `silver.built_environment` (CBG-level → HUC roll-up). |
| **EPA NPDES MS4 + CGP NOIs** | "73% of this watershed is regulated under MS4 stormwater permits"; "14 active construction sites >1 acre right now — sediment-pulse risk elevated for next 6 months". | MS4 layer is annual; CGP NOIs polled weekly; `silver.stormwater_jurisdictions` + `silver.active_construction_sites`. |
| **USACE Section 404 + USFS FIA** | "Forest cover in this watershed: 62%, ↓4.1 pp since 2015 (development conversion 78% of loss)". 404 permit count for wetland fill in the last 5 years. | Annual; `silver.land_conversion`. |
| **EPA ICLUS scenario projections** | Forward-looking "By 2050, projected housing density implies +17% impervious surface in this watershed (SSP2 baseline)" — a sustainability-positioning narrative for Steward. | One-time scenario raster ETL; `silver.land_use_projection`. |
| **Chesapeake Bay Phase 6 land-use (VA only)** | VA-specific high-fidelity "watershed land-use change since 2010" overlay for Bay drainages. | One-time; `silver.cbp_landuse`. |

### 5.3 Catch-Probability + fishing intelligence

| Feed | Product feature | Integration shape |
|---|---|---|
| **NADP MDN + WQP fish-tissue Hg** | Auto-attach "⚠️ State fish-consumption advisory: limit to 1 meal/month" on the catch-probability card for the affected species (smallmouth bass, striped bass, walleye, channel cat). | New `silver.fish_tissue_contaminants` + state-advisory cross-walk. Pairs with the warmwater models already added in `plan-2026-05-15-warmwater-species-coverage.md`. |
| **CyAN + HAB** | Suppress "good day for bass" recommendations on lakes during active bloom. | Use the advisory MV from 5.1 as a Catch-Probability scoring penalty. |
| **NIFC WFIGS + NOAA HMS** | Two-year post-fire flag downgrades hatch-reliability scores (ash slug + suspended-sediment risk). | Watershed-level post-fire flag in `gold.hatch_chart`. |
| **EPA NPDES CAFO + USDA NASS Chemical Use** | Surface "high nutrient pulse risk: agriculture-dominated headwaters" for the affected species set; useful for explaining anomalous hatch failures. | Annual + survey-cycle; `silver.ag_pressure_index` keyed to HUC. |

### 5.4 DeepTrail / Explore (place-based context)

| Feed | Product feature | Integration shape |
|---|---|---|
| **USGS MRDS + Abandoned Mine Lands** | Mine cards in Explore for OR/WA/UT/VA mining regions; "Old gold-stamp mill, 1873, acid drainage to Eel Creek" deep links. | One-time load. |
| **PHMSA pipeline incidents** | Layer on the Explore map: red dots for historical hazmat releases (especially Yellowstone-style oil spills, OR Columbia gorge crude-by-rail incidents). | One-time + annual; `silver.pipeline_incidents`. |
| **EPA FRS** | Universal "What facility is this?" lookup near user location. | Cross-walk; not a customer-visible feature, but powers the others. |
| **USA Structures + Microsoft Building Footprints** | "What's here?" lookup: building footprints draped on the Explore map; lets DeepTrail anchor user-location stories ("you are 320 m from the historic Lewis Mill, built 1887"). | One-time large download; `silver.building_footprints` partitioned by watershed bbox. |
| **OR DLCD UGB / WA GMA UGA boundaries** | "You are inside the Portland UGB" / "Inside the Spokane UGA" context tag on Path Now; explains why density is high here and rural protections apply elsewhere. | One-time; `silver.urban_growth_boundaries`. |
| **EPA NPDES CGP active sites** | Path Now ephemeral warning: "Construction site upstream of you, sediment pulse possible after next rain". | Weekly polled; same `silver.active_construction_sites` from §5.2. |

### 5.5 Infra cross-cuts

- **EPA Water Quality Portal expansion (existing #3)** — broaden the characteristic filter to add **Hg, PFAS (PFOA/PFOS), atrazine, glyphosate, total dissolved solids, fecal coliform, E. coli, enterococci**. Reuses the existing adapter; low-risk schema-only change in the chemistry MV.
- **ECHO DMR adapter** — first net-new pollution adapter. Once shipped, FRS + RCRA + SEMS + Brownfields + CAFO all reuse the same facility→HUC cross-walk and snapshot infrastructure.
- **Raster ETL infrastructure** — NLCD, CDL, SSURGO, USGS post-fire risk, LCMAP, NOAA C-CAP, ICLUS scenarios all need a watershed-aggregated rasterstats pipeline (`rasterio` is already in `pyproject.toml`). Worth standing up once and reusing — this is the single highest-leverage infra investment in this plan.
- **Vector polygon ingest infrastructure** — UGBs, UGAs, MS4 service boundaries, USACE 404 polygons, USA Structures, building footprints all share an "ingest large polygon set, clip to watershed bbox, persist with PostGIS index" pattern. One adapter base class can serve all of them.
- **Census API key + HUD/HUD-User account** — manage the new auth surface explicitly; matches the secret-store work flagged in §7 Q4.

### 5.6 Layout sketch: /riversignal Stewardship tab

`/riversignal` is positioned as the "Watershed Research Assistant" for citizen scientists + amateur naturalists (`frontend/src/pages/LandingPage.tsx:13-19`). The right-side `SitePanel` (`frontend/src/components/SitePanel.tsx:21`) already has tabs `overview / species / rocks / predict / ask`. The natural home for the pollution + development feeds is either a beefed-up **overview** tab or a new **stewardship** tab.

The layout below is ordered to honor the doom-scroll guard from §4: lead with strengths, pair every alarm with an action or explainer, surface positive trends with the same visual weight as negative ones. ASCII for editor preview; production version is responsive desktop-first.

```
┌─────────────────────────────────────────────┬────────────────────────────────────────────────────┐
│                                             │ Shenandoah ·  VA                              ✕    │
│                                             │ ─────────────────────────────────────────────────  │
│                                             │ [overview] [species] [rocks] [STEWARDSHIP] [pred]  │
│                                             │ ─────────────────────────────────────────────────  │
│                                             │                                                    │
│                                             │ ┌─ Watershed Health Score ───────────────────────┐ │
│                                             │ │     72 / 100   ↗ +3 since 2020                 │ │
│                                             │ │   ▼ Water 78  ▼ Habitat 70  ▼ Development 65   │ │
│                MAP VIEW                     │ │   "Improving on N deposition + flow;            │ │
│                                             │ │    degrading on impervious surface + Hg."       │ │
│         (existing observation +             │ └────────────────────────────────────────────────┘ │
│          fossil overlays remain)            │                                                    │
│                                             │ ── 1. What's Intact ──────────────────────────────│
│                                             │ ┌────────────────────────┬─────────────────────┐ │
│                                             │ │ 🌲 Forest cover  62%   │ ⛰  Protected land  │ │
│                                             │ │ (USFS FIA + LCMAP)     │  18%  (PAD-US)      │ │
│                                             │ ├────────────────────────┼─────────────────────┤ │
│                                             │ │ 🐟 Native species 24   │ 🤝 4 active monitor │ │
│                                             │ │ documented (iNat)      │ programs (WQP orgs) │ │
│                                             │ └────────────────────────┴─────────────────────┘ │
│                                             │                                                    │
│                                             │ ── 2. Right Now ──────────────────────────────────│
│                                             │ ┌──────────────────────────────────────────────┐ │
│                                             │ │ ✅ Swim safety: OK as of 2 hr ago             │ │
│                                             │ │   (WQP bacteria + CyAN + VDH HAB dashboard)  │ │
│                                             │ ├──────────────────────────────────────────────┤ │
│                                             │ │ ⚠ Fish-consumption: smallmouth ≤2 meals/mo   │ │
│                                             │ │   (NADP MDN + WQP fish-tissue Hg)            │ │
│                                             │ │   → "Why?" → "How VDH tracks Hg"             │ │
│                                             │ ├──────────────────────────────────────────────┤ │
│                                             │ │ 🏗 1 active construction site 2.4 mi upstream│ │
│                                             │ │   New 15-ac warehouse, NOI filed 2026-04-22  │ │
│                                             │ │   (EPA CGP NOI feed)                          │ │
│                                             │ │   → "Comment on permit" (link to VA portal)  │ │
│                                             │ └──────────────────────────────────────────────┘ │
│                                             │                                                    │
│                                             │ ── 3. Trend (10-year story) ─────────────────────│
│                                             │ ┌──────────────────────────────────────────────┐ │
│                                             │ │ Impervious surface       6.1% → 8.4%  ↑      │ │
│                                             │ │ (NLCD annual)            ▁▂▂▃▃▄▅▅▆▇         │ │
│                                             │ ├──────────────────────────────────────────────┤ │
│                                             │ │ Housing units          22,100 → 26,300  ↑    │ │
│                                             │ │ (Census BPS + ACS)       ▁▂▃▃▄▅▅▆▇▇         │ │
│                                             │ ├──────────────────────────────────────────────┤ │
│                                             │ │ Forest cover           66% → 62%  ↓          │ │
│                                             │ │ (LCMAP + FIA)            ▇▆▆▅▅▄▄▃▃▂         │ │
│                                             │ ├──────────────────────────────────────────────┤ │
│                                             │ │ N deposition         8.1 → 6.8 kg/ha/yr  ↓   │ │
│                                             │ │ (NADP NTN)               ▇▆▆▅▅▅▄▄▄▃ ✓ good  │ │
│                                             │ ├──────────────────────────────────────────────┤ │
│                                             │ │ Impaired stream miles    32 → 28  ↓          │ │
│                                             │ │ (EPA ATTAINS 303(d))     ▇▇▆▆▆▅▅▅▄▄ ✓ good  │ │
│                                             │ └──────────────────────────────────────────────┘ │
│                                             │                                                    │
│                                             │ ── 4. Why (sources & attribution) ───────────────│
│                                             │ ┌──────────────────────────────────────────────┐ │
│                                             │ │ Top discharger        Front Royal WWTP        │ │
│                                             │ │ (ECHO DMR)            no exceedances 2025–26 │ │
│                                             │ ├──────────────────────────────────────────────┤ │
│                                             │ │ Toxic releases (2024)  43,200 lb to water    │ │
│                                             │ │ (EPA TRI)               top: ammonia, zinc    │ │
│                                             │ ├──────────────────────────────────────────────┤ │
│                                             │ │ Legacy sites          1 Superfund (NPL), 3   │ │
│                                             │ │ (FRS + SEMS + RCRA)   RCRA generators        │ │
│                                             │ ├──────────────────────────────────────────────┤ │
│                                             │ │ Upwind Hg sources     2 EGUs in OH river vly │ │
│                                             │ │ (NEI + HYSPLIT — future)                     │ │
│                                             │ └──────────────────────────────────────────────┘ │
│                                             │                                                    │
│                                             │ ── 5. Take Action ────────────────────────────────│
│                                             │ ┌──────────────────────────────────────────────┐ │
│                                             │ │ 📝 2 open permits in comment window           │ │
│                                             │ │    (VA DEQ public-notice scrape)              │ │
│                                             │ │ 🔬 Volunteer monitoring near you (VA DEQ CMP) │ │
│                                             │ │ 🤝 Friends of Shenandoah River (local group)  │ │
│                                             │ │ 🚨 Report a HAB / spill / fish kill           │ │
│                                             │ └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────┴────────────────────────────────────────────────────┘
```

**Doom-scroll guards baked into the order**:

1. **Strengths first.** The very first tile under the score is "What's Intact" — forest %, protected acres, native species, active monitoring. A user lands and feels the watershed is *something worth caring about*, not a write-off.
2. **Every alarm pairs with action or context.** The Hg advisory has a "How VDH tracks Hg" explainer; the construction NOI has a "Comment on permit" link; the impaired-miles trend gets a green ✓ when it's actually improving.
3. **Positive trends share visual weight with negative ones.** N deposition and 303(d) impaired-miles are *down* in the Shenandoah — the design must show those with the same prominence as the impervious-surface increase, or naturalists will tune out as "yet another doom dashboard."
4. **Forward-looking projections (ICLUS) are deliberately absent from v1.** Per §7 Q10, projections need stronger visual separation from observed history; better added later as a labeled "Outlook" section than mixed into the trend tiles.
5. **No section is mandatory.** If a watershed has no active construction, §2's right-now tile collapses; if there are no Superfund sites, §4 shrinks. The doom-scroll risk drops further when sections naturally compress.

**Feed → tile mapping** (dependency chain for §6 bead triage):

| Section | Feeds required | Tier in §6 |
|---|---|---|
| Watershed Health Score (composite) | All of the below, weighted | Last to build — see §7 Q11 |
| 1. What's Intact | USFS FIA, LCMAP, PAD-US, iNat (have), WQP organizations | T1 item 7 + T3 items 16–17 |
| 2. Right Now | WQP (expanded), CyAN, VDH HAB, NADP MDN + fish-tissue, CGP NOIs | T1 items 1+5 + T2 item 14 |
| 3. Trend | NLCD, BPS, LCMAP, FIA, NADP NTN, ATTAINS | T1 items 2+7 + T3 items 16–17 |
| 4. Why (attribution) | ECHO DMR, TRI, FRS+SEMS+RCRA, NEI | T2 items 9–12 |
| 5. Take Action | State public-notice scrapes, volunteer-monitoring portals, watershed-group directory | **New: T2 item 23 (see §6)** |

**Two design follow-ups the sketch surfaces**:

- **Watershed Health Score composite** needs its own design plan. Weighting, trend-arrow math, sub-score definitions (Water / Habitat / Development), and the "improving on X, degrading on Y" headline-generation logic are all decisions that determine what "improving" and "degrading" mean across the rest of the UI. Tracked in §7 Q11; recommend authoring as `plan-2026-05-XX-watershed-health-score.md` before any tile in this sketch ships.
- **Section 5 "Take Action"** isn't really a data feed — it's a curated directory of state public-notice systems (OR Your DEQ Online, WA ERTS, UT DEQ Public Notices, VA DEQ Public Notices), volunteer-monitoring portals (state CMPs), and watershed groups (Friends-of-X organizations, riverkeepers, soil and water conservation districts). Added as **Tier 2 item 23** in §6. Closes the doom-scroll loop and is the cheapest section to ship — most of it is a structured links registry, not an ingest adapter.

---

## 6. Prioritization

### Tier 1 — High value, low effort (next 2 weeks if greenlit)

1. **Expand Water Quality Portal characteristic filter** to add Hg, PFAS, pesticide residues, fecal indicators. Reuses source #3 adapter. Unlocks fish-consumption advisory cards and bacteria-driven swim warnings. **Effort: L.**
2. **EPA ATTAINS 303(d) adapter** — populates a "what's wrong with this water" tile. Critical Steward storytelling. **Effort: M.**
3. **NIFC WFIGS active wildfire perimeters** — already on roadmap; pulls into hero card + Catch Probability post-fire penalty. **Effort: L.**
4. **AirNow live AQI** — REST API, free key. Smoke advisories on hero card. **Effort: L.**
5. **VDH HAB Dashboard (VA)** + **CyAN satellite cyanobacteria** — fastest path to Shenandoah swim-safety badge for the 2026 summer season. **Effort: M.**
6. **PHMSA pipeline incidents (historical)** — one-time CSV ETL, immediate Explore-map value. **Effort: L.**
7. **Census BPS + ACS + PEP** — monthly building permits + 5-year housing characteristics + annual population. Drives the Steward development-pressure tile and is the lowest-effort development feed by a wide margin. **Effort: L.**
8. **OR DLCD UGB + WA GMA UGA boundaries** — one-shot ArcGIS pulls; powers "you are inside/outside an urban growth boundary" context tag and is the cheapest land-use-policy signal available. **Effort: L.**

### Tier 2 — High value, medium effort (1-month horizon)

9. **EPA ECHO ICIS-NPDES DMR** — gateway to the FRS family. Steward gains its strongest "industrial discharge" story. **Effort: M.**
10. **EPA TRI water + land releases** — pairs with DMR; annual snapshot is easy. **Effort: L–M.**
11. **NADP NTN + MDN** — atmospheric N and Hg deposition trends; supports mercury advisories and Chesapeake/Cascade airshed storytelling. **Effort: L (data is small).**
12. **EPA FRS + SEMS + RCRA + Brownfields** — one adapter, four reusable layers via the FRS cross-walk. **Effort: M.**
13. **Beach Advisory (BEACON)** — coastal and large-lake closures for OR, WA, VA. **Effort: L.**
14. **EPA NPDES MS4 permitted operators + CGP Notices of Intent** — first development feed with operational impact: weekly poll of CGP NOIs lights up an "active construction upstream" Path Now warning. MS4 layer is annual. **Effort: M.**
15. **EPA Smart Location Database (SLD v3.0)** — ArcGIS REST, CBG-level built-environment metrics; one adapter unlocks Steward "walkability + urbanization" tile and feeds urban-stormwater modeling. **Effort: M.**
23. **State public-notice + volunteer-monitoring + watershed-group registry** (the "Take Action" §5.6.5 layer) — curated structured-links registry, not an ingest adapter. Per-state list of public-notice URLs (OR Your DEQ Online, WA ERTS, UT DEQ Public Notices, VA DEQ Public Notices), volunteer-monitoring portals (state CMPs), and watershed groups (Friends-of-X, Riverkeepers, SWCDs). Closes the doom-scroll loop in §5.6. **Effort: L (data is small, mostly hand-curated).**

### Tier 3 — High value, higher effort (raster ETL or scraping)

16. **NLCD impervious surface + USDA CDL** — raster ETL into HUC summaries. Once the ETL stack exists, USGS post-fire risk, SSURGO, LCMAP, C-CAP, and ICLUS all ride the same rails. **Effort: H.**
17. **USGS LCMAP land-change** — 1985–2021 annual change product. Best long-trend "developed since year X" signal. Requires the §5.5 raster stack. **Effort: H.**
18. **USA Structures + Microsoft Building Footprints** — large-volume vector ingest, partitioned by watershed bbox. Powers DeepTrail "what's here?" lookups + impervious-area refinement. **Effort: M–H.**
19. **USDA NASS Quick Stats (pesticide use)** — survey rotation, needs careful crop-by-state mapping. **Effort: M–H.**
20. **EPA ICLUS scenario projections** — forward-looking housing density rasters; useful only after Steward has a trend story to project forward. **Effort: H.** Hold.
21. **WA Ecology EIM scrape (non-WQX fields)** — only justified if a specific contaminant series is missing from WQP. **Effort: H.** Hold until specific need surfaces.
22. **NOAA HYSPLIT source attribution** — only if Steward needs "where did this airshed Hg come from" causality. **Effort: H.** Hold.

### Watershed-specific quick wins

- **Shenandoah (VA)**: Tier 1 items 1+5+7 + Tier 2 items 9+14. Unblocks Shenandoah's biggest gaps: swim safety, fish-consumption advisories (for smallmouth + striper from `plan-2026-05-15-warmwater-species-coverage.md`), "is the river upstream-of-me polluted?", and **the development story** (NOVA-driven housing pressure on Shenandoah headwaters, Loudoun + Clarke + Frederick County BPS growth rates among the highest in VA).
- **Skagit (WA)**: Tier 1 items 3+4+7+8 (wildfire + smoke + BPS + GMA UGA) + Tier 2 items 11+14 (atmospheric N — Cascade airshed is N-saturated — and MS4 for Burlington/Mount Vernon urban watershed).
- **Green River (UT)**: Tier 2 item 9 (DMR — Uinta Basin O&G) + USGS Abandoned Mine Lands + DOGM AWQMS for coal-country tributaries. Development pressure is low here but **Wasatch Front BPS data is essential for the Jordan/Provo watersheds** if those become active.
- **OR pilots** (Willamette / Deschutes): Tier 1 items 5+7+8 (CyAN + BPS + DLCD UGBs — Portland metro UGB is the iconic land-use boundary, makes Path Now feel locally-grounded for Willamette users) + Tier 1 item 6.

---

## 7. Open Questions / Decisions Needed

1. **Storage shape** — do contaminant time series go into `observations` (current pattern, treats each measurement as an "observation") or a new `measurements` table with explicit units, detection-limit handling, and QA flags? WQX rows have ~30+ metadata fields; current `observations.data_payload` is a JSON catch-all that's already starting to show strain (cf. RiverSignal-713afbac iNat photo_license bug).
2. **Freshness SLAs** — USGS NWIS sensors (15-min), CyAN (weekly), DMR (monthly +90d lag), TRI (annual +12-mo lag), NEI (triennial). Need explicit per-source freshness display on the data-status panel (cf. `app/routers/data_status.py`).
3. **Coverage cut for "watershed"** — pulling DMR/TRI nationally is 100s of MB/yr. Filter to HUCs intersecting active watersheds (`sites.bbox`) at ingest time, or pull everything and filter at MV time? Recommendation: filter at ingest by HUC-8 polygon, since the four pilot states give us a clear scope cut.
4. **Authentication keys** — AirNow, AQS, PurpleAir, NASS Quick Stats all require free keys. Need a managed-secret strategy (currently SNOTEL and a few others use env vars; this would push us to a real secret store).
5. **Tribal data sovereignty** — Yakama, CTUIR, Warm Springs, Ute, EBCI may not want their air/water data redistributed. Default to federal aggregators (WQP, AQS) which already handle the sharing-policy layer, rather than pulling tribal portals directly.
6. **Mercury advisory cross-walk** — fish-consumption advisories are state-specific (OR/WA/UT/VA each have their own). EPA aggregates them but updates are slow. Probably want to build per-state scrapes for the species/waterbody/limit triple. Out of scope for v1; revisit when MDN data is in.
7. **Order of operations vs. existing data-sources-roadmap** — does this plan supersede the "HABs (retry)" and "Wildfire (NIFC current-year)" rows already in the roadmap, or are those phased separately? Recommendation: this plan supersedes them; the roadmap row references this plan once committed.
8. **County → HUC apportionment for Census BPS / ACS / PEP** — BPS reports at county and permit-issuing place; watersheds cross county lines. Areal-weighting by intersection is the standard approach (cf. Chesapeake Bay Program Phase 6 method). Need a documented apportionment function before any housing-pressure tile ships, otherwise Steward will show implausible numbers for watersheds that span urban + rural counties.
9. **Building-footprint update cadence** — USA Structures refreshes irregularly (FEMA-driven); Microsoft Global re-releases roughly annually. Trend storytelling requires committing to one source's version cadence — recommendation: USA Structures as authoritative point inventory, Microsoft Footprints for polygon area calculations, refresh both annually as part of a coordinated "land-use snapshot" pipeline.
10. **Forward-looking vs current-state separation** — ICLUS projections and Chesapeake Phase 6 modeled scenarios are forecasts, not measurements. Steward must visually distinguish "observed historical" from "modeled projection" tiles so users don't conflate the two; this is a UI requirement that should be specified before the data feeds land.
11. **Watershed Health Score composite — needs its own plan** — the score, sub-scores (Water / Habitat / Development), and trend arrow proposed in §5.6 are the load-bearing semantics for every other tile in the layout. Weighting choices (do impervious-surface deltas weigh more than 303(d) listings? how do you compare a watershed with no NPDES facilities to one with 12?), normalization across watersheds of different sizes, headline-generation logic ("improving on X, degrading on Y"), and how the score behaves when key feeds are missing — none of these are derivable from the feed inventory alone. Recommend authoring as `plan-2026-05-XX-watershed-health-score.md` before any tile in §5.6 ships, otherwise each tile re-litigates the meaning of "good" and "bad" independently.

---

## 8. References

### Water
- [EPA Water Quality Data Download](https://www.epa.gov/waterdata/water-quality-data-download)
- [Water Quality Portal](https://www.waterqualitydata.us/) — [User Guide](https://www.waterqualitydata.us/portal_userguide/)
- [USGS Water Data APIs](https://api.waterdata.usgs.gov/) — [OpenAPI](https://nwis.waterservices.usgs.gov/openapi/) — [dataretrieval Python](https://github.com/DOI-USGS/dataretrieval-python)
- [EPA ECHO NPDES DMR downloads](https://echo.epa.gov/tools/data-downloads/icis-npdes-dmr-and-limit-data-set) — [Web Services](https://echo.epa.gov/tools/web-services)
- [EPA TRI Program](https://www.epa.gov/toxics-release-inventory-tri-program) — [Envirofacts REST API](https://www.epa.gov/enviro/envirofacts-data-service-api-v1)
- [EPA HAB Data](https://www.epa.gov/habs/hab-data) — [State & Tribal HAB Programs](https://www.epa.gov/habs/state-tribal-hab-programs-and-resources)
- [CDC OHHABS 2022 Summary](https://www.cdc.gov/ohhabs/data/summary-report-united-states-2022.html)
- [EPA ATTAINS](https://www.epa.gov/waterdata/attains)
- [Oregon DEQ Water Quality Data](https://www.oregon.gov/deq/wq/pages/wqdata.aspx) — [AWQMS R package](https://github.com/TravisPritchardODEQ/AWQMSdata) — [OregonExplorer AWQMS](https://oregonexplorer.info/content/oregon-department-environmental-quality-deq-ambient-water-quality-monitoring-system-awqms)
- [Oregon DEQ Spill Reporting](https://www.oregon.gov/deq/hazards-and-cleanup/er/pages/how-to-report-a-spill.aspx) — [Environmental Cleanup / ECSI → Your DEQ Online](https://www.oregon.gov/deq/Hazards-and-Cleanup/env-cleanup/Pages/ecsi.aspx)
- [Washington Ecology EIM](https://ecology.wa.gov/research-data/data-resources/environmental-information-management-database) — [EIM Search](https://apps.ecology.wa.gov/eim/search/) — [WA 303(d) List](https://ecology.wa.gov/water-shorelines/water-quality/water-improvement/assessment-303d-list) — [WA Ecology GIS Data](https://ecology.wa.gov/research-data/data-resources/geographic-information-systems-gis/data)
- [Utah DEQ Water Quality Databases](https://deq.utah.gov/water-quality/databases-and-information) — [Utah DWQ AWQMS R tools](https://rdrr.io/github/utah-dwq/wqTools/man/readAWQMS.html) — [Utah Integrated Report](https://deq.utah.gov/water-quality/utahs-integrated-report) — [Utah OGM coal mining AWQMS](https://ogm.utah.gov/awqms-access/)
- [Virginia DEQ Water Quality Monitoring](https://www.deq.virginia.gov/our-programs/water/water-quality/monitoring) — [Virginia Environmental Data Hub](https://geohub-vadeq.hub.arcgis.com/) — [VA DEQ Annual Monitoring Plan](https://www.deq.virginia.gov/our-programs/water/water-quality/monitoring/water-quality-monitoring-plan) — [VA DEQ Integrated Report](https://www.deq.virginia.gov/water/water-quality/assessments/integrated-report) — [VDH HAB Dashboard](https://www.vdh.virginia.gov/waterborne-hazards-control/algal-bloom-surveillance-map/)

### Land
- [EPA FRS REST Services](https://www.epa.gov/frs/frs-rest-services) — [FRS API](https://www.epa.gov/frs/frs-api) — [FRS Download Summary](https://echo.epa.gov/tools/data-downloads/frs-download-summary)
- [EPA SEMS Overview](https://www.epa.gov/enviro/sems-overview) — [Superfund Data and Reports](https://www.epa.gov/superfund/superfund-data-and-reports) — [EPA FRS SEMS dataset on Data.gov](https://catalog.data.gov/dataset/epa-facility-registry-service-frs-sems)
- [USDA NASS Agricultural Chemical Use Program](https://www.nass.usda.gov/Surveys/Guide_to_NASS_Surveys/Chemical_Use/) — [NASS Developers / Quick Stats API](https://www.nass.usda.gov/developer/index.php) — [NASS Cropland Data Layer](https://www.nass.usda.gov/Research_and_Science/Cropland/Release/)
- [PHMSA Pipeline Source Data](https://www.phmsa.dot.gov/data-and-statistics/pipeline/source-data) — [PHMSA Incident Statistics](https://www.phmsa.dot.gov/hazmat-program-management-data-and-statistics/data-operations/incident-statistics) — [PHMSA Distribution/Transmission/Liquid Incident Data](https://www.phmsa.dot.gov/data-and-statistics/pipeline/distribution-transmission-gathering-lng-and-liquid-accident-and-incident-data)
- [NIFC WFIGS Current Fire Perimeters](https://data-nifc.opendata.arcgis.com/datasets/nifc::wfigs-current-interagency-fire-perimeters/about) — [NIFC Open Data Hub](https://data-nifc.opendata.arcgis.com/) — [USGS Water Quality After Wildfire](https://www.usgs.gov/mission-areas/water-resources/science/water-quality-after-wildfire) — [USGS post-fire Hg research](https://pubs.usgs.gov/publication/70257008)

### Land-Use Change & Development Pressure
- [U.S. Census Building Permits Survey](https://www.census.gov/permits) — [BPS State Annual](https://www.census.gov/construction/bps/stateannual.html) — [BPS State Monthly](https://www.census.gov/construction/bps/statemonthly.html) — [BPS Methodology](https://www.census.gov/construction/bps/methodology.html) — [BPS Release Schedule](https://www.census.gov/construction/bps/schedule.html)
- [EPA Smart Location Mapping](https://www.epa.gov/smartgrowth/smart-location-mapping) — [SLD v3.0 Technical Doc](https://www.epa.gov/system/files/documents/2023-10/epa_sld_3.0_technicaldocumentationuserguide_may2021_0.pdf) — [SLD ArcGIS MapServer](https://geodata.epa.gov/arcgis/rest/services/OA/SmartLocationDatabase/MapServer)
- [USA Structures on Data.gov](https://catalog.data.gov/dataset/usa-structures-4749e) — [FEMA GIS USA Structures](https://gis-fema.hub.arcgis.com/pages/usa-structures) — [HIFLD](https://hifld-geoplatform.hub.arcgis.com/) — [CISA Infrastructure Datasets](https://www.cisa.gov/resources-tools/resources/mapping-your-infrastructure-datasets-infrastructure-identification)
- [Microsoft Global ML Building Footprints](https://github.com/microsoft/GlobalMLBuildingFootprints) — [Microsoft US Building Footprints](https://github.com/microsoft/USBuildingFootprints) — [Microsoft Open Buildings on Source Cooperative](https://source.coop/hdx/microsoft-open-buildings)
- [USGS LCMAP overview](https://www.usgs.gov/special-topics/lcmap) — [LCMAP Data Access](https://www.usgs.gov/special-topics/lcmap/lcmap-data-access) — [USGS Annual NLCD](https://www.usgs.gov/centers/eros/science/annual-nlcd-data-access)
- [EPA 2022 Construction General Permit (CGP)](https://www.epa.gov/npdes/2022-construction-general-permit-cgp) — [CGP Frequent Questions](https://www.epa.gov/npdes/construction-general-permit-cgp-frequent-questions) — [NPDES Tools](https://www.epa.gov/npdes/npdes-tools) — [Electronic Reporting for EPA NPDES General Permits](https://www.epa.gov/npdes/electronic-reporting-epas-npdes-general-permits) — [ECHO NPDES Program Search](https://echo.epa.gov/help/facility-search/npdes-program-search-criteria-help)

### Air
- [NADP — UW Wisconsin host](https://nadp.slh.wisc.edu/) — [USGS NADP overview](https://www.usgs.gov/mission-areas/water-resources/science/national-atmospheric-deposition-program-nadp)
- [EPA AirNow — About the Data](https://www.airnow.gov/about-the-data/) — [AirNow API docs](https://docs.airnowapi.org/) — [EPA AirData](https://www.epa.gov/outdoor-air-quality-data) — [EPA AirData download files](https://aqs.epa.gov/aqsweb/airdata/download_files.html) — [EPA AQS API](https://aqs.epa.gov/aqsweb/documents/data_api.html)

---

## 9. Traceability

- Builds on: `docs/helix/02-design/data-sources-roadmap.md`
- Adjacent: `docs/helix/02-design/plan-2026-05-15-warmwater-species-coverage.md` (mercury advisories on warmwater species are conditional on §5.3 here)
- Anticipated companion plan: `plan-2026-05-XX-watershed-health-score.md` — see §7 Q11. The §5.6 layout depends on this for the score, sub-scores, and trend semantics; no tile in §5.6 should ship before the composite is defined.
- UI surface: `frontend/src/pages/MapPage.tsx` (route `/riversignal`, `/riversignal/:watershed`) + `frontend/src/components/SitePanel.tsx` (tab additions for `stewardship`).
- Existing implementation precedents to mirror:
  - Adapter pattern: `pipeline/ingest/inaturalist.py`, `pipeline/ingest/streamnet.py`, `pipeline/ingest/washington.py`
  - Materialized view pattern: `pipeline/medallion.py:GOLD_HEAVY` (note: cf. RiverSignal-6a76a3ae for UNIQUE-index work that should land before adding new gold MVs)
  - Data-payload JSON pattern: see `inaturalist.py:_parse_observation` (and RiverSignal-713afbac for known limitations)
- Open beads this plan does not address: RiverSignal-6a76a3ae, RiverSignal-7ea2ac57, RiverSignal-713afbac (all p1/p2 bugs unrelated to ingestion expansion).
