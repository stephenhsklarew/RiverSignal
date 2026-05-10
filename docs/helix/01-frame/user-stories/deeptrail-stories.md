# User Stories — DeepTrail (B2C Geology)

## FEAT-008: Geologic Context

### US-030 — Researcher queries geologic controls on water temperature
**As** Dr. Torres (geologist),
**I want** to see which geologic units underlie the McKenzie River and how they control water temperature,
**So that** I can explain to colleagues why certain reaches have spring-fed cold water.

**Acceptance Criteria:**
- Geologic units at a lat/lon are displayed with formation name, rock type, lithology, age
- Rock type badges (igneous/sedimentary/metamorphic) are color-coded
- Geology-ecology link explains how basalt aquifers create cold-water springs

---

### US-031 — Family asks "Why is this water so blue?" at Tamolitch
**As** Sarah (river-visiting family),
**I want** to ask "Why is this water so blue?" at Tamolitch Blue Pool and get a geologic explanation,
**So that** my kids understand the science behind what they're seeing.

**Acceptance Criteria:**
- Chat or story explains lava tube hydrology in accessible language
- Geologic context shows the volcanic formation at this location
- Kid-friendly reading level available

---

### US-032 — Watershed manager correlates post-fire recovery with soil type
**As** Maria (watershed program manager),
**I want** to see which geologic parent material underlies my fire-affected restoration sites,
**So that** I can understand why some sites recover faster than others.

**Acceptance Criteria:**
- Geologic units are shown for the fire-affected area
- Geology-watershed link connects rock type to soil properties
- Multiple sites can be compared by their underlying geology

---

## FEAT-009: Fossil Discovery

### US-033 — Family at Painted Hills asks "What fossils can we find here?"
**As** Rachel (road trip family),
**I want** to see what fossils have been found near the Painted Hills,
**So that** my kids can imagine what lived here millions of years ago.

**Acceptance Criteria:**
- Fossil cards show within 50km radius with taxon name, common name, period, age, distance
- Museum specimen photos displayed when available
- Phylum-based icons for fossils without photos
- Results filterable by geologic period and phylum

---

### US-034 — Rockhound plans a legal collecting trip
**As** Mike (rockhound),
**I want** to find BLM land near Fossil, Oregon where collecting is legally permitted,
**So that** I can plan a weekend trip with confidence about the rules.

**Acceptance Criteria:**
- Legal collecting status shows green/yellow/red badge
- BLM land shows "permitted for personal use" with specific rules
- Disclaimer "verify on-site with posted signs" always present
- Mineral deposit sites nearby are shown with commodity names

---

### US-035 — Teacher plans a field trip with species list by period
**As** an educator,
**I want** to see fossil species organized by geologic period at John Day Fossil Beds,
**So that** I can prepare a chronological lesson plan for my students.

**Acceptance Criteria:**
- Fossils sortable/filterable by geologic period (Eocene, Oligocene, Miocene)
- Each fossil shows taxon name, common name, and age in Ma
- PBDB source links available for further research
- Deep time timeline provides chronological context

---

## FEAT-010: Deep Time Storytelling

### US-036 — Family at Clarno asks "What lived here?"
**As** Rachel,
**I want** to tap "Ask About This Place" at Clarno and hear a vivid story of what lived here 44 million years ago,
**So that** my kids are excited about the ancient world beneath their feet.

**Acceptance Criteria:**
- LLM-generated narrative describes the Eocene tropical forest
- Narrative mentions specific fossil taxa found at this location (palms, crocodiles, dawn horses)
- Kid-friendly reading level uses relatable comparisons ("horses the size of dogs")
- "Listen to Story" plays the narrative aloud via OpenAI TTS

---

### US-037 — Geologist compares modern ecology to Eocene-era ecosystem
**As** Dr. Torres,
**I want** to see a deep time story at expert reading level for the McKenzie watershed,
**So that** I can compare the modern ecosystem to what existed here 40 million years ago.

**Acceptance Criteria:**
- Expert reading level uses proper geological and paleontological terminology
- Formation names and radiometric ages are included
- Taxonomic classifications are given at family/genus level
- Modern vs. ancient ecosystem contrast is discussed

---

## FEAT-011: Three-Product UI

### US-038 — Family on phone opens DeepTrail at Painted Hills
**As** Rachel,
**I want** to open DeepTrail on my phone at the Painted Hills and immediately see the deep time story,
**So that** I don't have to navigate a complex desktop interface.

**Acceptance Criteria:**
- DeepTrail loads in under 3 seconds on 4G
- Location picker shows "Use My Location" as the primary action
- After selecting location, story and chat are the first things visible
- All touch targets are at least 48px
- Dark theme is easy to read outdoors

---

### US-039 — Geologist uses RiverSignal's geology layer to correlate basalt units with springs
**As** Dr. Torres,
**I want** to use RiverSignal's desktop geology layer to see geologic unit polygons overlaid with spring locations,
**So that** I can identify geologic controls on hydrology.

**Acceptance Criteria:**
- Geologic unit table shows formation, rock type, lithology, period, age
- Rock type badges are color-coded
- Period chips show distribution of geologic ages in the watershed
- Multiple watersheds selectable from nav buttons

---

### US-040 — Angler on phone checks Deschutes conditions via RiverPath
**As** Alex (fishing guide),
**I want** to open RiverPath on my phone and quickly see Deschutes conditions,
**So that** I can brief my clients before we launch.

**Acceptance Criteria:**
- RiverPath home shows Deschutes as a tappable watershed block
- Tapping navigates to the dashboard with fishing brief pre-loaded
- Water temp, flow, species activity, stocking info all visible
- Works on mobile without horizontal scrolling

---

## FEAT-013: DeepTrail B2C

### US-046 — Family at Painted Hills gets deep time narrative
**As** Rachel,
**I want** to select "John Day River" on the DeepTrail pick screen and read a story about what this place looked like 33 million years ago,
**So that** our road trip stop becomes an unforgettable time-travel experience.

**Acceptance Criteria:**
- Selecting a watershed loads geology data, fossils, minerals, and legal status
- Deep time story is LLM-generated and rendered as formatted markdown
- "Listen to Story" plays natural-sounding narration (OpenAI TTS)
- Story is cached so repeat visits don't regenerate

---

### US-047 — Rockhound checks collecting legality
**As** Mike (rockhound),
**I want** to enter coordinates of a site I found on a forum and check if collecting is legal there,
**So that** I don't accidentally break the law.

**Acceptance Criteria:**
- Custom lat/lon input on the pick screen accepts any coordinates
- Legal collecting status shows with prominent green/yellow/red badge
- Agency name and specific rules are displayed
- Disclaimer about verifying on-site is always visible

---

### US-048 — Parent activates kid-friendly mode
**As** Rachel,
**I want** to tap "Kids" on the reading level toggle and have the deep time story rewritten for my 8-year-old,
**So that** the whole family can enjoy the story together.

**Acceptance Criteria:**
- Tapping "Kids" re-fetches the narrative at 5th-grade reading level
- Kid-friendly narrative uses "imagine you're standing in..." framing
- Size comparisons kids understand ("as big as a school bus")
- Story is cached per reading level

---

### US-049 — Teacher prepares geology field trip
**As** an educator,
**I want** to browse the fossil list for John Day Fossil Beds filtered by geologic period,
**So that** I can prepare a species list organized by era for my students.

**Acceptance Criteria:**
- Tapping "Fossils Found Nearby" opens the fossil list screen
- Period filter dropdown narrows results to a specific era
- Each fossil shows common name, scientific name, period, age, museum
- PBDB links allow further research
- Map shows fossil locations as pins

---

### US-050 — Family discovers Eocene tropical forest at Clarno
**As** Rachel,
**I want** to select a different watershed and see a completely different deep time story,
**So that** each stop on our road trip reveals a unique ancient world.

**Acceptance Criteria:**
- Selecting a new watershed from the pick screen loads fresh data
- Story narrative is specific to the new location's geology and fossils
- Previous location's audio stops when switching
- Loading state shows while new data fetches

---

### US-051 — Rockhound searches for thunderegg sites near Madras
**As** Mike,
**I want** to tap "Mineral Sites Nearby" and filter by commodity to find thunderegg locations,
**So that** I can plan a collecting trip to the right spot.

**Acceptance Criteria:**
- Mineral list screen shows sites with commodity names, dev status, distance
- Commodity filter dropdown includes all available mineral types
- Map shows mineral site pins with click popups
- Commodity codes are expanded to human-readable names (not abbreviations)

---

### US-052 — Geologist visualizes volcanic history of Newberry Crater
**As** Dr. Torres,
**I want** to view the deep time timeline at Newberry Volcanic Monument,
**So that** I can see the chronological sequence of volcanic events.

**Acceptance Criteria:**
- Timeline shows geologic units ordered by age (oldest at top)
- Volcanic formations (basalt flows, obsidian, tuff) are labeled with rock type
- Any fossil occurrences in the area are interleaved in the timeline
- Age in Ma is displayed for each entry

---

### US-053 — Family navigates from DeepTrail to RiverPath
**As** Rachel,
**I want** to tap a link from DeepTrail to RiverPath to understand why the Metolius River is spring-fed,
**So that** I can connect the geology story to the living river story.

**Acceptance Criteria:**
- Cross-product navigation link is visible in DeepTrail header
- Tapping "RiverPath" navigates to /path
- Context is preserved (user can navigate back)
- RiverPath explains the volcanic aquifer connection in its river story

---

## 5-Tab Navigation Stories (2026-05-08)

Source: FEAT-013 updates, alignment review AR-2026-05-08

### US-054 — Family navigates DeepTrail using bottom tabs
**As** Rachel (road trip family),
**I want** to tap between Story, Explore, Collect, Learn, and Saved tabs at the bottom of the screen,
**So that** I can easily switch between reading the deep time story, browsing fossils, checking collecting rules, taking a quiz, and reviewing my saved items.

**Acceptance Criteria:**
- 5-tab bottom navigation bar visible on all DeepTrail pages
- Active tab is visually highlighted
- Tapping a tab navigates to the corresponding page without losing location context
- Tab labels: Story, Explore, Collect, Learn, Saved

---

### US-055 — Rockhound switches watersheds via header
**As** Mike (rockhound),
**I want** to tap the location name in the DeepTrail header and switch to a different watershed,
**So that** I can compare geology and collecting sites across different locations without going back to the pick screen.

**Acceptance Criteria:**
- DeepTrailHeader shows current location name with dropdown trigger
- Tapping opens a modal with all configured watersheds
- Selecting a new watershed reloads geology, fossils, minerals, and legal status for the new location
- All 5 tabs update to reflect the new location

---

### US-056 — Family saves a fossil to view later
**As** Rachel,
**I want** to tap a save button on a fossil card in the Explore tab,
**So that** I can find it later in my Saved tab and show my kids at dinner.

**Acceptance Criteria:**
- Heart/bookmark icon on fossil cards toggles save/unsave
- Saved fossil appears in Saved tab (TrailSavedPage)
- Saved state persists across browser sessions via localStorage
- Saved item shows: taxon name, period, age, location

---

### US-057 — Family listens to the deep time story
**As** Rachel,
**I want** to tap "Listen" on the Story tab and hear the deep time narrative read aloud,
**So that** the kids can enjoy the story while we drive to our next stop.

**Acceptance Criteria:**
- "Listen to Story" button visible on TrailStoryPage
- Audio plays using OpenAI gpt-4o-audio-preview TTS
- Play/pause controls available
- Audio stops when switching to a different location
