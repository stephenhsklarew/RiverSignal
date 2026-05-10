# Opportunity Canvas

## Problem Statement

| Aspect | Description |
|--------|-------------|
| Problem | Fragmented public data about rivers, fish, weather, geology, fossils, and restoration outcomes is locked behind agency portals, PDFs, and academic APIs. Anglers, families, and watershed managers can't easily synthesize it for a place. |
| Who | Recreational anglers, families on river trips, rockhounds, restoration ecologists, watershed councils, K–12 educators |
| Impact | Lost hours digging through agency websites; bad fishing trips on closed/depleted rivers; restoration decisions made without integrated context; kids who lose interest because the data doesn't tell a story |
| Evidence | iNaturalist has 100M+ obs but no fishing context; USGS Water Data is powerful but unusable to non-experts; no app today combines water + species + geology |

**Problem Hypothesis**: People exploring or managing watersheds need a unified, narrative-aware view of place that crosses disciplines they don't naturally bridge themselves.

## Customer Segments

| Segment | Priority | Size | Characteristics | Current Solution |
|---------|----------|------|-----------------|------------------|
| Recreational anglers (PNW/Utah) | P0 | ~3M licensed anglers | Active, mobile-first, willing to pay $20–80/yr for fishing apps | FishBrain, river-specific Facebook groups, ODFW/WDFW PDFs |
| Families on river trips | P0 | ~10M trip-takers / yr in region | Story-driven, kid-engagement matters, opportunistic users | Wikipedia, ranger pamphlets, dad-knows-best |
| Watershed restoration NGOs | P1 | ~200 PNW councils + agency partners | Need integrated analytics, restoration tracking, funder reporting | Custom GIS, Excel, in-house stats |
| Rockhounds & geo-curious | P1 | ~50k active in region | Adventure-focused, photographic | Rockd, club newsletters, road-trip guidebooks |
| K–12 educators / nature centers | P2 | ~5k regional educators | Need accurate, story-driven content for field trips | Hand-curated PDFs, museum websites |

**Early Adopters**: PNW fly-fishing community (active forums, willing to test), restoration councils we have personal contacts at, rockhounding clubs with Facebook presences.

## Unique Value

| Value Proposition | Customer Benefit | Proof Point |
|-------------------|------------------|-------------|
| One query crosses water + species + geology + restoration | Get real answers about *this place* in seconds, not hours | Production warehouse: 8.4M time-series + 1.3M observations + 50k fossils + 36k geologic units |
| AI narrative grounded in real public data | Trustworthy stories at adult/kid/expert reading levels with audio | `gold.deep_time_story` + TTS pipeline already shipping |
| Predictive intelligence (catch probability, hatch timing, etc.) | Better fishing trips, better restoration decisions | FEAT-017 — 5 production models, refreshed daily |
| Anonymous-first, optional sign-in | Use the app without losing your data; sync when you're ready | Production OAuth (Google + Apple) live |

**Elevator Pitch**: Liquid Marble unifies 30+ public scientific datasets into three apps that turn raw data into stories, predictions, and decisions about the rivers and rocks of the Pacific Northwest.

## Solution Concept

| Capability | Problem Addressed | Priority |
|------------|-------------------|----------|
| Medallion warehouse (bronze/silver/gold) reconciling 30+ sources | Data fragmentation | P0 |
| Three apps (RiverSignal/RiverPath/DeepTrail) on one backend | Audience differentiation w/o duplicating infra | P0 |
| AI narrative + audio stories | Engagement, accessibility | P0 |
| Predictive models (catch, hatch, health) | Decision support | P0 |
| Photo observations w/ public/private | User contribution + privacy | P1 |
| Saved-favorites cross-app | Personalization, retention | P1 |
| Restoration outcomes & funder reports (RiverSignal) | B2B value capture | P1 |

**NOT in Scope**: Hunting, marine/saltwater, climbing, social/community features (no comments/feed), national-scale coverage (PNW + Utah only for now).

## Key Metrics

| Metric | Type | Target | Timeline |
|--------|------|--------|----------|
| Monthly Active Users | Outcome | 10k | End Y1 |
| Sign-up conversion (anonymous → authed) | Outcome | 8% | End Y1 |
| Sessions per MAU per month | Leading | 6 | Ongoing |
| AI narrative cost per MAU | Operational | < $0.05 | Always |
| Time-to-first-value (landing → useful answer) | Leading | < 30s | Continuous |
| B2B accounts paying | Outcome | 10 | End Y2 |

**North Star Metric**: Sessions where the user successfully saved a finding (observation, fly, fossil, recreation site) — proxies the unified "found something useful here" outcome we're optimizing for across all three apps.

## Unfair Advantage

| Advantage Type | Our Position | Sustainability |
|----------------|--------------|----------------|
| Data integration depth | 30+ sources unified in medallion warehouse with provenance tracking | H — operationally hard to replicate |
| Domain breadth (water × geology) | Only platform combining both with cross-references | H — UX integration takes years to build |
| AI grounding pipeline | Retrieval over our own warehouse, not generic LLM | M — pattern is replicable but our prompts/data tuning is private |
| Founder domain expertise | Direct watershed/geology/AI experience | M — not transferable but adds quality bar |
| Production infra already deployed | Live since 2026-04, paying-customer-ready | L — table stakes |

**Honest Assessment**: We have the platform and apps shipping. We *don't* yet have a distribution moat — that has to be built via partnerships and content. We don't have the dataset network-effects of iNaturalist or the brand of OnX.

## Go/No-Go Decision

**Decision**: Go

**Rationale**: Production is live, three differentiated apps are in production with monetization paths, and the data moat is real. The remaining work is distribution + monetization, not technical risk.
