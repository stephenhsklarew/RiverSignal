# User Stories — RiverSignal (B2B)

## FEAT-001: Observation Interpretation

### US-001 — Manager requests site ecological summary
**As** Maria (watershed program manager),
**I want** to request an ecological summary for my Williamson River restoration site for Q1 2026,
**So that** I can understand species richness changes, invasive emergence, and water quality trends without manually synthesizing 5+ data sources.

**Acceptance Criteria:**
- Summary includes species richness delta vs. prior Q1
- Invasive species are flagged with detection count and date
- Indicator species presence/absence is listed with detection numbers
- Water quality trend (temperature, DO) is reported with specific values
- Summary cites specific observation data (source, count, date range)
- Generates in under 120 seconds

---

### US-002 — Ecologist drills into anomaly explanation
**As** Jake (restoration ecologist),
**I want** to click on an anomaly flag in the ecological summary and see the specific observations that triggered it,
**So that** I can determine if it's a real ecological signal or a data artifact.

**Acceptance Criteria:**
- Anomaly flags are clickable in the summary view
- Clicking shows the triggering observations with dates, locations, and values
- Anomaly type is classified (temperature exceedance, DO drop, unexpected species)
- Ecologist can dismiss false positives with a note

---

### US-003 — Manager compares current summary to prior period
**As** Maria,
**I want** to see this quarter's ecological summary side-by-side with the same quarter last year,
**So that** I can tell funders whether the site is improving.

**Acceptance Criteria:**
- Year-over-year species richness delta is shown with specific numbers
- Water quality trends show directional change (improving/declining/stable)
- Fire recovery trajectory is visible if applicable
- Comparison data is available for at least 3 prior years

---

## FEAT-002: Restoration Forecasting

### US-004 — Ecologist generates restoration forecast
**As** Jake,
**I want** to generate a 6-month restoration forecast for a riparian replanting site,
**So that** I can tell the team what species we should expect to see return and what risks to watch for.

**Acceptance Criteria:**
- Forecast names 3-5 specific species expected to return
- Each prediction has a confidence level (HIGH/MEDIUM/LOW) with justification
- Risk factors are listed (invasive recolonization, drought, etc.)
- Evidence basis cites specific intervention history and current conditions
- Generates in under 90 seconds

---

### US-005 — Manager reviews forecast vs. actuals
**As** Maria,
**I want** to compare last season's forecast predictions against actual monitoring observations,
**So that** I can assess the system's accuracy and adjust expectations for funders.

**Acceptance Criteria:**
- Each prior prediction is shown with its outcome (confirmed/not confirmed/insufficient data)
- Overall accuracy percentage is calculated
- Predictions that failed include explanation of what differed

---

### US-006 — Ecologist adjusts intervention plan based on forecast risk factors
**As** Jake,
**I want** the forecast to highlight specific risk factors that I should address in my intervention plan,
**So that** I can proactively prevent restoration setbacks.

**Acceptance Criteria:**
- Risk factors are specific and actionable (e.g., "knotweed recolonization risk in disturbed corridor within 200m of planting zone")
- Each risk cites the evidence that triggered it
- Suggested mitigation actions are included

---

## FEAT-003: Management Recommendations

### US-007 — Manager reviews weekly field priorities Monday morning
**As** Maria,
**I want** to open RiverSignal on Monday morning and see a ranked list of 3-5 recommended field actions across my managed sites,
**So that** I can plan the week's field work based on ecological priority rather than guesswork.

**Acceptance Criteria:**
- Recommendations are ranked by priority (1 = most urgent)
- Each recommendation includes: action, target site, time sensitivity, and 2-3 sentence reasoning
- Reasoning is grounded in specific data (anomalies, seasonal windows, invasive detections)
- "No priority actions" is shown when sites are stable, with health summary
- Generates in under 60 seconds

---

### US-008 — Manager assigns recommended action to field crew
**As** Maria,
**I want** to accept a recommendation and assign it to a field crew member,
**So that** the action is tracked from recommendation to completion.

**Acceptance Criteria:**
- "Accept" button marks recommendation as assigned
- Accepted recommendations appear in a task list
- Completion can be logged with date and notes

---

### US-009 — Manager dismisses irrelevant recommendation with feedback
**As** Maria,
**I want** to dismiss a recommendation that doesn't apply and explain why,
**So that** future recommendations are more relevant.

**Acceptance Criteria:**
- "Dismiss" button with required notes field
- Dismiss reason is stored and available for system improvement
- Dismissed action is not re-recommended in the same period

---

## FEAT-004: Funder Report Generation

### US-010 — Manager generates quarterly OWEB progress report
**As** Maria,
**I want** to generate a quarterly progress report for my OWEB-funded restoration project,
**So that** I can submit it in under 1 hour instead of 2-3 days.

**Acceptance Criteria:**
- Report includes: executive summary, intervention timeline, species indicator table, water quality trends, outcome KPIs
- Available in Markdown and PDF formats
- All data values match the gold layer (no fabrication)
- Generates in under 5 minutes

---

### US-011 — Manager edits generated report narrative
**As** Maria,
**I want** to edit the AI-generated narrative sections before submitting the report,
**So that** I can add context the system doesn't know about (e.g., a landowner meeting outcome).

**Acceptance Criteria:**
- Narrative text is editable in the report view
- Data tables and KPIs remain linked to source data
- Edits are saved and reflected in the exported PDF/Markdown

---

### US-012 — Grant manager compares reports across funded sites
**As** Dr. Chen (agency grant manager),
**I want** to compare restoration outcome metrics across multiple funded sites,
**So that** I can evaluate which approaches are delivering the best ecological ROI.

**Acceptance Criteria:**
- Multiple site reports can be viewed in comparison
- Key metrics (species richness, water quality, intervention count) are shown side-by-side
- Sites are ranked by outcome improvement

---

## FEAT-005: Data Ingestion Pipeline

### US-013 — Admin configures a new watershed
**As** a system admin,
**I want** to add a new watershed site with its bounding box and data source configuration,
**So that** the system begins ingesting data for it automatically.

**Acceptance Criteria:**
- New site appears in the site list after creation
- Data ingestion begins within 24 hours
- First observations and time series records appear in the database

---

### US-014 — Ecologist uploads field notes PDF
**As** Jake,
**I want** to upload a PDF of my field notes from a site visit,
**So that** the system can incorporate my qualitative observations into the ecological summary.

**Acceptance Criteria:**
- PDF upload is accepted (max 100 MB / 50 pages)
- Content is extractable and appears in site context
- Upload is confirmed with success/error feedback

---

### US-015 — Admin reviews data ingestion health
**As** a system admin,
**I want** to see the ingestion health dashboard showing last sync time, record counts, and failure status per data source,
**So that** I can identify and fix broken pipelines.

**Acceptance Criteria:**
- Each data source shows: last sync time, records synced, status (healthy/degraded/failed)
- Failed sources show error message
- Dashboard refreshes automatically

---

## FEAT-006: Map Workspace

### US-016 — Manager checks all-sites status Monday morning
**As** Maria,
**I want** to open the map dashboard and see all my managed watersheds with health indicators,
**So that** I can identify which sites need attention this week.

**Acceptance Criteria:**
- All 5 watersheds visible on the map with color-coded markers
- KPI chips show total observations and interventions
- Clicking a watershed opens the detail panel

---

### US-017 — Manager investigates an amber alert
**As** Maria,
**I want** to click on an amber-flagged watershed and understand what triggered the alert,
**So that** I can decide if immediate action is needed.

**Acceptance Criteria:**
- Alert ticker shows specific anomaly (e.g., "391 temperature anomalies")
- Detail panel opens with anomaly context
- Alert is dismissible after review

---

### US-018 — Ecologist asks a natural-language question
**As** Jake,
**I want** to type "What fish are spawning in the McKenzie right now?" and get a data-grounded answer,
**So that** I can get quick answers without navigating through multiple tabs.

**Acceptance Criteria:**
- Chat input accepts natural-language questions
- Response is grounded in gold-layer data (not hallucinated)
- Response includes specific data values and species names
- Renders markdown formatting correctly

---

### US-019 — Admin defines a new site boundary
**As** a system admin,
**I want** to draw or upload a watershed boundary polygon on the map,
**So that** I can define the geographic scope of a new managed site.

**Acceptance Criteria:**
- Boundary can be drawn on the map or uploaded as GeoJSON
- Boundary is stored as PostGIS geometry
- New boundary appears on the map immediately

---

## FEAT-007: Fishing Intelligence

### US-020 — Guide checks morning conditions before a Deschutes trip
**As** Alex (fly fishing guide),
**I want** to check the Deschutes fishing brief before my morning trip,
**So that** I know water conditions, active species, and any recent stocking.

**Acceptance Criteria:**
- Fishing brief shows: water temp, flow, active species, recent stocking, harvest trends
- Brief is available for the current date and selected watershed
- Generates in under 15 seconds

---

### US-021 — Angler looks up what species are in the Metolius
**As** an angler,
**I want** to see what fish species are present in the Metolius River by reach,
**So that** I know what I might catch and where.

**Acceptance Criteria:**
- Species list shows: common name, scientific name, use type (spawning/rearing/migration/resident)
- List is organized by stream reach
- Photo available for species with iNaturalist observations

---

### US-022 — Guide compares this year's steelhead run to last year
**As** Alex,
**I want** to see steelhead harvest trends year-over-year on the Deschutes,
**So that** I can tell clients whether this season is better or worse than usual.

**Acceptance Criteria:**
- Harvest data shows annual totals with year-over-year delta
- At least 3 years of comparison data
- Specific to steelhead (or other selected species)

---

### US-023 — Angler sets alert for stocking at a favorite lake
**As** an angler,
**I want** to be notified when trout are stocked at my favorite waterbody,
**So that** I can plan a trip while the fishing is hot.

**Acceptance Criteria:**
- Alert shows upcoming stocking events with date, waterbody, and fish count
- Distinction between past and upcoming events
- Alert is visible in the fishing alerts banner
