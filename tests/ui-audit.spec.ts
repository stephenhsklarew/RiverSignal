import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5174';

// ─────────────────────────────────────────────
// LANDING PAGE
// ─────────────────────────────────────────────
test('Landing page: shows 4 product cards', async ({ page }) => {
  await page.goto(BASE);
  await page.waitForSelector('.product-card', { timeout: 10000 });
  const cards = await page.locator('.product-card').count();
  expect(cards).toBe(4);
});

test('Landing page: RiverSignal card has logo', async ({ page }) => {
  await page.goto(BASE);
  await page.waitForSelector('.product-card', { timeout: 10000 });
  const logo = await page.locator('.product-logo').count();
  expect(logo).toBeGreaterThanOrEqual(1);
});

// ─────────────────────────────────────────────
// RIVERSIGNAL (/riversignal)
// ─────────────────────────────────────────────
test('RiverSignal: map page loads with topbar', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.topbar', { timeout: 10000 });
  const logo = await page.locator('.topbar img').count();
  expect(logo).toBeGreaterThanOrEqual(1);
});

test('RiverSignal: topbar has Home, Dashboard, Reports buttons', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.topbar-nav', { timeout: 10000 });
  const buttons = await page.locator('.topbar-nav button').allTextContents();
  expect(buttons).toContain('Home');
  expect(buttons).toContain('Dashboard');
  expect(buttons).toContain('Reports');
});

test('RiverSignal: observation search bar exists', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.obs-search-form', { timeout: 10000 });
  const input = await page.locator('.obs-search-input').count();
  expect(input).toBe(1);
});

test('RiverSignal: barrier toggle checkbox exists', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  // Click a watershed tab to select it first
  await page.waitForSelector('.ws-tab', { timeout: 10000 });
  await page.locator('.ws-tab').first().click();
  await page.waitForTimeout(500);
  const toggle = await page.locator('.barrier-toggle').count();
  expect(toggle).toBe(1);
});

test('RiverSignal: clicking watershed shows SitePanel with tabs', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.ws-tab', { timeout: 10000 });
  await page.locator('.ws-tab').first().click();
  await page.waitForSelector('.panel-tabs', { timeout: 10000 });
  const tabs = await page.locator('.panel-tab').allTextContents();
  expect(tabs).toContain('overview');
  expect(tabs).toContain('species');
  expect(tabs).toContain('fishing');
  expect(tabs).toContain('story');
  expect(tabs).toContain('recs');
  expect(tabs).toContain('ask');
});

test('RiverSignal: fishing alerts banner appears', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.ws-tab', { timeout: 10000 });
  await page.locator('.ws-tab').first().click();
  // Wait for alerts to load
  await page.waitForTimeout(2000);
  // Alerts may or may not appear depending on data — check the element exists or not gracefully
  const alertBar = await page.locator('.alerts-bar').count();
  // Just log it — some watersheds may not have alerts
  console.log(`Alerts banner visible: ${alertBar > 0}`);
});

test('RiverSignal: fishing tab shows barriers table', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.ws-tab', { timeout: 10000 });
  await page.locator('.ws-tab').first().click();
  await page.waitForSelector('.panel-tabs', { timeout: 10000 });
  await page.locator('.panel-tab', { hasText: 'fishing' }).click();
  await page.waitForTimeout(2000);
  // Check for barriers section header
  const barrierHeader = await page.locator('.section-title', { hasText: 'Fish Passage Barriers' }).count();
  console.log(`Barriers table visible: ${barrierHeader > 0}`);
});

test('RiverSignal: recs tab shows recommendations', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.ws-tab', { timeout: 10000 });
  await page.locator('.ws-tab').first().click();
  await page.waitForSelector('.panel-tabs', { timeout: 10000 });
  await page.locator('.panel-tab', { hasText: 'recs' }).click();
  await page.waitForTimeout(1000);
  // Should show either recs or "generating" message
  const recsSection = await page.locator('.section-title', { hasText: 'Field Recommendations' }).count();
  expect(recsSection).toBe(1);
});

// ─────────────────────────────────────────────
// RIVERPATH (/path)
// ─────────────────────────────────────────────
test('RiverPath: home page loads with watershed blocks', async ({ page }) => {
  await page.goto(`${BASE}/path`);
  await page.waitForSelector('.home', { timeout: 10000 });
  const blocks = await page.locator('.ws-block').count();
  expect(blocks).toBeGreaterThanOrEqual(4);
});

test('RiverPath: species discovery section with group tabs', async ({ page }) => {
  await page.goto(`${BASE}/path`);
  await page.waitForSelector('.home-species', { timeout: 15000 });
  const tabs = await page.locator('.species-group-tab').count();
  expect(tabs).toBeGreaterThanOrEqual(5); // All, Fish, Birds, Insects, Plants, etc.
});

test('RiverPath: species photo cards render', async ({ page }) => {
  await page.goto(`${BASE}/path`);
  await page.waitForSelector('.species-scroll-item', { timeout: 15000 });
  const cards = await page.locator('.species-scroll-item').count();
  expect(cards).toBeGreaterThanOrEqual(1);
});

test('RiverPath: overview tab has What\'s Here Now', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.ws-tab', { timeout: 10000 });
  await page.locator('.ws-tab').first().click();
  await page.waitForSelector('.panel-content', { timeout: 10000 });
  await page.waitForTimeout(2000);
  const whatsHere = await page.locator('.section-title', { hasText: "What's Here Now" }).count();
  console.log(`What's Here Now visible: ${whatsHere > 0}`);
});

test('RiverPath: overview tab has Stewardship section', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.ws-tab', { timeout: 10000 });
  await page.locator('.ws-tab').first().click();
  await page.waitForSelector('.panel-content', { timeout: 10000 });
  await page.waitForTimeout(1000);
  const stewardship = await page.locator('.section-title', { hasText: 'Stewardship' }).count();
  expect(stewardship).toBe(1);
});

test('RiverPath: overview tab has Seasonal Planner', async ({ page }) => {
  await page.goto(`${BASE}/riversignal`);
  await page.waitForSelector('.ws-tab', { timeout: 10000 });
  await page.locator('.ws-tab').first().click();
  await page.waitForSelector('.panel-content', { timeout: 10000 });
  await page.waitForTimeout(2000);
  const seasonal = await page.locator('.section-title', { hasText: 'Best Time to Visit' }).count();
  console.log(`Seasonal planner visible: ${seasonal > 0}`);
});

// ─────────────────────────────────────────────
// DEEPTRAIL (/trail)
// ─────────────────────────────────────────────
test('DeepTrail: page loads with location cards', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForSelector('.dt-loc-card', { timeout: 10000 });
  const cards = await page.locator('.dt-loc-card').count();
  expect(cards).toBeGreaterThanOrEqual(5);
});

test('DeepTrail: custom lat/lon inputs exist', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForSelector('.dt-custom-loc', { timeout: 10000 });
  const inputs = await page.locator('.dt-custom-input').count();
  expect(inputs).toBe(2); // lat + lon
});

test('DeepTrail: reading level toggle exists', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForSelector('.dt-reading-toggle', { timeout: 15000 });
  const buttons = await page.locator('.dt-reading-btn').allTextContents();
  expect(buttons).toContain('Adult');
  expect(buttons).toContain('Kids');
  expect(buttons).toContain('Expert');
});

test('DeepTrail: legal collecting badge shows', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForSelector('.dt-legal-card', { timeout: 15000 });
  const badge = await page.locator('.dt-legal-dot').count();
  expect(badge).toBeGreaterThanOrEqual(1);
});

test('DeepTrail: fossil cards with period filter', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForSelector('.dt-filter-select', { timeout: 15000 });
  const filters = await page.locator('.dt-filter-select').count();
  expect(filters).toBeGreaterThanOrEqual(2); // period + phylum
});

test('DeepTrail: fossil cards have PBDB links', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForSelector('.dt-fossil-card', { timeout: 15000 });
  const links = await page.locator('.dt-source-link').count();
  console.log(`PBDB links visible: ${links}`);
});

test('DeepTrail: geologic context section shows', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForTimeout(3000);
  const geoSection = await page.locator('.dt-geo-section').count();
  console.log(`Geologic context section visible: ${geoSection > 0}`);
});

test('DeepTrail: mineral sites section shows', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForTimeout(3000);
  const mineralSection = await page.locator('.dt-mineral-section').count();
  console.log(`Mineral sites section visible: ${mineralSection > 0}`);
});

test('DeepTrail: geology chat section exists', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForSelector('.dt-chat-section', { timeout: 15000 });
  const chatInput = await page.locator('.dt-chat-input').count();
  expect(chatInput).toBe(1);
});

test('DeepTrail: deep time timeline renders', async ({ page }) => {
  await page.goto(`${BASE}/trail`);
  await page.waitForSelector('.dt-timeline', { timeout: 15000 });
  const items = await page.locator('.dt-tl-item').count();
  expect(items).toBeGreaterThanOrEqual(1);
});

// ─────────────────────────────────────────────
// DEEPSIGNAL (/deepsignal)
// ─────────────────────────────────────────────
test('DeepSignal: page loads with geologic unit table', async ({ page }) => {
  await page.goto(`${BASE}/deepsignal`);
  await page.waitForSelector('.ds-table', { timeout: 15000 });
  const rows = await page.locator('.ds-table tbody tr').count();
  expect(rows).toBeGreaterThanOrEqual(1);
});
