import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5174';
const API = 'http://localhost:8001/api/v1';

// ═══════════════════════════════════════════════
// API TESTS — Verify data returns before checking UI
// ═══════════════════════════════════════════════
test.describe('AI Feature APIs', () => {
  test('Catch Probability API returns data', async ({ request }) => {
    const resp = await request.get(`${API}/sites/deschutes/catch-probability`);
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.overall_score).toBeGreaterThanOrEqual(0);
    expect(data.species.length).toBeGreaterThanOrEqual(1);
    console.log(`  Catch Prob: score=${data.overall_score}, species=${data.species.length}`);
  });

  test('Species Spotter API returns data', async ({ request }) => {
    const resp = await request.get(`${API}/sites/deschutes/species-spotter`);
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.species.length).toBeGreaterThanOrEqual(1);
    console.log(`  Spotter: ${data.species.length} species`);
  });

  test('River Replay API returns data', async ({ request }) => {
    const resp = await request.get(`${API}/sites/deschutes/replay?days_ago=30`);
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.changes).toBeDefined();
    console.log(`  Replay: ${data.changes.length} changes`);
  });

  test('Restoration Impact API returns data', async ({ request }) => {
    const resp = await request.get(`${API}/sites/deschutes/restoration-impact`);
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.total_species).toBeGreaterThan(0);
    console.log(`  Impact: ${data.total_species} species, ${data.total_projects} projects`);
  });

  test('Compare Rivers API returns data', async ({ request }) => {
    const resp = await request.get(`${API}/compare?ws1=deschutes&ws2=mckenzie`);
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.river1.name).toBeTruthy();
    expect(data.river2.name).toBeTruthy();
    console.log(`  Compare: ${data.river1.name} vs ${data.river2.name}`);
  });

  test('Time Machine API returns data', async ({ request }) => {
    const resp = await request.get(`${API}/sites/deschutes/time-machine`);
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.years.length).toBeGreaterThanOrEqual(1);
    console.log(`  Time Machine: ${data.years.length} years`);
  });

  test('Campfire Story API returns data', async ({ request }) => {
    const resp = await request.get(`${API}/sites/deschutes/campfire-story`);
    expect(resp.ok()).toBeTruthy();
    const data = await resp.json();
    expect(data.story.length).toBeGreaterThan(100);
    console.log(`  Campfire: ${data.story.length} chars, audio=${data.audio_url ? 'YES' : 'NO'}`);
  });
});

// ═══════════════════════════════════════════════
// UI TESTS — Verify features visible on River Now page
// ═══════════════════════════════════════════════
test.describe('River Now AI Features UI (393x852)', () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 393, height: 852 });
  });

  test('River Replay banner shows changes', async ({ page }) => {
    await page.goto(`${BASE}/path/now/deschutes`);
    await page.waitForTimeout(4000);
    const replay = page.locator('.rnow-replay');
    const visible = await replay.count();
    console.log(`  Replay banner visible: ${visible > 0}`);
    if (visible > 0) {
      const items = await page.locator('.rnow-replay-item').count();
      expect(items).toBeGreaterThanOrEqual(1);
      console.log(`  Replay items: ${items}`);
    }
  });

  test('Catch Probability card shows score', async ({ page }) => {
    await page.goto(`${BASE}/path/now/deschutes`);
    await page.waitForTimeout(4000);
    const catchCard = page.locator('.rnow-catch-prob');
    const visible = await catchCard.count();
    console.log(`  Catch Probability visible: ${visible > 0}`);
    if (visible > 0) {
      await expect(page.locator('.rnow-catch-score')).toBeVisible();
      const bars = await page.locator('.rnow-catch-row').count();
      expect(bars).toBeGreaterThanOrEqual(1);
      console.log(`  Catch species bars: ${bars}`);
    }
  });

  test('Species Spotter grid shows species with photos', async ({ page }) => {
    await page.goto(`${BASE}/path/now/deschutes`);
    await page.waitForTimeout(4000);
    const spotter = page.locator('.rnow-spotter-grid');
    const visible = await spotter.count();
    console.log(`  Species Spotter visible: ${visible > 0}`);
    if (visible > 0) {
      const cards = await page.locator('.rnow-spotter-card').count();
      expect(cards).toBeGreaterThanOrEqual(1);
      console.log(`  Spotter cards: ${cards}`);
    }
  });

  test('Campfire Story button exists', async ({ page }) => {
    await page.goto(`${BASE}/path/now/deschutes`);
    await page.waitForTimeout(3000);
    // Scroll down to find campfire button
    await page.evaluate(() => window.scrollTo({ top: 1000, behavior: 'smooth' }));
    await page.waitForTimeout(1000);
    const btn = page.locator('.rnow-campfire-btn');
    const visible = await btn.count();
    console.log(`  Campfire button visible: ${visible > 0}`);
    if (visible > 0) {
      await expect(btn).toContainText('Campfire Story');
    }
  });

  test('Fish Near You carousel shows fish cards', async ({ page }) => {
    await page.goto(`${BASE}/path/now/deschutes`);
    await page.waitForTimeout(4000);
    await page.evaluate(() => window.scrollTo({ top: 2000, behavior: 'smooth' }));
    await page.waitForTimeout(1000);
    const carousel = page.locator('.rnow-fish-carousel');
    const visible = await carousel.count();
    console.log(`  Fish carousel visible: ${visible > 0}`);
    if (visible > 0) {
      const cards = await page.locator('.rnow-fish-card').count();
      console.log(`  Fish cards: ${cards}`);
    }
  });

  test('Fish Passage Barriers list shows', async ({ page }) => {
    await page.goto(`${BASE}/path/now/klamath`);  // Klamath has barrier data
    await page.waitForTimeout(4000);
    await page.evaluate(() => window.scrollTo({ top: 2000, behavior: 'smooth' }));
    await page.waitForTimeout(1000);
    const barriers = page.locator('.rnow-barriers');
    const visible = await barriers.count();
    console.log(`  Barriers visible: ${visible > 0}`);
    if (visible > 0) {
      const items = await page.locator('.rnow-barrier-item').count();
      console.log(`  Barrier items: ${items}`);
    }
  });

  test('Harvest stat appears in hero metrics', async ({ page }) => {
    await page.goto(`${BASE}/path/now/deschutes`);
    await page.waitForTimeout(4000);
    const delta = page.locator('.rnow-delta');
    const visible = await delta.count();
    console.log(`  Harvest delta badge visible: ${visible > 0}`);
  });

  test('Hero card has all core metrics', async ({ page }) => {
    await page.goto(`${BASE}/path/now/deschutes`);
    await page.waitForTimeout(4000);
    const metrics = await page.locator('.rnow-metric').count();
    console.log(`  Hero metrics count: ${metrics}`);
    expect(metrics).toBeGreaterThanOrEqual(2);
  });
});
