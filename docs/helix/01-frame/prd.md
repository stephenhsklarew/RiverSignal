---
dun:
  id: helix.prd
---
# Product Requirements Document

## Summary

This project builds a shared data platform serving four products across two domains (watershed ecology and deep-time geology) and two markets (B2B professional and B2C consumer):

- **RiverSignal** (B2B) — watershed intelligence copilot for restoration professionals
- **RiverPath** (B2C) — AI river field companion for families, anglers, educators
- **DeepSignal** (B2B) — geologic and paleontological intelligence for researchers, land managers
- **DeepTrail** (B2C) — AI geology field companion for families, rockhounds, educators

The data platform is operational with 15+ ingestion pipelines feeding 2.5M+ records across 5 Oregon watersheds from 15+ public data sources, a 27-view medallion architecture, and a FastAPI + React application with LLM reasoning. The geology/paleontology expansion adds 7+ new data sources (USGS NGMDB, Paleobiology Database, Macrostrat, BLM lands, DOGAMI, mineral deposits, volcanic features), 8 new bronze tables, 3 silver views, and 10 gold views. The key integration insight: geology IS the foundation of watershed ecology — every river, species habitat, and water quality reading is shaped by the rocks beneath.

## Product-Specific Context

### RiverPath — B2C River Field Companion

**Mission**: Help families, anglers, and educators understand the living ecological story of every Oregon river they visit.

**Target users**: Families visiting Oregon rivers 3-10 times/year, fly fishing guides running 150+ trips/year, teachers running field trips, citizen scientists.

**Core experience**: A parent opens RiverPath at the McKenzie River. They see that salmon are spawning upstream right now, the forest burned in 2020 and is recovering (species richness up 180%), the cold water comes from Cascade snowmelt, and a watershed council is planting native trees this Saturday. The kids identify caddisfly larvae. The family returns in September for the salmon migration.

**Key differentiators from RiverSignal**:
- Mobile-first responsive design (not desktop dashboard)
- Story-driven narrative tone (not data-dense professional)
- Location-aware: "What's happening at THIS river RIGHT NOW?"
- Species photo gallery by river mile for field identification
- Seasonal trip optimization (when to visit for salmon, hatches, wildflowers)
- Stewardship connection (volunteer events, how to help)

**Success metrics**:

| Metric | Target |
|--------|--------|
| Families using monthly during season (May-Oct) | 10,000 within 18 months |
| Fishing guide daily active users | 500 within 12 months |
| Return visits to same river | 3+ per season per active user |
| NPS among active families | > 60 |

### DeepTrail — B2C Ancient World Explorer

**Mission**: Help families, travelers, and rockhounds discover what ancient world they're standing in, find legal places to explore, and turn geology into adventure.

**Target users**: Road trip families visiting Painted Hills/John Day Fossil Beds, rockhounds looking for legal collecting sites, educators planning geology field trips, curious travelers at Oregon's geologic landmarks.

**Core experience**: A family at the Painted Hills asks "What was this place like 33 million years ago?" and gets: "You're standing in a subtropical forest with towering redwoods and palms. Rhinoceros-like brontotheres browsed nearby, and early horses the size of dogs ran through the underbrush. The colorful clay layers formed from volcanic ash that blanketed the forest floor." They check collecting legality (NPS — prohibited here), find a nearby BLM site where collecting is legal, and discover what minerals and fossils others have found.

**Key differentiators from DeepSignal**:
- Mobile-first dark-themed adventure UI (not desktop data tables)
- Deep time narrative stories (not raw geologic unit data)
- Legal collecting status with green/yellow/red badges
- Fossil gallery with photo cards
- Geologic time slider for visualizing ancient worlds
- Kid-friendly reading level option
- Offline support for remote areas (PWA)

**Success metrics**:

| Metric | Target |
|--------|--------|
| DeepTrail monthly active families (May-Oct) | 5,000 within 18 months |
| Legal collecting confidence score | 90% of users feel confident about rules |
| Cross-product users (River + Deep) | 30% of active users engage both |
| NPS among active families | > 55 |

---

## Problem and Goals

### Problem

Organizations managing Pacific Northwest watersheds collect more ecological data than they can interpret. A typical watershed program manager with 3-5 active restoration sites spends 15-25 hours per week manually synthesizing iNaturalist exports, stream gauge readings, water quality CSVs, field notes, and acoustic recordings into management decisions. Quarterly funder reports take 2-3 analyst-days each because outcome evidence must be assembled from disconnected sources. Junior field staff cannot interpret monitoring data without senior review, creating a bottleneck: Oregon has ~40% fewer working restoration ecologists than a decade ago while citizen-science observation volume grows 20-30% annually. The result is delayed interventions (invasive species outbreaks discovered weeks late), weak outcome evidence (grant renewals at risk), and institutional knowledge loss when senior staff retire.

**Validated by data platform build**: The fragmented-data problem is now proven, not hypothetical. Building the RiverSignal data platform required integrating 15 distinct public data sources (iNaturalist, USGS NWIS, WQP, EPA ATTAINS, NHDPlus HR, NWI, NIFC, MTBS, WBD, ODF, ODFW, OWRI, PRISM, Oregon DEQ, USFS) across 8 database tables to produce a unified watershed picture. No existing tool combines these sources, confirming the core fragmentation problem with concrete evidence: 2.2M records across 4 Oregon watersheds, each requiring different APIs, schemas, coordinate systems, and update cadences.

### Goals

1. Watershed staff can interpret a season's monitoring data for a restoration site in under 30 minutes instead of 4-6 hours
2. Funder and compliance reports auto-generate from monitored data, requiring only human review before submission
3. Restoration forecasts give managers quantified expectations for what species and indicators should return, enabling adaptive management before outcomes are overdue
4. Invasive species alerts reach managers within 48 hours of observation pattern detection, with spread-path reasoning and recommended response

### Success Metrics

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Interpretation time per site per season | Reduced from 4-6 hours to under 30 minutes | Pre/post time-tracking logs from pilot watershed staff |
| Quarterly report generation time | Under 1 hour (baseline: 2-3 days) | In-app report generation timestamps vs. baseline interviews |
| Restoration forecast accuracy | 70%+ predictions confirmed next monitoring cycle | Automated prediction-vs-observation match scoring |
| Invasive alert latency | Detection-to-alert within 48 hours of pattern emergence | Alert timestamp vs. triggering observation timestamps |
| Pilot NPS | > 50 among active pilot users | Quarterly in-app survey of pilot watershed staff |
| Angler engagement | 100+ weekly active fishing guide users within 6 months of fishing feature launch | In-app analytics |

### Non-Goals

- **Real-time field sensor integration**: The MVP ingests data via API polling and manual upload, not live IoT streaming. Real-time edge processing is Phase 2.
- **Species identification from photos**: RiverSignal reasons over observations already identified in iNaturalist, eBird, or by field staff. It is not a species ID tool competing with Merlin or iNaturalist's CV.
- **Drone imagery analysis**: Aerial/satellite imagery ingestion is deferred to Phase 2. MVP uses ground-level observations and existing GIS layers.
- **Multi-state regulatory compliance**: MVP focuses on Oregon OWEB/NOAA/BPA reporting formats. Other state frameworks are expansion scope.
- **General-purpose ecological chatbot**: RiverSignal is site-specific and intervention-aware, not a generic ecology Q&A system.

Deferred items tracked in `docs/helix/parking-lot.md`.

## Users and Scope

### Primary Persona: Maria -- Watershed Program Manager

**Role**: Program manager at a watershed council, overseeing 3-5 active restoration projects with a team of 4 field staff and 1 GIS analyst
**Goals**: Prove restoration outcomes to funders (OWEB, NOAA), prioritize field actions across sites each week, onboard new seasonal staff quickly
**Pain Points**: Spends half her week synthesizing data from disconnected sources; quarterly OWEB reports take 3 full days; when her senior ecologist retired last year, the team lost 20 years of site-specific pattern recognition; invasive knotweed was detected 3 weeks late last summer because nobody connected observations across tributaries

### Secondary Persona: Jake -- Restoration Ecologist

**Role**: Field ecologist conducting monitoring surveys, interpreting species data, and recommending interventions at 2-3 restoration sites
**Goals**: Understand what changed at each site since last visit, predict what should return next season if the intervention is succeeding, write defensible monitoring reports
**Pain Points**: Spends 6+ hours per site assembling observation data into a coherent ecological narrative; lacks water quality and hydrology context when interpreting biodiversity shifts; frequently re-derives analyses that a retired colleague had already done for the same reach

### Tertiary Persona: Dr. Chen -- Agency Grant Manager

**Role**: Division lead at a state natural resource agency, allocating restoration grants and reviewing outcome reports
**Goals**: Evaluate which funded projects are delivering measurable ecological improvement, justify budget requests to legislature
**Pain Points**: Receives inconsistent reporting formats across grantees; cannot compare restoration ROI across watersheds; outcome evidence is often anecdotal rather than quantified

### Quaternary Persona: Alex -- Fly Fishing Guide

**Role**: Licensed fishing guide running 150+ trips/year on the Deschutes and McKenzie
**Goals**: Know which reaches have active fish, when stocking happens, water conditions, species distribution by stream segment
**Pain Points**: Checks 5+ websites daily for stocking schedules, water flows, fishing reports; clients ask "what's biting where?" and he relies on word-of-mouth; no single source combines water conditions + species data + harvest trends

### Quinary Persona: Sarah -- River-Visiting Family (RiverPath)

**Role**: Parent of two kids (ages 6 and 10) who camps and hikes along Oregon rivers 5-8 times per summer
**Goals**: Turn river visits from "pretty scenery" into engaging, educational family experiences; answer kids' questions ("Is this river healthy?" "What fish live here?"); find the best time to see salmon; discover volunteer opportunities
**Pain Points**: River visits feel shallow — "it's pretty but we don't understand what we're looking at"; kids lose interest after 10 minutes; no app combines species photos + conditions + stories + stewardship for a specific river; occasionally reads an interpretive sign but wants more depth
**Why she switches**: Kids engage with species photos and river stories; family develops annual river traditions (salmon migration trips, summer hatch adventures); parents feel like better outdoor educators

### Senary Persona: Rachel -- Road Trip Family (DeepTrail)

**Role**: Parent of two kids (ages 8 and 12) planning an Oregon road trip through the John Day Fossil Beds and Painted Hills
**Goals**: Find kid-friendly fossil sites, know what's legal to collect, understand what ancient world existed at each stop, make the drive educational and exciting
**Pain Points**: Googles "can I collect fossils in Oregon" and gets contradictory answers; park brochures are generic; no single app combines geologic history + fossil sites + legal collecting rules + kid-friendly content; doesn't know which museums are worth stopping at
**Why she switches**: DeepTrail turns a normal Oregon road trip into a prehistoric adventure; kids are engaged for hours; she feels confident about where collecting is legal; discovers sites she never would have found

### Septenary Persona: Mike -- Rockhound / Mineral Collector (DeepTrail)

**Role**: Amateur mineral collector who explores BLM land in central Oregon 15-20 times/year looking for thundereggs, agates, and obsidian
**Goals**: Find new legal collecting sites on public land, know exactly what agency manages a parcel, learn what minerals have been found at specific locations, plan weekend field trips
**Pain Points**: Legal status of collecting sites is confusing (BLM vs USFS vs NPS vs state rules differ); uses paper BLM maps and word-of-mouth from rockhound clubs; USGS mineral data exists but is designed for economic geologists, not hobbyists; no mobile app combines land ownership + mineral data + directions
**Why he switches**: DeepTrail shows legal collecting sites with green/yellow/red badges, tells him what others have found at each site, and gives him access info — replaces paper maps and club forums

### Octonary Persona: Dr. Torres -- Geologic Researcher (DeepSignal)

**Role**: University geologist studying volcanic influences on watershed hydrology in the Oregon Cascades
**Goals**: Correlate geologic unit maps with water chemistry data, understand how basalt aquifers create spring-fed systems, identify geologic controls on fish habitat distribution
**Pain Points**: Geologic maps and watershed data live in completely separate systems; manually overlays USGS geologic maps on water quality data in GIS; no tool connects rock type to water chemistry to species distribution in a queryable way

## Requirements

### Must Have (P0)

1. **Observation interpretation engine**: Given a set of iNaturalist observations, water quality readings, and hydrology data for a defined watershed boundary, produce a site-level ecological summary including species richness changes, invasive emergence, indicator species presence/absence, and anomaly flags
2. **Restoration forecast**: Given intervention history and current observation baseline for a site, predict which flora/fauna indicators should appear in the next monitoring cycle with confidence scores
3. **Management recommendation generation**: Given current site state and seasonal context, produce a ranked list of recommended field actions (surveys, treatments, monitoring passes) with reasoning
4. **Funder report generation**: Given a date range and site boundary, auto-generate a structured report with before/after species counts, intervention timeline, outcome KPIs, and narrative summary in OWEB-compatible format
5. **Map-first workspace**: Display managed watersheds on an interactive map with site boundaries, observation overlays, alert indicators, and a linked detail/chat panel
6. **Data ingestion pipeline**: Ingest and normalize data from iNaturalist API, USGS water data services, Oregon Water Data Portal, and manual CSV/PDF upload

### Should Have (P1)

1. **Invasive species alert system**: Detect emerging invasive patterns from observation feeds, model likely spread paths using river network topology and disturbance corridors, and notify managers with recommended response
2. **Intervention outcome memory**: Store and index past interventions and their ecological outcomes per site, enabling the reasoning engine to learn from historical success/failure patterns
3. **Multi-site comparison dashboard**: Compare ecological indicators across managed sites to identify which restoration approaches are most effective
4. **Acoustic biodiversity integration**: Ingest bird/frog audio classification results (from BirdNET or similar) as additional observation inputs
5. **Fishing intelligence layer**: Species-by-reach distribution, sport catch harvest trends, stocking schedule alerts, and water condition correlation for angler decision support
6. **Geologic context layer**: For any location, provide the geologic unit, rock type, age, formation name, and narrative explanation of how geology drives local ecology (DeepSignal/DeepTrail)
7. **Fossil discovery layer**: Fossil occurrences from Paleobiology Database with taxa, ages, and museum links; legal collecting status based on land ownership (DeepTrail)
8. **Land access and legality**: Public land boundaries (BLM, USFS, NPS, state) with collecting rules clearly displayed per parcel (DeepTrail)
9. **Deep time storytelling**: For any location, generate an AI narrative of what ancient ecosystem existed there in each geologic period, with fossil evidence (DeepTrail)

### Nice to Have (P2)

1. **Collaborative annotation**: Allow senior ecologists to annotate, correct, or override system interpretations, feeding back into reasoning quality
2. **Custom report templates**: Support additional report formats beyond OWEB (NOAA, BPA, tribal reporting frameworks)
3. **Historical trend visualization**: Show multi-year ecological trajectory graphs per site with intervention markers
4. **Geology-ecology correlation engine**: Automated analysis linking geologic unit properties (lithology, permeability, mineral content) to downstream water chemistry, species distribution, and restoration outcomes (DeepSignal)
5. **Museum and site guide**: Nearby fossil museums, geologic interpretive sites, and visitor centers with hours, exhibits, and kid-friendliness ratings (DeepTrail)
6. **Volcanic feature mapping**: Vents, flows, calderas, lava tubes, and hot springs with geologic history and hazard context (DeepTrail/DeepSignal)
7. **Mobile-first responsive PWA**: Progressive Web App for RiverPath and DeepTrail with offline caching for remote areas (B2C products)
4. **eBird integration**: Supplement iNaturalist bird observations with eBird data for richer avian indicators

## Functional Requirements

### Data Ingestion

- FR-1: System ingests iNaturalist observations by HUC12 watershed boundary via iNaturalist API, polling daily
- FR-2: System ingests USGS stream gauge data (flow, temperature, dissolved oxygen) via USGS Water Services API for configured station IDs
- FR-3: System ingests water quality data (phosphorus, chlorophyll, cyanotoxins) from Oregon Water Data Portal for configured stations
- FR-4: System accepts manual upload of CSV (species lists, water quality), PDF (field notes, grant reports), and GeoJSON (site boundaries, restoration polygons)
- FR-5: All ingested data is normalized to a canonical schema indexed by site, timestamp, and data source
- FR-6: System maintains a site registry where each site has a defined HUC boundary, intervention history log, and data source configuration

### Ecological Reasoning

- FR-7: Given a site and date range, the reasoning engine produces an ecological summary that includes: species richness delta vs. prior period, new species detections, invasive species detections, indicator species presence/absence vs. expected, water quality trend summary, and anomaly flags with explanations
- FR-8: Given a site with intervention history, the engine produces a restoration forecast listing expected species returns, habitat condition changes, and risk factors for the next monitoring period, each with a confidence score (high/medium/low)
- FR-9: Given a site and current month, the engine produces a ranked list of 3-5 recommended field actions with reasoning tied to current observations, seasonal context, and restoration goals
- FR-10: All reasoning outputs include citations to specific observations, data points, or intervention records that informed the conclusion

### Report Generation

- FR-11: Given a site and date range, the system generates a structured funder report containing: executive summary, intervention timeline, before/after species indicator table, water quality trend summary, outcome KPI scorecard, and confidence assessment
- FR-12: Reports are exportable as PDF and Markdown
- FR-13: Reports include auto-generated maps showing observation density, species detection locations, and intervention zones
- FR-14: Users can edit generated report text before export without losing data linkages

### Map Workspace

- FR-15: Interactive map displays all managed sites with watershed boundaries overlaid on satellite/terrain basemap
- FR-16: Map markers show observation density, alert status (green/amber/red), and most recent ecological summary score per site
- FR-17: Clicking a site opens a detail panel with site timeline, recent observations, current alerts, ecological summary, and a chat interface for natural-language queries about the site
- FR-18: Map supports filtering by date range, data source, species group, and alert type

### Access and Multi-tenancy

- FR-19: Users authenticate via email/password or SSO
- FR-20: Each organization (watershed council, agency, land trust) has a private workspace with its own sites, data, and reports
- FR-21: Organization admins can invite members and assign role-based access (viewer, analyst, manager, admin)

## Acceptance Test Sketches

| Requirement | Scenario | Input | Expected Output |
|-------------|----------|-------|-----------------|
| P0-1 (Observation interpretation) | Manager requests ecological summary for Williamson River site, Q1 2026 | Site boundary (HUC12), date range Jan-Mar 2026, 340 iNaturalist observations, 90 days of USGS stream data | Summary showing species richness increased by 12 taxa vs. prior Q1, 2 new native fish observations, 1 invasive plant flag (reed canarygrass at 2 locations), dissolved oxygen trending upward, with citations to specific observation IDs |
| P0-2 (Restoration forecast) | Ecologist asks for next-season prediction at a riparian replanting site | Site with 18-month intervention history (native planting + invasive removal), current species baseline of 45 taxa | Forecast predicting 3-5 expected bird species returns (named), 2 amphibian indicators, estimated native plant cover increase of 10-15%, confidence scores per prediction, risk flag for knotweed recolonization in disturbed corridor |
| P0-3 (Management recommendations) | Manager requests weekly field priorities across 3 sites in April | 3 sites with current observation data, seasonal calendar = early spring, one site with recent invasive detection | Ranked list: (1) invasive sweep at flagged site within 10 days, (2) amphibian dusk audio pass at wetland site -- breeding season window, (3) photo-point re-survey at replanting site for canopy closure tracking; each with 2-3 sentence reasoning |
| P0-4 (Funder report) | Manager generates Q4 2025 OWEB progress report for Upper Klamath marsh restoration | Site boundary, date range Oct-Dec 2025, intervention log, all ingested observations and water quality data for period | PDF report with: executive summary (3 paragraphs), intervention timeline, before/after species table (20+ indicator species with detection status), water quality chart, 3 outcome KPIs with targets vs. actuals, confidence narrative |
| P0-5 (Map workspace) | Manager opens dashboard Monday morning | 4 configured sites in Upper Klamath basin, weekend iNaturalist observations ingested | Map shows 4 site polygons, 1 amber alert on site with new invasive detection, click reveals detail panel with observation list, ecological summary, and chat pane |
| P0-6 (Data ingestion) | System completes daily iNaturalist sync | Configured HUC12 boundary for Upper Klamath Lake | New observations since last sync are ingested, normalized, and appear on map within 15 minutes of sync completion |

### RiverPath Acceptance Test Sketches

| Requirement | Scenario | Input | Expected Output |
|-------------|----------|-------|-----------------|
| River story at location | Family opens RiverPath at McKenzie River | GPS location near McKenzie, or watershed selected | Story-driven narrative: what's happening now (spawning, fire recovery, water conditions), species gallery with photos, seasonal tips, nearby stewardship events |
| Species photo gallery | Parent wants to identify what they see | Watershed = deschutes, river mile range 40-50 | Grid of species photo cards with common name, scientific name, last observed date; sorted by observation frequency; filterable by taxonomic group |
| Fishing morning brief | Guide checks conditions before Deschutes trip | Watershed = deschutes, month = July | Natural-language brief: water temp 15°C, flow 4,200 cfs; steelhead active in canyon reach; recent stocking at Lake Billy Chinook; harvest down 12% vs last year |
| Observation map search | Angler asks "show me all salmon observations" | Watershed = deschutes, search = "salmon" | Map pins at every salmon observation location with photo popups; count badge showing total matches |
| Offline access | Family at river with no cell signal | Previously viewed McKenzie data cached via service worker | Cached river story, species gallery, and conditions display with "Last updated X ago" banner; chat disabled with explanation |

### DeepTrail Acceptance Test Sketches

| Requirement | Scenario | Input | Expected Output |
|-------------|----------|-------|-----------------|
| Deep time story | Family at Painted Hills asks "What was this place like?" | lat=44.66, lon=-120.23 | Narrative describing Oligocene subtropical forest (33 Ma) with redwoods, brontotheres, and early horses; clay layers from volcanic ash; cited fossil evidence from PBDB |
| Legal collecting status | Rockhound checks if BLM land allows collecting | lat=44.5, lon=-120.8 (BLM land near Fossil, OR) | Green badge: "Collecting: permitted — BLM land, casual collecting of common fossils for personal use"; disclaimer to verify on-site |
| Fossil gallery | Family wants to know what fossils exist nearby | lat=44.66, lon=-120.23, radius=50km | Cards showing nearby fossil taxa (Mesohippus, Archaeotherium, etc.) with phylum, period, age, distance; sorted by proximity |
| Deep time timeline | Educator shows geologic history at a site | lat=44.66, lon=-120.23 | Chronological timeline: oldest geologic unit at top, fossil occurrences interspersed, each with age (Ma) and description |
| Mineral site search | Rockhound looks for thunderegg sites | Search for mineral deposits near Madras, OR | MRDS mineral deposit locations with commodity names, development status, and coordinates |
| Kid-friendly narrative | Family mode activated | Same location, reading_level = kid_friendly | Same deep time story rewritten at 5th-grade reading level; simpler vocabulary, shorter sentences, "imagine you're standing in..." framing |

## Technical Context

- **Language/Runtime**: Python 3.12+, TypeScript 5.x
- **Frontend**: React 18 with MapLibre GL JS for map rendering, Vite 6 build
- **Backend**: FastAPI on Python for reasoning and data pipelines, Node.js for real-time workspace API
- **LLM Integration**: Claude API (Anthropic) for ecological reasoning and report generation; tool-using agent architecture with geospatial and data-query tools
- **Data/Storage**: PostgreSQL 17 with PostGIS 3.6.2 on port 5433; S3-compatible object store for media (photos, audio, PDFs)
- **Data Sources (15 operational pipelines)**: iNaturalist API v1, USGS NWIS (stream gauges), Water Quality Portal (WQP), EPA ATTAINS (impaired waters), NHDPlus HR (stream flowlines), National Wetlands Inventory (NWI), NIFC/MTBS (fire perimeters and burn severity), USGS WBD (watershed boundaries), Oregon Dept of Forestry (ODF), Oregon Dept of Fish & Wildlife (ODFW sport catch/stocking), Oregon Watershed Restoration Inventory (OWRI), PRISM (climate), Oregon DEQ (water quality), USFS (land management)
- **Database Tables (13)**: observations, time_series, interventions, fire_perimeters, stream_flowlines, impaired_waters, wetlands, watershed_boundaries, geologic_units, fossil_occurrences, mineral_deposits, land_ownership, deep_time_stories
- **Data Volume**: 2.5M+ records loaded across 5 watersheds (Klamath, McKenzie, Deschutes, Metolius, John Day); 17,288 geologic units, 1,959 fossil occurrences, 1,980 mineral deposits
- **Medallion Architecture**: 7 silver views + 31 gold views = 38 materialized views
- **Geology Data Sources (6)**: Macrostrat, USGS NGMDB via DOGAMI OGDC v6, Paleobiology Database (PBDB), iDigBio museum specimens, USGS MRDS mineral deposits, BLM Surface Management Agency
- **GIS**: HUC12 watershed boundaries from USGS WBD, wetland layers from NWI, burn severity from MTBS, stream flowlines from NHDPlus HR
- **Platform Targets**: Web application; Chrome, Firefox, Safari latest; responsive but desktop-primary (field tablet secondary)

## Constraints, Assumptions, Dependencies

### Constraints

- **Technical**: LLM context windows limit the number of observations that can be reasoned over in a single pass; batching and summarization strategies required for sites with >500 observations per period
- **Business**: MVP must be demonstrable to first lighthouse customer (Oregon watershed board or council) within 90 days of development start; team is 2-3 engineers + 1 domain advisor
- **Legal/Compliance**: iNaturalist data is CC-BY-NC for observations; commercial use requires attribution and cannot resell raw observation data. USGS and Oregon Water Data Portal data is public domain.

### Assumptions

- iNaturalist observation density in target watersheds is sufficient (>100 observations/quarter) to support meaningful ecological reasoning -- VALIDATED: all 4 watersheds exceed threshold by 10x
- USGS stream gauge and water quality stations in target watersheds have >95% uptime and data availability -- VALIDATED: 98K+ time-series records loaded
- Fishing/angler use case expands addressable market beyond restoration professionals
- Watershed managers will adopt a map-first web interface rather than requiring integration into existing GIS desktop tools (ArcGIS, QGIS) for MVP
- Claude API multimodal capabilities are sufficient for photo and document interpretation without fine-tuned models
- One domain-expert advisor (restoration ecologist) is available for weekly feedback during MVP development

### Dependencies

- iNaturalist API availability and rate limits (currently 100 requests/minute for authenticated apps)
- USGS Water Services API availability
- Anthropic Claude API for LLM reasoning (no self-hosted model for MVP)
- PostGIS/TimescaleDB for geospatial time-series storage
- MapLibre GL JS (open-source) for map rendering

## Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| iNaturalist observation density in target watersheds is too sparse for meaningful seasonal reasoning | MITIGATED | High | All 4 watersheds far exceed the 100/quarter threshold: Klamath avg 1,281/quarter, McKenzie 2,789, Deschutes 4,021, Metolius 900. Risk retired. |
| Data volume (2.2M records) exceeds single LLM context capacity | High | High | Pre-aggregation and semantic search layer required; reasoning engine must work with summarized/filtered subsets rather than raw records; vector embeddings for observation search |
| LLM ecological reasoning produces plausible but ecologically incorrect recommendations | High | High | Implement mandatory HITL review queue for all management recommendations; flag low-confidence outputs; weekly review sessions with domain advisor during pilot; track correction rate as quality metric |
| Pilot customer (watershed council/agency) procurement cycle exceeds 90-day demo timeline | Medium | Medium | Identify 2-3 potential pilot partners in parallel; offer initial 60-day free evaluation period; target watershed councils (faster procurement than state agencies) for first engagement |
| Senior ecologist domain advisor is unavailable during critical development sprints | Low | High | Front-load domain knowledge capture in first 2 weeks; build ecological reasoning test suite from advisor-validated examples; maintain written heuristic library |
| iNaturalist API changes rate limits or terms of service | Low | Medium | Abstract data ingestion behind adapter interface; cache observations locally after ingestion; monitor iNaturalist developer communications |

## Open Questions

- [ ] Which specific OWEB report template format should the MVP target? -- blocks FR-11 report generation design, ask OWEB program staff or pilot customer
- [x] What is the minimum observation density per HUC12 per quarter that produces useful ecological reasoning? -- ANSWERED: All 4 watersheds exceed 100/quarter by 10x. Klamath avg 1,281/quarter, McKenzie 2,789, Deschutes 4,021, Metolius 900.
- [ ] Should the MVP support tribal data sovereignty requirements (data residency, access controls for culturally sensitive species observations)? -- blocks FR-20 multi-tenancy design, ask Klamath Tribes natural resource team
- [ ] Is BirdNET audio classification output available as a structured API or only as app-level results? -- blocks P1-4 acoustic integration scoping, ask BirdNET/Cornell team
- [x] What intervention history format do watershed councils currently use (if any standardized format exists)? -- ANSWERED: OWRI uses project_nbr with 5 related tables (activities, goals, metrics, results, species). 1,391 intervention records loaded, 805 with outcome results.

## Success Criteria

### RiverSignal (B2B Watershed)
- Pilot watershed staff report that RiverSignal reduces their monitoring interpretation time by at least 40% (validated via pre/post time tracking)
- At least one quarterly funder report is generated and submitted using RiverSignal output during the pilot period
- Restoration forecasts achieve 70%+ confirmation rate in the monitoring cycle following the prediction
- Pilot organization agrees to continue using RiverSignal after the evaluation period (renewal or paid contract)
- System maintains ecological reasoning quality as judged by domain advisor review: fewer than 20% of outputs require substantive correction

### RiverPath (B2C Watershed)
- 10,000 monthly active families during season (May-Oct) within 18 months of launch
- 500 daily active fishing guide users within 12 months
- Active users return to same river 3+ times per season
- NPS > 60 among active families (quarterly survey)
- B2C mobile Lighthouse performance score > 80

### DeepTrail (B2C Geology)
- 5,000 monthly active families during season (May-Oct) within 18 months of launch
- 90% of users report feeling confident about collecting legality after checking DeepTrail
- 30% of active users engage with both river (RiverPath) and geology (DeepTrail) products
- Deep time narratives cite specific fossil evidence in 80%+ of Oregon locations with PBDB data
- NPS > 55 among active families

## Review Checklist

- [x] Summary works as a standalone 1-pager -- someone can decide whether to read the rest
- [x] Problem statement describes a specific failure mode with concrete cost
- [x] Goals are outcomes, not activities ("users can X" not "we build Y")
- [x] Success metrics have numeric targets and named measurement methods
- [x] Non-goals exclude things a reasonable person might assume are in scope
- [x] Personas have specific pain points, not generic descriptions
- [x] P0 requirements are necessary for launch -- removing any one makes the product unusable
- [x] P1/P2 requirements are correctly prioritized relative to each other
- [x] Every P0 requirement has an acceptance test sketch
- [x] Functional requirements are testable -- each can be verified with specific inputs and expected outputs
- [x] Technical context names specific versions and interfaces, not vague technology areas
- [x] Risks have concrete mitigations ("we do X"), not vague strategies ("we monitor")
- [x] Open questions name who can answer and what is blocked
- [x] No contradictions between requirements sections
- [x] PRD is consistent with the governing product vision
