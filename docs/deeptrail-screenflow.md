# DeepTrail — Screen Flow & Navigation

## Entry Points

```
Landing Page (/)
  └─ Click "DeepTrail" card ─→ /trail

RiverPath (/path)
  └─ Footer "Explore DeepTrail" link ─→ /trail

DeepSignal (/deepsignal)
  └─ Header "DeepTrail" link ─→ /trail

Direct URL: /trail or /trail/:location
```

## Screen Layout

DeepTrail is a **single scrolling page** (no tabs, no side panel). Dark theme (#1a1612 background). All content loads for one location at a time.

```
┌──────────────────────────────────────────────────┐
│ HEADER                                           │
│ [Logo] [DeepTrail badge]         [RiverPath link]│
│                                  [DeepSignal link]│
│                                                  │
│ "Discover the Ancient Worlds Beneath Your Feet"  │
├──────────────────────────────────────────────────┤
│ LOCATION SELECTOR (horizontal scroll)            │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │Painted│ │Clarno│ │John  │ │Smith │ │Newber│   │
│ │Hills ▪│ │      │ │Day   │ │Rock  │ │ry    │   │
│ │33 Ma  │ │44 Ma │ │7-28Ma│ │30 Ma │ │<1 Ma │   │
│ └──────┘ └──────┘ └──────┘ └──────┘ └──────┘   │
│                              [Lat] [Lon] [Go]    │
├──────────────────────────────────────────────────┤
│                                                  │
│ ┌─ STORY CARD ─────────────────── [Adult|Kids|Ex]│
│ │ Painted Hills                                  │
│ │ Oligocene — 33 Ma                              │
│ │ Subtropical forest with towering redwoods...   │
│ └────────────────────────────────────────────────│
│                                                  │
│ ┌─ GEOLOGIC CONTEXT ────────────────────────────│
│ │ [igneous] Clarno Formation                     │
│ │           basalt · Eocene · 38-49 Ma           │
│ │ [sedimentary] John Day Formation               │
│ │               tuff · Oligocene · 28-33 Ma      │
│ └────────────────────────────────────────────────│
│                                                  │
│ ┌─ LEGAL COLLECTING STATUS ─────────────────────│
│ │ ● Collecting: prohibited — NPS                 │
│ │   All fossil, mineral, and rock collecting is  │
│ │   prohibited in National Park Service areas.   │
│ │   Always verify on-site with posted signs.     │
│ └────────────────────────────────────────────────│
│                                                  │
│ ┌─ DEEP TIME TIMELINE ──────────────────────────│
│ │ ● 49.85 Ma  Clarno Formation                  │
│ │             igneous — Eocene                   │
│ │ ○ 38.6 Ma   Mesohippus                        │
│ │             Chordata — Oligocene               │
│ │ ● 33.0 Ma   John Day Formation                │
│ │             sedimentary — Oligocene            │
│ │ ○ 28.0 Ma   Archaeotherium                    │
│ │             Chordata — Oligocene               │
│ │ (● = geologic unit, ○ = fossil)               │
│ └────────────────────────────────────────────────│
│                                                  │
│ ┌─ FOSSILS FOUND NEARBY (50) ───────────────────│
│ │ [All Periods ▼] [All Phyla ▼]                  │
│ │ ┌────────┐ ┌────────┐ ┌────────┐              │
│ │ │ [photo]│ │ 🦴     │ │ 🐚     │              │
│ │ │Mesohip.│ │Archae..│ │Turrite.│              │
│ │ │Chordata│ │Chordata│ │Mollusca│              │
│ │ │Oligo.. │ │Oligo.. │ │Eocene  │              │
│ │ │12.3 km │ │15.1 km │ │22.0 km │              │
│ │ │PBDB →  │ │PBDB →  │ │PBDB →  │              │
│ │ └────────┘ └────────┘ └────────┘              │
│ └────────────────────────────────────────────────│
│                                                  │
│ ┌─ MINERAL SITES NEARBY (20) ───────────────────│
│ │ [All Commodities ▼]                            │
│ │ ┌────────┐ ┌────────┐ ┌────────┐              │
│ │ │ 🥇     │ │ 💧     │ │ 💎     │              │
│ │ │Gold Hl │ │Mercury │ │Agate P │              │
│ │ │Gold    │ │Mercury │ │Agate   │              │
│ │ │Prospect│ │Past Pr.│ │Prospect│              │
│ │ │5.2 km  │ │8.7 km  │ │12.1 km │              │
│ │ └────────┘ └────────┘ └────────┘              │
│ └────────────────────────────────────────────────│
│                                                  │
│ ┌─ ASK ABOUT THIS PLACE ───────────────────────│
│ │ [user] What was this place like 33M years ago? │
│ │ [bot]  You're standing in what was once a...   │
│ │                                                │
│ │ [What minerals can I find here?______] [Ask]   │
│ └────────────────────────────────────────────────│
│                                                  │
└──────────────────────────────────────────────────┘
```

## User Interactions

### 1. Select a Location
- **Click a curated location card** → reloads all sections for that location
- **Enter custom lat/lon + click Go** → creates a custom location, loads data for those coordinates
- Active card gets amber border highlight

### 2. Reading Level Toggle
- Three buttons on story card: **Adult** (default), **Kids**, **Expert**
- Clicking changes the `readingLevel` state
- Currently changes active button styling; future: re-fetches narrative from LLM at new reading level

### 3. Browse Fossils
- **Period filter dropdown** → filters fossil cards (e.g., only Eocene)
- **Phylum filter dropdown** → filters by organism type (e.g., only Mollusca)
- Both filters combine; count updates in section header
- Cards show museum specimen photos (154 with images) or phylum emoji icons
- **PBDB → link** opens Paleobiology Database record in new tab

### 4. Browse Minerals
- **Commodity filter dropdown** → filters by Gold, Silver, Mercury, etc.
- Cards show commodity emoji icons (🥇 gold, 🥈 silver, etc.)

### 5. Chat
- Type a question → sends to `/deep-time/story` endpoint with location context
- Response appears as chat bubble
- Examples: "What was this place like 33 million years ago?", "Can I collect fossils here?"

### 6. Cross-Product Navigation
- **Header → RiverPath** link: goes to `/path` (river stories)
- **Header → DeepSignal** link: goes to `/deepsignal` (professional geology dashboard)
- **Header → Logo**: goes to `/` (landing page)

## Data Sources Per Section

| Section | API Endpoint | Data Source |
|---------|-------------|-------------|
| Story Card | Hardcoded in LOCATIONS array | Static (future: `/deep-time/story` LLM) |
| Geologic Context | `GET /geology/at/{lat}/{lon}` | geologic_units (DOGAMI + Macrostrat) |
| Legal Status | `GET /land/at/{lat}/{lon}` | Real-time BLM SMA API query |
| Timeline | `GET /deep-time/timeline/{lat}/{lon}` | geologic_units + fossil_occurrences |
| Fossils | `GET /fossils/near/{lat}/{lon}?radius_km=50` | fossil_occurrences (PBDB + iDigBio) |
| Minerals | `GET /minerals/near/{lat}/{lon}?radius_km=50` | mineral_deposits (USGS MRDS) |
| Chat | `POST /deep-time/story` | LLM + geologic_units + fossil_occurrences |

## What's NOT Built Yet

| Gap | FEAT-013 Ref | Status |
|-----|-------------|--------|
| LLM-generated story (currently hardcoded text) | FR-1 | API exists, not wired to story card |
| Kid-friendly narrative (toggle is visual only) | FR-2 | Toggle changes state but doesn't re-fetch |
| Boundary proximity warning (within 100m) | FR-13 | Not implemented in API |
| Map showing fossil/mineral locations | AD-15 | Design says compact map; not built |
| Offline/PWA for remote areas | FR-offline | Service worker registered but untested |
