# User Stories — RiverPath (B2C Watershed)

## FEAT-012: RiverPath B2C

### US-040 — Family sees fire recovery story at McKenzie
**As** Sarah (river-visiting family),
**I want** to open RiverPath at the McKenzie River and see the Holiday Farm Fire recovery story with before/after species richness,
**So that** my kids understand why the forest looks burned and that it's coming back.

**Acceptance Criteria:**
- McKenzie watershed block shows fire recovery narrative
- Species richness increase since 2020 is displayed with specific numbers
- Health score is visible
- Photo shows the McKenzie River landscape

---

### US-041 — Angler searches steelhead observations on map
**As** Alex (fishing guide),
**I want** to search "steelhead" on the Deschutes and see every observation pinned on the map,
**So that** I know which reaches have the most fish activity.

**Acceptance Criteria:**
- Observation search returns steelhead observations as orange map pins
- Each pin shows a popup with taxon name, date, and photo (if available)
- Count badge shows total matches (e.g., "252 found")
- Search handles plural variations (steelhead/steelheads)

---

### US-042 — Guide opens morning brief before Deschutes trip
**As** Alex,
**I want** to open the Deschutes fishing brief and get conditions, species, and stocking in one view,
**So that** I can brief my clients in 2 minutes instead of checking 5 websites.

**Acceptance Criteria:**
- Fishing tab shows: water temp, flow, steelhead harvest, trout stocked
- Recent stocking table shows waterbody, fish count, date
- Species by reach table shows what's present and where
- Fish passage barriers listed with passage status

---

### US-043 — Parent plans September salmon trip
**As** Sarah,
**I want** to check when salmon spawn on the McKenzie River,
**So that** I can plan a family trip to see the migration.

**Acceptance Criteria:**
- Seasonal planner shows peak month for fish (e.g., "Peak: Sep")
- Hatch chart shows insect activity by month
- Species gallery shows salmon with photos and observation dates
- Information is accessible from the Overview tab

---

### US-044 — Teacher preps field trip with species checklist
**As** an educator,
**I want** to browse the species gallery for the Deschutes filtered by taxonomic group,
**So that** I can create a checklist of fish, birds, and insects for my students to find.

**Acceptance Criteria:**
- Species tab shows photo cards with common name, scientific name, conservation status
- Gallery is filterable by taxonomic group
- At least 30 species displayed per watershed
- Photos are CC-licensed from iNaturalist

---

### US-045 — Family discovers volunteer event at swimming hole
**As** Sarah,
**I want** to see nearby volunteer events and restoration projects when visiting a river,
**So that** my family can participate in stewardship.

**Acceptance Criteria:**
- Stewardship section in Overview tab shows restoration projects with year and name
- Watershed council contact information or link is suggested
- "How to help" framing connects projects to the river's recovery story

---

## Wireframe-Driven Stories (2026-04-12)

Source: `riverpath_mobile_web_mvp_features_v2.md`, `riverpath_wireframe_screen_map.md`

### US-046 — Family opens River Now via GPS and sees hero card
**As** Sarah (river-visiting family),
**I want** to open RiverPath at my current location and instantly see what river I'm near with current conditions,
**So that** I can decide what to do without searching or navigating.

**Acceptance Criteria:**
- GPS resolves to nearest watershed and reach in under 3 seconds
- Hero card displays: river name, water temperature, flow trend (rising/falling/stable), hatch confidence (high/medium/low)
- If GPS is denied or unavailable, a watershed picker appears as fallback
- Hero card is visible without scrolling on a 375px-wide screen

---

### US-047 — Angler checks hatch confidence and matching flies
**As** Alex (fishing guide),
**I want** to see the top 3 most likely aquatic insects with confidence levels and matching fly patterns,
**So that** I can match the hatch without guessing.

**Acceptance Criteria:**
- Hatch tab shows top 3 insects ranked by confidence (high/medium/low)
- Each insect card shows: photo, common name, lifecycle stage (nymph/emerger/adult), suggested fly pattern
- Matching fly cards below show: pattern name, hook size, fly type, time of day, water type
- Confidence is derived from observation frequency + current water temp + seasonal patterns
- Time horizon is "this month / next month" (not hourly)

---

### US-048 — Angler views cold-water refuge map to find holding water
**As** Alex (fishing guide),
**I want** to see cold-water refuges and thermal stress zones on the map,
**So that** I can target reaches where fish are holding in summer.

**Acceptance Criteria:**
- Fish + Refuge drilldown shows MapLibre map with thermal station overlay
- Stations color-coded: blue=cold refuge, teal=cool, amber=warm, red=thermal stress
- Refuge cards below map explain: why cold-water refuges matter, which species depend on them, current thermal status
- Fish carousel shows species with preferred temperature range compared to current water temp
- Trout cards are color-coded: green=in range, amber=marginal, red=stress

---

### US-049 — Parent switches river story to Kids reading mode
**As** Sarah (river-visiting family),
**I want** to switch the river story to a kid-friendly reading level,
**So that** my 7-year-old can understand and engage with the ecological narrative.

**Acceptance Criteria:**
- Reading mode toggle visible on story view with three options: Kids, Adult, Science
- Kids mode uses 5th-grade vocabulary, shorter sentences, "imagine you're standing in..." framing
- Adult mode is the default narrative style
- Science mode adds technical citations, data references, and measurement units
- Toggle persists during the session (does not reset on scroll or tab switch)

---

### US-050 — Family finds campground near Metolius
**As** Sarah (river-visiting family),
**I want** to find campgrounds, trailheads, and day-use areas near the Metolius River,
**So that** I can plan where to stay and what to explore.

**Acceptance Criteria:**
- Explore tab shows recreation sites as adventure cards sorted by distance
- Cards display: name, type badge (campground/trailhead/boat ramp/day use), distance, amenity icons
- Map/list toggle allows switching between map pins and card list
- Tapping a card shows expanded details with amenities and a link to source (Recreation.gov)

---

### US-051 — Angler finds boat ramp on Deschutes
**As** Alex (fishing guide),
**I want** to find the nearest boat ramp on the Deschutes for a float trip,
**So that** I can plan put-in and take-out logistics.

**Acceptance Criteria:**
- Explore tab filtered by "Fishing" shows boat ramps and fishing access points
- Cards include type "boat_ramp" with distance and amenities (parking, restrooms)
- Map view shows boat ramp pins in blue

---

### US-052 — Parent filters for dog-friendly access
**As** Sarah (river-visiting family),
**I want** to filter Explore results by "Dogs" to find places our dog is welcome,
**So that** we don't show up somewhere and have to leave.

**Acceptance Criteria:**
- "Dogs" filter chip on Explore page filters to sites where pets_allowed is true
- Adventure cards show a dog-friendly badge when pets are allowed
- If no dog-friendly sites match, empty state suggests removing the filter

---

### US-053 — Family saves campground for trip planning
**As** Sarah (river-visiting family),
**I want** to save a campground from the Explore tab so I can find it later when planning our trip,
**So that** I don't lose track of places I want to visit.

**Acceptance Criteria:**
- Heart icon on adventure cards toggles save/unsave with visual feedback
- Saved campground appears in Saved tab under "Saved Adventures"
- Saved item shows: name, type, watershed, date saved
- Saved data persists across browser sessions (localStorage)

---

### US-054 — Angler saves fly pattern that worked
**As** Alex (fishing guide),
**I want** to save a fly recommendation from the Hatch tab,
**So that** I can quickly find patterns that work on this river.

**Acceptance Criteria:**
- Heart icon on fly recommendation cards toggles save/unsave
- Saved fly appears in Saved tab under "Saved Flies"
- Saved item shows: pattern name, hook size, fly type, watershed
- Multiple fly patterns can be saved across different watersheds

---

### US-055 — Steward saves restoration project
**As** a river advocate,
**I want** to save a restoration project from the Steward tab,
**So that** I can follow its progress and share it with others.

**Acceptance Criteria:**
- Save button on restoration outcome cards bookmarks the project
- Saved project appears in Saved tab under "Saved Projects"
- Share CTA on stewardship cards copies a link or opens native share dialog

---

### US-056 — Steward shares restoration outcome
**As** a river advocate,
**I want** to share a restoration outcome card showing before/after species counts,
**So that** I can show others the impact of watershed restoration work.

**Acceptance Criteria:**
- Share button on restoration outcome cards triggers native Web Share API (if available) or copies a link to clipboard
- Shared content includes: project name, watershed, before/after species counts
- Fallback on desktop: "Link copied to clipboard" toast

---

### US-057 — Guide swipes through condition cards on River Now
**As** Alex (fishing guide),
**I want** to swipe through Fish, Bugs, and Refuge condition cards on the River Now screen,
**So that** I can quickly assess conditions for my morning trip.

**Acceptance Criteria:**
- Three horizontal swipeable cards below the hero: Fish Activity, Insect Activity, Refuge Status
- Fish card shows: species currently active, preferred temp ranges
- Insect card shows: current hatch species, confidence level
- Refuge card shows: cold-water refuge status, thermal classification
- Swipe gesture works on touch; arrow buttons appear on desktop

---

### US-058 — Family asks inline question on homepage
**As** Sarah (river-visiting family),
**I want** to type a question about the McKenzie on the homepage and see the answer right there,
**So that** I don't get sent to a different product or lose my place.

**Acceptance Criteria:**
- Ask input on each watershed block submits the question within RiverPath (/path context)
- Chat response renders as markdown inline below the watershed block
- Page auto-scrolls to the target watershed when the response loads
- Placeholder text is consumer-oriented (e.g., "Is today a good day to fly fish the McKenzie?")
- Question param is cleared from URL after the response loads
