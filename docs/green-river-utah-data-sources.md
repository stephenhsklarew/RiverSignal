# Green River Watershed Data Sources Report

**Prepared:** 2026-04-15
**Watershed:** Green River, Upper Colorado Basin (HUC 1404, 1406)
**Scope:** Data source inventory for RiverSignal platform expansion from Pacific Northwest to Utah

---

## 1. Executive Summary

The Green River watershed has strong coverage from our existing national adapters (USGS, WQP, SNOTEL, NHDPlus, PRISM, MTBS, Macrostrat, PBDB, iDigBio, GBIF, MRDS, NWI, WBD, iNaturalist, BLM SMA). Six Oregon/Washington-specific adapters will not work and need Utah equivalents. Utah's data ecosystem is mature, anchored by the AGRC/SGID geospatial clearinghouse, which provides ArcGIS FeatureServer endpoints compatible with our existing `_arcgis_bbox_query()` pattern.

**Key findings:**
- 14 of 16 national adapters work with bbox changes only -- no code modifications needed
- 6 Oregon-specific adapters need Utah replacements; 5 have direct equivalents available
- The Green River Formation is exceptionally well-represented in fossil databases (7,740 iDigBio records, 1,277 PBDB occurrences, ~30,900 GBIF fossil specimens in the broader area)
- Bureau of Reclamation HydroData provides a JSON API for Flaming Gorge Dam operations -- a new adapter class with no Oregon equivalent
- Utah DWR fish stocking data is accessible via a structured HTML/AJAX endpoint with 24 years of history (2002-2026)
- 18 boat ramps on the Green River/Flaming Gorge are available from Utah AGRC
- Flaming Gorge is stocked with ~500,000+ fish/year (kokanee, rainbow, cutthroat, brown, lake trout)

**Estimated new records for Green River:** ~85,000-120,000 observations + time series from national sources, plus ~15,000-25,000 from Utah-specific sources.

---

## 2. National Sources (Already in Pipeline -- New Bbox Only)

These adapters work nationally. Configuring the Green River bbox is the only change needed.

**Green River watershed bbox (approximate):**
```python
"green_river": {
    "name": "Green River",
    "description": (
        "Green River from headwaters in Wind River Range through "
        "Flaming Gorge, Dinosaur NM, Desolation Canyon, to confluence "
        "with Colorado River in Canyonlands"
    ),
    "bbox": {
        "north": 43.50,   # Wind River Range headwaters
        "south": 38.10,   # Confluence with Colorado River
        "east": -109.00,  # Dinosaur NM eastern extent
        "west": -111.50,  # Wasatch Plateau western tributaries
    },
}
```

> **Note:** The Green River watershed spans ~730 river miles and crosses Wyoming, Colorado, and Utah. The bbox is large. Consider splitting into sub-watersheds (Upper Green / Flaming Gorge / Dinosaur / Desolation / Lower Green) for manageable ingestion batches.

### 2.1 USGS Stream Gauges

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/usgs.py` |
| Coverage | **42+ active stream gauges** across HUC 1404 subbasins (verified via NWIS API) |
| Key stations | 09217000 (Green R near Green River, WY), 09234500 (Green R near Greendale, UT below Flaming Gorge), 09261000 (Green R near Jensen, UT), 09272400 (Green R at Ouray, UT) |
| Parameters | Discharge, water temperature, dissolved oxygen, specific conductance |
| Changes needed | Bbox only |
| Estimated records | ~25,000-40,000 time series values |

### 2.2 Water Quality Portal (WQP)

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/wqp_bugs.py` (macroinvertebrates) + WQP chemistry |
| Coverage | **228 stations** in HUC 14040106 alone; **383 stations** across Lower Green HUC 1406 subbasins (verified) |
| Providers | USGS CO/UT/WY Water Science Centers, NPS, EPA |
| Parameters | Nutrients, turbidity, pH, conductivity, metals, macroinvertebrates |
| Changes needed | Bbox only |
| Estimated records | ~30,000-50,000 water quality results |

### 2.3 SNOTEL

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/snotel.py` |
| Coverage | Multiple stations in Upper Green River headwaters (Wind River Range, Uinta Mountains) |
| Parameters | Snow water equivalent, temperature, precipitation |
| Changes needed | Bbox only. Note: Colorado Basin River Forecast Center (CBRFC) handles forecasting for this area, not NW RFC |
| Estimated records | ~50,000+ time series values |

### 2.4 PRISM Climate

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/prism.py` |
| Coverage | Full CONUS grid coverage |
| Changes needed | Bbox only |
| Estimated records | ~50,000+ monthly temp/precip normals |

### 2.5 NHDPlus (Stream Network)

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/nhdplus.py` |
| Coverage | Full national coverage. Green River is a major NHD feature |
| Changes needed | Bbox only |
| Estimated records | ~15,000-25,000 flowline segments |

### 2.6 MTBS (Fire Perimeters)

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/mtbs.py` |
| Coverage | National. Several significant fires in the Green River watershed |
| Changes needed | Bbox only |
| Estimated records | ~50-100 fire perimeters |

### 2.7 iNaturalist

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/inaturalist.py` |
| Coverage | Strong citizen science coverage, especially around Flaming Gorge, Dinosaur NM, Moab area |
| Changes needed | Bbox only |
| Estimated records | ~20,000-40,000 observations |

### 2.8 Macrostrat (Geologic Units)

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/geology.py` |
| Coverage | National. Green River Formation, Uinta Formation, Morrison Formation, Mancos Shale, etc. |
| Changes needed | Bbox only |
| Estimated records | ~5,000-10,000 geologic units |

### 2.9 PBDB (Paleobiology Database)

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/gbif.py` (shared fossil adapter pattern) |
| Coverage | **1,277 fossil occurrences** in the Green River Formation alone (verified via PBDB API) |
| Key taxa | Knightia (fossil fish), Diplomystus, Lambdotherium, Anemorhysis, Pantolestidae |
| API | `paleobiodb.org/data1.2/occs/list.csv?formation=Green+River&show=coords,loc,strat` |
| Changes needed | Bbox only |
| Estimated records | ~1,500-2,000 occurrences |

### 2.10 iDigBio (Museum Specimens)

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/fossil_images.py` |
| Coverage | **7,740 total Green River Formation specimens**; **837 within the Utah/Wyoming watershed area** (verified) |
| Key institutions | Carnegie Museum of Natural History (~2,221 records), plus multiple other collections |
| Image availability | Most records lack images (`hasImage: false` in sample) -- similar to Oregon experience |
| API | `search.idigbio.org/v2/search/records?rq={"formation":"Green River"}` |
| Changes needed | Bbox only |
| Estimated records | ~800-1,000 specimens |

### 2.11 GBIF (Fossil Specimens)

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/gbif.py` |
| Coverage | **~30,906 fossil specimens** in the broader watershed bbox (verified). Includes Morrison Formation dinosaurs, Triassic, and Eocene material |
| Changes needed | Bbox only + filter for `basisOfRecord=FOSSIL_SPECIMEN` |
| Estimated records | ~5,000-10,000 with bbox filter |

### 2.12 MRDS (Mineral Deposits)

| Field | Value |
|-------|-------|
| Coverage | National. Green River area has significant mineral deposits (oil shale, trona, gilsonite, uranium) |
| Changes needed | Bbox only |
| Estimated records | ~500-1,000 deposit records |

### 2.13 NWI (Wetlands)

| Field | Value |
|-------|-------|
| Coverage | National. Riparian and wetland areas along the Green River corridor |
| Changes needed | Bbox only |
| Estimated records | ~2,000-5,000 polygons |

### 2.14 WBD (Watershed Boundaries)

| Field | Value |
|-------|-------|
| Coverage | National. HUC 1404 (Upper Green) and HUC 1406 (Lower Green) |
| Changes needed | Bbox only |
| Estimated records | ~200-400 HUC boundaries |

### 2.15 BLM SMA (Land Ownership)

| Field | Value |
|-------|-------|
| Coverage | Extensive BLM land in the Green River corridor. NPS (Dinosaur NM, Canyonlands) also significant |
| Changes needed | Bbox only |
| Estimated records | ~100-300 land parcels |

### 2.16 BioData (Macroinvertebrates)

| Field | Value |
|-------|-------|
| Adapter | `pipeline/ingest/biodata.py` |
| Coverage | USGS professional bioassessment data. Likely moderate coverage on Green River |
| Changes needed | Bbox only |
| Estimated records | ~5,000-15,000 observations |

---

## 3. Utah-Specific Sources (New Adapters Needed)

### 3.1 Utah DWR Fish Stocking (replaces ODFW Stocking)

| Field | Value |
|-------|-------|
| Name | Utah Division of Wildlife Resources Fish Stocking Database |
| URL | `https://dwrapps.utah.gov/fishstocking/Fish` |
| Data endpoint | `https://dwrapps.utah.gov/fishstocking/FishAjax?y={year}&sort=waterName&sortorder=ASC&sortspecific={water_name}&whichSpecific=water` |
| Data format | HTML table via AJAX (not a REST API -- needs HTML parsing) |
| Coverage | All Utah waters, 2002-2026. **Green River**: cutthroat, rainbow trout (8+ events/yr). **Flaming Gorge**: kokanee, rainbow, cutthroat, brown, lake trout (20+ events/yr, ~500K+ fish/yr) |
| License | Public data, no terms specified |
| Maps to | New adapter: `utah_fishing.py` (replaces `fishing.py` ODFW pattern) |
| Adapter pattern | Similar to ODFW stocking scraper -- parse HTML table rows. Filter by `sortspecific` parameter for Green River and Flaming Gorge waters |
| Priority | **HIGH** -- direct equivalent of ODFW stocking, rich data, 24-year archive |
| Estimated records | ~5,000-8,000 stocking events across all years |

**Query pattern (verified working):**
```
GET /fishstocking/FishAjax?y=2025&sort=waterName&sortorder=ASC&sortspecific=GREEN%20RIVER&whichSpecific=water
GET /fishstocking/FishAjax?y=2025&sort=waterName&sortorder=ASC&sortspecific=FLAMING%20GORGE&whichSpecific=water
```

**Fields returned:** Water Name, County, Species, Number, Average Length (inches), Date

### 3.2 Utah AGRC/SGID GIS Layers (replaces DOGAMI + Oregon State Parks + OSMB)

The Utah Automated Geographic Reference Center (AGRC) operates the SGID (State Geographic Information Database), which is a comprehensive GIS data clearinghouse served via ArcGIS FeatureServer endpoints. These are directly compatible with our existing `_arcgis_bbox_query()` helper.

#### 3.2.1 Utah Boat Ramps (replaces OSMB)

| Field | Value |
|-------|-------|
| Name | Utah SGID Boat Ramps |
| URL | `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/BoatRamps/FeatureServer/0/query` |
| Data format | ArcGIS FeatureServer (JSON) -- same pattern as OSMB adapter |
| Coverage | **18 boat ramps** on Green River and Flaming Gorge (verified). Statewide coverage ~200+ |
| Fields | `Name`, `Water_body`, `OWNER`, `AGENCY`, `ADMIN`, `DESIG`, `Vessels`, `STATE_LGD` |
| Key sites | Crystal Geyser, Green River State Park, Swaseys, Nefertiti, Sand Wash, Split Mountain Gorge, Rainbow Park (Green R); Cedar Springs Marina, Dutch John Marina, Sheep Creek Bay, Antelope Flat, Lucerne Valley (Flaming Gorge) |
| Maps to | Extend `recreation.py` RecreationAdapter -- add `_ingest_utah_boat_ramps()` method |
| Priority | **HIGH** -- direct OSMB replacement, same adapter pattern |
| Estimated records | ~18-25 in Green River watershed |

#### 3.2.2 Utah Trailheads & Trails

| Field | Value |
|-------|-------|
| Name | Utah SGID Trailheads / Trails and Pathways |
| Trailheads URL | `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahTrailheads/FeatureServer/0/query` |
| Trails URL | `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/TrailsAndPathways/FeatureServer/0/query` |
| Data format | ArcGIS FeatureServer (JSON) |
| Coverage | Statewide. Green River area has trail data (verified: Hamburger Rock, Roundhouse, etc.). Transfer limit exceeded = more data available |
| Trailhead fields | `PrimaryName`, `TrailheadID`, `Features`, `PrimaryMaintenance`, `SeasonalRestriction`, `InfoURL` |
| Trail fields | `PrimaryName`, `DesignatedUses`, `SurfaceType` |
| Maps to | Extend `recreation.py` -- add `_ingest_utah_trailheads()` and `_ingest_utah_trails()` |
| Priority | **MEDIUM** -- USFS recreation adapter already captures some trailheads |
| Estimated records | ~50-150 trailheads, ~200-500 trail segments |

#### 3.2.3 Utah Quaternary Faults (replaces DOGAMI geology)

| Field | Value |
|-------|-------|
| Name | Utah SGID Quaternary Faults |
| URL | `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/QuaternaryFaults/FeatureServer/0/query` |
| Data format | ArcGIS FeatureServer (JSON) |
| Coverage | Statewide. Green River area has faults (verified: Little Dolores River Fault, Ryan Creek Fault Zone) |
| Fields | `FaultNum`, `FaultZone`, `FaultName`, `SectionName`, `DipDirection`, `SlipSense`, `SlipRate`, `FaultClass`, `FaultAge`, `USGS_Link` |
| Maps to | Extend `geology.py` or create new `utah_geology.py` |
| Priority | **MEDIUM** -- Macrostrat covers geologic units; faults add structural geology detail |
| Estimated records | ~20-50 fault segments |

#### 3.2.4 Utah Geologic Contacts

| Field | Value |
|-------|-------|
| Name | Utah SGID Geologic Contacts |
| URL | `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/GeologicContacts/FeatureServer/0/query` |
| Data format | ArcGIS FeatureServer (JSON) |
| Coverage | Statewide. Green River area has contacts (verified: transfer limit exceeded) |
| Fields | `L_TYPE`, `MODIFIER`, `ACCURACY`, `FAULT_CON`, `SOURCE`, `LINE_DESCR` |
| Maps to | Extend `geology.py` |
| Priority | **LOW** -- Macrostrat provides geologic unit polygons; contacts are supplementary |
| Estimated records | ~500-2,000 contact lines |

### 3.3 Utah DEQ Water Quality Assessment (replaces Oregon DEQ 303(d))

| Field | Value |
|-------|-------|
| Name | Utah DWQ Assessment Units (303(d) / Integrated Report) |
| URL | `https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/DWQAssessmentUnits/FeatureServer/0/query` |
| Data format | ArcGIS FeatureServer (JSON) -- same pattern as EPA ATTAINS |
| Coverage | Statewide. Green River assessment units include "Green River-1 Tribs" and "Green River-2" (verified) |
| Fields | `AU_ID`, `AU_NAME`, `AU_DESCRIP`, `BEN_CLASS`, `Protected` (beneficial uses: Drinking Water, Cold Water Aquatic Life, etc.), `CAT_2006`, `STATUS2006`, `CAUSE_2006` |
| License | Public data |
| Maps to | New adapter or extend existing EPA ATTAINS ingestion. Same schema concept |
| Priority | **HIGH** -- direct Oregon DEQ 303(d) equivalent. State-specific impairment data |
| Estimated records | ~20-50 assessment unit polygons in Green River |
| Notes | Data appears to be from 2006 cycle. Check for newer integrated report GIS layers at `deq.utah.gov/water-quality/integrated-report` |

**Additional Utah DWQ layers available:**

| Layer | URL Base |
|-------|----------|
| DWQ Monitored Lakes | `services1.arcgis.com/.../DWQMonitoredLakes132/FeatureServer/0/query` |
| DWQ Stormwater Dischargers | `services1.arcgis.com/.../DWQStormWaterDischargers/FeatureServer/0/query` |
| DWQ UPDES Dischargers | `services1.arcgis.com/.../DWQUPDESDischargers/FeatureServer/0/query` |

### 3.4 Bureau of Reclamation Flaming Gorge Operations (NEW -- no Oregon equivalent)

| Field | Value |
|-------|-------|
| Name | Bureau of Reclamation HydroData -- Flaming Gorge Reservoir |
| Base URL | `https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/` |
| JSON API | `https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/{param_id}.json` |
| CSV API | `https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/csv/{param_id}.csv` |
| Data format | JSON and CSV -- simple two-column format (`datetime`, `value`) |
| License | Public domain (federal) |
| Station ID | 937 (Flaming Gorge Reservoir) |

**Available parameters (verified):**

| Param ID | Parameter | Unit |
|----------|-----------|------|
| 17 | Storage | acre-feet |
| 25 | Evaporation | acre-feet |
| 29 | Inflow | cfs |
| 30 | Inflow Volume | acre-feet |
| 42 | Total Release | cfs |
| 43 | Release Volume | acre-feet |
| 47 | Delta Storage | acre-feet |
| 49 | Pool Elevation | feet |
| 89 | Area | acres |

**Adapter design:**
- New adapter: `bor_hydrodata.py`
- Simple JSON parsing: `{"columns": ["datetime", "storage"], "data": [["1988-01-01", 12345.6], ...]}`
- Daily time series, historical data back to 1988
- Maps to `time_series` table with `source_type = 'bor_reservoir'`
- Can be generalized for any BOR reservoir (Fontenelle, Blue Mesa, etc.)

**Priority: HIGH** -- Critical for understanding Green River hydrology. Flaming Gorge Dam operations control flow, temperature, and endangered species habitat downstream. No equivalent exists in Oregon pipeline.

**Estimated records:** ~15,000 daily values per parameter x 9 parameters = ~135,000 time series records

### 3.5 NPS Data API (Dinosaur NM + Canyonlands)

| Field | Value |
|-------|-------|
| Name | National Park Service Data API |
| Base URL | `https://developer.nps.gov/api/v1/` |
| Data format | REST JSON API |
| Key required | Yes -- free registration at `developer.nps.gov` (DEMO_KEY works for testing) |
| Parks | `dino` (Dinosaur National Monument), `cany` (Canyonlands National Park) |
| License | Public domain (federal) |

**Available endpoints (verified):**

| Endpoint | DINO | CANY | Data |
|----------|------|------|------|
| `/parks` | 1 park with 35 activities, 29 topics, 10 images | Similar | Park info, fees, hours, weather |
| `/campgrounds` | **6 campgrounds** | **3 campgrounds** | Sites, amenities, fees, reservability, accessibility |
| `/alerts` | Active alerts | Active alerts | Closures, hazards, park info |
| `/events` | Upcoming events | Upcoming events | Dates, times, descriptions |
| `/visitorcenters` | 2 | 1 | Hours, contacts, location |

**Adapter design:**
- Extend `recreation.py` with `_ingest_nps()` method
- Map campgrounds to `recreation_sites` table with `source_type = 'nps'`
- Also map visitor centers and alert data

**Priority: MEDIUM** -- 9 campgrounds total. BLM and USFS recreation adapters already capture many federal sites. NPS API adds park-specific detail (fees, reservability, accessibility).

**Estimated records:** ~15-25 recreation sites

### 3.6 Utah Geological Survey Interactive Map (replaces DOGAMI)

| Field | Value |
|-------|-------|
| Name | UGS Geologic Map Portal |
| URL | `https://geomap.geology.utah.gov/` |
| Data format | GeoJSON export (with polygon simplification options: High/Medium/Low) |
| Coverage | ~800 geologic maps at 3 scales (1:500K, 1:50K-1:125K, 1:24K). ~25% of all UGS maps |
| Features | Geologic unit polygons with descriptions, searchable by formation name |
| License | Public data |
| Maps to | Supplement `geology.py` Macrostrat data with higher-resolution Utah-specific mapping |
| Priority | **LOW** -- Macrostrat already provides geologic units; UGS adds detail but requires GeoJSON parsing instead of ArcGIS query |
| Estimated records | ~500-2,000 polygon units in Green River area |

**Additional UGS data:**
- Energy & Mineral Statistics databases (oil shale, trona, gilsonite)
- GeoData Archive System (scanned documents, photos)
- LiDAR elevation data
- Analytical data (geochemistry, geochronology)

### 3.7 Colorado River Recovery Program (NEW -- no Oregon equivalent)

| Field | Value |
|-------|-------|
| Name | Upper Colorado River Endangered Fish Recovery Program |
| URL | `https://coloradoriverrecovery.org` |
| Species | Colorado pikeminnow (*Ptychocheilus lucius*), razorback sucker (*Xyrauchen texanus*), bonytail chub (*Gila elegans*), humpback chub (*Gila cypha*) |
| Data format | Primarily PDF reports, annual monitoring summaries |
| Coverage | Green River (main stem + tributaries), Upper Colorado basin |
| Available data | Stocking records, population estimates, nonnative fish removal data, habitat monitoring |
| Programmatic access | **None confirmed** -- reports are PDFs, no API identified |
| License | Public (USFWS/BOR funded) |
| Priority | **MEDIUM** -- High value for species conservation context, but likely manual data extraction from reports |
| Notes | USFWS ECOS may have critical habitat GIS layers (endpoint verification failed due to certificate issues). Try: `services.arcgis.com/QVENGdaPbd4LUkLV/arcgis/rest/services/FWSCritHab_v2/FeatureServer` |

### 3.8 NPS Inventory & Monitoring -- Northern Colorado Plateau Network

| Field | Value |
|-------|-------|
| Name | NCPN Water Quality Monitoring |
| URL | `https://nps.gov/im/ncpn/water-quality.htm` |
| Data portal | `https://irma.nps.gov/DataStore/` |
| Coverage | 11 parks including Dinosaur NM and Canyonlands NP |
| Parameters | ~30 parameters per site visit: conductivity, flow, temperature, pH, dissolved oxygen |
| Data format | Reports + DataStore downloads (format varies) |
| Priority | **LOW** -- WQP already captures much of this data via USGS/EPA providers |
| Notes | Protocol led by Carolyn Livensperger and Rebecca Weissinger. Data compared against Utah state water quality standards |

---

## 4. Gap Analysis: Green River vs. Oregon Coverage

### 4.1 Direct Equivalents Found

| Oregon Source | Utah Equivalent | Status | Effort |
|---------------|----------------|--------|--------|
| ODFW Fish Stocking | UDWR Fish Stocking (`dwrapps.utah.gov`) | Ready to build | Medium -- HTML scrape similar to ODFW |
| ODFW Sport Catch CSVs | No direct equivalent found | **GAP** | N/A |
| ODFW Fish Habitat Distribution | No direct equivalent found | **GAP** -- UDWR may have internal data not publicly served |
| DOGAMI Geology | UGS Geologic Map Portal + AGRC Quaternary Faults + Geologic Contacts | Available | Medium |
| Oregon DEQ 303(d) | Utah DWQ Assessment Units (ArcGIS) | Ready to build | Low -- same `_arcgis_bbox_query()` pattern |
| OSMB Boat Ramps | Utah AGRC Boat Ramps (ArcGIS) | Ready to build | Low -- same adapter pattern |
| Oregon State Parks | Utah State Parks Facilities (AGRC -- endpoint needs verification) | Partially available | Low-Medium |
| StreamNet (salmon/steelhead) | Recovery Program (endangered species) | Different scope | High -- PDF reports, no API |
| WDFW (Washington) | N/A | Not applicable | N/A |

### 4.2 New Sources with No Oregon Equivalent

| Source | Value | Effort |
|--------|-------|--------|
| BOR Flaming Gorge HydroData | **Critical** -- dam operations control everything downstream | Medium -- clean JSON API |
| Colorado River Recovery Program | High -- endangered species context | High -- manual/PDF |
| NPS Data API (DINO, CANY) | Medium -- campgrounds and park info | Low -- clean REST API |
| Flaming Gorge fishing data (lake trout, kokanee) | High -- Flaming Gorge is a destination fishery | Medium -- via UDWR stocking data |
| River rafting permits (Desolation Canyon, Dinosaur NM) | Medium -- recreation context | High -- recreation.gov scraping |

### 4.3 Coverage Gaps Remaining

1. **Sport catch/harvest data** -- Oregon has ODFW sport catch CSVs with monthly harvest by species. No equivalent found for Utah. UDWR has stocking data but not harvest/creel survey results accessible online.

2. **Fish habitat distribution maps** -- Oregon's ODFW Fish Habitat Distribution ArcGIS service (150 species layers) has no Utah equivalent found. UDWR may have internal GIS data but it is not publicly served via ArcGIS.

3. **Endangered fish monitoring data** -- Recovery Program data exists but is primarily in PDF reports, not machine-readable format. No API or download endpoint identified.

4. **River permit/usage data** -- Desolation Canyon (BLM), Dinosaur NM (NPS), and Labyrinth/Stillwater (Canyonlands NPS) all require permits. Usage data may exist at recreation.gov but no public API confirmed for permit statistics.

5. **Water temperature profiles below Flaming Gorge Dam** -- Critical for endangered species. BOR and USGS have this data but it requires specific station queries rather than a single download.

6. **Oil shale / trona / mineral extraction data** -- Unique to Green River Basin. MRDS covers mineral deposits generally but not production data or active mining permits.

7. **HABs (Harmful Algal Blooms)** -- Oregon has a HABs advisory layer. No Utah equivalent identified (Flaming Gorge occasionally has algal blooms).

---

## 5. Recommendations (Priority Order)

### Tier 1: Immediate (bbox changes only, no new code)

| # | Action | Estimated records | Effort |
|---|--------|-------------------|--------|
| 1 | Add `green_river` to `pipeline/config/watersheds.py` | -- | 10 min |
| 2 | Run all national adapters with new bbox | ~85,000-120,000 | 1-2 hours runtime |
| 3 | Verify PBDB Green River Formation yields (`formation=Green+River`) | ~1,277 | Verify |
| 4 | Verify iDigBio Green River Formation yields | ~837 | Verify |
| 5 | Verify GBIF fossil specimens with bbox filter | ~5,000-10,000 | Verify |

### Tier 2: Quick Wins (ArcGIS adapters, same pattern as Oregon)

| # | Action | Estimated records | Effort |
|---|--------|-------------------|--------|
| 6 | Add Utah boat ramps to `recreation.py` | ~18 | 2 hours |
| 7 | Add Utah DWQ Assessment Units to existing ATTAINS/303(d) adapter | ~30-50 | 3 hours |
| 8 | Add Utah trailheads to `recreation.py` | ~50-150 | 2 hours |
| 9 | Add Utah Quaternary Faults to `geology.py` | ~20-50 | 3 hours |

### Tier 3: New Adapters (medium effort)

| # | Action | Estimated records | Effort |
|---|--------|-------------------|--------|
| 10 | Build UDWR fish stocking adapter (`utah_fishing.py`) | ~5,000-8,000 | 1 day |
| 11 | Build BOR HydroData adapter (`bor_hydrodata.py`) | ~135,000 | 1 day |
| 12 | Build NPS Data API adapter (campgrounds/alerts) | ~15-25 | 0.5 day |

### Tier 4: High Effort / Research Needed

| # | Action | Estimated records | Effort |
|---|--------|-------------------|--------|
| 13 | Colorado River Recovery Program data extraction | ~500-1,000 | 2-3 days (manual/PDF) |
| 14 | River permit data (recreation.gov scraping) | ~100-500 | 2 days |
| 15 | UDWR species surveys / fish habitat distribution (if data becomes available) | Unknown | Unknown |
| 16 | USFWS Critical Habitat GIS layers (needs endpoint debugging) | ~10-20 polygons | 0.5 day |

### Total Implementation Estimate

| Tier | Calendar time | New records |
|------|--------------|-------------|
| Tier 1 (bbox only) | 1 day | ~85,000-120,000 |
| Tier 2 (ArcGIS quick wins) | 2-3 days | ~120-270 |
| Tier 3 (new adapters) | 3-4 days | ~140,000-143,000 |
| Tier 4 (research/manual) | 1-2 weeks | ~600-1,500 |
| **Total** | **~2 weeks** | **~225,000-265,000** |

---

## 6. Estimated Record Counts

### National Sources (bbox change only)

| Source | Low | High | Notes |
|--------|-----|------|-------|
| USGS Stream Gauges | 25,000 | 40,000 | 42+ active gauges x years of daily data |
| WQP Chemistry | 30,000 | 50,000 | 611+ stations across Upper + Lower Green |
| SNOTEL | 50,000 | 80,000 | Multiple stations, multi-year time series |
| PRISM | 50,000 | 80,000 | Grid cells x monthly normals |
| NHDPlus | 15,000 | 25,000 | Flowline segments |
| iNaturalist | 20,000 | 40,000 | Strong coverage near parks/recreation areas |
| MTBS | 50 | 100 | Fire perimeters |
| Macrostrat | 5,000 | 10,000 | Geologic units |
| PBDB | 1,277 | 2,000 | Green River Formation + other formations |
| iDigBio | 800 | 1,000 | Museum specimens |
| GBIF Fossils | 5,000 | 10,000 | Fossil specimens in bbox |
| MRDS | 500 | 1,000 | Mineral deposits |
| NWI | 2,000 | 5,000 | Wetland polygons |
| WBD | 200 | 400 | Watershed boundaries |
| BLM SMA | 100 | 300 | Land parcels |
| BioData | 5,000 | 15,000 | Macroinvertebrate surveys |
| **Subtotal** | **~210,000** | **~360,000** | |

### Utah-Specific Sources (new adapters)

| Source | Low | High | Notes |
|--------|-----|------|-------|
| UDWR Fish Stocking | 5,000 | 8,000 | 24 years, Green River + Flaming Gorge |
| Utah Boat Ramps | 18 | 25 | Green River + Flaming Gorge |
| Utah DWQ Assessment | 20 | 50 | Impaired waters polygons |
| Utah Trailheads | 50 | 150 | Point features |
| Utah Trails | 200 | 500 | Line features |
| Utah Quaternary Faults | 20 | 50 | Fault line segments |
| Utah Geologic Contacts | 500 | 2,000 | Contact lines |
| BOR HydroData (Flaming Gorge) | 100,000 | 135,000 | 9 parameters x ~15K daily values |
| NPS Campgrounds (DINO + CANY) | 9 | 15 | Plus visitor centers, alerts |
| Recovery Program | 500 | 1,000 | If extractable from PDFs |
| **Subtotal** | **~106,000** | **~147,000** | |

### Grand Total Estimate

| Category | Low | High |
|----------|-----|------|
| National sources | 210,000 | 360,000 |
| Utah-specific | 106,000 | 147,000 |
| **Grand total** | **~316,000** | **~507,000** |

---

## Appendix A: Verified API Endpoints

```
# USGS Stream Gauges (active sites in Upper Green)
https://waterservices.usgs.gov/nwis/site/?format=rdb&huc=14040106&siteType=ST&siteStatus=active

# WQP Stations (Lower Green)
https://www.waterqualitydata.us/data/Station/search?huc=14060001;14060002;...&mimeType=csv

# PBDB Green River Formation
https://paleobiodb.org/data1.2/occs/list.csv?formation=Green+River&show=coords,loc,strat

# iDigBio Green River Formation (all)
https://search.idigbio.org/v2/search/records?rq={"formation":"Green River"}&limit=0

# iDigBio Green River Formation (in watershed bbox)
https://search.idigbio.org/v2/search/records?rq={"geopoint":{"type":"geo_bounding_box","top_left":{"lat":43.5,"lon":-111.5},"bottom_right":{"lat":38.0,"lon":-109.0}},"formation":"Green River"}&limit=0

# Utah AGRC Boat Ramps (Green River + Flaming Gorge)
https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/BoatRamps/FeatureServer/0/query?where=Water_body LIKE '%Green River%' OR Water_body LIKE '%Flaming Gorge%'&outFields=*&f=json

# Utah AGRC Trailheads
https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/UtahTrailheads/FeatureServer/0/query

# Utah AGRC Trails
https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/TrailsAndPathways/FeatureServer/0/query

# Utah AGRC Quaternary Faults
https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/QuaternaryFaults/FeatureServer/0/query

# Utah AGRC Geologic Contacts
https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/GeologicContacts/FeatureServer/0/query

# Utah DWQ Assessment Units (303d)
https://services1.arcgis.com/99lidPhWCzftIe9K/arcgis/rest/services/DWQAssessmentUnits/FeatureServer/0/query

# Utah DWR Fish Stocking
https://dwrapps.utah.gov/fishstocking/FishAjax?y={year}&sort=waterName&sortorder=ASC&sortspecific={water}&whichSpecific=water

# BOR Flaming Gorge Reservoir (station 937)
https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/17.json  (storage)
https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/29.json  (inflow)
https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/42.json  (total release)
https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/49.json  (pool elevation)
https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/25.json  (evaporation)
https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/43.json  (release volume)
https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/47.json  (delta storage)
https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/30.json  (inflow volume)
https://www.usbr.gov/uc/water/hydrodata/reservoir_data/937/json/89.json  (area)

# NPS API (free key required)
https://developer.nps.gov/api/v1/parks?parkCode=dino&api_key={key}
https://developer.nps.gov/api/v1/campgrounds?parkCode=dino&api_key={key}
https://developer.nps.gov/api/v1/campgrounds?parkCode=cany&api_key={key}
https://developer.nps.gov/api/v1/alerts?parkCode=dino,cany&api_key={key}

# UGS Geologic Map Portal
https://geomap.geology.utah.gov/
```

## Appendix B: Key Water Bodies for Fish Stocking Queries

Query these `sortspecific` values against the UDWR fish stocking endpoint:

| Water Body | County | Key Species |
|------------|--------|-------------|
| GREEN RIVER | Daggett | Cutthroat, Rainbow |
| GREEN RIVER | Emery | Rainbow |
| FLAMING GORGE RES | Daggett | Kokanee, Rainbow, Cutthroat, Brown, Lake Trout |
| RED FLEET RES | Uintah | Rainbow, Brown, Bluegill |
| STEINAKER RES | Uintah | Rainbow, Largemouth Bass |
| STARVATION RES | Duchesne | Rainbow, Walleye |
| STRAWBERRY RES | Wasatch | Cutthroat, Rainbow, Kokanee (nearby, contributes to Green R tributaries) |

## Appendix C: Green River Formation Fossil Context

The Green River Formation (Eocene, ~53-48 Ma) spans Wyoming, Colorado, and Utah. It preserves one of the world's finest lacustrine fossil assemblages:

**Database coverage (verified):**
- **PBDB**: 1,277 fossil occurrences. Key taxa: Knightia, Diplomystus, Lambdotherium, Anemorhysis, Pantolestidae
- **iDigBio**: 7,740 total specimens (837 within the Utah/Wyoming watershed bbox). Primary collection: Carnegie Museum of Natural History (~2,221 records). Most specimens lack images
- **GBIF**: ~30,906 fossil specimens in the broader Utah/Wyoming area (includes Morrison Formation dinosaurs and other formations beyond Green River)

**Image availability:** Low across all databases. iDigBio specimens in the Green River Formation are predominantly catalog records without digitized images. This is consistent with our Oregon experience where only 18 of 965 GBIF fossil specimens had images.

**Collecting legality:** BLM SMA adapter already handles land ownership. Fossil collecting on BLM land follows the Paleontological Resources Preservation Act (2009). NPS lands (Dinosaur NM) prohibit all fossil collecting. This context is important for the DeepTrail feature.
