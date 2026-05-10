---
dun:
  id: FEAT-016
  depends_on:
    - helix.prd
    - FEAT-012
    - FEAT-014
---
# Feature Specification: FEAT-016 — Saved & Favorites

**Feature ID**: FEAT-016
**Status**: Implemented
**Priority**: P1
**Owner**: Core Engineering

## Overview

RiverPath's Saved tab lets users bookmark reaches, species, fly patterns, recreation sites, stewardship projects, and observations for quick access later. This is the persistence layer that makes RiverPath feel personal — a user's saved items represent their river interests and trip planning state.

Non-observation items use localStorage with a React context provider. Observations are synced across devices via the API when the user is authenticated, so observations saved on one device appear on all others.

This addresses wireframe Screen 6 (Saved) and the "Save Trip" / "Save Spot" steps in the primary user flows.

## Problem Statement

- **Current situation**: Users want to bookmark content and track their own observations across the app.
- **Pain points**: Families planning trips need to save access points. Anglers need to bookmark fly recommendations. Users who submit observations need to see them in one place and on a map, regardless of which device they're using.
- **Desired outcome**: A heart/bookmark icon appears on every saveable card. Tapping it saves the item. The Saved tab shows all saved items for the currently selected watershed, grouped by item type with descriptive section headers.

## Requirements

### Functional Requirements

#### Persistence Layer
1. `SavedContext` React context provider wraps the app, backed by localStorage key `riverpath-saved`
2. Saved items stored as JSON array: `{ type: 'reach'|'species'|'fly'|'recreation'|'restoration'|'fossil'|'mineral'|'rocksite'|'observation', id: string, watershed: string, label: string, sublabel?: string, thumbnail?: string, latitude?: number, longitude?: number, savedAt: string }`
3. Context exposes: `save(item)`, `unsave(type, id)`, `isSaved(type, id)`, `listSaved(type?)`, `countSaved(watershed?)`
4. Maximum 500 saved items (localStorage size constraint)
5. Saved data persists across browser sessions and survives page refresh
6. `countSaved()` accepts an optional watershed parameter to return count for a specific watershed only

#### Observation Sync (API-backed)
7. Observations are fetched from `GET /api/v1/observations/user?mine=true&watershed={ws}` with `credentials: 'include'`
8. When authenticated, the API returns all of the user's observations (both public and private) for the selected watershed
9. Observations sync across devices — saving an observation on phone makes it visible on desktop when logged in with the same account
10. When not authenticated, the observation section is empty (observations require login)

#### Save Button
11. `SaveButton` component renders a heart icon (outline when unsaved, filled when saved) on any saveable card
12. Tapping toggles save/unsave state with immediate visual feedback (no network call for non-observation types)
13. SaveButton appears on: watershed blocks (reach), species gallery cards, fly recommendation cards, adventure cards (FEAT-015), restoration project cards
14. Save/unsave triggers a subtle animation (heart fills/empties with scale pulse)

#### Saved Page
15. Saved page accessible via bottom nav "Saved" tab at `/path/saved`
16. Page filters all items by the currently selected watershed (from WatershedHeader). Users do not see items from other watersheds.
17. Items grouped by type with descriptive section headers and type icons:
    - `📷 Observations` (fetched from API, shown first)
    - `🐟 Species`
    - `🪶 Recommended Flies`
    - `📍 Reaches`
    - `⛺ Recreation Sites`
    - `♻ Restoration Projects`
    - `🦴 Fossils`
    - `💎 Minerals`
    - `🪨 Rock Sites`
18. Observations section includes a "View all on map" link that navigates to a map view. Individual observations with coordinates show a 📍 map link.
19. Observations display visibility status (public/private) and observation date in the item meta row.
20. Each non-observation saved item renders with: thumbnail (if available), label, sublabel, and saved date
21. Delete button (✕) removes a non-observation saved item. Observations are managed via the observation form.
22. Empty state: "No saved items for {watershed name} — tap the heart icon on any card to save it here"
23. Empty section headers are hidden (only show groups that have items)

#### Bottom Nav Badge
24. Saved tab in bottom nav shows a count badge when items exist for the selected watershed
25. Badge count is watershed-specific: only counts non-observation saved items for the currently selected watershed
26. Badge updates in real-time as items are saved/unsaved from any screen

### Non-Functional Requirements

- **Performance**: Save/unsave operation < 50ms (localStorage write is synchronous)
- **Storage**: localStorage entry stays under 1MB (500 items with thumbnails is ~200KB)
- **Offline**: Non-observation saved items work fully offline. Observation section requires network to fetch from API.
- **Accessibility**: SaveButton has `aria-label="Save [item name]"` / `aria-label="Remove [item name] from saved"`

## User Stories

- [US-053 — Family saves campground for trip planning](../user-stories/riverpath-stories.md)
- [US-054 — Angler saves fly pattern that worked](../user-stories/riverpath-stories.md)
- [US-055 — Steward saves restoration project](../user-stories/riverpath-stories.md)

## Edge Cases and Error Handling

- **localStorage full**: Catch `QuotaExceededError` on write; items remain in state
- **Corrupted localStorage data**: Wrap JSON.parse in try/catch; if corrupt, reset to empty array
- **Duplicate save**: `save()` is idempotent — if item with same type+id exists, update savedAt timestamp
- **API fetch failure**: Observation section shows empty if the API call fails; non-observation items from localStorage still render
- **Not logged in**: Observation section does not appear; only localStorage items are shown
- **Watershed switch**: Changing watershed in the header re-filters the saved list and re-fetches observations for the new watershed

## Success Metrics

- 20%+ of returning users have at least 1 saved item
- Average saved items per active user > 3
- Saved tab is the 3rd most-visited tab (after River Now and Hatch)
- Zero data loss incidents from localStorage corruption

## Constraints and Assumptions

- Non-observation saves are device-local (localStorage only); no backend sync
- Observation saves sync via the API using the authenticated user's `user_id`
- Migration path: when full backend sync is implemented, migrate localStorage items to `user_favorites` table on first login
- Thumbnail URLs are stored as-is; if the source changes URLs, thumbnails break but labels persist

## Dependencies

- **Other features**: FEAT-014 (bottom nav — Saved tab lives here), FEAT-012 (cards to save from), FEAT-015 (adventure cards to save)
- **Backend**: `GET /api/v1/observations/user` with `mine=true` parameter for observation sync
- **PRD requirements**: Addresses wireframe Screen 6 (Saved) and core mobile design requirement "offline cached saved reaches"

## Out of Scope

- Cloud sync of non-observation saved items across devices
- Trip journal with photos and notes (parking lot as UGC feature)
- Sharing saved items via link or social media
- Export saved items as PDF or checklist
- Saved search filters or saved map views
