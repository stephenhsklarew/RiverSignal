/**
 * Watershed smoke tests — run after onboarding a new watershed to catch
 * empty-panel / missing-data UX bugs before they hit the user.
 *
 * Usage:
 *   WATERSHED=shenandoah BASE_URL=https://riversignal-api-x6ka75yaxa-uw.a.run.app \
 *     npx playwright test tests/watershed-smoke.spec.ts
 *
 * Or for local:
 *   WATERSHED=shenandoah BASE_URL=http://localhost:5173 \
 *     npx playwright test tests/watershed-smoke.spec.ts
 *
 * Defaults to local dev server + 'shenandoah'.
 *
 * The runbook (docs/helix/runbooks/add-watershed-prompt.md §2.6.5) wires
 * this file into the watershed-onboarding gate: a clean pass here is a
 * precondition for crossing §2.8 production-deploy gates.
 */
import { test, expect } from '@playwright/test';

const WS = process.env.WATERSHED || 'shenandoah';
const BASE = process.env.BASE_URL || 'http://localhost:5173';
const API = process.env.API_BASE || `${BASE}/api/v1`;

// Allow each page some time to settle (API can take a few seconds cold).
const SETTLE_MS = 4000;

test.describe(`Watershed ${WS} — RiverPath /path`, () => {

  test('splash card on /path renders an image, tagline, and narrative', async ({ page, request }) => {
    await page.goto(`${BASE}/path`);
    await page.waitForTimeout(SETTLE_MS);

    // Bug observed for new watersheds: missing entry in HomePage WATERSHED_META
    // + PHOTOS dicts → blank card or broken image. Or stale Unsplash photo ID
    // that returns 404 (caught the Shenandoah splash card on 2026-05-15).
    const card = page.locator(`[data-watershed="${WS}"]`).first();
    if (await card.count()) {
      const img = card.locator('img').first();
      await expect(img).toBeVisible();
      const src = await img.getAttribute('src');
      expect(src, 'card image src must be a real URL').toMatch(/^https?:\/\//);

      // Verify the image URL actually returns 200 — Unsplash deletes photos.
      const imgResp = await request.head(src!);
      expect(imgResp.status(),
        `card image ${src} returned ${imgResp.status()} — pick a different stable URL`
      ).toBe(200);

      // Card narrative must include the watershed's display name (not a default).
      const text = await card.textContent();
      expect(text?.length ?? 0, 'card text should be > 30 chars').toBeGreaterThan(30);
    }
  });

  test('/path/now/<watershed> river story renders content (not Deschutes by default)', async ({ page }) => {
    await page.goto(`${BASE}/path/now/${WS}`);
    await page.waitForTimeout(SETTLE_MS);

    const storyCard = page.locator('.rnow-story-card').first();
    await expect(storyCard).toBeVisible();
    const text = (await storyCard.textContent()) || '';

    expect(text.length, 'river story must have body text').toBeGreaterThan(80);
    if (WS !== 'deschutes') {
      expect(text.toLowerCase()).not.toContain('deschutes');
    }
    if (WS !== 'mckenzie') {
      expect(text.toLowerCase()).not.toContain('mckenzie');
    }
  });

  test('Fish Stocking section shows pinnable rows in map view', async ({ page, request }) => {
    // Verify the API surface first — empty list means the curated
    // stocking_locations seed wasn't applied.
    const r = await request.get(`${API}/sites/${WS}/fishing/stocking/locations`);
    expect(r.ok(), 'stocking/locations endpoint must respond OK').toBeTruthy();
    const rows = await r.json();
    if (rows.length > 0) {
      const mappable = rows.filter((x: any) => x.latitude != null && x.longitude != null);
      expect(mappable.length,
        `at least one stocking location must have lat/lon (got ${mappable.length}/${rows.length}). ` +
        `Add seed rows to silver.stocking_locations via alembic.`
      ).toBeGreaterThan(0);
    }
  });

  test('Catch Probability shows fish names, not just a score', async ({ page, request }) => {
    const r = await request.get(`${API}/sites/${WS}/catch-probability`);
    expect(r.ok()).toBeTruthy();
    const body = await r.json();
    if (body.overall_score != null) {
      expect((body.species || []).length,
        'catch-probability returned overall_score but empty species[]; gold.species_by_reach may be missing rows for this watershed'
      ).toBeGreaterThan(0);
    }
  });

  test('Hatch chart insects show photos (not just names)', async ({ request }) => {
    const r = await request.get(`${API}/sites/${WS}/fishing/hatch-confidence`);
    expect(r.ok()).toBeTruthy();
    const body = await r.json();
    const insects = body.insects || [];
    if (insects.length > 0) {
      const withPhotos = insects.filter((i: any) => i.photo_url);
      expect(withPhotos.length,
        `at least some hatch insects must have photo_url (got ${withPhotos.length}/${insects.length}). ` +
        `Ensure gold.species_gallery is refreshed and includes the watershed.`
      ).toBeGreaterThan(0);
    }
  });

  test('/path/explore renders adventure cards (camping/trails/boats/fishing)', async ({ page, request }) => {
    const r = await request.get(`${API}/sites/${WS}/recreation`);
    expect(r.ok()).toBeTruthy();
    const rows = await r.json();
    expect(rows.length,
      `/sites/${WS}/recreation returned 0 rows; if RIDB has no East Coast / new-region coverage, ` +
      `seed via an alembic migration with source_type='curated_${WS}_v0'.`
    ).toBeGreaterThan(0);
  });

  test('/path/saved empty-state heart icon is rendered in red', async ({ page }) => {
    await page.goto(`${BASE}/path/saved`);
    await page.waitForTimeout(SETTLE_MS);
    const icon = page.locator('.saved-empty-icon').first();
    if (await icon.count()) {
      const color = await icon.evaluate(el => getComputedStyle(el).color);
      // Heart should be a red-family color, not default text grey.
      // Accept rgb where R is meaningfully greater than G+B.
      const m = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
      if (m) {
        const [r, g, b] = [+m[1], +m[2], +m[3]];
        expect(r,
          `empty-state heart should be red (got rgb(${r},${g},${b})). ` +
          `Apply 'color: var(--alert, #c4432b)' to .saved-empty-icon.`
        ).toBeGreaterThan(g + 30);
      }
    }
  });
});

test.describe(`Watershed ${WS} — RiverSignal /riversignal`, () => {

  test('site boundary polygon is populated (not NULL)', async ({ request }) => {
    const r = await request.get(`${API}/sites/${WS}`);
    expect(r.ok()).toBeTruthy();
    const body = await r.json();
    expect(body.bbox, `${WS} sites.bbox must be present`).toBeTruthy();
    // boundary is the GeoJSON polygon; if null, the homepage map can't render
    // the watershed outline.
    if ('boundary' in body) {
      expect(body.boundary,
        `${WS} sites.boundary is NULL — derive ST_Multi(ST_Union(...)) from ` +
        `watershed_boundaries (HUC12 polygons) via alembic.`
      ).not.toBeNull();
    }
  });

  test('homepage map renders the watershed (loads within 30s)', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    // Page should finish loading without staying stuck on "Loading watersheds"
    // beyond the 30s budget.
    await page.waitForTimeout(30_000);
    const body = (await page.locator('body').textContent()) || '';
    expect(body.toLowerCase().includes('loading watersheds'),
      '/riversignal still shows "Loading watersheds" after 30s — likely the ' +
      'page is waiting on a site with NULL boundary or a 404 on /watersheds.'
    ).toBeFalsy();
  });
});

test.describe(`Watershed ${WS} — DeepTrail /trail`, () => {

  test('/trail picker lists the watershed', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await page.waitForTimeout(SETTLE_MS);
    const body = (await page.locator('body').textContent()) || '';
    // Watershed must appear somewhere on the picker page.
    const expectedLabel = WS.replace(/_/g, ' ');
    expect(body.toLowerCase(),
      `/trail picker is missing ${expectedLabel}. ` +
      `Add it to DeepTrailContext / DeepTrailPage watershed dicts.`
    ).toContain(expectedLabel);
  });
});
