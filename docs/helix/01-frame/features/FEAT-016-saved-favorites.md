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
**Status**: Draft
**Priority**: P1
**Owner**: Core Engineering

## Overview

RiverPath's Saved tab lets users bookmark reaches, species, fly patterns, recreation sites, and stewardship projects for quick access later. This is the persistence layer that makes RiverPath feel personal — a user's saved items represent their river interests and trip planning state. MVP uses localStorage with a React context provider; no backend auth or user model required.

This addresses wireframe Screen 6 (Saved) and the "Save Trip" / "Save Spot" steps in the primary user flows. It was explicitly out of scope in FEAT-012 but is now in scope per the wireframe spec.

## Problem Statement

- **Current situation**: RiverPath has no way to save or bookmark anything. Every session starts from zero. Users cannot mark a campground for later, save a fly pattern that worked, or bookmark a watershed they want to revisit.
- **Pain points**: Families planning trips cannot save access points or species they want to find. Anglers cannot bookmark fly recommendations. Stewardship advocates cannot save restoration projects. Every visit requires re-navigating to the same content.
- **Desired outcome**: A heart/bookmark icon appears on every saveable card (reach, species, fly, recreation site, restoration project). Tapping it saves the item. The Saved tab shows all saved items grouped by watershed (river name), persisted across browser sessions.

## Requirements

### Functional Requirements

#### Persistence Layer
1. `SavedContext` React context provider wraps the app, backed by localStorage key `riverpath-saved`
2. Saved items stored as JSON array: `{ type: 'reach'|'species'|'fly'|'recreation'|'restoration', id: string, watershed: string, label: string, sublabel?: string, thumbnail?: string, savedAt: string }`
3. Context exposes: `save(item)`, `unsave(type, id)`, `isSaved(type, id)`, `listSaved(type?)`, `countSaved()`
4. Maximum 500 saved items (localStorage size constraint) — show warning at 450: "Approaching save limit"
5. Saved data persists across browser sessions and survives page refresh

#### Save Button
6. `SaveButton` component renders a heart icon (outline when unsaved, filled when saved) on any saveable card
7. Tapping toggles save/unsave state with immediate visual feedback (no network call)
8. SaveButton appears on: watershed blocks (reach), species gallery cards, fly recommendation cards, adventure cards (FEAT-015), restoration project cards
9. Save/unsave triggers a subtle animation (heart fills/empties with scale pulse)

#### Saved Page
10. Saved page accessible via bottom nav "Saved" tab at `/path/saved`
11. Items grouped by watershed (river name) with section headers showing river name and item count. Within each watershed group, items display with type icon, label, sublabel, and saved date.
12. Each saved item renders as a compact card with: thumbnail (if available), label, sublabel, watershed name, saved date
13. Swipe-to-delete or tap-delete button removes a saved item
14. Empty state: "Nothing saved yet — tap the heart icon on any card to save it here"
15. Empty section headers are hidden (only show groups that have items)

#### Bottom Nav Badge
16. Saved tab in bottom nav shows a count badge when saved items > 0
17. Badge updates in real-time as items are saved/unsaved from any screen

### Non-Functional Requirements

- **Performance**: Save/unsave operation < 50ms (localStorage write is synchronous)
- **Storage**: localStorage entry stays under 1MB (500 items with thumbnails is ~200KB)
- **Offline**: Saved page works fully offline — all data is in localStorage; thumbnails may not load but labels and metadata do
- **Accessibility**: SaveButton has `aria-label="Save [item name]"` / `aria-label="Remove [item name] from saved"`

## User Stories

- [US-053 — Family saves campground for trip planning](../user-stories/riverpath-stories.md)
- [US-054 — Angler saves fly pattern that worked](../user-stories/riverpath-stories.md)
- [US-055 — Steward saves restoration project](../user-stories/riverpath-stories.md)

## Edge Cases and Error Handling

- **localStorage full**: Catch `QuotaExceededError` on write; show toast: "Storage full — remove some saved items to save more"
- **localStorage disabled (private browsing)**: Detect on mount; show banner on Saved page: "Saves won't persist in private browsing mode"
- **Corrupted localStorage data**: Wrap JSON.parse in try/catch; if corrupt, reset to empty array with console warning
- **Duplicate save**: `save()` is idempotent — if item with same type+id exists, update savedAt timestamp instead of creating duplicate
- **Item no longer exists in API**: Saved items are labels + IDs; if the underlying data is removed from the database, the saved entry persists with its label but may not deep-link correctly. Show "This item may no longer be available" if a detail fetch fails.

## Success Metrics

- 20%+ of returning users have at least 1 saved item
- Average saved items per active user > 3
- Saved tab is the 3rd most-visited tab (after River Now and Hatch)
- Zero data loss incidents from localStorage corruption

## Constraints and Assumptions

- No backend user model or authentication — saves are device-local only
- Saved items do not sync across devices or browsers
- Migration path: when auth is implemented, sync localStorage to `user_favorites` table on first login
- Thumbnail URLs are stored as-is; if the source (iNaturalist, RIDB) changes URLs, thumbnails break but labels persist

## Dependencies

- **Other features**: FEAT-014 (bottom nav — Saved tab lives here), FEAT-012 (cards to save from), FEAT-015 (adventure cards to save)
- **External services**: None — fully client-side
- **PRD requirements**: Addresses wireframe Screen 6 (Saved) and core mobile design requirement "offline cached saved reaches"

## Out of Scope

- User accounts or authentication
- Cloud sync of saved items across devices
- Trip journal with photos and notes (wireframe implied this — descoped to parking lot as UGC feature)
- Sharing saved items via link or social media
- Export saved items as PDF or checklist
- Saved search filters or saved map views
