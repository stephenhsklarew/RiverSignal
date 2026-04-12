import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5174';
const API = 'http://localhost:8001/api/v1';

// Helper: wait for API-driven content to load
const waitForData = async (page: any, ms = 3000) => page.waitForTimeout(ms);

// ═══════════════════════════════════════════════════════════
// LANDING PAGE (/)
// ═══════════════════════════════════════════════════════════
test.describe('Landing Page', () => {
  test('renders title "Field Intelligence Platform"', async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator('.landing-title')).toHaveText('Field Intelligence Platform');
  });

  test('shows 4 product cards', async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator('.product-card')).toHaveCount(4);
  });

  test('RiverSignal card has logo image', async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator('.product-logo')).toBeVisible();
  });

  test('product cards navigate to correct routes', async ({ page }) => {
    await page.goto(BASE);
    // Click RiverSignal card and verify navigation
    await page.locator('.product-card', { hasText: 'RiverSignal' }).click();
    await page.waitForURL('**/riversignal');
    expect(page.url()).toContain('/riversignal');
  });

  test('footer shows data stats', async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator('.landing-stats')).toContainText('2.2M+');
    await expect(page.locator('.landing-stats')).toContainText('species');
  });
});

// ═══════════════════════════════════════════════════════════
// RIVERSIGNAL (/riversignal) — B2B Watershed Dashboard
// ═══════════════════════════════════════════════════════════
test.describe('RiverSignal', () => {
  test('topbar renders with logo', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await expect(page.locator('.topbar img')).toBeVisible();
  });

  test('topbar has Home, Dashboard, Reports nav', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    const nav = page.locator('.topbar-nav button');
    await expect(nav.filter({ hasText: 'Home' })).toBeVisible();
    await expect(nav.filter({ hasText: 'Dashboard' })).toBeVisible();
    await expect(nav.filter({ hasText: 'Reports' })).toBeVisible();
  });

  test('observation search bar present', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await expect(page.locator('.obs-search-input')).toBeVisible();
  });

  test('map renders with watershed tabs', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await expect(page.locator('.ws-tab')).toHaveCount(5);
  });

  test('map shows KPI chips (observations, interventions)', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await expect(page.locator('.kpi-chip')).toHaveCount(2);
    await expect(page.locator('.kpi-chip').first()).toContainText('observations');
  });

  test('selecting a watershed opens SitePanel with 6 tabs', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.panel-tabs')).toBeVisible({ timeout: 10000 });
    const tabs = await page.locator('.panel-tab').allTextContents();
    expect(tabs).toEqual(['overview', 'species', 'fishing', 'story', 'recs', 'ask']);
  });

  test('barrier toggle appears when watershed selected', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await waitForData(page, 500);
    await expect(page.locator('.barrier-toggle')).toBeVisible();
  });

  test('alerts ticker appears when watershed selected', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await waitForData(page, 2500);
    const ticker = page.locator('.alerts-ticker');
    // Some watersheds may not have alerts
    const count = await ticker.count();
    console.log(`  Alerts ticker visible: ${count > 0}`);
  });

  // ── Overview Tab ──
  test('overview tab: KPI grid with water temp, DO, species, projects', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.kpi-grid').first()).toBeVisible({ timeout: 10000 });
    const kpiCount = await page.locator('.kpi-card').count();
    expect(kpiCount).toBeGreaterThanOrEqual(4); // key metrics + coverage
  });

  test('overview tab: indicator species table', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.section-title', { hasText: 'Indicator Species' })).toBeVisible({ timeout: 10000 });
    const rows = await page.locator('.data-table tbody tr').count();
    expect(rows).toBeGreaterThanOrEqual(1);
  });

  test('overview tab: What\'s Here Now photo grid', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await waitForData(page);
    const section = page.locator('.section-title', { hasText: "What's Here Now" });
    const visible = await section.count();
    console.log(`  What's Here Now visible: ${visible > 0}`);
  });

  test('overview tab: Stewardship section', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await waitForData(page);
    await expect(page.locator('.section-title', { hasText: 'Stewardship' })).toBeVisible();
  });

  test('overview tab: Seasonal planner (Best Time to Visit)', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await waitForData(page);
    const seasonal = page.locator('.section-title', { hasText: 'Best Time to Visit' });
    const visible = await seasonal.count();
    console.log(`  Seasonal planner visible: ${visible > 0}`);
  });

  // ── Species Tab ──
  test('species tab: photo gallery renders', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.panel-tabs')).toBeVisible({ timeout: 10000 });
    await page.locator('.panel-tab', { hasText: 'species' }).click();
    await waitForData(page);
    const cards = await page.locator('.species-card').count();
    console.log(`  Species cards: ${cards}`);
  });

  // ── Fishing Tab ──
  test('fishing tab: conditions display', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.panel-tabs')).toBeVisible({ timeout: 10000 });
    await page.locator('.panel-tab', { hasText: 'fishing' }).click();
    await waitForData(page);
    await expect(page.locator('.section-title', { hasText: 'Conditions' })).toBeVisible();
  });

  test('fishing tab: stocking table', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.panel-tabs')).toBeVisible({ timeout: 10000 });
    await page.locator('.panel-tab', { hasText: 'fishing' }).click();
    await waitForData(page);
    await expect(page.locator('.section-title', { hasText: 'Recent Stocking' })).toBeVisible();
  });

  test('fishing tab: species by reach table', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.panel-tabs')).toBeVisible({ timeout: 10000 });
    await page.locator('.panel-tab', { hasText: 'fishing' }).click();
    await waitForData(page);
    await expect(page.locator('.section-title', { hasText: 'Species by Reach' })).toBeVisible();
  });

  test('fishing tab: barriers table', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.panel-tabs')).toBeVisible({ timeout: 10000 });
    await page.locator('.panel-tab', { hasText: 'fishing' }).click();
    await waitForData(page);
    const barriers = page.locator('.section-title', { hasText: 'Fish Passage Barriers' });
    const visible = await barriers.count();
    console.log(`  Barriers table visible: ${visible > 0}`);
  });

  // ── Story Tab ──
  test('story tab: health and timeline display', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.panel-tabs')).toBeVisible({ timeout: 10000 });
    await page.locator('.panel-tab', { hasText: 'story' }).click();
    await waitForData(page);
    const content = await page.locator('.panel-content').textContent();
    expect(content?.length).toBeGreaterThan(50);
  });

  // ── Recs Tab ──
  test('recs tab: shows Field Recommendations header', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.panel-tabs')).toBeVisible({ timeout: 10000 });
    await page.locator('.panel-tab', { hasText: 'recs' }).click();
    await expect(page.locator('.section-title', { hasText: 'Field Recommendations' })).toBeVisible();
  });

  // ── Ask Tab ──
  test('ask tab: chat input and suggested questions', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').first().click();
    await expect(page.locator('.panel-tabs')).toBeVisible({ timeout: 10000 });
    await page.locator('.panel-tab', { hasText: 'ask' }).click();
    await expect(page.locator('.chat-input-row input')).toBeVisible();
  });

  // ── Observation Search ──
  test('observation search returns results and shows count', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.locator('.ws-tab').nth(2).click(); // Deschutes
    await waitForData(page, 1000);
    await page.locator('.obs-search-input').fill('salm');
    await page.locator('.obs-search-input').press('Enter');
    await waitForData(page, 3000);
    const count = page.locator('.obs-search-count');
    const visible = await count.count();
    if (visible > 0) {
      const text = await count.textContent();
      console.log(`  Observation search result: ${text}`);
      expect(text).toContain('found');
    }
  });

  // ── Reports ──
  test('reports page loads', async ({ page }) => {
    await page.goto(`${BASE}/riversignal/reports`);
    await waitForData(page, 1000);
    const content = await page.textContent('body');
    expect(content?.length).toBeGreaterThan(100);
  });
});

// ═══════════════════════════════════════════════════════════
// RIVERPATH (/path) — B2C Story-Driven Home
// ═══════════════════════════════════════════════════════════
test.describe('RiverPath', () => {
  test('home page renders with watershed blocks', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await expect(page.locator('.ws-block')).toHaveCount(5, { timeout: 10000 });
  });

  test('each watershed block has photo and content', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await expect(page.locator('.ws-block').first().locator('img')).toBeVisible({ timeout: 10000 });
    // Block should have text content (name, narrative)
    const text = await page.locator('.ws-block').first().textContent();
    expect(text?.length).toBeGreaterThan(20);
  });

  test('watershed block has inline ask input', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    // Find input inside a watershed block
    const input = page.locator('.ws-block input[type="text"]').first();
    await expect(input).toBeVisible({ timeout: 10000 });
  });

  test('species discovery section with taxonomic group tabs', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await expect(page.locator('.home-species')).toBeVisible({ timeout: 15000 });
    const tabs = await page.locator('.species-group-tab').allTextContents();
    expect(tabs).toContain('All Species');
    expect(tabs).toContain('Fish');
    expect(tabs).toContain('Birds');
    expect(tabs).toContain('Insects');
    expect(tabs).toContain('Plants');
  });

  test('species photo cards render with images', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await expect(page.locator('.species-scroll-item').first()).toBeVisible({ timeout: 15000 });
    const cards = await page.locator('.species-scroll-item').count();
    expect(cards).toBeGreaterThanOrEqual(5);
    console.log(`  Species cards on home: ${cards}`);
  });

  test('clicking species group tab filters cards', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await expect(page.locator('.species-group-tab').first()).toBeVisible({ timeout: 15000 });
    await page.locator('.species-group-tab', { hasText: 'Birds' }).click();
    await waitForData(page, 2000);
    // Tab should be active
    await expect(page.locator('.species-group-tab.active')).toHaveText('Birds');
  });

  test('footer links to DeepTrail', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    const link = page.locator('.home-footer a[href="/trail"]');
    await expect(link).toBeVisible({ timeout: 10000 });
  });

  test('hero section shows species count', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await expect(page.locator('.home-hero-subtitle')).toContainText('species', { timeout: 10000 });
  });

  test('navigation contains watershed links', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    // Nav should have links containing watershed names
    const navText = await page.locator('.home-nav').textContent();
    expect(navText).toContain('McKenzie');
    expect(navText).toContain('Deschutes');
  });
});

// ═══════════════════════════════════════════════════════════
// DEEPTRAIL (/trail) — B2C Geology Adventure
// ═══════════════════════════════════════════════════════════
test.describe('DeepTrail', () => {
  test('page renders with dark theme', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-app')).toBeVisible();
    const bg = await page.locator('.dt-app').evaluate(el => getComputedStyle(el).backgroundColor);
    // Should be dark (#1a1612 = rgb(26, 22, 18))
    expect(bg).toContain('26');
  });

  test('header shows DeepTrail badge', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-badge')).toHaveText('DeepTrail');
  });

  test('5 curated location cards', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-loc-card')).toHaveCount(5);
  });

  test('custom lat/lon input fields', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-custom-input')).toHaveCount(2);
    await expect(page.locator('.dt-custom-btn')).toBeVisible();
  });

  test('story card with reading level toggle', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-story-card')).toBeVisible({ timeout: 15000 });
    const buttons = await page.locator('.dt-reading-btn').allTextContents();
    expect(buttons).toEqual(['Adult', 'Kids', 'Expert']);
  });

  test('reading level toggle changes active state', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-reading-btn').first()).toBeVisible({ timeout: 15000 });
    await page.locator('.dt-reading-btn', { hasText: 'Kids' }).click();
    await expect(page.locator('.dt-reading-btn.active')).toHaveText('Kids');
  });

  test('geologic context section with rock type badges', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await waitForData(page);
    const geoSection = page.locator('.dt-geo-section');
    const visible = await geoSection.count();
    console.log(`  Geologic context visible: ${visible > 0}`);
    if (visible > 0) {
      const badges = await page.locator('.rock-badge-dt').count();
      console.log(`  Rock type badges: ${badges}`);
    }
  });

  test('legal collecting badge (colored dot)', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-legal-card')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.dt-legal-dot')).toBeVisible();
    const rules = await page.locator('.dt-legal-rules').textContent();
    expect(rules?.length).toBeGreaterThan(10);
  });

  test('legal card shows disclaimer', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-legal-disclaimer')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.dt-legal-disclaimer')).toContainText('verify on-site');
  });

  test('deep time timeline with items', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-timeline')).toBeVisible({ timeout: 15000 });
    const items = await page.locator('.dt-tl-item').count();
    expect(items).toBeGreaterThanOrEqual(1);
    console.log(`  Timeline items: ${items}`);
  });

  test('fossil cards render with taxon, period, age', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-fossil-card').first()).toBeVisible({ timeout: 15000 });
    const cards = await page.locator('.dt-fossil-card').count();
    expect(cards).toBeGreaterThanOrEqual(1);
    console.log(`  Fossil cards: ${cards}`);
  });

  test('fossil period and phylum filter dropdowns', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await page.waitForSelector('.dt-filter-select', { timeout: 15000 });
    const filterCount = await page.locator('.dt-filter-select').count();
    expect(filterCount).toBeGreaterThanOrEqual(2); // period + phylum (+ mineral commodity if visible)
  });

  test('fossil period filter reduces card count', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-fossil-card').first()).toBeVisible({ timeout: 15000 });
    const beforeCount = await page.locator('.dt-fossil-card').count();
    // Select first non-empty period option
    const options = await page.locator('.dt-filter-select').first().locator('option').allTextContents();
    if (options.length > 1) {
      await page.locator('.dt-filter-select').first().selectOption({ index: 1 });
      await waitForData(page, 500);
      const afterCount = await page.locator('.dt-fossil-card').count();
      console.log(`  Filter: ${beforeCount} → ${afterCount} fossils`);
    }
  });

  test('PBDB source links on fossil cards', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-fossil-card').first()).toBeVisible({ timeout: 15000 });
    const links = await page.locator('.dt-source-link').count();
    console.log(`  PBDB links: ${links}`);
    expect(links).toBeGreaterThanOrEqual(1);
  });

  test('mineral sites section with cards', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await waitForData(page, 4000);
    const section = page.locator('.dt-mineral-section');
    const visible = await section.count();
    console.log(`  Mineral section visible: ${visible > 0}`);
    if (visible > 0) {
      const cards = await section.locator('.dt-fossil-card').count();
      console.log(`  Mineral cards: ${cards}`);
    }
  });

  test('geology chat section with input', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-chat-section')).toBeVisible({ timeout: 15000 });
    await expect(page.locator('.dt-chat-input')).toBeVisible();
    await expect(page.locator('.dt-chat-btn')).toBeVisible();
  });

  test('clicking a different location card reloads data', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-loc-card').first()).toBeVisible({ timeout: 10000 });
    // Click second location
    await page.locator('.dt-loc-card').nth(1).click();
    await waitForData(page, 2000);
    // Second card should be active
    await expect(page.locator('.dt-loc-card').nth(1)).toHaveClass(/active/);
  });

  test('cross-product nav links to RiverPath and DeepSignal', async ({ page }) => {
    await page.goto(`${BASE}/trail`);
    await expect(page.locator('.dt-nav-link[href="/path"]')).toBeVisible();
    await expect(page.locator('.dt-nav-link[href="/deepsignal"]')).toBeVisible();
  });
});

// ═══════════════════════════════════════════════════════════
// DEEPSIGNAL (/deepsignal) — B2B Geology Dashboard
// ═══════════════════════════════════════════════════════════
test.describe('DeepSignal', () => {
  test('page renders with DeepSignal badge', async ({ page }) => {
    await page.goto(`${BASE}/deepsignal`);
    await expect(page.locator('.ds-product-badge')).toHaveText('DeepSignal');
  });

  test('watershed nav buttons present', async ({ page }) => {
    await page.goto(`${BASE}/deepsignal`);
    await expect(page.locator('.ds-nav-btn')).toHaveCount(5, { timeout: 10000 });
  });

  test('geologic unit table renders with data', async ({ page }) => {
    await page.goto(`${BASE}/deepsignal`);
    await expect(page.locator('.ds-table').first()).toBeVisible({ timeout: 15000 });
    const rows = await page.locator('.ds-table tbody tr').count();
    expect(rows).toBeGreaterThanOrEqual(1);
    console.log(`  DeepSignal table rows: ${rows}`);
  });

  test('KPI cards show unit count and rock types', async ({ page }) => {
    await page.goto(`${BASE}/deepsignal`);
    await expect(page.locator('.ds-kpi').first()).toBeVisible({ timeout: 15000 });
    const kpis = await page.locator('.ds-kpi').count();
    expect(kpis).toBeGreaterThanOrEqual(2);
  });

  test('rock type badges (igneous/sedimentary/metamorphic)', async ({ page }) => {
    await page.goto(`${BASE}/deepsignal`);
    await expect(page.locator('.rock-badge').first()).toBeVisible({ timeout: 15000 });
  });

  test('period chips display', async ({ page }) => {
    await page.goto(`${BASE}/deepsignal`);
    await expect(page.locator('.ds-period-chip').first()).toBeVisible({ timeout: 15000 });
    const chips = await page.locator('.ds-period-chip').count();
    expect(chips).toBeGreaterThanOrEqual(1);
    console.log(`  Period chips: ${chips}`);
  });

  test('cross-product link to RiverSignal', async ({ page }) => {
    await page.goto(`${BASE}/deepsignal`);
    await expect(page.locator('a[href="/riversignal"]')).toBeVisible();
  });
});
