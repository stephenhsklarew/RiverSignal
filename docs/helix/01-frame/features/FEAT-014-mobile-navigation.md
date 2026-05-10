---
dun:
  id: FEAT-014
  depends_on:
    - helix.prd
    - FEAT-012
---
# Feature Specification: FEAT-014 — RiverPath Mobile Navigation Architecture

**Feature ID**: FEAT-014
**Status**: Draft
**Priority**: P0
**Owner**: Core Engineering

## Overview

RiverPath requires a purpose-built mobile navigation model to support the wireframe's 5-tab bottom navigation (River Now / Explore / Hatch / Steward / Saved), GPS-first reach lookup, and one-handed scrolling UX. The current product-level picker (RiverSignal / RiverPath / RiverSignal geology layer / DeepTrail) does not provide in-product navigation for RiverPath's screen architecture. This feature establishes the navigation shell, route structure, shared UI patterns, and responsive layout that all other RiverPath screens depend on.

## Problem Statement

- **Current situation**: RiverPath reuses RiverSignal's top navigation and SitePanel tabbed layout. Navigation between RiverPath screens requires the SitePanel tab bar, which was designed for desktop sidebar use. There is no bottom navigation, no GPS locate button, and no mobile-first screen architecture.
- **Pain points**: Users cannot navigate between River Now, Explore, Hatch, Steward, and Saved with a single tap. The product picker consumes screen real estate on mobile without adding in-product value. GPS reach resolution requires navigating to DeepTrail.
- **Desired outcome**: On `/path/*` routes, a fixed bottom tab bar provides single-tap access to all 5 RiverPath screens. A floating GPS button resolves the user's location to the nearest river reach. The layout is optimized for one-handed mobile use at 375px width.

## Requirements

### Functional Requirements

1. Fixed bottom tab bar with 5 tabs (River Now, Explore, Hatch, Steward, Saved) renders on all `/path/*` routes
2. Active tab is visually highlighted; inactive tabs show icon + label
3. Bottom nav is hidden on non-`/path` routes (RiverSignal, RiverSignal geology layer, DeepTrail retain existing navigation)
4. Each tab maps to a dedicated route: `/path/now`, `/path/explore`, `/path/hatch`, `/path/steward`, `/path/saved`
5. `/path` redirects to `/path/now` (default tab)
6. Fish + Refuge is a drilldown at `/path/fish/:watershed`, not a bottom tab (no tab highlight)
7. Floating GPS locate button (FAB) is available on River Now and Explore screens
8. GPS button triggers browser geolocation API, sends coordinates to `/api/v1/sites/nearest`, and navigates to the resolved watershed's River Now view
9. If GPS is denied or unavailable, GPS button opens a watershed selector dropdown
10. GPS reach lookup completes in under 3 seconds (per wireframe acceptance criteria)
11. Browser back/forward navigation works correctly between tabs and drilldowns
12. Deep links to any `/path/*` route render the correct screen with bottom nav

### Non-Functional Requirements

- **Performance**: Bottom nav renders in < 100ms; no layout shift on tab switch
- **Responsive**: Bottom nav hides at widths > 1024px; replaced by sidebar or top nav on desktop
- **Touch targets**: All tab targets minimum 48px height
- **Accessibility**: Tab bar uses `role="tablist"` + `role="tab"` with `aria-selected`

## User Stories

- [US-040 — Family at McKenzie](../user-stories/riverpath-stories.md) (navigates via River Now tab)
- [US-042 — Guide opens morning brief](../user-stories/riverpath-stories.md) (navigates via Hatch tab)

## Edge Cases and Error Handling

- **GPS timeout (> 5s)**: Show "Finding your river..." spinner for 3s, then fall back to watershed selector with message "Couldn't get your location — choose a river"
- **GPS coordinates outside any watershed**: Show "You're not near a tracked river" with option to browse all 5 watersheds
- **Narrow screen (< 320px)**: Tab labels hidden; icons only
- **Tab content still loading**: Show skeleton screen per tab while data fetches; tab switch is instant (route change), data loads in the background

## Success Metrics

- Tab-to-tab navigation < 200ms (no full page reload)
- GPS → River Now hero card displayed in < 3 seconds on 4G
- Zero horizontal overflow at 320px width

## Constraints and Assumptions

- Bottom nav is RiverPath-only; other products retain existing navigation
- No new backend auth or user model required
- GPS accuracy depends on device; reach resolution uses nearest-segment match

## Dependencies

- **Other features**: FEAT-012 (RiverPath B2C — all screens live within this nav shell)
- **External services**: Browser Geolocation API; PostGIS for nearest-reach query
- **PRD requirements**: P2-7 (Mobile-first responsive PWA)

## Out of Scope

- Redesigning navigation for RiverSignal, or DeepTrail
- Animated tab transitions or gesture-based tab switching
- Desktop sidebar navigation layout (desktop responsive handled separately)
