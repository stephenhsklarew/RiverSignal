---
dun:
  id: FEAT-011
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-011 -- Three-Product UI Architecture

**Feature ID**: FEAT-011
**Status**: Implemented (spec retroactive)
**Priority**: P0
**Owner**: Founder

## Overview

The three-product UI architecture provides distinct web experiences for **RiverSignal** (B2B watershed analytics, desktop-first), **RiverPath** (B2C watershed companion, mobile-first), and **DeepTrail** (B2C geology adventure, mobile-first), all sharing one backend API, one Postgres warehouse, and one Cloud Run service. Implements PRD P2-7.

> **History**: This spec previously described a four-product layout including a separate "DeepSignal" B2B geology surface. DeepSignal was removed from the landing page on 2026-05-08 and its B2B geology functionality consolidated into RiverSignal. The current shipping platform is three products.

## Problem Statement

- **Current situation**: One backend, three differentiated React routes. Each route has UX appropriate to its audience: dense analytics for B2B desktop, story-driven mobile for B2C.
- **Pain points** (historical, now resolved): a single UI couldn't serve both a watershed manager needing dense data tables and a family wanting adventure stories; mobile users on trail needed touch-optimized interfaces.
- **Desired outcome**: Three distinct web experiences accessible at separate routes, each with appropriate UX, tone, and feature set, all powered by the same API.

## Requirements

### Functional Requirements

1. Three product UI entry points plus a landing page:
   - `/` — Liquid Marble landing page (product selector with three cards)
   - `/riversignal` — RiverSignal (B2B desktop-first watershed analytics)
   - `/path/*` — RiverPath (B2C mobile-first watershed companion, with bottom-nav tabs)
   - `/trail/*` — DeepTrail (B2C mobile-first geology adventure, with 5-tab navigation)
2. **RiverSignal** (B2B desktop-first): Professional data-dense layout with split-pane map+panel, data tables, KPI grids, report generator, indicator species table. Geologic context (formerly DeepSignal) merged in as a layer.
3. **RiverPath** (B2C mobile-first responsive): Story-driven mobile companion with bottom-nav tabs (`now`, `explore`, `hatch`, `steward`, `saved`); watershed picker with caret in shared sticky header; AI narrative cards.
4. **DeepTrail** (B2C mobile-first responsive): Adventure-focused mobile guide with 5-tab navigation (`story`, `explore`, `collect`, `learn`, `saved`); geologic time slider, fossil photo cards, legal collecting status badges, audio narrative.
5. All three products share: MapLibre map component (with switchable basemaps), AI grounded narrative pipeline, data freshness indicator (`/status`), authentication (FEAT-019), saved favorites (FEAT-016).
6. Shared component library: `WatershedHeader` (logo + watershed picker + UserMenu + optional ⚙), `BottomNav`, `DeepTrailHeader`, `DeepTrailBottomNav`, `MapView`, `PhotoObservation`, `SaveButton`, `AuthContext`, `SavedContext`, `LoginModal`, `InfoTooltip`.
7. B2C products register as Progressive Web Apps (PWA) with service worker for offline caching (TODO — service worker not yet wired).

### Non-Functional Requirements

- **Mobile performance**: B2C products achieve Lighthouse performance > 80 on mobile.
- **Offline support**: Previously viewed watershed/geologic data accessible without internet (TODO — service worker).
- **Responsive**: B2C products tested at 320px, 375px, 414px, 768px, 1024px, 1440px breakpoints.
- **Accessibility**: WCAG 2.1 AA on non-map elements for all products.

## User Stories

- US-038 — Family on phone at Painted Hills opens DeepTrail and sees deep time story
- US-040 — Angler on phone uses RiverPath to check Deschutes conditions before a trip
- US-046 — Watershed manager on desktop uses RiverSignal to view geology layer overlay (formerly DeepSignal use case)

## Edge Cases and Error Handling

- **Offline mode** (when service worker ships): cached data with "Last updated X ago" banner; disable chat/ask features with explanation.
- **Small screen**: On < 375px, collapse side panels to full-screen modals; hide non-essential KPI chips.
- **Cross-product navigation**: User on RiverPath clicks a geologic feature → seamless link to DeepTrail with context preserved.

## Success Metrics

- B2C mobile users complete primary task (check conditions, read story) within 30 seconds of opening.
- 30% of active users engage with both RiverPath and DeepTrail.
- PWA install rate > 10% among returning mobile users (post-service-worker ship).

## Dependencies

- **Other features**: FEAT-006 (Map Workspace), FEAT-008 (Geologic Context), FEAT-009 (Fossil Discovery), FEAT-010 (Deep Time Storytelling), FEAT-014 (Mobile Navigation), FEAT-016 (Saved Favorites).
- **External services**: MapLibre basemap tiles, Anthropic Claude API.
- **PRD requirements**: Implements P2-7 (Mobile-first responsive PWA).

## Out of Scope

- Native iOS/Android apps (PWA first).
- White-label / multi-tenant branding.
- A separate DeepSignal B2B surface (consolidated into RiverSignal as of 2026-05-08).
