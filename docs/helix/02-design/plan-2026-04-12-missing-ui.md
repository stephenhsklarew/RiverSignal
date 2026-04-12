# Design Plan: Missing UI Components

**Date**: 2026-04-12
**Status**: CONVERGED
**Refinement Rounds**: 4
**Scope**: UI for fish barriers, fishing alerts, seasonal planner, citation display, confidence scores

## 1. Problem Statement

Five API endpoints and LLM features have been built but lack frontend display. Users cannot see fish passage barriers on the map, receive fishing alerts, plan seasonal trips, or distinguish high-confidence from low-confidence AI outputs. This is the last mile between a working backend and a usable product.

## 2. Component Designs

### CD-1: Fish Passage Barriers Display

**Where**: RiverSignal MapPage + SitePanel Fishing tab
**Data**: GET /sites/{ws}/fishing/barriers (476 records with lat/lon, barrier_type, passage_status, stream_name)

**Map layer**: Orange triangle markers on the map for each barrier. Click shows popup with barrier name, type, passage status, and stream name. Toggled via a "Barriers" checkbox in the map KPI area.

**Fishing tab table**: Add a "Barriers" sub-section to the Fishing tab in SitePanel showing a compact table: Stream | Type | Status. Color-code status: green=passable, red=blocked, yellow=partial.

### CD-2: Fishing Alerts Banner

**Where**: RiverSignal MapPage topbar area, below the topbar
**Data**: GET /sites/{ws}/fishing/alerts (temperature anomalies, DO anomalies, stocking events)

**Design**: When a watershed is selected and has alerts, show a thin colored alert bar below the topbar:
- Warning (amber): "3 temperature anomalies detected"
- Info (blue): "12 stocking events on record, latest: 2025-03-15"

Multiple alerts stack. Dismissible with × button. Only shows when a watershed is selected.

### CD-3: Seasonal Trip Planner

**Where**: RiverPath SitePanel — new section in Overview tab after Stewardship
**Data**: GET /sites/{ws}/seasonal (peak months by taxon group + hatch chart)

**Design**: A "Best Time to Visit" card grid showing 4-6 taxon groups with their peak month:
- Fish: Peak Jun-Sep
- Birds: Peak Apr-Jun
- Insects: Peak May-Aug
- Plants: Peak May-Jul

Below: compact hatch chart showing top 10 insects by month as a mini bar chart or dot grid. Each row = species, each column = month, dot size = observation count.

### CD-4: Citation Highlights in AI Responses

**Where**: SitePanel Ask tab (chat), Summary narrative, Forecast narrative
**Data**: Already in LLM responses as text — needs visual treatment

**Design**: When the AI response contains bracketed citations like [iNaturalist #12345] or specific numbers, render them as styled inline badges. Use a regex to detect patterns like numbers with units (e.g., "2,400 species", "11.3 mg/L", "8.4°C") and wrap them in a `<span class="citation-value">` for visual emphasis (monospace, slight background highlight).

### CD-5: Confidence Score Display

**Where**: SitePanel Overview tab (after summary/forecast), Recs tab
**Data**: LLM responses include HIGH/MEDIUM/LOW confidence — parse from text

**Design**: After the narrative text in summary/forecast views, show a confidence badge:
- HIGH → green pill "High Confidence"
- MEDIUM → amber pill "Medium Confidence"  
- LOW → red pill "Low Confidence"

For recommendations, each rec card already shows the `grounded_in` tag. Add a confidence indicator if the LLM includes one.

## 3. Implementation Plan

```
U1: Fish barrier map layer + fishing tab table
U2: Fishing alerts banner on MapPage
U3: Seasonal trip planner in SitePanel
U4: Citation value highlighting in AI responses
U5: Confidence score badge display
```

All 5 are independent — no dependencies between them. Can be built in any order.

## 4. CSS Patterns

All new components use existing CSS variables from App.css (--accent, --border, --bg, --text-secondary, --mono, --warm). No new color system needed. The barrier markers reuse the MapView observation overlay pattern (GeoJSON source + circle layer). The alert bar reuses the existing `.alert-bar` CSS class.
