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

## Data Platform (Operational)

**2.2M records** from 15 public data sources across 4 Oregon watersheds:

| Table | Records | Sources |
|-------|---------|---------|
| observations | 515K | iNaturalist, BioData, OWRI, PCSRF, ODFW barriers, GBIF, NOAA, fish habitat |
| time_series | 1.46M | PRISM climate, SNOTEL snowpack/soil, USGS gauges, WQP chemistry, sport catch, stocking |
| stream_flowlines | 81K | NHDPlus HR with routing attributes |
| wetlands | 11.5K | NWI polygons with classification |
| interventions | 1,391 | OWRI + PCSRF + NOAA restoration projects (enriched with outcomes) |
| watershed_boundaries | 751 | HUC12 polygons |
| impaired_waters | 580 | EPA ATTAINS 303(d) assessments |
| fire_perimeters | 197 | MTBS 1984-2024 |

```bash
# Pull all latest data (incremental)
source .venv/bin/activate
python -m pipeline.cli ingest all --watershed all

# Check status
python -m pipeline.cli status
```

## Architecture

- **Data Layer:** 15 incremental pipelines: iNaturalist, USGS, WQP, SNOTEL, BioData, StreamNet/GBIF, MTBS fire, NHDPlus HR, OWRI/PCSRF/NOAA restoration, ODFW fish barriers, PRISM climate, fishing (sport catch, habitat, stocking), 303(d) impaired waters, NWI wetlands, WBD boundaries
- **Intelligence Layer:** Multimodal observation understanding (VLM, audio, OCR) + ecological reasoning LLM with tool-using agent architecture
- **Workflow Layer:** Site-level copilots, survey scheduling, anomaly escalation, report generation, HITL review queues
- **Interface:** Map-first workspace with site timeline, observations panel, chat pane, and action recommendations

## Technical Stack

- **Backend:** Python 3.12+ / FastAPI
- **Frontend:** React 18 / TypeScript 5.x / MapLibre GL JS / Vite 6
- **Data:** PostgreSQL 17 + PostGIS 3.6.2 (port 5433), 8 tables, Alembic migrations
- **LLM:** Anthropic Claude API (tool-using agent architecture)
- **Pipelines:** 15 ingestion adapters in `pipeline/ingest/`, CLI via `python -m pipeline.cli`

## Moat

The durable moat is **intervention outcome memory** -- over time the system learns which restoration actions worked, what indicators preceded success or failure, and region-specific ecological heuristics. This compounds into a longitudinal ecological decision graph that is very hard to replicate. With 1,391 intervention records (805 with measured outcomes) already loaded, the memory graph has a real foundation.

## Repository Structure

```
seed/                          # Original product strategy and research documents
pipeline/                      # Data ingestion platform (15 adapters)
  cli.py                       # CLI entry point
  config/watersheds.py         # 4 watershed bounding box configs
  ingest/                      # Ingestion adapters
    inaturalist.py, usgs.py, owdp.py, snotel.py, biodata.py,
    streamnet.py, mtbs.py, nhdplus.py, restoration.py,
    fish_passage.py, prism.py, spatial.py, fishing.py
  models/                      # SQLAlchemy ORM models
  db.py                        # Database connection
alembic/                       # Database migrations
docs/helix/
  00-discover/
    product-vision.md          # Mission, positioning, target market, success metrics
  01-frame/
    prd.md                     # Problem, goals, requirements (P0/P1/P2), personas, risks
    features/
      FEAT-001 through FEAT-007
  02-design/
    plan-2026-04-10.md         # Full system design plan
  parking-lot.md               # Deferred items for Phase 2 and Phase 3
```

## Documentation

- [Product Vision](docs/helix/00-discover/product-vision.md) -- north star, positioning, and success definition
- [PRD](docs/helix/01-frame/prd.md) -- full requirements, personas, acceptance tests, technical context, and risks
- [Design Plan](docs/helix/02-design/plan-2026-04-10.md) -- architecture decisions, data model, implementation plan
- [FEAT-007 Fishing Intelligence](docs/helix/01-frame/features/FEAT-007-fishing-intelligence.md) -- angler/guide use case
- [Parking Lot](docs/helix/parking-lot.md) -- deferred scope with rationale

## License

All rights reserved.
