# Design Plan: Four-Product Platform Expansion

**Date**: 2026-04-10
**Status**: CONVERGED
**Refinement Rounds**: 5
**Scope**: FEAT-008, FEAT-009, FEAT-010, FEAT-011 (Geology domain + four-product UI)
**Depends On**: plan-2026-04-10.md (RiverSignal MVP design)

## 1. Problem Statement and User Impact

The RiverSignal platform currently serves watershed ecology professionals and consumers through two products (RiverSignal B2B, RiverPath B2C) with a single React frontend that handles both personas via route-based layouts. Three critical gaps remain:

1. **Geology is invisible**: Every river, species habitat, and water quality reading is shaped by underlying geology, but the platform treats rocks as absent. A family at Tamolitch Blue Pool can't learn that the pool exists because the river flows underground through a lava tube. A researcher can't correlate basalt fracture springs with cold-water refuges.

2. **Fossils and deep time have no entry point**: Oregon has world-class fossil sites (John Day Fossil Beds, Clarno, Painted Hills) but no mobile tool combines fossil locations + legal collecting status + access information + deep-time narratives. Families standing at a fossil site cannot visualize the ancient world.

3. **The UI is a monolith**: One React app serves desktop professionals and mobile families through the same layout. B2C mobile users need touch-optimized, offline-capable, story-driven experiences. B2B users need data-dense professional dashboards. The current frontend cannot serve both well, and has no geology UI at all.

**If we don't solve it**: The platform misses the foundational insight that geology drives ecology, losing the most powerful cross-domain intelligence. Oregon's $2.3B outdoor recreation economy and 4M+ annual visitors to geologic sites have no digital companion. Families default to static interpretive signs.

**Who benefits**: Rachel (road trip family at Painted Hills), Dr. Torres (geologist correlating geology-ecology), Alex (fishing guide understanding spring-fed rivers), Senary (rockhound finding legal collecting sites), plus all existing RiverSignal/RiverPath personas who gain geologic context.

## 2. Requirements Analysis

### Functional Requirements

Derived from FEAT-008, FEAT-009, FEAT-010, FEAT-011 and the DeepTrail/DeepSignal vision documents.

**Geologic Context Layer (FEAT-008)**:
- Ingest USGS NGMDB geologic unit polygons for Oregon (unit name, age, rock type, lithology, formation description)
- Ingest Oregon DOGAMI state geologic maps where higher resolution than NGMDB
- Ingest Macrostrat geologic columns linking surface units to stratigraphic time
- Point-in-polygon lookup: for any lat/lon, return geologic unit with standardized fields (unit_name, formation, rock_type, lithology, age_min_ma, age_max_ma, period)
- Pre-join geologic units to watershed sites
- LLM tool: `get_geologic_context(lat, lon)` returns structured data + narrative
- Gold view: `gold.geology_watershed_link` correlating units with water chemistry, springs, species
- Map layer toggle for geologic unit polygons

**Fossil Discovery Layer (FEAT-009)**:
- Ingest PBDB fossil occurrences for Oregon (taxon, age, coordinates, collector, reference)
- Ingest BLM Surface Management Agency land ownership polygons (agency, designation, management status)
- Fossil search: for any lat/lon + radius, return occurrences with taxon, age, period
- Land ownership lookup: for any lat/lon, return ownership + legal collecting status
- Legal collecting rules: BLM=personal use, USFS=restricted, NPS=prohibited, State=varies, Private=prohibited
- Gold views: `gold.fossils_nearby`, `gold.legal_collecting_sites`
- LLM tools: `get_fossils_near_me(lat, lon, radius_km)`, `is_collecting_legal(lat, lon)`

**Deep Time Storytelling (FEAT-010)**:
- For any lat/lon + optional time period, generate narrative of ancient ecosystem using fossil + geologic data
- Narratives include: climate, vegetation, key animal species, geologic setting, physical evidence today
- Cite specific fossil taxa as evidence when available; use regional formation data as fallback
- Gold views: `gold.deep_time_story`, `gold.formation_species_history`
- LLM tool: `get_deep_time_story(lat, lon)` returns full narrative
- Three reading levels: expert (DeepSignal), general adult (DeepTrail), kid-friendly (DeepTrail family mode)

**Four-Product UI Architecture (FEAT-011)**:
- Four distinct entry points: `/signal`, `/path`, `/deepsignal`, `/trail`, plus `/` landing
- RiverSignal (B2B desktop-first): existing professional layout
- RiverPath (B2C mobile-first): existing story layout, enhanced for mobile
- DeepSignal (B2B desktop-first): professional geology dashboard
- DeepTrail (B2C mobile-first): adventure-focused geology stories
- Shared component library: map, chat, photo cards, data tables, KPI cards, status badges
- B2C products: PWA with service worker for offline caching
- Shared: MapLibre map (switchable basemaps), chat interface, data freshness, auth

### Non-Functional Requirements

| Requirement | Target | Source |
|-------------|--------|--------|
| Geologic unit point lookup | < 500ms | FEAT-008 |
| Fossil search within 25km radius | < 2s | FEAT-009 |
| Deep time narrative generation | < 15s (LLM call) | FEAT-010 |
| B2C mobile Lighthouse score | > 80 on mobile | FEAT-011 |
| Offline support | Previously viewed data accessible without internet | FEAT-011 |
| Responsive breakpoints | Tested at 320/375/414/768/1024/1440px | FEAT-011 |
| Accessibility | WCAG 2.1 AA on non-map elements | FEAT-011 |
| Geologic coverage | 95%+ of Oregon land area | FEAT-008 |
| Legal accuracy | BLM/USFS boundaries match published data | FEAT-009 |
| Scientific accuracy | All fossil claims traceable to PBDB/NGMDB/Macrostrat | FEAT-010 |
| Kid-friendly reading level | 5th grade for family mode | FEAT-010 |

### Constraints

- **Existing infrastructure**: Must extend, not replace, the existing PostgreSQL + PostGIS database, FastAPI backend, and React frontend
- **Geologic data volume**: Oregon NGMDB may have 50K+ polygons; spatial indexing critical
- **PBDB API**: Free but rate-limited; bulk download preferred for Oregon
- **BLM SMA data**: ArcGIS REST service; need to handle large polygon responses
- **Frontend complexity**: Four products from one codebase requires careful code splitting; cannot ship 4x bundle size
- **Offline storage**: Service worker cache limited to ~50-100MB per origin; must be selective

## 3. Architecture Decisions

### AD-9: Geology Data Storage Strategy

- **Question**: How should geologic unit polygons (50K+, complex geometries) be stored and queried?
- **Alternatives**:
  - (A) Same pattern as existing spatial tables: SQLAlchemy model + PostGIS + GiST index
  - (B) Separate schema (`geology`) to isolate geology tables from ecology tables
  - (C) Tile-based approach: pre-render geologic polygons as vector tiles for map display, keep raw data for queries
- **Chosen**: (A) Same pattern + GiST indexes, with (C) as a Phase 2 optimization
- **Rationale**: The existing spatial model pattern (PostGIS geometry, GiST index, JSONB payload) handles 81K stream flowlines and 11K wetland polygons without issues. 50K geologic polygons fits this pattern. Point-in-polygon ST_Contains queries with GiST index achieve sub-second performance at this scale. Vector tile pre-rendering can be added later if map rendering lags, but is premature for MVP.

### AD-10: Four-Product Frontend Architecture

- **Question**: How should four distinct product UIs be served from one codebase?
- **Alternatives**:
  - (A) Single React SPA with route-based code splitting: `/signal/*`, `/path/*`, `/deepsignal/*`, `/trail/*`
  - (B) Four separate React apps in a monorepo with shared component library (Turborepo/Nx)
  - (C) Micro-frontends: independent deployable frontend modules per product
  - (D) Two React apps: one for B2B (RiverSignal+DeepSignal), one for B2C (RiverPath+DeepTrail)
- **Chosen**: (A) Single SPA with route-based code splitting
- **Rationale**: The existing frontend is already a single SPA with route-based pages (`/`, `/map`, `/reports`). React Router's lazy loading + Vite's code splitting means each product only loads its own chunks. Shared components (map, chat, data tables) are in a common chunk. This avoids monorepo tooling complexity and keeps deployment simple (one build, one CDN). The B2B products share layout patterns, as do the B2C products, so the actual unique code per product is small. If bundle size becomes an issue, extraction to separate apps is straightforward because the route boundaries are clean.

### AD-11: PWA and Offline Strategy for B2C

- **Question**: How should B2C products (RiverPath, DeepTrail) work offline?
- **Alternatives**:
  - (A) Workbox service worker with cache-first for static assets + stale-while-revalidate for API data
  - (B) Full local database (IndexedDB via Dexie/idb) syncing from server
  - (C) Service worker cache only, no local database
- **Chosen**: (A) Workbox service worker + selective API caching
- **Rationale**: Users in the field need previously-viewed data without internet. Workbox provides reliable caching patterns with minimal code. Static assets use cache-first (always fast). API responses for viewed watersheds/locations use stale-while-revalidate (fast loads, background refresh). No need for a full sync engine -- the read-heavy, location-specific access pattern works well with cache. Chat/ask features are disabled offline with a clear message.

### AD-12: Deep Time Narrative Generation Architecture

- **Question**: How should deep time narratives be generated -- pre-computed or on-demand?
- **Alternatives**:
  - (A) On-demand LLM generation: every request calls Claude with geology + fossil context
  - (B) Pre-computed narratives: batch-generate stories for major sites and cache in database
  - (C) Hybrid: pre-compute for high-traffic sites, on-demand for arbitrary locations
- **Chosen**: (C) Hybrid pre-computation + on-demand
- **Rationale**: Major geologic sites (Painted Hills, Clarno, Smith Rock, Newberry) will receive most traffic. Pre-computing narratives for these eliminates LLM latency for the majority of requests. Arbitrary lat/lon requests go through on-demand generation with a 15-second budget. Generated narratives are cached in the database keyed by (geologic_unit_id, reading_level) so repeated visits to the same geologic unit don't re-generate. This bounds API costs while maintaining flexibility.

### AD-13: Geologic Map Layer Rendering

- **Question**: How should geologic unit polygons render on the MapLibre map?
- **Alternatives**:
  - (A) GeoJSON source loaded from API: fetch polygons as GeoJSON, add as MapLibre source
  - (B) Vector tiles (MVT): pre-render geologic polygons into vector tiles via PostGIS ST_AsMVT or tippecanoe
  - (C) Raster tiles: pre-render as colored raster images
- **Chosen**: (A) GeoJSON source for MVP, with (B) as Phase 2 optimization
- **Rationale**: For the Oregon-only MVP, fetching geologic polygons as GeoJSON for the visible bounding box is sufficient. MapLibre handles GeoJSON styling natively (fill-color by rock type, line by formation). The API endpoint returns polygons clipped to the viewport. If polygon count causes rendering lag at low zoom levels, vector tile pre-rendering via PostGIS `ST_AsMVT` can be added without changing the map component's rendering logic.

## 4. Interface Contracts

### New REST API Endpoints

Base URL: `/api/v1`

**Geology**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/geology/at/{lat}/{lon}` | Geologic unit at point (unit_name, formation, rock_type, lithology, age_min_ma, age_max_ma, period) |
| GET | `/geology/units` | Geologic unit polygons for bounding box (GeoJSON, for map layer) |
| GET | `/geology/watershed-link/{watershed}` | Geology-ecology correlations for a watershed |

**Fossils**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/fossils/near/{lat}/{lon}` | Fossil occurrences within radius (default 25km) |
| GET | `/fossils/by-formation/{formation}` | Fossils found in a specific geologic formation |

**Land Ownership**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/land/at/{lat}/{lon}` | Land ownership + legal collecting status at point |
| GET | `/land/collecting-sites` | Legal collecting sites within bounding box |

**Deep Time**

| Method | Path | Description |
|--------|------|-------------|
| POST | `/deep-time/story` | Generate deep time narrative for lat/lon (body: `{lat, lon, reading_level}`) |
| GET | `/deep-time/timeline/{lat}/{lon}` | Chronological geologic event timeline |

**Product Routes (Frontend)**

| Route | Product | Layout |
|-------|---------|--------|
| `/` | Landing page | Product selector |
| `/signal` | RiverSignal | B2B desktop-first (existing MapPage layout) |
| `/signal/:watershed` | RiverSignal detail | B2B with watershed pre-selected |
| `/path` | RiverPath | B2C mobile-first (existing HomePage layout) |
| `/path/:watershed` | RiverPath detail | B2C watershed story |
| `/deepsignal` | DeepSignal | B2B desktop-first geology dashboard |
| `/deepsignal/:location` | DeepSignal detail | B2B geology detail |
| `/trail` | DeepTrail | B2C mobile-first geology adventure |
| `/trail/:location` | DeepTrail detail | B2C geology story |

### New LLM Tool Definitions

```python
# Added to pipeline/tools.py

def get_geologic_context(lat: float, lon: float) -> dict:
    """Returns geologic unit, rock type, age, formation, and narrative
    for a geographic point."""
    # ST_Contains query on geologic_units table
    # Returns: unit_name, formation, rock_type, lithology,
    #          age_min_ma, age_max_ma, period, narrative

def get_fossils_near_me(lat: float, lon: float, radius_km: float = 25) -> dict:
    """Returns fossil occurrences within radius with taxa, ages,
    museum info, and photos."""
    # ST_DWithin query on fossil_occurrences table
    # Joins to land_ownership for legal status per occurrence
    # Returns: list of {taxon, common_name, age_ma, period,
    #          legal_status, museum, distance_km}

def get_deep_time_story(lat: float, lon: float) -> dict:
    """Returns chronological narrative of ancient ecosystems at location.
    Uses fossil evidence and geologic data."""
    # Checks cache in deep_time_stories table
    # If miss: assembles context from geology + fossils, calls Claude
    # Returns: {narrative, evidence_cited, reading_level, generated_at}

def is_collecting_legal(lat: float, lon: float) -> dict:
    """Returns definitive land ownership and collecting rules for a point."""
    # ST_Contains query on land_ownership table
    # Returns: {owner, agency, designation, collecting_status,
    #          collecting_rules, confidence}

def get_geology_ecology_link(watershed: str) -> dict:
    """Explains how geology drives water chemistry, springs, and fish
    habitat in a specific watershed."""
    # Queries gold.geology_watershed_link
    # Returns: {geologic_drivers: [...], spring_sources: [...],
    #          chemistry_impacts: [...]}
```

## 5. Data Model

### New Bronze Tables

```
┌──────────────────────┐     ┌──────────────────────┐
│   GeologicUnit       │     │  FossilOccurrence    │
│──────────────────────│     │──────────────────────│
│ id (uuid)            │     │ id (uuid)            │
│ site_id (fk, null)   │     │ site_id (fk, null)   │
│ source (ngmdb/dogami)│     │ source (pbdb/idigbio)│
│ source_id (varchar)  │     │ source_id (varchar)  │
│ unit_name (varchar)  │     │ taxon_name (varchar)  │
│ formation (varchar)  │     │ taxon_id (varchar)    │
│ rock_type (varchar)  │     │ common_name (varchar) │
│ lithology (varchar)  │     │ phylum (varchar)      │
│ age_min_ma (float)   │     │ class_name (varchar)  │
│ age_max_ma (float)   │     │ age_min_ma (float)    │
│ period (varchar)     │     │ age_max_ma (float)    │
│ description (text)   │     │ period (varchar)      │
│ geometry (multipolygon)│   │ location (point)      │
│ data_payload (jsonb) │     │ collector (varchar)   │
│ ingested_at (tstz)   │     │ reference (text)      │
└──────────────────────┘     │ museum (varchar)      │
                             │ data_payload (jsonb)  │
┌──────────────────────┐     │ ingested_at (tstz)    │
│   LandOwnership      │     └──────────────────────┘
│──────────────────────│
│ id (uuid)            │     ┌──────────────────────┐
│ source (blm_sma)     │     │  DeepTimeStory       │
│ source_id (varchar)  │     │──────────────────────│
│ agency (varchar)     │     │ id (uuid)            │
│ designation (varchar)│     │ geologic_unit_id(fk) │
│ admin_unit (varchar) │     │ lat (float)          │
│ collecting_status    │     │ lon (float)          │
│   (varchar)          │     │ reading_level(varchar│
│ collecting_rules     │     │ narrative (text)     │
│   (text)             │     │ evidence_cited(jsonb)│
│ geometry (multipolygon)│   │ generated_at (tstz)  │
│ data_payload (jsonb) │     │ model_version(varchar│
│ ingested_at (tstz)   │     └──────────────────────┘
└──────────────────────┘
```

### New Indexes

- `geologic_units`: GiST index on `geometry`; index on `formation`; index on `period`
- `fossil_occurrences`: GiST index on `location`; index on `period`; index on `taxon_name`
- `land_ownership`: GiST index on `geometry`; index on `agency`; index on `collecting_status`
- `deep_time_stories`: unique index on `(geologic_unit_id, reading_level)`; index on `(lat, lon)`

### New Silver Views

| View | Definition |
|------|-----------|
| `silver.geologic_context` | Standardized geologic units with age ranges normalized to Ma, rock_type enum, lithology enum, joined to nearest watershed site |
| `silver.fossil_records` | Unified fossil occurrences from PBDB with standardized taxonomy (phylum, class, order, family, genus, species), age normalized to Ma, period name |
| `silver.land_access` | Land ownership with derived collecting_status (green/yellow/red), agency rules text, nearest road access |

### New Gold Views

| View | Purpose | Key Joins |
|------|---------|-----------|
| `gold.geology_watershed_link` | Geologic units correlated with water chemistry, spring locations, species distribution per watershed | geologic_units × water_quality_monthly × species_by_reach |
| `gold.fossils_nearby` | Function-like view: fossil occurrences with taxa, ages, legal status, museum info within configurable radius | fossil_occurrences × land_ownership |
| `gold.legal_collecting_sites` | Public lands where collecting is permitted with agency rules and access info | land_ownership WHERE collecting_status IN ('permitted', 'restricted') |
| `gold.deep_time_story` | Chronological timeline of geologic events per location, assembled from units + fossils + Macrostrat columns | geologic_units × fossil_occurrences × macrostrat_columns |
| `gold.formation_species_history` | Links geologic formations to fossil taxa found within them, grouped by period | geologic_units × fossil_occurrences GROUP BY formation, period |
| `gold.geologic_age_at_location` | Simplified lookup: for any geologic unit, return age and rock type (used by all products) | geologic_units (simplified projection) |

### Medallion View Dependency Update

```
Existing (27 views) + New (9 views) = 36 total

New dependency chain:
silver.geologic_context         ← geologic_units
silver.fossil_records           ← fossil_occurrences
silver.land_access              ← land_ownership

gold.geologic_age_at_location   ← silver.geologic_context
gold.fossils_nearby             ← silver.fossil_records + silver.land_access
gold.legal_collecting_sites     ← silver.land_access
gold.deep_time_story            ← silver.geologic_context + silver.fossil_records
gold.formation_species_history  ← silver.geologic_context + silver.fossil_records
gold.geology_watershed_link     ← silver.geologic_context + gold.water_quality_monthly + gold.species_by_reach
```

## 6. Error Handling Strategy

### New Error Scenarios

| Scenario | HTTP Status | Behavior |
|----------|------------|----------|
| No geologic data for location (ocean, unmapped) | 200 | Return nearest onshore unit with `confidence: "regional"` flag |
| No fossil data within radius | 200 | Return empty list with suggestion to expand radius |
| Point on land ownership boundary (within 100m) | 200 | Return both parcels with `boundary_warning: true` |
| PBDB API unavailable during ingestion | 503 retry | Use last successful bulk download; mark source degraded |
| BLM SMA service unavailable | 503 retry | Land ownership queries still work from cached polygons |
| Deep time narrative generation timeout (>15s) | 504 | Return pre-computed narrative for geologic unit if cached; else return structured data without narrative |
| Offline mode (PWA) | N/A | Show cached data with "Last updated X ago" banner; disable chat with explanation |
| Sensitive fossil locality | 200 | Flag site but do not suppress; add "contact land manager" note |

### Legal Status Accuracy

Legal collecting status is derived from published BLM/USFS boundary data. The system:
- Always shows a disclaimer: "Verify on-site with posted signs and local regulations"
- Flags mixed-ownership boundaries (within 100m of boundary transition)
- Never states collecting is "definitely legal" -- uses "generally permitted under agency rules" language
- Updates land ownership data at least quarterly from BLM SMA service

## 7. Security Considerations

### New Attack Surfaces

| Surface | Threat | Mitigation |
|---------|--------|------------|
| Deep time narrative injection | Fossil occurrence data from PBDB could contain adversarial text in collector/reference fields | Data-quote all PBDB fields in LLM prompts; system prompt boundaries |
| Legal status misrepresentation | Stale land ownership data could misstate collecting rules | Quarterly refresh; disclaimer on all legal status responses; "last updated" timestamp |
| Service worker cache poisoning | Attacker could serve malicious cached responses | Service worker only caches same-origin API responses; HTTPS required |
| Geology data volume DoS | Requesting all geologic polygons at low zoom | Paginate polygon responses; require bounding box; max 1000 features per response |

### Data Protection (Geology-Specific)

- Fossil locality coordinates are from public PBDB data (already published)
- No sensitive fossil site coordinates are added beyond what PBDB publishes
- Land ownership boundaries are public BLM data
- Deep time narratives are generated content, not user data

## 8. Test Strategy

### New Unit Tests

| Module | What to Test |
|--------|-------------|
| Geologic unit lookup | Point-in-polygon for known Oregon locations; edge cases: water, state boundary, unmapped |
| Fossil radius search | Known PBDB locations with expected taxa; empty radius; large radius |
| Legal status derivation | BLM land → green, NPS → red, boundary proximity → warning |
| Deep time narrative cache | Cache hit, cache miss, cache invalidation on data refresh |
| Collecting rules logic | All agency combinations; private land; mixed ownership |
| PWA service worker | Cache hit/miss; stale-while-revalidate; offline fallback |

### New Integration Tests

| Scope | What to Test |
|-------|-------------|
| NGMDB ingestion → geologic_units table | Polygons stored with correct geometry and attributes |
| PBDB ingestion → fossil_occurrences table | Taxa, ages, coordinates parsed correctly |
| BLM SMA ingestion → land_ownership table | Agency boundaries stored; collecting_status derived correctly |
| Geology → LLM tools → narrative | Full pipeline: lat/lon → geologic context → tool call → narrative response |
| Four-product routing | Each product route loads correct layout; shared components work across products |
| PWA offline | Load page, go offline, verify cached data renders with staleness banner |

### New End-to-End Tests

| Scenario | Flow |
|----------|------|
| Family at Painted Hills | Open DeepTrail → location detected → see deep time story → check legal collecting status → view fossil gallery |
| Geologist correlating geology-ecology | Open DeepSignal → select McKenzie watershed → view geologic layer → see spring locations correlated with basalt fractures |
| Cross-product navigation | Start on RiverPath → click geologic feature → navigate to DeepTrail → context preserved |

## 9. Implementation Plan with Dependency Ordering

### Dependency Graph

```
Phase 7: Geology Data Foundation (Weeks 1-3)
├── 7A: GeologicUnit, FossilOccurrence, LandOwnership, DeepTimeStory models + migration
├── 7B: USGS NGMDB ingestion adapter ──depends on─→ 7A
├── 7C: Oregon DOGAMI ingestion adapter ──depends on─→ 7A
├── 7D: Macrostrat ingestion adapter ──depends on─→ 7A
├── 7E: PBDB fossil ingestion adapter ──depends on─→ 7A
├── 7F: BLM SMA land ownership adapter ──depends on─→ 7A
└── 7G: Run all geology pipelines for Oregon ──depends on─→ 7B-7F

Phase 8: Geology Medallion Layer (Weeks 3-4)
├── 8A: Silver views (geologic_context, fossil_records, land_access) ──depends on─→ 7G
├── 8B: Gold views (geology_watershed_link, fossils_nearby, legal_collecting_sites,
│       deep_time_story, formation_species_history, geologic_age_at_location)
│       ──depends on─→ 8A
└── 8C: Update medallion.py and medallion_ddl.py with new views ──depends on─→ 8B

Phase 9: Geology API + LLM Tools (Weeks 4-5)
├── 9A: Geology REST endpoints ──depends on─→ 8B
├── 9B: Fossil REST endpoints ──depends on─→ 8B
├── 9C: Land ownership REST endpoints ──depends on─→ 8B
├── 9D: Deep time story endpoint ──depends on─→ 8B
├── 9E: New LLM tool functions (5 tools) ──depends on─→ 8B
│   ├── get_geologic_context
│   ├── get_fossils_near_me
│   ├── get_deep_time_story
│   ├── is_collecting_legal
│   └── get_geology_ecology_link
└── 9F: Deep time narrative cache layer ──depends on─→ 9D, 9E

Phase 10: Four-Product UI Architecture (Weeks 5-8)
├── 10A: React Router restructure (/, /signal, /path, /deepsignal, /trail)
│        ──depends on─→ existing frontend
├── 10B: Shared component library extraction (map, chat, cards, tables)
│        ──depends on─→ 10A
├── 10C: Landing page (product selector) ──depends on─→ 10A
├── 10D: RiverSignal layout (/signal) — migrate existing MapPage
│        ──depends on─→ 10A, 10B
├── 10E: RiverPath layout (/path) — migrate existing HomePage + mobile enhancements
│        ──depends on─→ 10A, 10B
├── 10F: DeepSignal layout (/deepsignal) — new B2B geology dashboard
│        ──depends on─→ 10B, 9A, 9B
│   ├── Geologic map layer toggle
│   ├── Stratigraphic column panel
│   ├── Fossil occurrence table
│   └── Geology-ecology correlation view
├── 10G: DeepTrail layout (/trail) — new B2C geology adventure
│        ──depends on─→ 10B, 9D, 9E
│   ├── Geologic time slider
│   ├── Fossil photo cards
│   ├── Legal collecting status badges (green/yellow/red)
│   ├── Museum finder
│   └── Deep time narrative panels
└── 10H: Geologic map layer (basemap toggle: terrain/satellite/geologic)
│        ──depends on─→ 10B, 9A

Phase 11: PWA + Mobile Optimization (Weeks 7-9)
├── 11A: Workbox service worker setup ──depends on─→ 10E, 10G
├── 11B: API response caching strategy ──depends on─→ 11A
├── 11C: Offline mode UI (staleness banners, disabled chat) ──depends on─→ 11A
├── 11D: PWA manifest + install prompt ──depends on─→ 11A
├── 11E: Mobile touch optimization (48px targets, responsive breakpoints)
│        ──depends on─→ 10E, 10G
└── 11F: Lighthouse performance audit + optimization ──depends on─→ 11E

Phase 12: Integration + Polish (Weeks 9-10)
├── 12A: Cross-product navigation (RiverPath ↔ DeepTrail context transfer)
│        ──depends on─→ 10E, 10G
├── 12B: Geology test suite (unit + integration + E2E) ──depends on─→ all
├── 12C: Deep time golden example suite (domain advisor review) ──depends on─→ 9E, 9F
└── 12D: Four-product E2E test suite ──depends on─→ all
```

### Parallel Tracks

Two tracks can proceed concurrently:
- **Track C** (backend-heavy): Phases 7 → 8 → 9 (geology data → medallion → API)
- **Track D** (frontend-heavy): Phase 10 → 11 (UI restructure → PWA)

Track D begins once Phase 10A (router restructure) is done, using mock geology API responses while Track C builds the real backend. Integration in Phase 12.

### Issue Breakdown

| ID | Title | Phase | Depends On | Acceptance Criteria |
|----|-------|-------|-----------|---------------------|
| W-029 | Geology database models + migration | 7A | W-002 | GeologicUnit, FossilOccurrence, LandOwnership, DeepTimeStory tables created; GiST indexes on geometry columns |
| W-030 | USGS NGMDB ingestion adapter | 7B | W-029 | Oregon geologic polygons loaded; unit_name, formation, rock_type, lithology, age fields populated |
| W-031 | Oregon DOGAMI ingestion adapter | 7C | W-029 | Higher-resolution state maps loaded; merged with NGMDB where overlap |
| W-032 | Macrostrat ingestion adapter | 7D | W-029 | Stratigraphic columns linked to surface units; age correlations populated |
| W-033 | PBDB fossil ingestion adapter | 7E | W-029 | Oregon fossil occurrences loaded from PBDB; taxon, age, collector, reference fields populated |
| W-034 | BLM SMA land ownership adapter | 7F | W-029 | Oregon land ownership polygons loaded; agency and collecting_status derived |
| W-035 | Run geology pipelines for Oregon | 7G | W-030-034 | All geology data loaded; coverage > 95% Oregon land area; 5K+ fossil occurrences |
| W-036 | Geology silver views | 8A | W-035 | silver.geologic_context, silver.fossil_records, silver.land_access materialized and queryable |
| W-037 | Geology gold views | 8B | W-036 | All 6 new gold views created and returning correct data |
| W-038 | Update medallion refresh pipeline | 8C | W-037 | medallion.py includes new views in dependency order; refresh_all() handles 36 views |
| W-039 | Geology REST endpoints | 9A | W-037 | /geology/at, /geology/units, /geology/watershed-link return correct data; < 500ms |
| W-040 | Fossil REST endpoints | 9B | W-037 | /fossils/near, /fossils/by-formation return correct data; < 2s for 25km radius |
| W-041 | Land ownership REST endpoints | 9C | W-037 | /land/at, /land/collecting-sites return correct data with legal status |
| W-042 | Deep time story endpoint | 9D | W-037 | /deep-time/story generates narrative; /deep-time/timeline returns chronological events |
| W-043 | New LLM tool functions (5 tools) | 9E | W-037 | All 5 tools registered; return structured data; tool call traces logged |
| W-044 | Deep time narrative cache | 9F | W-042,043 | Narratives cached by (unit_id, reading_level); cache hit < 200ms; miss < 15s |
| W-045 | React Router four-product restructure | 10A | existing | Routes: /, /signal/*, /path/*, /deepsignal/*, /trail/*; lazy loading per product |
| W-046 | Shared component library | 10B | W-045 | Map, Chat, PhotoCards, DataTable, KPICard, StatusBadge extracted to shared/ |
| W-047 | Landing page | 10C | W-045 | Product selector with 4 cards; responsive; directs to correct product |
| W-048 | RiverSignal layout | 10D | W-045,046 | Existing MapPage migrated to /signal; all features preserved |
| W-049 | RiverPath layout + mobile | 10E | W-045,046 | Existing HomePage migrated to /path; 48px touch targets; responsive breakpoints |
| W-050 | DeepSignal layout | 10F | W-046,039,040 | B2B geology dashboard with map layer, stratigraphy panel, fossil table |
| W-051 | DeepTrail layout | 10G | W-046,042,043 | B2C geology adventure with time slider, fossil cards, legal badges, museum finder |
| W-052 | Geologic map layer | 10H | W-046,039 | Toggle geologic polygons on map; color-coded by rock type; tooltip on hover |
| W-053 | PWA service worker | 11A | W-049,051 | Workbox installed; static assets cached; API responses cached selectively |
| W-054 | Offline mode UI | 11C | W-053 | Staleness banners; disabled chat; clear offline indicator |
| W-055 | Mobile Lighthouse audit | 11F | W-049,051 | Score > 80 on mobile for /path and /trail |
| W-056 | Cross-product navigation | 12A | W-049,051 | RiverPath → DeepTrail with context; DeepTrail → RiverPath with context |
| W-057 | Geology test suite | 12B | all | Unit tests for all geology queries; integration tests for pipelines; E2E for all products |

## 10. Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| USGS NGMDB ArcGIS REST service is slow or rate-limited for bulk polygon download | Medium | Medium | Attempt bulk download first; if rate-limited, paginate by county/quad. Cache all polygons locally -- only need to fetch once. Fall back to Macrostrat if NGMDB is unavailable. |
| BLM SMA land ownership boundaries are stale or inaccurate at edges | Medium | High | Always show disclaimer. Flag boundary-proximity situations. Update quarterly. Never state absolute legality -- "generally permitted under published rules." |
| Deep time narratives hallucinate geologic facts | High | High | All LLM prompts include strict grounding instruction: "Only cite data provided in context. If no fossil data exists, explicitly state this." Pre-compute narratives for major sites with domain expert review. Flag narratives as "AI-generated interpretation" not "scientific fact." |
| 50K+ geologic polygons cause map rendering lag | Medium | Medium | Start with GeoJSON source (simple). If lag occurs: simplify geometries at low zoom via ST_Simplify; switch to vector tiles via PostGIS ST_AsMVT. MapLibre handles vector tiles natively. |
| PBDB has sparse fossil data for some Oregon regions | Medium | Low | Expected: ~5K Oregon records concentrated at major sites. For areas without fossil data, deep time narratives use regional formation-level data with "based on regional geology" qualifier. |
| Four-product code splitting increases frontend build time and bundle complexity | Low | Medium | Vite's built-in code splitting handles lazy routes well. Monitor bundle size per route. If any product chunk exceeds 500KB gzipped, investigate and split further. |
| PWA service worker causes stale data issues | Medium | Medium | Use stale-while-revalidate (not cache-first) for API data. Show "Last updated X ago" on all cached data. Provide manual refresh button. Cache TTL of 24 hours for API responses. |

## 11. Observability

### New Metrics

| Metric | Type | Labels |
|--------|------|--------|
| `geology_lookup_duration_seconds` | Histogram | `query_type` (point/bbox/radius) |
| `fossil_search_duration_seconds` | Histogram | `radius_km`, `result_count` |
| `deep_time_generation_seconds` | Histogram | `reading_level`, `cache_hit` |
| `product_page_views_total` | Counter | `product` (signal/path/deepsignal/trail), `platform` (desktop/mobile) |
| `pwa_cache_hit_total` | Counter | `resource_type` (api/static), `status` (hit/miss/stale) |
| `cross_product_navigation_total` | Counter | `from_product`, `to_product` |
| `legal_status_queries_total` | Counter | `collecting_status` (permitted/restricted/prohibited) |
| `geology_data_coverage_pct` | Gauge | `data_type` (units/fossils/land) |

### New Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| Geology lookup slow | p95 > 2s for 5 minutes | Warning |
| Deep time generation failures | > 3 failures in 10 minutes | Warning |
| PBDB ingestion failure | Sync fails after retry | Warning |
| BLM SMA data > 90 days stale | Last successful sync > 90 days ago | Critical |
| PWA cache > 80% full | Service worker storage estimate > 80% | Warning |

## Governing Artifacts

| Artifact | Path | Role |
|----------|------|------|
| Product Vision | `docs/helix/00-discover/product-vision.md` | Four-product platform strategy |
| RiverPath Vision | `docs/helix/00-discover/riverpath-vision.md` | B2C watershed product definition |
| DeepTrail Vision | `docs/helix/00-discover/deeptrail-vision.md` | B2C geology product definition |
| PRD | `docs/helix/01-frame/prd.md` | Authority for all requirements |
| FEAT-008 | `docs/helix/01-frame/features/FEAT-008-geologic-context.md` | Geologic context layer |
| FEAT-009 | `docs/helix/01-frame/features/FEAT-009-fossil-discovery.md` | Fossil discovery layer |
| FEAT-010 | `docs/helix/01-frame/features/FEAT-010-deep-time-storytelling.md` | Deep time storytelling |
| FEAT-011 | `docs/helix/01-frame/features/FEAT-011-four-product-ui.md` | Four-product UI architecture |
| MVP Design | `docs/helix/02-design/plan-2026-04-10.md` | Original MVP architecture decisions |
