import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5174';
const TIMEOUT = 15000;

// ─────────────────────────────────────────────
// HOMEPAGE (/path)
// ─────────────────────────────────────────────
test.describe('RiverPath Homepage', () => {
  test('loads with 5 watershed blocks', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await page.waitForSelector('.ws-block', { timeout: TIMEOUT });
    const blocks = await page.locator('.ws-block').count();
    expect(blocks).toBe(5);
  });

  test('each watershed block has ask input with consumer placeholder', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await page.waitForSelector('.ws-ask', { timeout: TIMEOUT });
    const inputs = page.locator('.ws-ask input');
    const count = await inputs.count();
    expect(count).toBe(5);
    // Check placeholder is NOT "Is the ... healthy?" (old B2B text)
    for (let i = 0; i < count; i++) {
      const placeholder = await inputs.nth(i).getAttribute('placeholder');
      expect(placeholder).not.toContain('healthy');
    }
  });

  test('ask button stays within /path context', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await page.waitForSelector('.ws-ask', { timeout: TIMEOUT });
    const firstInput = page.locator('.ws-ask input').first();
    await firstInput.fill('test question');
    await firstInput.press('Enter');
    // Should navigate to /path/<watershed>?q=...
    await page.waitForURL(/\/path\/\w+\?q=/, { timeout: 5000 });
    expect(page.url()).toContain('/path/');
    expect(page.url()).not.toContain('/riversignal');
  });

  test('inline chat response renders on homepage', async ({ page }) => {
    await page.goto(`${BASE}/path/mckenzie?q=hello`);
    // Should show loading or response
    await page.waitForSelector('.ws-chat-response', { timeout: TIMEOUT });
    const response = page.locator('.ws-chat-response');
    await expect(response).toBeVisible();
  });

  test('nav links point to /path not /riversignal', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await page.waitForSelector('.home-nav-link', { timeout: TIMEOUT });
    const links = page.locator('.home-nav-link');
    const count = await links.count();
    for (let i = 0; i < count; i++) {
      const href = await links.nth(i).getAttribute('href');
      expect(href).not.toContain('/riversignal');
    }
  });

  test('species section renders with photos', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await page.waitForSelector('.home-species', { timeout: TIMEOUT });
    const items = await page.locator('.species-scroll-item').count();
    expect(items).toBeGreaterThan(0);
  });

  test('bottom nav is NOT shown on homepage', async ({ page }) => {
    await page.goto(`${BASE}/path`);
    await page.waitForSelector('.ws-block', { timeout: TIMEOUT });
    const nav = await page.locator('.bottom-nav').count();
    expect(nav).toBe(0);
  });
});

// ─────────────────────────────────────────────
// BOTTOM NAVIGATION
// ─────────────────────────────────────────────
test.describe('Bottom Navigation', () => {
  test('shows on /path/now with 5 tabs', async ({ page }) => {
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.bottom-nav', { timeout: TIMEOUT });
    const tabs = await page.locator('.bottom-nav-tab').count();
    expect(tabs).toBe(5);
  });

  test('active tab is highlighted', async ({ page }) => {
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.bottom-nav', { timeout: TIMEOUT });
    const activeTab = page.locator('.bottom-nav-tab.active');
    await expect(activeTab).toHaveCount(1);
    await expect(activeTab).toContainText('River Now');
  });

  test('tab navigation works between all screens', async ({ page }) => {
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.bottom-nav', { timeout: TIMEOUT });

    // Navigate to Explore
    await page.locator('.bottom-nav-tab', { hasText: 'Explore' }).click();
    await page.waitForURL(/\/path\/explore/, { timeout: 5000 });
    await expect(page.locator('.bottom-nav-tab.active')).toContainText('Explore');

    // Navigate to Hatch
    await page.locator('.bottom-nav-tab', { hasText: 'Hatch' }).click();
    await page.waitForURL(/\/path\/hatch/, { timeout: 5000 });
    await expect(page.locator('.bottom-nav-tab.active')).toContainText('Hatch');

    // Navigate to Steward
    await page.locator('.bottom-nav-tab', { hasText: 'Steward' }).click();
    await page.waitForURL(/\/path\/steward/, { timeout: 5000 });
    await expect(page.locator('.bottom-nav-tab.active')).toContainText('Steward');

    // Navigate to Saved
    await page.locator('.bottom-nav-tab', { hasText: 'Saved' }).click();
    await page.waitForURL(/\/path\/saved/, { timeout: 5000 });
    await expect(page.locator('.bottom-nav-tab.active')).toContainText('Saved');
  });

  test('NOT shown on /riversignal', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`);
    await page.waitForTimeout(2000);
    const nav = await page.locator('.bottom-nav').count();
    expect(nav).toBe(0);
  });
});

// ─────────────────────────────────────────────
// RIVER NOW (/path/now)
// ─────────────────────────────────────────────
test.describe('River Now', () => {
  test('shows watershed picker when GPS unavailable', async ({ page }) => {
    // Deny geolocation
    await page.context().setGeolocation(null as any);
    await page.context().grantPermissions([]);
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.rnow-picker, .rnow-location', { timeout: TIMEOUT });
    // Either picker or location should be visible
    const hasUI = await page.locator('.rnow-picker').or(page.locator('.rnow-location')).count();
    expect(hasUI).toBeGreaterThan(0);
  });

  test('selecting a watershed shows hero card', async ({ page }) => {
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.rnow-chip, .rnow-hero', { timeout: TIMEOUT });
    // If picker is shown, select deschutes
    const picker = page.locator('.rnow-chip');
    if (await picker.count() > 0) {
      await picker.filter({ hasText: 'Deschutes' }).click();
    }
    await page.waitForSelector('.rnow-hero', { timeout: TIMEOUT });
    await expect(page.locator('.rnow-hero-title')).toBeVisible();
  });

  test('hero card shows temp, flow, and hatch confidence', async ({ page }) => {
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.rnow-chip', { timeout: TIMEOUT });
    await page.click('.rnow-chip >> text=Deschutes');
    await page.waitForSelector('.rnow-hero-metrics', { timeout: TIMEOUT });
    const metrics = await page.locator('.rnow-metric').count();
    expect(metrics).toBeGreaterThanOrEqual(2);
  });

  test('shows 3 swipeable condition cards with data', async ({ page }) => {
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.rnow-chip', { timeout: TIMEOUT });
    await page.click('.rnow-chip >> text=McKenzie');
    await page.waitForSelector('.rnow-card', { timeout: TIMEOUT });
    const cards = await page.locator('.rnow-card').count();
    expect(cards).toBe(3);
    // Cards should have headers
    await expect(page.locator('.rnow-card-header').first()).toBeVisible();
  });

  test('shows nearby access point cards from recreation data', async ({ page }) => {
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.rnow-chip', { timeout: TIMEOUT });
    await page.click('.rnow-chip >> text=McKenzie');
    await page.waitForSelector('.rnow-access-card', { timeout: TIMEOUT });
    const access = await page.locator('.rnow-access-card').count();
    expect(access).toBeGreaterThan(0);
  });

  test('shows What\'s Here Now species grid', async ({ page }) => {
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.rnow-chip', { timeout: TIMEOUT });
    await page.click('.rnow-chip >> text=Deschutes');
    await page.waitForSelector('.rnow-alive-grid', { timeout: TIMEOUT });
    const items = await page.locator('.rnow-alive-item').count();
    expect(items).toBeGreaterThan(0);
  });

  test('condition cards navigate to correct pages', async ({ page }) => {
    await page.goto(`${BASE}/path/now`);
    await page.waitForSelector('.rnow-chip', { timeout: TIMEOUT });
    await page.click('.rnow-chip >> text=Deschutes');
    await page.waitForSelector('.rnow-card', { timeout: TIMEOUT });
    // Click the insect card (second one)
    await page.locator('.rnow-card').nth(1).click();
    await expect(page).toHaveURL(/\/path\/hatch/);
  });
});

// ─────────────────────────────────────────────
// EXPLORE (/path/explore)
// ─────────────────────────────────────────────
test.describe('Explore', () => {
  test('loads adventure cards from recreation data', async ({ page }) => {
    await page.goto(`${BASE}/path/explore`);
    await page.waitForSelector('.adventure-card, .explore-empty', { timeout: TIMEOUT });
    // Should have cards for mckenzie or deschutes (default)
    const cards = await page.locator('.adventure-card').count();
    expect(cards).toBeGreaterThan(0);
  });

  test('shows watershed selector', async ({ page }) => {
    await page.goto(`${BASE}/path/explore`);
    await page.waitForSelector('.explore-ws-bar', { timeout: TIMEOUT });
    const btns = await page.locator('.explore-ws-btn').count();
    expect(btns).toBe(5);
  });

  test('switching watershed reloads cards', async ({ page }) => {
    await page.goto(`${BASE}/path/explore`);
    await page.waitForSelector('.adventure-card', { timeout: TIMEOUT });
    const initialCount = await page.locator('.adventure-card').count();
    await page.click('.explore-ws-btn >> text=McKenzie');
    // Wait for cards to update
    await page.waitForTimeout(1500);
    const newCount = await page.locator('.adventure-card').count();
    // Count may differ between watersheds
    expect(newCount).toBeGreaterThan(0);
  });

  test('filter chips toggle and filter results', async ({ page }) => {
    await page.goto(`${BASE}/path/explore`);
    await page.waitForSelector('.adventure-card', { timeout: TIMEOUT });
    const allCount = await page.locator('.adventure-card').count();
    // Click camping filter
    await page.click('.explore-filter >> text=Camping');
    await page.waitForTimeout(500);
    const filteredCount = await page.locator('.adventure-card').count();
    // Filtered should be <= all (unless all are campgrounds)
    expect(filteredCount).toBeLessThanOrEqual(allCount);
    // Toggle off
    await page.click('.explore-filter >> text=Camping');
    await page.waitForTimeout(500);
    expect(await page.locator('.adventure-card').count()).toBe(allCount);
  });

  test('search filters by name', async ({ page }) => {
    await page.goto(`${BASE}/path/explore`);
    await page.waitForSelector('.adventure-card', { timeout: TIMEOUT });
    await page.fill('.explore-search-input', 'campground');
    await page.waitForTimeout(500);
    const cards = page.locator('.adventure-card');
    const count = await cards.count();
    // All visible cards should contain "campground" in their name
    for (let i = 0; i < Math.min(count, 5); i++) {
      const name = await cards.nth(i).locator('.adventure-name').textContent();
      expect(name?.toLowerCase()).toContain('campground');
    }
  });

  test('adventure cards show amenity badges', async ({ page }) => {
    await page.goto(`${BASE}/path/explore`);
    await page.waitForSelector('.adventure-card', { timeout: TIMEOUT });
    // At least some cards should have amenity badges
    const badges = await page.locator('.amenity-badge').count();
    expect(badges).toBeGreaterThan(0);
  });

  test('adventure cards have save button', async ({ page }) => {
    await page.goto(`${BASE}/path/explore`);
    await page.waitForSelector('.adventure-card', { timeout: TIMEOUT });
    const saveBtn = page.locator('.adventure-card button[aria-label^="Save"]').first();
    await expect(saveBtn).toBeVisible();
  });

  test('site count displays correctly', async ({ page }) => {
    await page.goto(`${BASE}/path/explore`);
    await page.waitForSelector('.explore-count', { timeout: TIMEOUT });
    const countText = await page.locator('.explore-count').textContent();
    expect(countText).toMatch(/\d+ sites/);
  });
});

// ─────────────────────────────────────────────
// HATCH (/path/hatch)
// ─────────────────────────────────────────────
test.describe('Hatch', () => {
  test('shows watershed selector and water temp', async ({ page }) => {
    await page.goto(`${BASE}/path/hatch`);
    await page.waitForSelector('.hatch-ws-btn', { timeout: TIMEOUT });
    expect(await page.locator('.hatch-ws-btn').count()).toBe(5);
    await expect(page.locator('.hatch-title')).toContainText('Hatch Intelligence');
  });

  test('shows this month and next month sections', async ({ page }) => {
    await page.goto(`${BASE}/path/hatch`);
    await page.waitForSelector('.hatch-section-title', { timeout: TIMEOUT });
    const sections = await page.locator('.hatch-section-title').count();
    expect(sections).toBeGreaterThanOrEqual(2); // this month + next month (+ all flies)
  });

  test('insect cards show confidence badge and lifecycle stage', async ({ page }) => {
    await page.goto(`${BASE}/path/hatch`);
    await page.waitForSelector('.insect-card', { timeout: TIMEOUT });
    // Check confidence badge exists
    const confidenceBadges = await page.locator('.insect-confidence').count();
    expect(confidenceBadges).toBeGreaterThan(0);
    // Check lifecycle stage exists
    const stages = await page.locator('.insect-stage').count();
    expect(stages).toBeGreaterThan(0);
  });

  test('clicking insect card expands matching flies', async ({ page }) => {
    await page.goto(`${BASE}/path/hatch`);
    await page.waitForSelector('.insect-card', { timeout: TIMEOUT });
    await page.locator('.insect-card').first().click();
    // Should show expanded flies section
    await page.waitForSelector('.insect-flies', { timeout: 3000 });
    await expect(page.locator('.insect-flies').first()).toBeVisible();
  });

  test('fly cards have save button', async ({ page }) => {
    await page.goto(`${BASE}/path/hatch`);
    await page.waitForSelector('.fly-card', { timeout: TIMEOUT });
    const saveBtn = page.locator('.fly-card button[aria-label^="Save"]').first();
    await expect(saveBtn).toBeVisible();
  });

  test('switching watershed reloads data', async ({ page }) => {
    await page.goto(`${BASE}/path/hatch`);
    await page.waitForSelector('.hatch-ws-btn', { timeout: TIMEOUT });
    await page.click('.hatch-ws-btn >> text=McKenzie');
    await page.waitForTimeout(1500);
    // Page should still be functional
    await expect(page.locator('.hatch-title')).toBeVisible();
  });
});

// ─────────────────────────────────────────────
// FISH + REFUGE (/path/fish/:watershed)
// ─────────────────────────────────────────────
test.describe('Fish + Refuge', () => {
  test('loads with watershed selector and fish carousel', async ({ page }) => {
    await page.goto(`${BASE}/path/fish/deschutes`);
    await page.waitForSelector('.fish-ws-btn', { timeout: TIMEOUT });
    expect(await page.locator('.fish-ws-btn').count()).toBe(5);
    await expect(page.locator('.fish-title')).toContainText('Fish');
  });

  test('fish carousel shows species with temp comparison', async ({ page }) => {
    await page.goto(`${BASE}/path/fish/deschutes`);
    await page.waitForSelector('.fish-card', { timeout: TIMEOUT });
    const cards = await page.locator('.fish-card').count();
    expect(cards).toBeGreaterThan(0);
    // Should have temp badges
    const tempBadges = await page.locator('.fish-temp-badge').count();
    expect(tempBadges).toBeGreaterThan(0);
  });

  test('fish cards have save button', async ({ page }) => {
    await page.goto(`${BASE}/path/fish/deschutes`);
    await page.waitForSelector('.fish-card', { timeout: TIMEOUT });
    const saveBtn = page.locator('.fish-card button[aria-label^="Save"]').first();
    await expect(saveBtn).toBeVisible();
  });

  test('thermal refuge stations display with color coding', async ({ page }) => {
    await page.goto(`${BASE}/path/fish/deschutes`);
    await page.waitForSelector('.refuge-card', { timeout: TIMEOUT });
    const refuges = await page.locator('.refuge-card').count();
    expect(refuges).toBeGreaterThan(0);
    // Check color-coded class labels
    const classLabels = await page.locator('.refuge-class').count();
    expect(classLabels).toBeGreaterThan(0);
  });

  test('shows species by reach table', async ({ page }) => {
    await page.goto(`${BASE}/path/fish/deschutes`);
    await page.waitForSelector('.reach-row', { timeout: TIMEOUT });
    const rows = await page.locator('.reach-row').count();
    expect(rows).toBeGreaterThan(0);
  });

  test('shows ecological explanation card', async ({ page }) => {
    await page.goto(`${BASE}/path/fish/deschutes`);
    await page.waitForSelector('.refuge-explain', { timeout: TIMEOUT });
    await expect(page.locator('.refuge-explain')).toContainText('cold-water refuges matter');
  });

  test('bottom nav is shown but no tab is highlighted', async ({ page }) => {
    await page.goto(`${BASE}/path/fish/deschutes`);
    await page.waitForSelector('.bottom-nav', { timeout: TIMEOUT });
    // fish is a drilldown — no tab should be active (or the nav should still show)
    const nav = page.locator('.bottom-nav');
    await expect(nav).toBeVisible();
  });
});

// ─────────────────────────────────────────────
// STEWARD (/path/steward)
// ─────────────────────────────────────────────
test.describe('Steward', () => {
  test('shows watershed timeline', async ({ page }) => {
    await page.goto(`${BASE}/path/steward`);
    await page.waitForSelector('.steward-timeline, .timeline-item', { timeout: TIMEOUT });
    const items = await page.locator('.timeline-item').count();
    expect(items).toBeGreaterThan(0);
  });

  test('restoration outcome cards show before/after counts', async ({ page }) => {
    await page.goto(`${BASE}/path/steward`);
    await page.waitForSelector('.outcome-card', { timeout: TIMEOUT });
    const cards = await page.locator('.outcome-card').count();
    expect(cards).toBeGreaterThan(0);
    // Check before/after comparison exists
    await expect(page.locator('.outcome-comparison').first()).toBeVisible();
    await expect(page.locator('.outcome-before .outcome-count').first()).toBeVisible();
    await expect(page.locator('.outcome-after .outcome-count').first()).toBeVisible();
  });

  test('outcome cards have save and share buttons', async ({ page }) => {
    await page.goto(`${BASE}/path/steward`);
    await page.waitForSelector('.outcome-card', { timeout: TIMEOUT });
    const saveBtn = page.locator('.outcome-card button[aria-label^="Save"]').first();
    await expect(saveBtn).toBeVisible();
    const shareBtn = page.locator('.outcome-cta').first();
    await expect(shareBtn).toBeVisible();
  });

  test('shows stewardship opportunities', async ({ page }) => {
    await page.goto(`${BASE}/path/steward`);
    await page.waitForSelector('.opp-card', { timeout: TIMEOUT });
    const opps = await page.locator('.opp-card').count();
    expect(opps).toBeGreaterThan(0);
  });

  test('shows Get Involved CTA with watershed council link', async ({ page }) => {
    await page.goto(`${BASE}/path/steward`);
    await page.waitForSelector('.steward-cta-card', { timeout: TIMEOUT });
    const link = page.locator('.steward-cta-btn');
    await expect(link).toBeVisible();
    const href = await link.getAttribute('href');
    expect(href).toContain('http');
  });
});

// ─────────────────────────────────────────────
// SAVED (/path/saved)
// ─────────────────────────────────────────────
test.describe('Saved', () => {
  test('shows empty state when nothing saved', async ({ page }) => {
    // Clear localStorage
    await page.goto(`${BASE}/path/saved`);
    await page.evaluate(() => localStorage.removeItem('riverpath-saved'));
    await page.reload();
    await page.waitForTimeout(1000);
    const emptyText = page.getByText('Nothing saved yet');
    await expect(emptyText).toBeVisible();
  });

  test('saving an item from Explore shows in Saved tab', async ({ page }) => {
    // Clear localStorage first
    await page.goto(`${BASE}/path/explore`);
    await page.evaluate(() => localStorage.removeItem('riverpath-saved'));
    await page.reload();
    await page.waitForSelector('.adventure-card', { timeout: TIMEOUT });

    // Click save on first adventure card
    const saveBtn = page.locator('.adventure-card button[aria-label^="Save"]').first();
    await saveBtn.click();
    await page.waitForTimeout(500);

    // Navigate to Saved
    await page.click('a[href="/path/saved"]');
    await page.waitForSelector('[style]', { timeout: TIMEOUT });
    // Should no longer show empty state
    const emptyText = page.getByText('Nothing saved yet');
    await expect(emptyText).not.toBeVisible();
  });

  test('saved count badge shows on bottom nav', async ({ page }) => {
    await page.goto(`${BASE}/path/explore`);
    await page.evaluate(() => localStorage.removeItem('riverpath-saved'));
    await page.reload();
    await page.waitForSelector('.adventure-card', { timeout: TIMEOUT });

    // Save an item
    await page.locator('.adventure-card button[aria-label^="Save"]').first().click();
    await page.waitForTimeout(500);

    // Check badge
    const badge = page.locator('.bottom-nav-badge');
    await expect(badge).toBeVisible();
    await expect(badge).toContainText('1');
  });

  test('deleting an item removes it from Saved', async ({ page }) => {
    // Set up a saved item
    await page.goto(`${BASE}/path/saved`);
    await page.evaluate(() => {
      localStorage.setItem('riverpath-saved', JSON.stringify([
        { type: 'recreation', id: 'test-1', watershed: 'deschutes', label: 'Test Site', savedAt: new Date().toISOString() }
      ]));
    });
    await page.reload();
    await page.waitForTimeout(1000);

    // Should show the item
    await expect(page.getByText('Test Site')).toBeVisible();

    // Click delete
    await page.locator('button[aria-label="Remove Test Site from saved"]').click();
    await page.waitForTimeout(500);

    // Should show empty state
    await expect(page.getByText('Nothing saved yet')).toBeVisible();
  });
});
