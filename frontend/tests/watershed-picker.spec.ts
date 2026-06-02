import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5174'

test.describe('WatershedPicker — state → watershed drill-down', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(`${BASE}/riversignal`)
    await page.waitForLoadState('networkidle')
    await expect(page.locator('.wp-pill')).toBeVisible({ timeout: 10000 })
  })

  test('first load shows "All rivers" with empty-state hint on open', async ({ page }) => {
    // Closed pill reads "All rivers" before any selection
    await expect(page.locator('.wp-pill')).toContainText('All rivers')

    // Open the panel
    await page.locator('.wp-pill').click()
    await expect(page.locator('.wp-panel')).toBeVisible()

    // States are listed with count badges; no state active yet → hint shown
    await expect(page.locator('.wp-state', { hasText: 'Oregon' })).toBeVisible()
    await expect(page.locator('.wp-hint')).toContainText('Pick a state')

    await page.screenshot({ path: 'tests/screenshots/wp-empty-open.png' })
  })

  test('selecting a state then a river updates the pill and closes the panel', async ({ page }) => {
    await page.locator('.wp-pill').click()

    // Pick Oregon → its rivers appear in the right column
    await page.locator('.wp-state', { hasText: 'Oregon' }).click()
    await expect(page.locator('.wp-river', { hasText: 'McKenzie' })).toBeVisible()

    // Pick McKenzie
    await page.locator('.wp-river', { hasText: 'McKenzie' }).click()

    // Panel closes, pill shows "Oregon · McKenzie" with the selected pin
    await expect(page.locator('.wp-panel')).toHaveCount(0)
    await expect(page.locator('.wp-pill')).toContainText('Oregon')
    await expect(page.locator('.wp-pill')).toContainText('McKenzie')
    await expect(page.locator('.wp-pin.is-selected')).toBeVisible()

    await page.screenshot({ path: 'tests/screenshots/wp-selected.png' })
  })

  test('state count badges match the number of rivers shown', async ({ page }) => {
    await page.locator('.wp-pill').click()

    const oregon = page.locator('.wp-state', { hasText: 'Oregon' })
    const badge = await oregon.locator('.wp-count').textContent()
    await oregon.click()
    const riverCount = await page.locator('.wp-river').count()
    expect(riverCount).toBe(Number(badge))
  })

  test('"Show all rivers" clears the selection back to All rivers', async ({ page }) => {
    // First select a watershed
    await page.locator('.wp-pill').click()
    await page.locator('.wp-state', { hasText: 'Washington' }).click()
    await page.locator('.wp-river', { hasText: 'Skagit' }).click()
    await expect(page.locator('.wp-pill')).toContainText('Skagit')

    // Reopen and use "Show all rivers"
    await page.locator('.wp-pill').click()
    await page.locator('.wp-all').click()
    await expect(page.locator('.wp-panel')).toHaveCount(0)
    await expect(page.locator('.wp-pill')).toContainText('All rivers')
  })

  test('clicking outside closes the panel', async ({ page }) => {
    await page.locator('.wp-pill').click()
    await expect(page.locator('.wp-panel')).toBeVisible()
    await page.mouse.click(20, 400) // click on the map, away from the panel
    await expect(page.locator('.wp-panel')).toHaveCount(0)
  })
})
