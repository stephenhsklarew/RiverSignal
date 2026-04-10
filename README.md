# RiverSignal

AI-native biodiversity intelligence copilot for watershed restoration, land management, and conservation decisions.

## Overview

RiverSignal transforms fragmented ecological data into actionable management recommendations. It combines multimodal LLMs with ecological reasoning to bridge the gap between data collection and expert interpretation at operational speed.

**The core pain:** people can collect nature data faster than they can interpret it -- and that gap is widening with drones, edge sensors, acoustics, and citizen science feeds.

**The differentiation:** reasoning, not retrieval. The output isn't "here are 400 observations" -- it's "here's what these observations imply for management."

## Target Users

**Professional users:** restoration ecologists, watershed managers, land trusts, state fish & wildlife agencies, tribal natural resource teams, environmental consultants, invasive species specialists

**Enterprise buyers:** utilities (vegetation/wildfire), insurers (nature-risk underwriting), water districts, renewable energy developers, ESG/sustainability teams

## MVP Focus: Watershed Restoration Intelligence

The initial product targets **Pacific Northwest salmon and watershed restoration** with a focus on publicly accessible datasets and the Upper Klamath basin as the flagship watershed.

### Priority Watersheds

| Watershed | Wedge | Best First Buyer |
|---|---|---|
| Upper Klamath | Salmon return + dam removal reasoning | Agencies / Tribes |
| McKenzie River | Drinking water resilience + wildfire recovery | Utilities / Councils |
| Deschutes River | Flow + cold-water habitat intelligence | Utilities / Fish habitat |
| Metolius River | Salmonid habitat precision | Conservation / Science |

### P0 Features

| Feature | Description | Key Metric |
|---------|-------------|------------|
| [Observation Interpretation](docs/helix/01-frame/features/FEAT-001-observation-interpretation.md) | Synthesize iNaturalist, hydrology, and water quality data into site-level ecological summaries with anomaly detection | <10% outputs needing expert correction |
| [Restoration Forecasting](docs/helix/01-frame/features/FEAT-002-restoration-forecasting.md) | Predict species returns and habitat changes with confidence scores, tracked against actuals | 70%+ prediction accuracy |
| [Management Recommendations](docs/helix/01-frame/features/FEAT-003-management-recommendations.md) | Prioritized field actions grounded in observations, seasonal context, and restoration goals | <25% dismissal rate |
| [Funder Report Generation](docs/helix/01-frame/features/FEAT-004-funder-report-generation.md) | Auto-generate OWEB-format quarterly reports from monitored data | <5 min generation (from 2-3 days) |
| [Data Ingestion Pipeline](docs/helix/01-frame/features/FEAT-005-data-ingestion-pipeline.md) | Daily sync from iNaturalist, USGS, Oregon Water Data Portal + manual CSV/PDF/GeoJSON upload | 99% sync success rate |
| [Map-First Workspace](docs/helix/01-frame/features/FEAT-006-map-workspace.md) | Interactive map with site health indicators, observation overlays, detail panels, and natural-language chat | <15 min daily check-in |

## Architecture

- **Data Layer:** iNaturalist API, USGS stream gauges, Oregon Water Data Portal, watershed GIS layers, intervention logs
- **Intelligence Layer:** Multimodal observation understanding (VLM, audio, OCR) + ecological reasoning LLM with tool-using agent architecture
- **Workflow Layer:** Site-level copilots, survey scheduling, anomaly escalation, report generation, HITL review queues
- **Interface:** Map-first workspace with site timeline, observations panel, chat pane, and action recommendations

## Technical Stack

- **Backend:** Python 3.12+ / FastAPI, Node.js for real-time workspace API
- **Frontend:** React 18 / TypeScript 5.x / MapLibre GL JS / Vite 6
- **Data:** PostgreSQL 16 + PostGIS + TimescaleDB, S3-compatible object store
- **LLM:** Anthropic Claude API (tool-using agent architecture)

## Moat

The durable moat is **intervention outcome memory** -- over time the system learns which restoration actions worked, what indicators preceded success or failure, and region-specific ecological heuristics. This compounds into a longitudinal ecological decision graph that is very hard to replicate.

## Repository Structure

```
seed/                          # Original product strategy and research documents
docs/helix/
  00-discover/
    product-vision.md          # Mission, positioning, target market, success metrics
  01-frame/
    prd.md                     # Problem, goals, requirements (P0/P1/P2), personas, risks
    features/
      FEAT-001-observation-interpretation.md
      FEAT-002-restoration-forecasting.md
      FEAT-003-management-recommendations.md
      FEAT-004-funder-report-generation.md
      FEAT-005-data-ingestion-pipeline.md
      FEAT-006-map-workspace.md
  parking-lot.md               # Deferred items for Phase 2 and Phase 3
```

## Documentation

- [Product Vision](docs/helix/00-discover/product-vision.md) -- north star, positioning, and success definition
- [PRD](docs/helix/01-frame/prd.md) -- full requirements, personas, acceptance tests, technical context, and risks
- [Parking Lot](docs/helix/parking-lot.md) -- deferred scope with rationale

## License

All rights reserved.
