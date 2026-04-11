---
dun:
  id: FEAT-011
  depends_on:
    - helix.prd
---
# Feature Specification: FEAT-011 -- Four-Product UI Architecture

**Feature ID**: FEAT-011
**Status**: Draft
**Priority**: P1
**Owner**: Core Engineering

## Overview

The four-product UI architecture provides distinct web experiences for RiverSignal (B2B watershed), RiverPath (B2C watershed), DeepSignal (B2B geology), and DeepTrail (B2C geology) sharing the same backend API and data lake. B2C products (RiverPath, DeepTrail) are mobile-first responsive; B2B products (RiverSignal, DeepSignal) are desktop-first professional. Implements PRD P2-7.

## Problem Statement

- **Current situation**: The application has one frontend serving both B2B (professional dashboard) and B2C (story home page) use cases through a single React app. The geology/paleontology domain has no UI at all. Mobile experience is adequate but not optimized.
- **Pain points**: A single UI cannot serve both a watershed manager needing dense data tables and a family wanting adventure stories; geology users have no entry point; mobile users on trail need touch-optimized, offline-capable interfaces.
- **Desired outcome**: Four distinct web experiences accessible at separate routes (or subdomains), each with appropriate UX, tone, and feature set, all powered by the same API.

## Requirements

### Functional Requirements

1. Four distinct UI entry points: `/signal` (RiverSignal), `/path` (RiverPath), `/deepsignal` (DeepSignal), `/trail` (DeepTrail) — plus `/` as a landing page directing users to the appropriate product
2. **RiverSignal** (B2B desktop-first): Professional data-dense layout with split-pane map+panel, data tables, KPI grids, report generator, indicator species table. Existing design.
3. **RiverPath** (B2C mobile-first responsive): Story-driven home page with watershed narratives, species photo gallery, inline chat, fishing intelligence. Existing design, enhanced for mobile touch targets (48px minimum), responsive breakpoints (320px-1200px).
4. **DeepSignal** (B2B desktop-first): Professional layout similar to RiverSignal but with geologic map layer, stratigraphic column panel, fossil occurrence table, geology-ecology correlation views.
5. **DeepTrail** (B2C mobile-first responsive): Adventure-focused story layout similar to RiverPath but themed for geology/fossils. Geologic time slider, fossil photo cards, legal collecting status badges (green/yellow/red), museum finder, deep time narrative panels.
6. All four products share: MapLibre map component (with switchable basemaps), chat/ask interface (same Claude API), data freshness indicator, and authentication (when added).
7. Shared component library for common elements: map, chat, photo cards, data tables, KPI cards, status badges.
8. B2C products register as Progressive Web Apps (PWA) with service worker for offline caching of recently viewed data.

### Non-Functional Requirements

- **Mobile performance**: B2C products achieve Lighthouse performance score > 80 on mobile
- **Offline support**: Previously viewed watershed/geologic data accessible without internet (service worker cache)
- **Responsive**: B2C products tested at 320px, 375px, 414px, 768px, 1024px, 1440px breakpoints
- **Accessibility**: WCAG 2.1 AA on non-map elements for all products

## User Stories

- US-038 -- Family on phone at Painted Hills opens DeepTrail and sees deep time story (to be created)
- US-039 -- Geologist on desktop uses DeepSignal to correlate basalt units with spring locations (to be created)
- US-040 -- Angler on phone uses RiverPath to check Deschutes conditions before a trip (to be created)

## Edge Cases and Error Handling

- **Offline mode**: When internet is unavailable, show cached data with "Last updated X ago" banner; disable chat/ask features with explanation
- **Small screen**: On screens < 375px, collapse side panels to full-screen modals; hide non-essential KPI chips
- **Cross-product navigation**: User on RiverPath clicks a geologic feature → seamless link to DeepTrail with context preserved

## Success Metrics

- B2C mobile users complete primary task (check conditions, read story) within 30 seconds of opening
- 30% of active users engage with both river and geology products
- PWA install rate > 10% among returning mobile users

## Dependencies

- **Other features**: FEAT-006 (Map Workspace), FEAT-008 (Geologic Context), FEAT-009 (Fossil Discovery), FEAT-010 (Deep Time Storytelling)
- **External services**: MapLibre basemap tiles, Claude API
- **PRD requirements**: Implements P2-7 (Mobile-first responsive PWA)

## Out of Scope

- Native iOS/Android apps (PWA first)
- User accounts and data sync across devices (deferred to auth implementation)
- Payment processing for subscriptions (deferred)
- White-label / multi-tenant branding
