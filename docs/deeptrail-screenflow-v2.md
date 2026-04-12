# DeepTrail — Screen Flow v2

## Overview

3-screen mobile-first flow: Location Picker → Location Detail → Fossil/Mineral List+Map

```
Screen 1: PICK LOCATION
  ├─ Use My Location (GPS)
  ├─ Enter Lat/Lon
  └─ Pick a Curated Site
        │
        ▼
Screen 2: LOCATION DETAIL
  ├─ Location name + coords
  ├─ Ask About This Place (chat)
  ├─ Geologic Context card
  ├─ Legal Collecting Status card
  ├─ Deep Time Timeline
  ├─ Fossils Found Nearby (X) → tap to go to Screen 3a
  └─ Mineral Sites Nearby (X) → tap to go to Screen 3b
        │
        ▼
Screen 3a: FOSSIL LIST + MAP          Screen 3b: MINERAL LIST + MAP
  ├─ Map with fossil pins              ├─ Map with mineral pins
  ├─ Period / Phylum filters           ├─ Commodity filter
  └─ Scrollable card list              └─ Scrollable card list
     ├─ Photo (if available)              ├─ Commodity icon
     ├─ Taxon name                        ├─ Site name
     ├─ Phylum · Class · Museum           ├─ Commodity
     ├─ Period · Age (Ma)                 ├─ Development status
     ├─ Distance                          ├─ Distance
     └─ PBDB link                         └─ MRDS link
```

## Screen 1: Pick Your Location

```
┌──────────────────────────────────┐
│         [Logo] DeepTrail         │
│                                  │
│   Discover the Ancient Worlds    │
│     Beneath Your Feet            │
│                                  │
│  ┌────────────────────────────┐  │
│  │  📍 Use My Location        │  │
│  └────────────────────────────┘  │
│                                  │
│  ── or enter coordinates ──      │
│  ┌──────────┐ ┌──────────────┐  │
│  │ Latitude  │ │ Longitude    │  │
│  └──────────┘ └──────────────┘  │
│          [ Explore → ]           │
│                                  │
│  ── or pick a site ──            │
│                                  │
│  ┌──────────────────────────┐   │
│  │ 🏔 Painted Hills         │   │
│  │   Oligocene · 33 Ma      │   │
│  ├──────────────────────────┤   │
│  │ 🌴 Clarno                │   │
│  │   Eocene · 44 Ma         │   │
│  ├──────────────────────────┤   │
│  │ 🦴 John Day Fossil Beds  │   │
│  │   Miocene · 7-28 Ma      │   │
│  ├──────────────────────────┤   │
│  │ 🪨 Smith Rock            │   │
│  │   Oligocene · 30 Ma      │   │
│  ├──────────────────────────┤   │
│  │ 🌋 Newberry Volcanic     │   │
│  │   Pleistocene · <1 Ma    │   │
│  └──────────────────────────┘   │
│                                  │
│         [RiverPath] [DeepSignal] │
└──────────────────────────────────┘
```

## Screen 2: Location Detail

```
┌──────────────────────────────────┐
│ ← Back          DeepTrail        │
│                                  │
│ ══ Painted Hills ════════════    │
│ 44.663°N, 120.229°W             │
│ Oligocene · 33 Ma               │
│ [Adult] [Kids] [Expert]         │
│                                  │
│ ┌─ Ask About This Place ──────┐ │
│ │                              │ │
│ │ [What was here 33M yrs ago?] │ │
│ │                         [Ask]│ │
│ │                              │ │
│ │ (chat messages appear here)  │ │
│ └──────────────────────────────┘ │
│                                  │
│ ┌─ Geologic Context ──────────┐ │
│ │ [igneous] Clarno Formation   │ │
│ │ basalt · Eocene · 38-49 Ma  │ │
│ └──────────────────────────────┘ │
│                                  │
│ ┌─ Legal Collecting ──────────┐ │
│ │ 🔴 Prohibited — NPS          │ │
│ │ All collecting prohibited... │ │
│ │ ⚠ Verify on-site with signs │ │
│ └──────────────────────────────┘ │
│                                  │
│ ┌─ Deep Time Timeline ────────┐ │
│ │ ● 49 Ma  Clarno Formation   │ │
│ │ ○ 38 Ma  Mesohippus         │ │
│ │ ● 33 Ma  John Day Formation │ │
│ └──────────────────────────────┘ │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ 🦴 Fossils Found Nearby  50 →│ │
│ └──────────────────────────────┘ │
│ ┌──────────────────────────────┐ │
│ │ 💎 Mineral Sites Nearby  20 →│ │
│ └──────────────────────────────┘ │
│                                  │
└──────────────────────────────────┘
```

## Screen 3a: Fossil List + Map

```
┌──────────────────────────────────┐
│ ← Painted Hills     Fossils (50)│
│                                  │
│ ┌──────────────────────────────┐ │
│ │        [ MAP ]                │ │
│ │    pins at each fossil loc    │ │
│ │    tap pin → highlight card   │ │
│ │                       200px   │ │
│ └──────────────────────────────┘ │
│                                  │
│ [All Periods ▼] [All Phyla ▼]   │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ ┌──────┐                     │ │
│ │ │[photo]│ Mesohippus          │ │
│ │ │      │ Chordata · Mammalia  │ │
│ │ │ 80x80│ Oligocene · 33 Ma   │ │
│ │ │      │ 12.3 km · YPM       │ │
│ │ └──────┘ PBDB →               │ │
│ ├──────────────────────────────┤ │
│ │ ┌──────┐                     │ │
│ │ │ 🦴   │ Archaeotherium       │ │
│ │ │      │ Chordata · Mammalia  │ │
│ │ │ icon │ Oligocene · 28 Ma   │ │
│ │ │      │ 15.1 km              │ │
│ │ └──────┘ PBDB →               │ │
│ ├──────────────────────────────┤ │
│ │ ┌──────┐                     │ │
│ │ │[photo]│ Turritella           │ │
│ │ │      │ Mollusca · Gastropoda│ │
│ │ │      │ Eocene · 44 Ma      │ │
│ │ │      │ 22.0 km · LACM      │ │
│ │ └──────┘ PBDB →               │ │
│ └──────────────────────────────┘ │
│           (scroll)               │
└──────────────────────────────────┘
```

## Screen 3b: Mineral List + Map

```
┌──────────────────────────────────┐
│ ← Painted Hills   Minerals (20) │
│                                  │
│ ┌──────────────────────────────┐ │
│ │        [ MAP ]                │ │
│ │    pins at each mineral loc   │ │
│ │    color by commodity         │ │
│ │                       200px   │ │
│ └──────────────────────────────┘ │
│                                  │
│ [All Commodities ▼]             │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ 🥇 Iron Dike Prospect        │ │
│ │    Gold, Silver               │ │
│ │    Past Producer · 5.2 km    │ │
│ ├──────────────────────────────┤ │
│ │ 💧 Ochoco Mercury Mine       │ │
│ │    Mercury                    │ │
│ │    Past Producer · 8.7 km    │ │
│ ├──────────────────────────────┤ │
│ │ 💎 Gravel Pit                │ │
│ │    Sand, Gravel               │ │
│ │    Prospect · 12.1 km        │ │
│ └──────────────────────────────┘ │
│           (scroll)               │
└──────────────────────────────────┘
```

## Navigation Summary

```
         ┌──────────┐
    ┌────│ Landing / │────┐
    │    └──────────┘    │
    ▼                    ▼
┌────────┐         ┌──────────┐
│RiverPath│         │DeepSignal│
└────────┘         └──────────┘
    │                    │
    └───────┬────────────┘
            ▼
    ┌──────────────┐
    │ Screen 1:    │
    │ Pick Location│
    └──────┬───────┘
           │ select / GPS / lat-lon
           ▼
    ┌──────────────┐
    │ Screen 2:    │
    │ Location     │
    │ Detail       │
    ├──────┬───────┤
    │      │       │
    ▼      │       ▼
┌──────┐   │   ┌──────┐
│Fossil│   │   │Miner.│
│List  │   │   │List  │
│+Map  │   │   │+Map  │
└──┬───┘   │   └──┬───┘
   │       │      │
   └───────┼──────┘
           │ ← Back
           ▼
    ┌──────────────┐
    │ Screen 2     │
    │ (return)     │
    └──────────────┘
```
