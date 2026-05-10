# Competitive Analysis

## Market Landscape

| Attribute | Assessment |
|-----------|------------|
| Market Maturity | Growing (outdoor rec post-COVID secular tailwind; AI-assisted apps emerging 2024+) |
| Growth Rate | Outdoor recreation tech ~8% / yr; watershed analytics ~12% / yr; geo-edutainment ~6% / yr |
| Key Trends | (1) AI-narrative summaries replacing static guidebooks; (2) federal/state agencies opening more APIs; (3) consolidation of fishing/hiking apps; (4) growth of citizen-science platforms (iNaturalist crossed 100M obs in 2024) |
| Entry Barriers | Medium — data ingestion + reconciliation of 30+ sources is hard; UI/UX bar is high; AI narrative quality requires careful prompting and grounding |

## Competitor Profiles

| Competitor | Positioning | Target Segment | Strengths | Weaknesses |
|------------|-------------|----------------|-----------|------------|
| **iNaturalist** | Citizen science species observations | Naturalists, educators | Massive global obs DB, free, network effects | No fishing/geology focus, no narrative AI, no localized hatch/flow predictions |
| **OnX Hunt / OnX Backcountry** | Map app for hunters/hikers | Hunters, hikers (paid, $30/yr) | Polished maps, offline tiles, large user base | No species/water-quality data, no fishing-specific intelligence, no geology |
| **FishBrain** | Social fishing app | Anglers (freemium, $79/yr Pro) | Catch logs, community, weather | Crowd-only data; no agency stocking schedules; no scientific water-quality; no restoration outcomes |
| **Riverkeeper / Waterkeeper apps** | Local water-quality alerts | Citizen advocates | Trusted brand, agency relationships | Geographic fragmentation, dated UI, no aggregated analytics |
| **Rockd / Macrostrat** | Geologic map app | Geologists, students | Authoritative geology data (we use it!) | Single-domain, no fossils-by-location, no audio narrative, no consumer polish |
| **AllTrails** | Hiking/exploration | General outdoor (paid, $35/yr) | Massive trail DB, strong brand | No water/fishing/geology depth, no scientific data |
| **Riverside (B2B watershed councils)** | Hosted GIS workspace | Restoration NGOs (custom $$$) | Domain-fit features | Expensive, slow, fragmented per-region |

**Indirect Competitors**: PDF guidebooks, regional fishing forums, ranger station chat groups, Wikipedia, Google Maps. Threat level low individually; collectively they fragment user attention.

## Feature Comparison

| Feature | Liquid Marble | iNaturalist | OnX | FishBrain | Macrostrat |
|---------|---------------|-------------|-----|-----------|------------|
| Species observations | Full (ingests iNat + agency surveys) | Full | None | Partial (catches only) | None |
| Real-time stream gauge data | Full (USGS) | None | None | Partial (weather only) | None |
| Snowpack & hydrology | Full (SNOTEL) | None | Partial | None | None |
| Hatch charts (insects) | Full (curated + iNat) | None | None | Partial | None |
| Catch probability prediction | Full (FEAT-017) | None | None | Partial | None |
| Geologic context (rocks/units) | Full (Macrostrat + DOGAMI) | None | None | None | Full |
| Fossil occurrences w/ images | Full (PBDB + iDigBio + GBIF) | None | None | None | None |
| Restoration project outcomes | Full (OWRI + NOAA + PCSRF) | None | None | None | None |
| AI narrative + audio TTS | Full (Anthropic + OpenAI) | None | None | None | None |
| User photo observations | Full (with private/public) | Full | None | Full | None |
| Anonymous-first usage | Full | Partial | None | None | Full |

**Legend**: Full ✓ | Partial ◐ | None ✗

## Differentiation Strategy

| Differentiator | Why It Matters | Defensibility |
|----------------|----------------|---------------|
| Unified medallion warehouse across 30+ sources | One query reaches species, water, geology, fire, restoration — competitors re-fetch from each provider | H — labor-intensive to replicate; we maintain reconciliation logic |
| Watershed *and* deep-time geology in same surface | Nobody else covers both axes; opens cross-domain narratives ("this fish lives where 33Ma lava cooled") | M — others *could* combine, but UX integration is genuinely hard |
| Three apps from one platform | Lower CAC across audiences; cross-app discovery; shared infra | M — strategy is replicable but operationally heavy |
| AI narrative with verifiable grounding | Audio stories + Q&A trained against the same warehouse, not generic LLM hallucination | H — our retrieval pipeline + prompt patterns are not trivial |
| Anonymous-first with optional auth | Lower friction than competitors who gate at signup | L — easy to copy, but matters culturally |

**Positioning**: For anglers, naturalists, and watershed managers who need to make sense of fragmented public data, Liquid Marble is a unified platform that translates the science into stories, predictions, and decisions. Unlike single-domain apps (FishBrain, Macrostrat), we connect water and rock; unlike agency portals, we're polished and mobile-first.

## Strategic Implications

- **Attack**: AI-narrative + audio storytelling; cross-domain (water × geology) experiences; PNW/Utah depth before national breadth.
- **Defend**: Data quality and provenance (audit trail per row); Cloud-Run-on-private-VPC ops posture; partnerships with watershed councils for distribution.
- **Avoid**: National-scale general hiking (AllTrails); social/community features (FishBrain) — keep it data-first; hunting (OnX Hunt) — adjacent but cultural mismatch.
