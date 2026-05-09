# Product Vision

## Platform Strategy

This project builds a **shared data platform** serving four products across two domains:

|  | **B2B (Professional)** | **B2C (Consumer Mobile-First)** |
|---|---|---|
| **Watershed Ecology** | **RiverSignal** — watershed intelligence copilot | **[RiverPath](riverpath-vision.md)** — river field companion |
| **Deep Time Geology** | **DeepSignal** — geologic intelligence platform | **[DeepTrail](deeptrail-vision.md)** — ancient world explorer |

All four products share the same PostgreSQL + PostGIS data lake, ingestion pipeline architecture, silver/gold medallion layer, LLM reasoning engine, and FastAPI backend. The data platform is the strategic asset; the products are presentation layers with different UX, tone, and business models.

**The key insight**: geology IS the foundation of watershed ecology. Every river, every species habitat, every water quality reading is shaped by the rocks beneath. Deep time context makes ecological intelligence more powerful, and ecological context makes geology more relevant.

## Mission Statement (RiverSignal)

RiverSignal delivers AI-powered ecological reasoning to watershed managers, restoration ecologists, and conservation agencies so they can interpret biodiversity data at operational speed and prove restoration outcomes to funders.

## Positioning

For **watershed program managers and restoration ecologists** who spend 40-60% of interpretation time manually synthesizing field observations, GIS layers, sensor feeds, and compliance reports,
**RiverSignal** is a **watershed intelligence copilot** that transforms fragmented ecological data into management recommendations, restoration forecasts, and funder-ready reports.
Unlike **manual expert review and spreadsheet-based monitoring workflows**, RiverSignal compounds ecological reasoning over time by learning which interventions worked, what indicators preceded success or failure, and region-specific heuristics -- building a longitudinal decision graph no consulting engagement can replicate.

## Vision

Ecological decisions are no longer bottlenecked by the scarcity of expert interpretation. Watershed managers open a map-first workspace, see site-level ecological intelligence updated from live observation feeds, and receive prioritized field actions grounded in intervention history and seasonal context. Restoration outcomes are continuously scored against forecasts, and funder reports generate themselves from monitored data. Junior staff operate with the pattern-recognition support of senior ecologists. Tribal, agency, and nonprofit partners share a common operational picture of watershed health that compounds in value with every season of data.

**North Star**: Every Pacific Northwest watershed restoration project has access to AI-powered ecological reasoning that turns monitoring data into provable outcomes within one field season.

**Geographic scope**: Pacific Northwest + Utah — 7 watersheds across 3 states (Deschutes, McKenzie, Metolius, Klamath, John Day in Oregon; Skagit in Washington; Green River in Utah). Multi-state data adapter architecture supports state-specific agency APIs (ODFW, WDFW, UDWR).

**Predictive intelligence**: The platform generates forward-looking predictions — hatch emergence forecasts (degree-day models), catch probability scoring, river health anomaly detection, species distribution shift tracking, and restoration impact prediction — turning retrospective monitoring into proactive management.

**Production infrastructure**: GCP deployment (Cloud Run, Cloud SQL, Cloud Storage, Cloud Scheduler) with Terraform IaC, GitHub Actions CI/CD, and automated daily/weekly/monthly pipeline refresh.

## User Experience

A watershed program manager in Klamath Falls opens RiverSignal on Monday morning. The map shows her three managed sub-watersheds along the Williamson and Sprague rivers. An amber alert flags a new reed canarygrass cluster detected from weekend iNaturalist observations near a riparian restoration site. She taps the alert; the system explains that the invasive is expanding along a disturbed corridor 200m upstream of a native planting zone, recommends a sweep within the next 10 days based on seasonal growth rates, and estimates recolonization risk if untreated. She assigns the task to a field crew. On the same dashboard, a green indicator shows that native bird species richness at Agency Lake marsh increased 18% since last spring -- consistent with the system's restoration forecast from six months ago. She clicks "Generate Q1 Report" and receives a funder-ready summary with before/after species counts, intervention timeline, and outcome confidence scores. The entire session took twelve minutes.

## Target Market

| Attribute | Description |
|-----------|-------------|
| Who | **Primary**: Watershed program managers and restoration ecologists at Pacific Northwest and Utah state agencies, watershed councils, land trusts, and tribal natural resource teams managing 1-10 active restoration sites with 2-8 person field teams. **Secondary**: Fly fishing guides and serious anglers operating on rivers across 7 watersheds in Oregon, Washington, and Utah (150+ trips/year) |
| Pain | **Restoration**: Spend 15-25 hours/week synthesizing field observations, sensor data, GIS layers, and compliance records into management decisions and funder reports; junior staff lack the pattern-recognition to interpret monitoring data without senior review. **Fishing**: Check 5+ websites daily for conditions, stocking, flows; no single source combines water data + species distribution + harvest trends for a specific reach |
| Current Solution | **Restoration**: Manual expert review of iNaturalist exports, spreadsheet-based indicator tracking, GIS analyst producing static maps on request, and hand-written quarterly reports for grant funders. **Fishing**: ODFW website for stocking, USGS for flows, myodfw.com for recreation reports, word-of-mouth for fishing intel |
| Why They Switch | Federal and state restoration budgets (OWEB, NOAA, BPA) increasingly require quantified outcome evidence; senior ecologists are retiring faster than they are replaced; data volume from citizen science and sensors is growing 20-30% annually while interpretation capacity is flat. Fishing guides adopt because it replaces a fragmented daily research workflow with a single morning briefing |

## Key Value Propositions

| Value Proposition | Customer Benefit |
|-------------------|------------------|
| Ecological reasoning over raw observations | Managers receive "what these observations mean for your site" instead of data dumps -- cutting interpretation time by 40-60% |
| Restoration forecasting with confidence scores | Teams can set expectations with funders before field season begins, improving grant renewal rates |
| Automated funder/compliance reporting | Quarterly board reports that previously took 2-3 days of analyst time generate in minutes from monitored data |
| Intervention outcome memory | The system learns which restoration actions worked at which sites, building institutional knowledge that survives staff turnover |
| Invasive species early warning with spread modeling | Managers catch outbreaks weeks earlier by reasoning over observation patterns, river networks, and disturbance corridors |
| Fishing intelligence for guides and anglers | Guides get species-by-reach distribution, harvest trends, stocking alerts, and water conditions in one view -- replacing 5+ daily website checks |

## Success Definition

| Metric | Target | Measurement Method |
|--------|--------|--------------------|
| Monitoring interpretation time | 40% reduction within first field season | Time-tracking comparison: pre/post adoption weekly hours logged by watershed staff on interpretation tasks |
| Funder report generation time | From 2-3 days to under 1 hour per quarterly report | Tracked per-report generation time in RiverSignal vs. baseline interviews |
| Restoration forecast accuracy | 70%+ of seasonal species-return predictions confirmed by next monitoring cycle | Prediction vs. observation match rate across managed sites |
| Prediction model accuracy | Hatch emergence forecasts achieve 65%+ confirmation rate; catch probability scores correlate with reported catch at r > 0.5 | Model output vs. observation comparison |
| Pilot customer retention | 3 of 3 lighthouse customers renew after first year | Contract renewal tracking |
| Active managed watersheds | 10 watersheds across PNW within 24 months of launch | Customer count in billing system |

## Why Now

The 2023-2024 Klamath River dam removals -- the largest in US history -- triggered an unprecedented ecological monitoring effort with salmon returning to previously blocked habitat for the first time in a century. Simultaneously, federal climate resilience funding (IRA, BIL) is flowing to state agencies and tribes at historic levels, but these grants increasingly require quantified restoration outcome evidence that manual workflows cannot produce at scale. Multimodal LLMs can now reason over photos, audio, geospatial data, and narrative field notes in combination -- a capability that did not exist 18 months ago. The intersection of surging monitoring data, rising accountability requirements, and newly capable AI reasoning creates a narrow window to establish the intervention-outcome memory graph before competitors can accumulate the longitudinal ecological data that constitutes the durable moat.

## Review Checklist

- [x] Mission statement is specific -- names the user, the problem, and the approach
- [x] Positioning statement differentiates from the current alternative
- [x] Vision describes a desired end state, not a feature list
- [x] North star is a single measurable sentence
- [x] User experience section describes a concrete scenario, not abstract benefits
- [x] Target market identifies specific pain points and switching triggers
- [x] Value propositions map to customer benefits, not internal capabilities
- [x] Success metrics are measurable and time-bound
- [x] Why Now section names a specific change, not a vague opportunity
- [x] No implementation details (technology choices, architecture) -- those belong in design
