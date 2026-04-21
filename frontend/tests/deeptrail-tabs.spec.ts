import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5174'

test.describe('DeepTrail Tab Navigation', () => {

  test.beforeEach(async ({ page }) => {
    // Use mobile viewport so bottom nav is visible
    await page.setViewportSize({ width: 390, height: 844 })
  })

  test('Pick page loads and shows watersheds', async ({ page }) => {
    // Clear any stored location so we see the pick screen
    await page.goto(BASE)
    await page.evaluate(() => sessionStorage.removeItem('deeptrail-location'))

    await page.goto(`${BASE}/trail`)
    await page.waitForLoadState('networkidle')

    // Should see the title
    await expect(page.locator('h1')).toContainText('Ancient Worlds')

    // Should see GPS button
    await expect(page.locator('.dt-gps-btn')).toBeVisible()

    // Should see watershed buttons
    const watersheds = page.locator('.dt-watershed-btn')
    await expect(watersheds).toHaveCount(5)

    // Should NOT see coordinate entry (removed per user request)
    await expect(page.locator('.dt-coord-form')).toHaveCount(0)
  })

  test('Clicking a watershed navigates to Story tab', async ({ page }) => {
    await page.goto(BASE)
    await page.evaluate(() => sessionStorage.removeItem('deeptrail-location'))

    await page.goto(`${BASE}/trail`)
    await page.waitForLoadState('networkidle')

    // Click Deschutes
    await page.locator('.dt-watershed-btn', { hasText: 'Deschutes' }).click()
    await page.waitForURL(/\/trail\/story\/deschutes/)

    // Should see the Story page with location name
    await expect(page.locator('h1')).toContainText('Deschutes')

    // Should see bottom nav
    await expect(page.locator('.dt-bottom-nav')).toBeVisible()

    // Should see 5 tabs
    const tabs = page.locator('.dt-bottom-nav-tab')
    await expect(tabs).toHaveCount(5)
  })

  test('Story tab renders sections', async ({ page }) => {
    await page.goto(`${BASE}/trail/story/deschutes`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000) // Wait for data to load

    // Should show story card
    await expect(page.locator('.dt-story-card')).toBeVisible({ timeout: 10000 })

    // Should show reading level toggle
    await expect(page.locator('.dt-reading-toggle')).toBeVisible()

    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/trail-story.png', fullPage: true })
  })

  test('Explore tab loads without errors', async ({ page }) => {
    // Listen for console errors
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error') errors.push(msg.text())
    })
    page.on('pageerror', err => errors.push(err.message))

    await page.goto(`${BASE}/trail/explore/deschutes`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(3000)

    // Should NOT be blank — check for app container
    await expect(page.locator('.dt-app')).toBeVisible()

    // Should see location name
    await expect(page.locator('h1')).toContainText('Deschutes')

    // Should see the explore tabs (Fossils / Minerals)
    await expect(page.locator('.dt-explore-tabs')).toBeVisible({ timeout: 10000 })

    // Should see the map
    await expect(page.locator('.dt-mini-map')).toBeVisible({ timeout: 10000 })

    // Take screenshot
    await page.screenshot({ path: 'tests/screenshots/trail-explore.png', fullPage: true })

    // Report any errors
    if (errors.length > 0) {
      console.log('Console errors on Explore tab:', errors)
    }
    // Should have no critical errors that blank the page
    const criticalErrors = errors.filter(e => e.includes('TypeError') || e.includes('ReferenceError') || e.includes('Cannot read'))
    expect(criticalErrors).toHaveLength(0)
  })

  test('Collect tab renders rockhounding sites', async ({ page }) => {
    await page.goto(`${BASE}/trail/collect/deschutes`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    await expect(page.locator('.dt-app')).toBeVisible()
    await expect(page.locator('h1')).toContainText('Deschutes')

    // Should see rockhounding section
    await expect(page.locator('.dt-rockhounding')).toBeVisible({ timeout: 10000 })

    // Should have rockhounding site rows
    const rows = page.locator('.dt-rocksite-row')
    const count = await rows.count()
    expect(count).toBeGreaterThan(0)

    // Click first rockhounding site — should show detail
    await rows.first().click()
    await expect(page.locator('.dt-rockdetail-name')).toBeVisible({ timeout: 5000 })

    await page.screenshot({ path: 'tests/screenshots/trail-collect.png', fullPage: true })
  })

  test('Learn tab renders quiz and chat', async ({ page }) => {
    await page.goto(`${BASE}/trail/learn/deschutes`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(2000)

    await expect(page.locator('.dt-app')).toBeVisible()

    // Should see quiz section
    await expect(page.locator('.dt-quiz-section')).toBeVisible({ timeout: 10000 })

    // Should see chat section
    await expect(page.locator('.dt-chat-section')).toBeVisible()

    await page.screenshot({ path: 'tests/screenshots/trail-learn.png', fullPage: true })
  })

  test('Saved tab shows empty state', async ({ page }) => {
    // Clear saved items first
    await page.goto(BASE)
    await page.evaluate(() => localStorage.removeItem('riverpath-saved'))

    await page.goto(`${BASE}/trail/saved`)
    await page.waitForLoadState('networkidle')

    await expect(page.locator('.dt-app')).toBeVisible()

    // Should see empty state message
    await expect(page.locator('.dt-empty')).toBeVisible()
    await expect(page.locator('.dt-empty')).toContainText('No saved items')

    await page.screenshot({ path: 'tests/screenshots/trail-saved.png', fullPage: true })
  })

  test('Bottom nav navigates between tabs', async ({ page }) => {
    await page.goto(`${BASE}/trail/story/deschutes`)
    await page.waitForLoadState('networkidle')
    await page.waitForTimeout(1000)

    // Click Explore tab
    await page.locator('.dt-bottom-nav-tab', { hasText: 'Explore' }).click()
    await page.waitForURL(/\/trail\/explore\/deschutes/)
    await expect(page.locator('.dt-app')).toBeVisible()

    // Click Collect tab
    await page.locator('.dt-bottom-nav-tab', { hasText: 'Collect' }).click()
    await page.waitForURL(/\/trail\/collect\/deschutes/)
    await expect(page.locator('.dt-app')).toBeVisible()

    // Click Learn tab
    await page.locator('.dt-bottom-nav-tab', { hasText: 'Learn' }).click()
    await page.waitForURL(/\/trail\/learn\/deschutes/)
    await expect(page.locator('.dt-app')).toBeVisible()

    // Click Saved tab
    await page.locator('.dt-bottom-nav-tab', { hasText: 'Saved' }).click()
    await page.waitForURL(/\/trail\/saved/)
    await expect(page.locator('.dt-app')).toBeVisible()

    // Click Story tab to go back
    await page.locator('.dt-bottom-nav-tab', { hasText: 'Story' }).click()
    await page.waitForURL(/\/trail\/story\/deschutes/)
    await expect(page.locator('.dt-app')).toBeVisible()
  })
})
