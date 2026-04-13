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

| Source | Data | Value to App | Effort |
|--------|------|-------------|--------|
| **Water Quality Portal — Chemistry** | Nutrient, turbidity, pH, conductivity readings | Water clarity metric (missing from hero card), nutrient trends for Steward | Higher — large dataset, new silver/gold views |
| **Westfly.com** hatch charts | Expert hatch timing by river | Enrich curated hatch chart beyond our 50 entries | Higher — web scrape + manual curation |
| **USDA SNOTEL** (expand) | Real-time snowpack + soil moisture | "Snowmelt runoff starting" context for spring flow predictions | Higher — already have adapter, need real-time + forecast interpretation |
| **NPS API** | National park campgrounds, alerts, activities | Crater Lake data for Klamath users | Medium — free key required |
| **ODOT TripCheck** | Road conditions, closures, cameras | "Road to Metolius is open/closed" on River Now | Medium — free registration |

## DeepTrail-Specific

| Source | Data | Value |
|--------|------|-------|
| **Mindat.org API** | Mineral locality data with photos | Richer mineral site cards with specimen photos |
| **GBIF** (Global Biodiversity) | Additional fossil + specimen records | Fill fossil gaps beyond PBDB |
| **USGS Volcano Hazards** | Active/dormant volcano info, hazard zones | "You're near a volcano" context for Cascade locations |
| **Oregon LIDAR** (DOGAMI) | Terrain models | 3D terrain visualization potential |

## Top 3 Recommendations for Immediate Impact

1. **NWS Weather Forecast** — one API call, no key, answers the #1 question families and anglers have: "What's the weather this weekend?" Displays on the River Now hero card.

2. **USGS Real-Time Gauges** — already ingest USGS daily values. Switching to the instantaneous values endpoint (`https://waterservices.usgs.gov/nwis/iv/`) gives *right now* flow and temperature instead of monthly averages. Makes River Now feel live.

3. **Fix OSMB Boating Access URL** — have 23 boat ramps from USFS but Oregon's marine board has 1,815. Finding the correct ArcGIS endpoint would 80x the boat ramp coverage in Explore.

## Currently Implemented Data Sources (20)

| # | Source | Records | Type |
|---|--------|---------|------|
| 1 | iNaturalist | 534K+ | Citizen science observations |
| 2 | USGS NWIS | 98K+ time series | Stream gauges (flow, temp, DO) |
| 3 | Water Quality Portal (WQP) | 2.5K+ | Water chemistry |
| 4 | SNOTEL | Climate/snowpack | Temperature, precipitation, snow |
| 5 | BioData (USGS) | 292K | Professional bio surveys |
| 6 | WQP Bugs | 14.8K | Aquatic macroinvertebrates |
| 7 | StreamNet | Fish monitoring | Salmon/steelhead abundance |
| 8 | MTBS | Fire severity | Burn perimeters |
| 9 | NHDPlus HR | 15K+ segments | Stream flowlines |
| 10 | OWRI/NOAA/PCSRF | 1.4K | Restoration interventions |
| 11 | Fish Passage | 476 | Barrier locations |
| 12 | PRISM | Climate grids | Monthly temp/precip |
| 13 | EPA ATTAINS | Impaired waters | 303(d) listings |
| 14 | NWI | Wetlands | Wetland polygons |
| 15 | USGS WBD | Watershed boundaries | HUC boundaries |
| 16 | ODFW | Sport catch + stocking | Harvest/stocking data |
| 17 | Macrostrat | 17K+ geologic units | Rock type, age, formation |
| 18 | PBDB | 1.9K fossils | Paleontology occurrences |
| 19 | BLM SMA | Land ownership | Collecting legality |
| 20 | USFS Recreation | 406 sites | Campgrounds, trailheads |
