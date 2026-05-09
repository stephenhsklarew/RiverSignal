# Data Sources Roadmap — RiverPath + DeepTrail

Potential public data sources not yet implemented, organized by effort and impact.

## High Value, Easy to Implement (REST/ArcGIS APIs, no key needed)

| Source | Data | Value to App | Effort |
|--------|------|-------------|--------|
| **NWS Forecast API** | 7-day weather by lat/lon | "Will it rain on my fishing trip?" on River Now hero card | Low — single REST call, no key |
| **USGS Real-Time Stream Gauges** | Live flow + temp (15-min intervals) | Replace monthly averages with *right now* readings on River Now | Low — already have USGS adapter, just need real-time endpoint |
| **ODFW Fish Stocking Schedule** | Upcoming stocking dates, species, counts | "Trout stocking in 3 days at Lake Billy Chinook" alerts | Low — CSV scrape, already partially in fishing data |
| **Oregon HABs** (retry) | Active harmful algal bloom advisories | Swim safety warnings on River Now + Explore | Low — ArcGIS, URL needs fixing |
| **DOGAMI Hot/Warm Springs** | 649 geothermal springs in OR | "Hot springs nearby" in Explore + DeepTrail | Low — shapefile download, one-time load |
| **USFS Trails** | 5,949 trail segments with surface, use type, mileage | Trail cards in Explore, trail lines on map | Medium — ArcGIS, line geometry |

## High Value, Medium Effort

| Source | Data | Value to App | Effort |
|--------|------|-------------|--------|
| **eBird Hotspots API** | Birding locations with recent sightings | "Best birding spots" layer in Explore, seasonal bird migration on River Now | Medium — REST API, no key for hotspots |
| **SARP Barrier Inventory** (fix URL) | Fish passage barriers, waterfalls with height | Waterfall cards in Explore, barrier map overlay on species map | Medium — need correct ArcGIS endpoint |
| **OSMB Boating Access** (fix URL) | 1,815 boat ramps with amenities | Fill the boat ramp gap in Explore (currently 23 from USFS) | Medium — need correct ArcGIS endpoint |
| **Oregon State Parks** | 422 park parcels with designations | Park boundary overlay, "You're in X State Park" context | Medium — ArcGIS FeatureServer |
| **PRISM Real-Time Climate** | Daily precip, min/max temp grids | Actual current air temperature + recent rainfall on River Now | Medium — already have PRISM adapter for monthly, need daily |
| **Wildfire Perimeters (NIFC)** | Active + recent fire boundaries | Fire proximity warnings, recovery tracking on Steward | Medium — already ingested historical, need current year refresh |

## High Value, Higher Effort

| Source                               | Data                                           | Value to App                                                               | Effort                                                                  |
| ------------------------------------ | ---------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| **Water Quality Portal — Chemistry** | Nutrient, turbidity, pH, conductivity readings | Water clarity metric (missing from hero card), nutrient trends for Steward | Higher — large dataset, new silver/gold views                           |
| **Westfly.com** hatch charts         | Expert hatch timing by river                   | Enrich curated hatch chart beyond our 50 entries                           | Higher — web scrape + manual curation                                   |
| **USDA SNOTEL** (expand)             | Real-time snowpack + soil moisture             | "Snowmelt runoff starting" context for spring flow predictions             | Higher — already have adapter, need real-time + forecast interpretation |
| **NPS API**                          | National park campgrounds, alerts, activities  | Crater Lake data for Klamath users                                         | Medium — free key required                                              |
| **ODOT TripCheck**                   | Road conditions, closures, cameras             | "Road to Metolius is open/closed" on River Now                             | Medium — free registration                                              |

## DeepTrail-Specific

| Source                         | Data                                      | Value                                                 |
| ------------------------------ | ----------------------------------------- | ----------------------------------------------------- |
| **Mindat.org API**             | Mineral locality data with photos         | Richer mineral site cards with specimen photos        |
| **GBIF** (Global Biodiversity) | Additional fossil + specimen records      | Fill fossil gaps beyond PBDB                          |
| **USGS Volcano Hazards**       | Active/dormant volcano info, hazard zones | "You're near a volcano" context for Cascade locations |
| **Oregon LIDAR** (DOGAMI)      | Terrain models                            | 3D terrain visualization potential                    |

## Top 3 Recommendations for Immediate Impact

1. ~~**NWS Weather Forecast**~~ — **IMPLEMENTED**: Live API source #27. 7-day forecast displayed on River Now hero card.

2. ~~**USGS Real-Time Gauges**~~ — **IMPLEMENTED**: Live API source #28. Instantaneous values with 15-min cache, "LIVE" badge on hero card.

3. ~~**Fix OSMB Boating Access URL**~~ — **IMPLEMENTED**: 160 Oregon boat ramp/launch sites loaded from OSMB (source #25).

### Updated Recommendations (2026-05-08)

1. **Oregon State Parks recreation adapter** — ArcGIS FeatureServer with 422 park parcels; would add state-managed access points alongside existing USFS coverage.
2. **eBird Hotspots API** — No-key REST API for birding locations with recent sightings; would enrich the Explore tab for birding families.
3. **Fishing regulation structured data** — eRegulations.com has consistent HTML but no API; would enable regulatory context in fishing intelligence.

## Washington State Adapters (Implemented 2026-05-08)

Source: `pipeline/ingest/washington.py` (492 lines), 6 data sources for the Skagit River watershed.

| # | Source | Data | Status |
|---|--------|------|--------|
| 1 | **WDFW SalmonScape** | Salmon distribution, habitat, barriers | Implemented |
| 2 | **WDFW Fish Stocking** | WA state fish stocking records | Implemented |
| 3 | **WA DNR Surface Geology** | Washington geologic units | Implemented |
| 4 | **SRFB Salmon Recovery** | Salmon Recovery Funding Board restoration projects | Implemented |
| 5 | **WA State Parks** | Park locations, access points, amenities | Implemented |
| 6 | **WDFW Water Access** | Boat ramps, fishing access sites | Implemented |

## Utah State Adapters (Implemented 2026-05-08)

Source: `pipeline/ingest/utah.py` (408 lines), 5 data sources for the Green River watershed.

| # | Source | Data | Status |
|---|--------|------|--------|
| 1 | **AGRC Boat Ramps** | Utah boat ramp locations | Implemented |
| 2 | **DWQ Assessment Units** | Utah water quality assessment units | Implemented |
| 3 | **AGRC Trailheads** | Utah trailhead locations | Implemented |
| 4 | **BOR Flaming Gorge HydroData** | Bureau of Reclamation hydrological data | Implemented |
| 5 | **UDWR Fish Stocking** | Utah fish stocking records | Implemented |

## Currently Implemented Data Sources (30+ across 3 states)

### Ingested into Database (Bronze)

| # | Source | Records | Type |
|---|--------|---------|------|
| 1 | iNaturalist | 238K observations | Citizen science observations |
| 2 | USGS NWIS | 103K time series | Stream gauges (flow, temp, DO) |
| 3 | Water Quality Portal (WQP) | 66K time series | Water chemistry |
| 4 | SNOTEL | 650K time series | Temperature, precipitation, snow → gold.snowpack_current |
| 5 | BioData (USGS) | 293K observations | Professional bio surveys |
| 6 | WQP Bugs | 14.9K observations | Aquatic macroinvertebrates → gold.aquatic_hatch_chart |
| 7 | StreamNet | merged into obs | Salmon/steelhead abundance |
| 8 | MTBS | 277 fire perimeters | Burn perimeters |
| 9 | NHDPlus HR | 142K segments | Stream flowlines → gold.river_miles |
| 10 | OWRI/NOAA/PCSRF | 2.6K interventions | Restoration interventions |
| 11 | Fish Passage | 476 barriers | Barrier locations |
| 12 | PRISM | 914K time series | Monthly temp/precip |
| 13 | EPA ATTAINS | 778 segments | Impaired waters (303d) |
| 14 | NWI | 13K polygons | Wetland boundaries |
| 15 | USGS WBD | 975 boundaries | HUC watershed boundaries |
| 16 | ODFW | 953 time series | Sport catch + stocking |
| 17 | Macrostrat | 17.3K geologic units | Rock type, age, formation |
| 18 | PBDB | 667 fossils | Paleontology occurrences |
| 19 | iDigBio | 2,041 fossils | Museum specimen records |
| 20 | GBIF | 965 fossils (18 with images) | Fossil specimens with photos |
| 21 | BLM SMA | 40 land parcels | Land ownership + collecting legality |
| 22 | DOGAMI | merged into geologic_units | Oregon geology polygons |
| 23 | MRDS | 1,980 mineral deposits | Mineral deposit locations |
| 24 | USFS Recreation | 406 sites | Campgrounds, trailheads, day use |
| 25 | OSMB Boating Access | 160 sites | Oregon boat ramps + launches |
| 26 | Curated Hatch Chart | 50 entries | Expert fly fishing hatch data |

### Live API Sources (Not Stored in DB)

| # | Source | Data | Cache |
|---|--------|------|-------|
| 27 | NWS Weather API | 7-day forecast by watershed | 30 min |
| 28 | USGS Instantaneous Values | Real-time flow + water temp | 15 min |

### Totals (updated 2026-05-08)
- **Observations**: 550,014+
- **Time Series**: 1,734,579+
- **Silver Views**: 7
- **Gold Views**: 30+
- **Total Materialized Views**: 37+
- **Total Records**: ~2.3M+
- **Watersheds**: 7 (5 OR, 1 WA, 1 UT)
- **States**: 3 (Oregon, Washington, Utah)
- **Ingested Sources**: 30+ (26 core + 6 WA + 5 UT, some shared)
- **Live API Sources**: 2 (NWS Weather, USGS Instantaneous Values)
