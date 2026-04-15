import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:5174';
const TIMEOUT = 20000;

test.describe('RiverSignal Species Tab — Select & Map', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/riversignal/deschutes`);
    await page.waitForSelector('.panel-tab', { timeout: TIMEOUT });
    await page.locator('.panel-tab', { hasText: 'species' }).click();
    await page.waitForSelector('.species-grid', { timeout: TIMEOUT });
  });

  test('class filter chips render with counts', async ({ page }) => {
    const chips = await page.locator('.sp-class-chip').count();
    expect(chips).toBeGreaterThan(3);
    await expect(page.locator('.sp-class-chip.active')).toContainText('All');
  });

  test('clicking a class filter shows only that class', async ({ page }) => {
    const birdsChip = page.locator('.sp-class-chip', { hasText: 'Birds' });
    if (await birdsChip.count() > 0) {
      await birdsChip.click();
      await page.waitForTimeout(500);
      const labels = await page.locator('.sp-class-label').allTextContents();
      for (const l of labels) {
        expect(l).toContain('Birds');
      }
    }
  });

  test('clicking a species card selects it', async ({ page }) => {
    await page.locator('.species-card').first().click();
    await page.waitForTimeout(300);
    expect(await page.locator('.species-card.selected').count()).toBe(1);
    expect(await page.locator('.species-select-bar').isVisible()).toBe(true);
  });

  test('clicking a selected card deselects it', async ({ page }) => {
    await page.locator('.species-card').first().click();
    await page.waitForTimeout(300);
    expect(await page.locator('.species-card.selected').count()).toBe(1);
    // Click again to deselect
    await page.locator('.species-card').first().click();
    await page.waitForTimeout(300);
    expect(await page.locator('.species-card.selected').count()).toBe(0);
    expect(await page.locator('.species-select-bar').isVisible()).toBe(false);
  });

  test('multi-select: select two species shows select bar with count', async ({ page }) => {
    await page.locator('.species-card').nth(0).click();
    await page.waitForTimeout(200);
    await page.locator('.species-card').nth(1).click();
    await page.waitForTimeout(200);
    const bar = page.locator('.species-select-bar');
    await expect(bar).toBeVisible();
    await expect(bar).toContainText('2 selected');
  });

  test('multi-select: "Show on map" displays pins for all selected', async ({ page }) => {
    await page.locator('.species-card').nth(0).click();
    await page.waitForTimeout(200);
    await page.locator('.species-card').nth(1).click();
    await page.waitForTimeout(200);
    await page.locator('.sp-show-map-btn').click();
    await page.waitForTimeout(3000);
    const searchVal = await page.locator('.obs-search-input').inputValue();
    expect(searchVal).toContain(' OR ');
    // Should find observations
    const countBadge = page.locator('.obs-search-count');
    if (await countBadge.count() > 0) {
      const text = await countBadge.textContent();
      expect(text).toMatch(/\d+ found/);
    }
  });

  test('"Clear" removes all selections', async ({ page }) => {
    await page.locator('.species-card').nth(0).click();
    await page.locator('.species-card').nth(1).click();
    await page.waitForTimeout(200);
    await page.locator('.sp-clear-btn').click();
    await page.waitForTimeout(200);
    expect(await page.locator('.species-card.selected').count()).toBe(0);
    expect(await page.locator('.species-select-bar').isVisible()).toBe(false);
  });

  test('selected badge shows on selected cards', async ({ page }) => {
    await page.locator('.species-card').first().click();
    await page.waitForTimeout(200);
    expect(await page.locator('.sp-selected-badge').count()).toBe(1);
  });

  test('pagination works', async ({ page }) => {
    const pagination = page.locator('.species-pagination');
    if (await pagination.count() > 0) {
      await expect(pagination.locator('span')).toContainText(/1 \/ \d+/);
      await pagination.locator('button', { hasText: 'Next' }).click();
      await page.waitForTimeout(300);
      await expect(pagination.locator('span')).toContainText(/2 \/ \d+/);
    }
  });
});


test.describe('RiverSignal Rocks Tab — Select & Map', () => {

  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/riversignal/deschutes`);
    await page.waitForSelector('.panel-tab', { timeout: TIMEOUT });
    await page.locator('.panel-tab', { hasText: 'rocks' }).click();
    await page.waitForSelector('.species-grid', { timeout: TIMEOUT });
  });

  test('rocks tab loads with fossil and mineral data', async ({ page }) => {
    const cards = await page.locator('.species-card').count();
    expect(cards).toBeGreaterThan(0);
    await expect(page.locator('.sp-class-chip', { hasText: /^🦴 Fossils/ })).toBeVisible();
    await expect(page.locator('.sp-class-chip', { hasText: /^💎 Minerals/ })).toBeVisible();
  });

  test('filter by Fossils only', async ({ page }) => {
    await page.locator('.sp-class-chip', { hasText: /^🦴 Fossils/ }).click();
    await page.waitForTimeout(500);
    const labels = await page.locator('.sp-class-label').allTextContents();
    for (const l of labels) expect(l).toContain('🦴');
  });

  test('filter by Minerals only', async ({ page }) => {
    await page.locator('.sp-class-chip', { hasText: /^💎 Minerals/ }).click();
    await page.waitForTimeout(500);
    const labels = await page.locator('.sp-class-label').allTextContents();
    for (const l of labels) expect(l).toContain('💎');
  });

  test('clicking a rock card selects it', async ({ page }) => {
    await page.locator('.species-card').first().click();
    await page.waitForTimeout(300);
    expect(await page.locator('.species-card.selected').count()).toBe(1);
    expect(await page.locator('.species-select-bar').isVisible()).toBe(true);
  });

  test('multi-select rocks and show on map', async ({ page }) => {
    await page.locator('.species-card').nth(0).click();
    await page.waitForTimeout(200);
    await page.locator('.species-card').nth(1).click();
    await page.waitForTimeout(200);
    const bar = page.locator('.species-select-bar');
    await expect(bar).toBeVisible();
    await expect(bar).toContainText('2 selected');
    await page.locator('.sp-show-map-btn').click();
    await page.waitForTimeout(2000);
    const searchVal = await page.locator('.obs-search-input').inputValue();
    expect(searchVal.length).toBeGreaterThan(0);
  });

  test('clear selection works', async ({ page }) => {
    await page.locator('.species-card').first().click();
    await page.waitForTimeout(200);
    await expect(page.locator('.species-select-bar')).toBeVisible();
    await page.locator('.sp-clear-btn').click();
    await page.waitForTimeout(200);
    expect(await page.locator('.species-card.selected').count()).toBe(0);
  });

  test('pagination works for rocks', async ({ page }) => {
    const pagination = page.locator('.species-pagination');
    if (await pagination.count() > 0) {
      await expect(pagination.locator('span')).toContainText(/1 \/ \d+/);
    }
  });
});
