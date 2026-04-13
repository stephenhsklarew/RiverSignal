# RiverPath Product Vision

**Tagline**: Discover the living story of rivers.

## Mission Statement

RiverPath is the AI-native field companion for families, anglers, educators, and river advocates to understand the health, ecology, and restoration story of every river they visit across the Pacific Northwest.

## Positioning

For **families, outdoor travelers, and river enthusiasts** who visit Oregon rivers for recreation, fishing, and nature education but can't answer basic questions like "Is this river healthy?" or "What fish are spawning here?",
**RiverPath** is a **location-aware mobile river guide** that transforms fragmented hydrology feeds, species data, restoration projects, and access information into living river stories.
Unlike **USGS gauge dashboards, fishing report websites, and trail apps**, RiverPath combines ecological intelligence with storytelling and stewardship -- turning every river visit into adventure, education, and conservation participation.

## Relationship to RiverSignal

RiverPath is the **B2C consumer product** built on the same data platform as RiverSignal (B2B/B2G). Both products share:

- The same PostgreSQL + PostGIS database (2.2M+ records)
- The same 15 ingestion pipelines (bronze layer)
- The same silver/gold medallion architecture (21 materialized views)
- The same LLM reasoning engine (tool-using agent with ecological knowledge)

The products differ in:

| | RiverSignal (B2B) | RiverPath (B2C) |
|---|---|---|
| **Users** | Watershed managers, ecologists, agencies | Families, anglers, educators, citizen scientists |
| **Interface** | Map-first workspace + chat + reports | Mobile-first location-aware guide + stories |
| **Value** | Reduce interpretation time, prove outcomes | Create wonder, enable stewardship, optimize trips |
| **Revenue** | Per-seat SaaS, agency licenses | Freemium subscriptions, seasonal passes |
| **Tone** | Professional, data-dense, decision-support | Storytelling, wonder-first, family-friendly |

## Vision

Every family visiting an Oregon river understands its living ecological story. A parent opens RiverPath at the McKenzie River and learns that salmon are spawning upstream right now, that the forest here burned in the Holiday Farm Fire four years ago and is recovering (species richness up 180% since), that the cold water comes from Cascade snowmelt, and that a local watershed council is planting native trees this Saturday. The kids identify caddisfly larvae on rocks. The family decides to return in September for the salmon migration. They've become river stewards without trying.

**North Star**: River visits become repeatable conservation adventures for 100,000 Pacific Northwest families.

## Target Users

### Primary: Families + Outdoor Travelers

Families already visiting Oregon rivers for swimming, camping, hiking, and scenic stops. Their unmet need: make every river stop feel alive and meaningful.

| Attribute | Description |
|-----------|-------------|
| Who | Families with kids 6-16 visiting Oregon rivers 3-10 times/year; campground users; scenic drive travelers; swimming hole seekers |
| Pain | River visits feel shallow -- "it's pretty but we don't understand what we're looking at"; kids bored after 10 minutes; no connection to ecology or conservation |
| Current Solution | Nothing integrated. Occasionally read an interpretive sign. Google "is this river safe to swim in" |
| Why They Switch | Kids engage with species photos and stories; parents feel like better educators; family develops annual river rituals |

### Secondary: Fly Fishers + River Enthusiasts

High-frequency prosumer segment (already partially served by FEAT-007).

| Attribute | Description |
|-----------|-------------|
| Who | Serious anglers fishing 30-100+ days/year on Deschutes, McKenzie, Metolius; guides running 150+ trips/year |
| Pain | Check 5+ websites daily for conditions, hatch reports, stocking, flows; no single source correlates water temp with fish activity |
| Current Solution | ODFW website, USGS, myodfw.com, word-of-mouth, years of personal experience |
| Why They Switch | Morning briefing replaces 30 minutes of scattered research; river mile species data is unavailable anywhere else; cold-water refuge maps directly improve catch rates |

### Tertiary: Educators + Citizen Scientists

| Attribute | Description |
|-----------|-------------|
| Who | Teachers running field trips, nature center docents, master naturalists, watershed council volunteers |
| Pain | No ready-made outdoor learning modules tied to real local data; citizen science feels disconnected from outcomes |
| Current Solution | Create their own materials from agency PDFs; use iNaturalist in isolation |
| Why They Switch | Real-time local data makes every field trip unique; students see their observations connected to the bigger story |

## Key Value Propositions

| Value Proposition | Customer Benefit |
|-------------------|------------------|
| Living river stories at your location | "What's happening at THIS river, RIGHT NOW" -- not generic nature content |
| Species photo gallery by river mile | Kids and adults identify what they see with CC-licensed observation photos |
| Restoration and recovery narratives | Understanding why the forest is bare (fire), why the river is cold (springs), why salmon returned (dam removal) |
| Seasonal trip optimization | When to visit for salmon migration, insect hatches, wildflower season, or swimming |
| Stewardship connection | Nearby volunteer events, watershed council links, "how to help" actions |
| Fishing intelligence | Water temp, flow, species by reach, stocking schedule, harvest trends (highest-retention feature) |

## MVP Geography: Oregon's Living Rivers Loop

| River | Miles | Story | Family Appeal |
|-------|-------|-------|--------------|
| McKenzie River | 64.6 | Holiday Farm Fire recovery + Chinook spawning + cold-water springs | Clear water, swimming holes, old growth |
| Metolius River | 41.0 | Spring-fed cold-water refuge + bull trout + pristine ecosystem | Camp Sherman, headwaters walk |
| Deschutes River | 111.6 | Canyon ecology + steelhead + thermal gradients + smallmouth bass | Bend access, family float trips |
| Upper Klamath | 102.7 (Williamson) | Dam removal + sucker recovery + tribal stewardship + lake ecology | Crater Lake proximity |
| John Day River | TBD | Wild & Scenic + rangeland ecology + fossil beds | Remote adventure, dark skies |

## Data Platform Coverage (Already Built)

The RiverSignal data platform provides **100% of the core data needs** for RiverPath's ecological intelligence:

- **2.2M records** from 15 public data sources
- **18,544 species** with CC-licensed photo URLs
- **20,248 species-by-river-mile** records for reach-level queries
- **15,080 stream segments** with river mile references
- **1,391 restoration interventions** with outcomes
- **459 fire recovery trajectories** including Holiday Farm Fire
- **120 thermal station classifications** (cold-water refuge mapping)
- **21 materialized views** in the gold layer serving all product features

## Gaps to Close for RiverPath MVP

| Gap | Priority | Approach | Status |
|-----|----------|----------|--------|
| Mobile-first UI/UX | P0 | PWA with bottom nav, GPS reach lookup, swipeable cards | **Specified** — FEAT-014, design plan 2026-04-12 |
| Family-friendly content layer | P0 | Reading mode toggle (Kids/Adult/Science) on river stories | **Specified** — FEAT-012 FR-12 |
| River access points / boat ramps | P1 | USFS RIDB API + Oregon State Parks ArcGIS FeatureServer | **Specified** — FEAT-015 (recreation ingestion) |
| Swimming/wading safety index | P1 | Derive from water temp + flow + depth data already in DB | **Implemented** — gold.swim_safety view |
| Stewardship events calendar | P1 | Manual curation initially; scraping deferred to post-MVP | **Specified** — FEAT-012 FR-40 |
| John Day River data | P1 | Add watershed config + run existing 18 pipelines | Open |
| Saved/favorites | P1 | localStorage + React context; no backend auth needed | **Specified** — FEAT-016 |
| Trail data along rivers | P2 | OpenStreetMap or USFS trail data | Parking lot |
| Dog-friendly route info | P2 | RIDB amenity flags + manual curation seed table | **Specified** — FEAT-015 FR-10 |
| Citizen science write-back | P2 | iNaturalist observation submission API | Parking lot |
| Push notifications for conditions | P2 | Alert infrastructure for flow/temp thresholds | Parking lot |

## Product Principles

1. **River wonder first** -- Lead with "what living ecological story is happening here?" not charts
2. **Stewardship by design** -- Every experience shows why the river matters, what changed, and how to help
3. **Family ritual creation** -- Annual river trips, summer hatch adventures, salmon migration weekends
4. **Science-grade truth** -- All storytelling grounded in agency datasets, watershed council records, and fisheries science

## Success Definition

| Metric | Target | Measurement |
|--------|--------|-------------|
| Families using monthly during season (May-Oct) | 10,000 within 18 months | App analytics |
| Fishing guide daily active users | 500 within 12 months | Session tracking |
| Return visits to same river | 3+ per season per active user | Location + session data |
| Stewardship actions taken | 1,000 volunteer event clicks/season | In-app tracking |
| NPS | > 60 among active families | Quarterly survey |
| Annual subscription retention | > 70% after year 1 | Billing data |

## Long-Term Ambition

RiverPath expands from Oregon's Living Rivers Loop to:
- Columbia tributaries (Willamette, Sandy, Clackamas)
- California salmon rivers (Klamath lower, Sacramento, Eel)
- Idaho spring creeks (Silver Creek, Henry's Fork)
- Montana trout rivers (Madison, Yellowstone, Missouri)
- BC salmon watersheds (Fraser, Skeena, Thompson)

Long-term: **the default operating system for living river exploration and stewardship across western North America.**

The moat: AI-generated ecological storytelling + real-time river conditions + stewardship actions -- built on the deepest intervention-outcome memory graph in watershed science.
