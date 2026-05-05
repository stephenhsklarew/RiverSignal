# PostHog Analytics Integration Plan

## Overview

Integrate PostHog event tracking across all three apps (RiverPath, DeepTrail, RiverSignal) served from a single React SPA. New PostHog project, placeholder API key, manual instrumentation (no autocapture).

## Events (33 total)

### Shared (All Apps)

| # | Event | When It Fires | Key Properties |
|---|---|---|---|
| 1 | `page_viewed` | Every route change (automatic) | `path`, `app`, `watershed` |
| 2 | `tab_switched` | Bottom nav tab tap | `tab_name`, `app` |
| 3 | `item_saved` | Heart/save button tap | `item_type`, `item_id`, `label`, `watershed`, `app` |
| 4 | `item_unsaved` | Heart/unsave button tap | `item_type`, `item_id`, `app` |
| 5 | `observation_submitted` | Camera photo form submit | `app`, `category`, `has_photo`, `has_location`, `watershed` |
| 6 | `signup_started` | Login/signup button tap | `trigger`, `app` |
| 7 | `product_selected` | Landing page product card tap | `product_name`, `product_path` |
| 8 | `cross_app_navigation` | Cross-sell link tap | `from_app`, `to_app` |

### RiverPath (`/path`)

| # | Event | When It Fires | Key Properties |
|---|---|---|---|
| 9 | `watershed_changed` | Watershed picker modal select | `from_watershed`, `to_watershed` |
| 10 | `river_story_played` | Story audio play button | `watershed`, `reading_level` |
| 11 | `river_story_level_changed` | Adult/Kids/Expert toggle | `watershed`, `from_level`, `to_level` |
| 12 | `question_asked` | Ask box submit | `question_length`, `watershed` |
| 13 | `filter_applied` | Explore/species filter chip tap | `filter_type`, `filter_value` |
| 14 | `map_pin_tapped` | Explore map popup opened | `site_name`, `rec_type`, `watershed` |
| 15 | `card_settings_changed` | Card visibility/order saved | `page`, `cards_visible`, `cards_hidden` |
| 16 | `insect_expanded` | Hatch insect card expand | `insect_name`, `watershed` |
| 17 | `fly_video_clicked` | YouTube fly tying link tap | `fly_pattern`, `watershed` |

### DeepTrail (`/trail`)

| # | Event | When It Fires | Key Properties |
|---|---|---|---|
| 18 | `location_selected` | Pick page watershed or GPS select | `location_id`, `location_name`, `method` |
| 19 | `location_changed` | Header modal location switch | `from_location`, `to_location` |
| 20 | `story_page_turned` | Story prev/next pagination | `location_id`, `reading_level`, `page`, `total_pages` |
| 21 | `story_audio_played` | Story listen button | `location_id`, `reading_level` |
| 22 | `reading_level_changed` | Adult/Kids/Expert toggle | `location_id`, `from_level`, `to_level` |
| 23 | `eras_compared` | Compare Eras section used | `era1`, `era2`, `location_id` |
| 24 | `fossil_viewed` | Fossil card tap | `taxon_name`, `period`, `rarity` |
| 25 | `mineral_viewed` | Mineral card tap | `site_name`, `commodity` |
| 26 | `rockhounding_site_viewed` | Collect list site tap | `site_name`, `rock_type`, `land_owner` |
| 27 | `filter_applied` | Period/phylum/mineral chip tap | `filter_type`, `filter_value` |
| 28 | `quiz_answered` | Quiz choice tap | `question_index`, `is_correct` |
| 29 | `card_settings_changed` | Card visibility/order saved | `page`, `cards_visible`, `cards_hidden` |

### RiverSignal (`/riversignal`)

| # | Event | When It Fires | Key Properties |
|---|---|---|---|
| 30 | `watershed_selected` | Map marker or sidebar click | `watershed` |
| 31 | `species_searched` | Observation search submit | `query`, `result_count` |
| 32 | `barrier_toggle` | Barrier overlay toggle | `watershed`, `visible` |
| 33 | `alert_dismissed` | Alert X button | `alert_type`, `watershed` |

> Every event automatically carries `app` (riverpath/deeptrail/riversignal) and `watershed` via the `useAnalytics()` hook.

## Architecture

### New Files

| File | Purpose |
|---|---|
| `frontend/src/hooks/useAnalytics.ts` | Thin wrapper hook — auto-attaches `app` property |
| `frontend/src/components/PostHogPageView.tsx` | Auto `$pageview` on SPA route changes |
| `frontend/src/components/PostHogIdentify.tsx` | User identification on login, reset on logout |

### PostHog Configuration

```typescript
posthog.init(key, {
  api_host: host,
  person_profiles: 'identified_only',  // no profiles for anonymous users (saves cost)
  capture_pageview: false,             // manual SPA page tracking via PostHogPageView
  capture_pageleave: true,
  autocapture: false,                  // manual instrumentation only — clean data
  persistence: 'localStorage',
})
```

### Provider Placement (main.tsx)

```
BrowserRouter
  PostHogProvider          <-- NEW
    AuthProvider
      SavedProvider
        DeepTrailProvider
          PostHogPageView  <-- NEW (automatic page views)
          PostHogIdentify  <-- NEW (user identification)
          Routes
```

### useAnalytics() Hook

```typescript
export function useAnalytics() {
  const posthog = usePostHog()
  const { pathname } = useLocation()
  const app = detectApp(pathname)  // /path→riverpath, /trail→deeptrail, etc.

  const track = useCallback((event: string, props?: Record<string, any>) => {
    posthog?.capture(event, { app, ...props })
  }, [posthog, app])

  return { track, app }
}
```

Components call: `const { track } = useAnalytics()` then `track('item_saved', { item_type, item_id })`.

### User Identification Flow

1. **Anonymous**: PostHog auto-generates `distinct_id`. We register existing `rs_anonymous_id` as a super-property.
2. **Login**: `posthog.identify(user.id, { email, name, username })` — merges anonymous session.
3. **Logout**: `posthog.reset()` — starts fresh anonymous session.
4. **Person properties**: `apps_used` (array), `preferred_watershed`, `saved_item_count`.

### Multi-App Segmentation

Every event carries `app` property. Filter any PostHog dashboard by `app = 'riverpath'` etc. No Groups add-on needed.

## Implementation Phases

1. **Plumbing**: Install `posthog-js`, env vars, provider, PageView + Identify components
2. **Core hook**: Create `useAnalytics.ts`
3. **High-value events**: `item_saved`, `observation_submitted`, `signup_started`, `product_selected`, `question_asked`
4. **Engagement events**: All remaining events across all pages (~20 files touched)
5. **Verification**: Check PostHog Live Events dashboard for correct event flow

## Environment Variables

```
VITE_POSTHOG_KEY=phc_your_project_api_key_here
VITE_POSTHOG_HOST=https://us.i.posthog.com
```

## Modified Files (Full List)

`main.tsx`, `SaveButton.tsx`, `PhotoObservation.tsx`, `CardSettings.tsx`, `WatershedHeader.tsx`, `DeepTrailHeader.tsx`, `BottomNav.tsx`, `DeepTrailBottomNav.tsx`, `TrailStoryPage.tsx`, `TrailExplorePage.tsx`, `TrailCollectPage.tsx`, `TrailLearnPage.tsx`, `DeepTrailPickPage.tsx`, `RiverNowPage.tsx`, `ExplorePage.tsx`, `ExploreMapPage.tsx`, `HatchPage.tsx`, `MapPage.tsx`
