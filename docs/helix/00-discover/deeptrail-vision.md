# DeepTrail Product Vision

**Tagline**: Discover the ancient worlds beneath your feet.

## Mission Statement

DeepTrail is the AI-native field companion for geology, fossils, and deep-time discovery that helps families, travelers, and educators find legal public places to explore, understand what ancient world they are standing in, and turn geology into immersive adventure experiences.

## Four-Product Platform Strategy

The data platform now serves four products across two dimensions:

|  | **B2B (Professional)** | **B2C (Consumer)** |
|---|---|---|
| **Watershed Ecology** | **RiverSignal** — watershed intelligence copilot for restoration professionals, ecologists, and agencies | **RiverPath** — AI field companion for families, anglers, educators exploring living rivers |
| **Deep Time Geology** | **DeepSignal** — geologic and paleontological intelligence platform for researchers, land managers, and museums | **DeepTrail** — AI field companion for families, rockhounds, educators exploring ancient worlds |

All four products share:
- The same PostgreSQL + PostGIS data lake
- The same ingestion pipeline architecture
- The same silver/gold medallion layer
- The same LLM reasoning engine with tool functions
- The same API server (FastAPI)

They differ in:
- UI/UX (RiverSignal/DeepSignal: professional data-dense desktop-first; RiverPath/DeepTrail: story-driven mobile-first responsive)
- Tone (B2B: decision-support, reports, KPIs; B2C: storytelling, adventure, family-friendly)
- Revenue (B2B: per-seat SaaS, agency licenses; B2C: freemium subscriptions, seasonal passes)

## Deep Time × Watershed Ecology Integration

The most powerful insight: **geology IS the foundation of watershed ecology**. Every river, every species habitat, every water quality reading is shaped by the rocks beneath:

| Geologic Context | Ecological Impact |
|---|---|
| **Volcanic basalt aquifers** | Spring-fed rivers like the Metolius (constant 9.5°C from Cascade lava tubes) |
| **John Day Formation fossils** | Understanding what this ecosystem looked like 40 million years ago vs. today |
| **Cascade volcanic soils** | Nutrient-poor soils drive plant communities and insect diversity |
| **Klamath Basin lake sediments** | Cyanobacteria blooms driven by phosphorus from volcanic geology |
| **Deschutes canyon basalt** | Cold-water refuges exist where springs emerge from fractured basalt |
| **McKenzie River lava flows** | Tamolitch Blue Pool exists because the river goes underground through a lava tube |
| **Post-fire erosion geology** | Holiday Farm Fire recovery depends on soil type and slope geology |
| **Fish passage barriers** | Many barriers are natural geologic features (falls, cascades) not just culverts |

**DeepSignal** (B2B) can enhance watershed intelligence by answering:
- "Why is the Metolius so cold?" → geologic answer: Cascade volcanic aquifer
- "Why is Klamath Lake impaired?" → geologic answer: phosphorus-rich volcanic sediments
- "Where are cold-water refuges?" → geologic answer: basalt fracture springs
- "What drives post-fire recovery speed?" → geologic answer: soil parent material

**DeepTrail** (B2C) makes the same geology accessible as adventure:
- "What ancient world am I standing in?" at Painted Hills → 33-million-year-old subtropical forest
- "Why is this water so blue?" at Tamolitch → lava tube hydrology
- "Can I find fossils here?" → legal collecting sites with access info

## Public Data Sources for Geology & Paleontology

### High Priority (MVP)

| Source | Data Type | Access | Records Est. |
|---|---|---|---|
| **USGS National Geologic Map Database (NGMDB)** | Geologic unit polygons, rock types, ages, formations | ArcGIS REST service | ~50K polygons for Oregon |
| **Paleobiology Database (PBDB)** | Fossil occurrences, taxa, ages, localities worldwide | Free REST API (paleobiodb.org/data1.2) | ~5K Oregon records |
| **USGS Mineral Resources (MRDS)** | Mineral deposit locations and commodities | Free download/API | ~3K Oregon records |
| **Macrostrat** | Geologic units, columns, lithologies linked to map polygons | Free REST API (macrostrat.org/api) | Continental coverage |
| **BLM Surface Management Agency (SMA)** | Public land boundaries (BLM, USFS, NPS, state) — critical for legal collecting | ArcGIS REST service | Full Oregon coverage |
| **USGS 3DEP Elevation** | Digital elevation models for terrain context | REST tiles | Continuous coverage |
| **Oregon DOGAMI** | Oregon-specific geologic maps, hazards, landslides | ArcGIS REST / download | Statewide |

### Medium Priority (Phase 2)

| Source | Data Type | Access |
|---|---|---|
| **NPS Geologic Resources Inventory** | Park-specific geologic maps and reports | NPS Data Store |
| **iDigBio** | Digitized museum fossil specimens with photos | Free API |
| **GBIF (fossils)** | Fossil occurrence records from museums | Free API (already connected) |
| **Mindat.org** | Mineral locality database | API (requires key) |
| **Oregon State Parks** | Park boundaries, trails, facilities | Oregon GIS data |
| **USGS Earthquake Hazards** | Seismic activity, faults | Real-time API |
| **Smithsonian Volcano Database** | Volcanic history, eruption records | Free download |

### Lower Priority (Phase 3)

| Source | Data Type |
|---|---|
| **Stratigraphic Lexicon (Geolex)** | Formation names, ages, type sections |
| **USGS National Land Cover** | Land cover change over geologic time |
| **Oregon Water Well Logs** | Subsurface geology from well drilling records |
| **NASA Landsat** | Satellite-derived mineral mapping |
| **OpenTopography** | High-res lidar terrain for geologic features |

## New Database Tables (Bronze Layer)

```
geologic_units          — polygons with rock type, age, formation name, lithology
fossil_occurrences      — point locations with taxa, age, collector, museum
mineral_deposits        — point locations with commodity, deposit type
land_ownership          — polygons with agency, designation, collecting rules
geologic_columns        — stratigraphic columns linking units to time
volcanic_features       — vents, flows, calderas, lava tubes
geologic_hazards        — landslides, faults, liquefaction zones
museums_and_sites       — visitor centers, museums, interpretive sites
```

## Silver Layer Views

| View | Purpose |
|---|---|
| `silver.geologic_context` | Standardized geologic units with age (Ma), rock type, formation, lithology, joined to watershed sites |
| `silver.fossil_records` | Unified fossil occurrences from PBDB + GBIF + iDigBio with standardized taxonomy and age |
| `silver.land_access` | Public land boundaries with collecting legality rules per agency (BLM=yes with permit, NPS=no, USFS=limited, State=varies) |

## Gold Layer Views

| View | Purpose | Serves |
|---|---|---|
| `gold.geologic_age_at_location` | For any lat/lon, what geologic unit, age, and rock type is present | All 4 products |
| `gold.fossils_nearby` | Fossil occurrences within radius of a point, with museum/collection info | DeepTrail, DeepSignal |
| `gold.legal_collecting_sites` | Public lands where fossil/mineral collecting is permitted, with access info | DeepTrail |
| `gold.deep_time_story` | Narrative-ready timeline of geologic events at a location (volcanic eruptions, sea levels, fossil assemblages) | DeepTrail, DeepSignal |
| `gold.geology_watershed_link` | Joins geologic units to watershed ecology (why water chemistry is what it is, why springs emerge where they do) | RiverSignal, DeepSignal |
| `gold.volcanic_features_nearby` | Volcanic vents, flows, calderas near a location | DeepTrail |
| `gold.museum_and_site_guide` | Nearby museums, fossil beds, geologic interpretive sites | DeepTrail |
| `gold.geologic_hazards_at_location` | Landslide risk, fault proximity, seismic context | DeepSignal |
| `gold.mineral_sites_nearby` | Legal rockhounding locations with mineral types | DeepTrail |
| `gold.formation_species_history` | What species lived here in each geologic period (deep time biodiversity) | DeepTrail, DeepSignal |

## LLM Tool Functions (New)

| Function | Purpose |
|---|---|
| `get_geologic_context(lat, lon)` | Returns rock type, age, formation, and geologic history narrative for a point |
| `get_fossils_near_me(lat, lon, radius_km)` | Returns fossil occurrences with photos and museum links |
| `get_deep_time_story(lat, lon)` | Returns chronological narrative of what this location looked like in each geologic period |
| `is_collecting_legal(lat, lon)` | Returns land ownership, agency rules, and whether collecting is permitted |
| `get_geology_ecology_link(watershed)` | Explains how geology drives water chemistry, springs, fish habitat in a watershed |

## UI Architecture

### Desktop (RiverSignal + DeepSignal)
- Professional data-dense split-pane layout (existing design)
- DeepSignal adds: geologic map layer toggle, stratigraphic column panel, fossil occurrence table
- Cross-linked: clicking a geologic unit shows its ecological implications

### Mobile-First Responsive (RiverPath + DeepTrail)
- Story-driven scroll layout (existing design)
- Location-aware: "What's here?" as the primary interaction
- DeepTrail adds: geologic time slider, fossil photo cards, legal collecting status badge, museum finder
- Progressive Web App (PWA) for offline support in remote areas

### Shared Components
- Map (MapLibre) with switchable basemaps (terrain, satellite, geologic)
- Chat/Ask interface (same Claude API integration)
- Species gallery / Fossil gallery (same photo card pattern)
- Data freshness indicator
- Report generator

## MVP Geography: Oregon's Deep Time Loop

| Location | Deep Time Story | Integration with Watershed Ecology |
|---|---|---|
| **John Day Fossil Beds** | 7-44 Ma subtropical forests, savannas → arid rangeland | John Day River watershed ecology shaped by volcanic ash soils |
| **Painted Hills** | 33 Ma clay layers recording climate shifts | Erosion patterns drive modern water quality |
| **Clarno** | 44 Ma tropical forest with palms, crocodiles | Ancient vs modern species comparison |
| **Newberry Volcanic Monument** | <1 Ma obsidian flows, lava tubes | Deschutes watershed hydrology driven by volcanic aquifer |
| **Smith Rock** | 30 Ma welded tuff canyon | Deschutes/Crooked River canyon ecology |
| **Oregon Coast** | Marine fossils, tsunami deposits | Coastal ecology + geologic hazards |
| **Cascade volcanoes** | Active volcanism shaping all east-side watersheds | Spring-fed rivers, soil chemistry, fire risk |

## Success Definition

A successful DeepTrail user says:
> "We turned a normal Oregon road trip into an unforgettable prehistoric adventure."

A successful DeepSignal user says:
> "Now I understand why the water chemistry and species distribution look the way they do — it's the geology."

| Metric | Target |
|--------|--------|
| DeepTrail monthly active families (May-Oct) | 5,000 within 18 months |
| DeepSignal researcher/museum users | 200 within 12 months |
| Cross-product users (River + Deep) | 30% of active users engage both |
| Legal collecting confidence score | 90% of users report feeling confident about collecting rules |
| NPS | > 55 among active families |
