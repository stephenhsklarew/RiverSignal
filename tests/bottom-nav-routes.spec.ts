/**
 * Regression test for the ConditionalBottomNav route-matching logic
 * (frontend/src/main.tsx). Pure-string assertion against the same
 * regex so the test runs without a browser.
 *
 * The function should:
 *   - HIDE the toolbar on /path (HomePage splash)
 *   - HIDE the toolbar on /path/now (bare picker that renders the same
 *     card grid as /path)
 *   - SHOW the toolbar on every other /path/<tab> route, including
 *     watershed-less variants like /path/alerts and /path/saved
 *     (which default to the session-stored watershed)
 *   - SHOW the toolbar on /path/<tab>/<watershed> for every tab
 *   - HIDE the toolbar on /trail splash and bare /trail/<tab>
 *   - SHOW the DeepTrail toolbar on /trail/<tab>/<location>
 *
 * Two prior regressions this guards against:
 *   1. Original behaviour was too loose — toolbar appeared on /path
 *      and /path/now splash views (commit e82e028 tightened it).
 *   2. e82e028 was TOO strict — required /[^/]+ after the tab, which
 *      hid the toolbar on /path/alerts, /path/saved, and any other
 *      tab that defaults to a session-stored watershed.
 */
import { test, expect } from '@playwright/test';

// Mirror the regexes from frontend/src/main.tsx:ConditionalBottomNav
// exactly. If they change there, update both places.
const RIVER_PATH_TAB =
  /^\/path\/(now|explore|hatch|steward|saved|fish|map|explore-map|stocking|where|alerts)(\/|$)/;
const TRAIL_TAB = /^\/trail\/(story|explore|collect|learn|saved)\/[^/]+/;

function showsRiverPathNav(pathname: string): boolean {
  if (!RIVER_PATH_TAB.test(pathname)) return false;
  if (pathname === '/path/now' || pathname === '/path/now/') return false;
  return true;
}

function showsTrailNav(pathname: string): boolean {
  return TRAIL_TAB.test(pathname);
}

test.describe('ConditionalBottomNav route matching', () => {
  const cases: Array<{ path: string; rp: boolean; trail: boolean; reason: string }> = [
    // RiverPath: splash views — both should be toolbar-free
    { path: '/path', rp: false, trail: false, reason: 'HomePage splash' },
    { path: '/path/', rp: false, trail: false, reason: 'HomePage splash (trailing slash)' },
    { path: '/path/now', rp: false, trail: false, reason: 'RiverNowDefault picker' },
    { path: '/path/now/', rp: false, trail: false, reason: 'RiverNowDefault picker (trailing slash)' },
    { path: '/path/mckenzie', rp: false, trail: false, reason: 'HomePage with watershed param' },

    // RiverPath: tab routes with watershed — toolbar
    { path: '/path/now/shenandoah', rp: true, trail: false, reason: 'RiverNowDetail' },
    { path: '/path/now/mckenzie/photo', rp: true, trail: false, reason: 'PhotoDetailPage (deeper route)' },
    { path: '/path/hatch/shenandoah', rp: true, trail: false, reason: 'HatchPage with watershed' },
    { path: '/path/explore/deschutes', rp: true, trail: false, reason: 'ExplorePage with watershed' },
    { path: '/path/explore-map/skagit', rp: true, trail: false, reason: 'ExploreMapPage' },
    { path: '/path/stocking/green_river', rp: true, trail: false, reason: 'StockingMapPage' },
    { path: '/path/steward/johnday', rp: true, trail: false, reason: 'StewardPage' },
    { path: '/path/fish/klamath', rp: true, trail: false, reason: 'FishRefugePage' },
    { path: '/path/map/metolius', rp: true, trail: false, reason: 'SpeciesMapPage' },
    { path: '/path/where/shenandoah', rp: true, trail: false, reason: 'WhereToFishPage' },

    // RiverPath: WATERSHED-LESS tab routes — toolbar (regression test)
    { path: '/path/alerts', rp: true, trail: false, reason: 'AlertsPage (global, no watershed)' },
    { path: '/path/saved', rp: true, trail: false, reason: 'SavedPage (session watershed)' },
    { path: '/path/hatch', rp: true, trail: false, reason: 'HatchPage default-to-session-ws' },
    { path: '/path/explore', rp: true, trail: false, reason: 'ExplorePage default-to-session-ws' },
    { path: '/path/steward', rp: true, trail: false, reason: 'StewardPage default-to-session-ws' },
    { path: '/path/fish', rp: true, trail: false, reason: 'FishRefugePage default-to-session-ws' },

    // RiverPath: irrelevant paths
    { path: '/', rp: false, trail: false, reason: 'Landing' },
    { path: '/riversignal', rp: false, trail: false, reason: 'MapPage' },
    { path: '/riversignal/shenandoah', rp: false, trail: false, reason: 'MapPage with ws' },
    { path: '/status', rp: false, trail: false, reason: 'StatusPage' },

    // DeepTrail
    { path: '/trail', rp: false, trail: false, reason: 'DeepTrail picker' },
    { path: '/trail/story', rp: false, trail: false, reason: 'DeepTrail bare tab — no location yet' },
    { path: '/trail/story/some-place', rp: false, trail: true, reason: 'DeepTrail story with location' },
    { path: '/trail/explore/x', rp: false, trail: true, reason: 'DeepTrail explore with location' },
    { path: '/trail/learn/x', rp: false, trail: true, reason: 'DeepTrail learn with location' },
    { path: '/trail/collect/x', rp: false, trail: true, reason: 'DeepTrail collect with location' },
    { path: '/trail/saved/x', rp: false, trail: true, reason: 'DeepTrail saved with location' },
  ];

  for (const { path, rp, trail, reason } of cases) {
    test(`${path} → rp=${rp} trail=${trail} (${reason})`, () => {
      expect(showsRiverPathNav(path), `RiverPath nav for ${path}`).toBe(rp);
      expect(showsTrailNav(path), `Trail nav for ${path}`).toBe(trail);
    });
  }
});
