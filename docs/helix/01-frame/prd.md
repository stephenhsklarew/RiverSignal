---
dun:
  id: helix.prd
---
# Product Requirements Document

## Summary

RiverSignal is an AI-powered watershed intelligence copilot that transforms fragmented ecological monitoring data into management recommendations, restoration forecasts, and funder-ready reports. It serves watershed program managers, restoration ecologists, and agency staff in the Pacific Northwest who currently spend 15-25 hours/week manually interpreting field observations, GIS layers, and sensor feeds. The MVP targets watershed restoration intelligence for the Upper Klamath basin, ingesting iNaturalist observations, USGS hydrology, water quality stations, and intervention logs to answer questions like "Which tributaries show the strongest biological recovery since dam removal?" Success is measured by 40% reduction in monitoring interpretation time, quarterly reports generated in under 1 hour (down from 2-3 days), and 70%+ restoration forecast accuracy within one field season.

## Problem and Goals

### Problem

Organizations managing Pacific Northwest watersheds collect more ecological data than they can interpret. A typical watershed program manager with 3-5 active restoration sites spends 15-25 hours per week manually synthesizing iNaturalist exports, stream gauge readings, water quality CSVs, field notes, and acoustic recordings into management decisions. Quarterly funder reports take 2-3 analyst-days each because outcome evidence must be assembled from disconnected sources. Junior field staff cannot interpret monitoring data without senior review, creating a bottleneck: Oregon has ~40% fewer working restoration ecologists than a decade ago while citizen-science observation volume grows 20-30% annually. The result is delayed interventions (invasive species outbreaks discovered weeks late), weak outcome evidence (grant renewals at risk), and institutional knowledge loss when senior staff retire.

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

### Nice to Have (P2)

1. **Collaborative annotation**: Allow senior ecologists to annotate, correct, or override system interpretations, feeding back into reasoning quality
2. **Custom report templates**: Support additional report formats beyond OWEB (NOAA, BPA, tribal reporting frameworks)
3. **Historical trend visualization**: Show multi-year ecological trajectory graphs per site with intervention markers
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

## Technical Context

- **Language/Runtime**: Python 3.12+, TypeScript 5.x
- **Frontend**: React 18 with MapLibre GL JS for map rendering, Vite 6 build
- **Backend**: FastAPI on Python for reasoning and data pipelines, Node.js for real-time workspace API
- **LLM Integration**: Claude API (Anthropic) for ecological reasoning and report generation; tool-using agent architecture with geospatial and data-query tools
- **Data/Storage**: PostgreSQL 16 with PostGIS for geospatial data, TimescaleDB extension for time-series hydrology/water quality; S3-compatible object store for media (photos, audio, PDFs)
- **Data Sources**: iNaturalist API v1, USGS Water Services REST API, Oregon Water Data Portal API
- **GIS**: HUC12 watershed boundaries from USGS WBD, wetland layers from NWI, burn severity from MTBS
- **Platform Targets**: Web application; Chrome, Firefox, Safari latest; responsive but desktop-primary (field tablet secondary)

## Constraints, Assumptions, Dependencies

### Constraints

- **Technical**: LLM context windows limit the number of observations that can be reasoned over in a single pass; batching and summarization strategies required for sites with >500 observations per period
- **Business**: MVP must be demonstrable to first lighthouse customer (Oregon watershed board or council) within 90 days of development start; team is 2-3 engineers + 1 domain advisor
- **Legal/Compliance**: iNaturalist data is CC-BY-NC for observations; commercial use requires attribution and cannot resell raw observation data. USGS and Oregon Water Data Portal data is public domain.

### Assumptions

- iNaturalist observation density in Upper Klamath HUC12 boundaries is sufficient (>100 observations/quarter) to support meaningful ecological reasoning
- USGS stream gauge and water quality stations in the Upper Klamath basin have >95% uptime and data availability
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
| iNaturalist observation density in Upper Klamath is too sparse for meaningful seasonal reasoning | Medium | High | Pre-validate by querying iNaturalist API for observation counts per HUC12 per quarter before committing to watershed; define minimum threshold of 50 observations/quarter; supplement with USGS biological data if needed |
| LLM ecological reasoning produces plausible but ecologically incorrect recommendations | High | High | Implement mandatory HITL review queue for all management recommendations; flag low-confidence outputs; weekly review sessions with domain advisor during pilot; track correction rate as quality metric |
| Pilot customer (watershed council/agency) procurement cycle exceeds 90-day demo timeline | Medium | Medium | Identify 2-3 potential pilot partners in parallel; offer initial 60-day free evaluation period; target watershed councils (faster procurement than state agencies) for first engagement |
| Senior ecologist domain advisor is unavailable during critical development sprints | Low | High | Front-load domain knowledge capture in first 2 weeks; build ecological reasoning test suite from advisor-validated examples; maintain written heuristic library |
| iNaturalist API changes rate limits or terms of service | Low | Medium | Abstract data ingestion behind adapter interface; cache observations locally after ingestion; monitor iNaturalist developer communications |

## Open Questions

- [ ] Which specific OWEB report template format should the MVP target? -- blocks FR-11 report generation design, ask OWEB program staff or pilot customer
- [ ] What is the minimum observation density per HUC12 per quarter that produces useful ecological reasoning? -- blocks watershed selection validation, ask domain advisor after initial LLM experiments
- [ ] Should the MVP support tribal data sovereignty requirements (data residency, access controls for culturally sensitive species observations)? -- blocks FR-20 multi-tenancy design, ask Klamath Tribes natural resource team
- [ ] Is BirdNET audio classification output available as a structured API or only as app-level results? -- blocks P1-4 acoustic integration scoping, ask BirdNET/Cornell team
- [ ] What intervention history format do watershed councils currently use (if any standardized format exists)? -- blocks FR-6 intervention log schema, ask pilot customer

## Success Criteria

- Pilot watershed staff report that RiverSignal reduces their monitoring interpretation time by at least 40% (validated via pre/post time tracking)
- At least one quarterly funder report is generated and submitted using RiverSignal output during the pilot period
- Restoration forecasts achieve 70%+ confirmation rate in the monitoring cycle following the prediction
- Pilot organization agrees to continue using RiverSignal after the evaluation period (renewal or paid contract)
- System maintains ecological reasoning quality as judged by domain advisor review: fewer than 20% of outputs require substantive correction

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
