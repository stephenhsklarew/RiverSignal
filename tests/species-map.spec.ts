import { test, expect } from '@playwright/test';
const BASE = 'http://localhost:5174';

test('Species Map: loads with fish pins and popup', async ({ page }) => {
  await page.goto(`${BASE}/path/map/deschutes`);
  await page.waitForSelector('.species-map-container', { timeout: 15000 });

  // Back button exists
  await expect(page.locator('.species-map-back')).toBeVisible();
  await expect(page.locator('.species-map-back')).toContainText('River Now');

  // Category toggle defaults to Fish
  await expect(page.locator('.species-map-cat.active')).toContainText('Fish');

  // Observation count shows
  await page.waitForSelector('.species-map-count', { timeout: 10000 });
  await page.waitForFunction(() => !document.querySelector('.species-map-count')?.textContent?.includes('Loading'));
  const countText = await page.locator('.species-map-count').textContent();
  expect(countText).toMatch(/\d+ observations/);

  // Map pins rendered
  await page.waitForSelector('.species-map-pin', { timeout: 10000 });
  const pins = await page.locator('.species-map-pin').count();
  expect(pins).toBeGreaterThan(0);

  // Click a pin — popup should appear
  await page.locator('.species-map-pin').first().click();
  await page.waitForSelector('.species-popup', { timeout: 5000 });
  await expect(page.locator('.species-popup-name')).toBeVisible();
});

test('Species Map: switch to insects', async ({ page }) => {
  await page.goto(`${BASE}/path/map/deschutes`);
  await page.waitForSelector('.species-map-cat', { timeout: 15000 });

  await page.locator('.species-map-cat', { hasText: 'Insects' }).click();
  await expect(page.locator('.species-map-cat.active')).toContainText('Insects');

  // Wait for reload
  await page.waitForFunction(() => !document.querySelector('.species-map-count')?.textContent?.includes('Loading'));
  const countText = await page.locator('.species-map-count').textContent();
  expect(countText).toMatch(/\d+ observations/);
});

test('Species Map: back button goes to River Now', async ({ page }) => {
  await page.goto(`${BASE}/path/map/deschutes`);
  await page.waitForSelector('.species-map-back', { timeout: 15000 });
  await page.click('.species-map-back');
  await expect(page).toHaveURL(/\/path\/now\/deschutes/);
});

test('River Now: View Map button exists next to What\'s Here Now', async ({ page }) => {
  await page.goto(`${BASE}/path/now/deschutes`);
  await page.waitForSelector('.rnow-view-map-btn', { timeout: 15000 });
  await expect(page.locator('.rnow-view-map-btn')).toContainText('View Map');

  // Click it
  await page.click('.rnow-view-map-btn');
  await expect(page).toHaveURL(/\/path\/map\/deschutes/);
});
