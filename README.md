# RiverSignal

AI-native biodiversity intelligence copilot for watershed restoration, land management, and conservation decisions.

## Overview

RiverSignal (working name: EcoPilot) transforms fragmented ecological data into actionable management recommendations. It combines multimodal LLMs with ecological reasoning to bridge the gap between data collection and expert interpretation at operational speed.

### The Problem

Organizations managing land and natural assets are overwhelmed by biodiversity observations, monitoring data, invasive alerts, sensor feeds, GIS layers, and compliance reporting. **People can collect nature data faster than they can interpret it** -- and that gap is widening with drones, edge sensors, acoustics, and citizen science feeds.

### The Solution

RiverSignal reasons over iNaturalist observations, photos, soundscapes, geospatial layers, climate data, and intervention history to produce:

- Risk assessments and anomaly alerts
- Management recommendations
- Restoration forecasts
- Explainable compliance and funder reports
- Monitoring workflows

The differentiation is **reasoning, not retrieval**. The output isn't "here are 400 observations" -- it's "here's what these observations imply for management."

## Target Users

**Professional users:** restoration ecologists, land trusts, conservation NGOs, state fish & wildlife agencies, watershed managers, environmental consultants, tribal natural resource teams, invasive species specialists

**Enterprise buyers:** utilities (vegetation/wildfire), insurers (nature-risk underwriting), water districts, renewable energy developers, ESG/sustainability teams

## MVP Focus: Watershed Restoration Intelligence

The initial product targets **Pacific Northwest salmon and watershed restoration** with a focus on publicly accessible datasets.

### Priority Watersheds

| Watershed | Wedge | Best First Buyer |
|---|---|---|
| Upper Klamath | Salmon return + dam removal reasoning | Agencies / Tribes |
| McKenzie River | Drinking water resilience + wildfire recovery | Utilities / Councils |
| Deschutes River | Flow + cold-water habitat intelligence | Utilities / Fish habitat |
| Metolius River | Salmonid habitat precision | Conservation / Science |

### Core MVP Capabilities

1. **Observation Interpretation** -- species richness deltas, invasive emergence, indicator species return, phenology shifts, anomaly alerts
2. **Restoration Forecasting** -- likely flora/fauna progression, missing indicators, succession risks, confidence scoring
3. **Management Recommendations** -- prioritized field actions by site and season
4. **Grant/Compliance Reporting** -- auto-generated funder progress summaries, before/after ecological narratives, outcome KPI snapshots

## Architecture

- **Data Layer:** iNaturalist API, USGS stream gauges, weather/wildfire feeds, watershed GIS layers, intervention logs
- **Intelligence Layer:** Multimodal observation understanding (VLM, audio, OCR) + ecological reasoning LLM with tool-using agent architecture
- **Workflow Layer:** Site-level copilots, survey scheduling, anomaly escalation, report generation, HITL review queues
- **Interface:** Map-first workspace with site timeline, observations panel, chat pane, and action recommendations

## Moat

The durable moat is **intervention outcome memory** -- over time the system learns which restoration actions worked, what indicators preceded success or failure, and region-specific ecological heuristics. This compounds into a longitudinal ecological decision graph that is very hard to replicate.

## Repository Structure

```
seed/          # Original product strategy and research documents
```

## License

All rights reserved.
