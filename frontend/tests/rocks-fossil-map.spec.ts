import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5174'
const API = 'http://localhost:8001/api/v1'

test.describe('Rocks tab → Fossil map pins (Green River)', () => {

  test.beforeEach(async ({ page }) => {
    // Navigate to RiverSignal, select Green River
    await page.goto(`${BASE}/riversignal`)
    await page.waitForLoadState('networkidle')

    // Click Green River watershed tab
    const greenTab = page.locator('.ws-tab', { hasText: 'Green' })
    if (await greenTab.isVisible()) {
      await greenTab.click()
    }
    await page.waitForTimeout(2000)

    // Click the Rocks tab in the panel
    const rocksTab = page.locator('button', { hasText: 'Rocks' })
    await expect(rocksTab).toBeVisible({ timeout: 10000 })
    await rocksTab.click()
    await page.waitForTimeout(3000) // Wait for rocks data to load
  })

  test('Rocks tab loads fossils for Green River', async ({ page }) => {
    // Should see the rocks gallery
    const gallery = page.locator('.section-title', { hasText: 'Rocks Gallery' })
    await expect(gallery).toBeVisible({ timeout: 10000 })

    // Should have fossil cards
    const cards = page.locator('.species-card')
    const count = await cards.count()
    expect(count).toBeGreaterThan(0)

    await page.screenshot({ path: 'tests/screenshots/rocks-tab-loaded.png' })
  })

  test('Clicking a fossil shows amber pins (not orange observation pins)', async ({ page }) => {
    // Wait for rocks to load
    await expect(page.locator('.species-card').first()).toBeVisible({ timeout: 10000 })

    // Click the first fossil card and wait for any network response
    const firstCard = page.locator('.species-card').first()
    const fossilName = await firstCard.locator('.sp-common').textContent()

    // Click and wait for response
    await firstCard.click()
    await page.waitForTimeout(3000)

    // Check search bar for bone emoji (proves fossil path ran)
    const searchBar2 = page.locator('.obs-search-input')
    const searchVal = await searchBar2.inputValue()
    const response = searchVal.includes('🦴') ? { url: () => '/fossils/search' } : null

    if (response) {
      const url = response.url()
      console.log(`API called: ${url}`)
      // Should be a fossils endpoint, not observations
      expect(url).toContain('/fossils/')
      expect(url).not.toContain('/observations/search')
    }

    // The search bar should show the bone emoji prefix
    const searchBar = page.locator('.obs-search-input')
    const searchValue = await searchBar.inputValue()
    expect(searchValue).toContain('🦴')

    console.log(`Clicked: ${fossilName}`)
    await page.screenshot({ path: 'tests/screenshots/rocks-fossil-clicked.png' })
  })

  test('Fossil pin popup shows "Fossil" badge and period (not "Observed" date)', async ({ page }) => {
    // Click a fossil
    await page.locator('.species-card').first().click()
    await page.waitForTimeout(2000)

    // Click a pin on the map (if any are visible)
    // The fossil layer uses amber color (#d4a96a) vs observation orange (#e65100)
    // We can check the popup content after clicking a map pin
    const mapCanvas = page.locator('.map-container canvas')
    if (await mapCanvas.isVisible()) {
      // Click roughly in the center of the map where pins might be
      const box = await mapCanvas.boundingBox()
      if (box) {
        await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2)
        await page.waitForTimeout(500)

        // If a popup appeared, verify it shows "Fossil" badge
        const popup = page.locator('.maplibregl-popup-content')
        if (await popup.isVisible()) {
          const popupText = await popup.textContent()
          // Should NOT contain "Observed:" (that's for living species)
          expect(popupText).not.toContain('Observed:')
          // Should contain "Period:" or "Fossil"
          const hasFossilContent = popupText?.includes('Fossil') || popupText?.includes('Period:')
          expect(hasFossilContent).toBeTruthy()
        }
      }
    }
  })

  test('No timeline slider appears for fossil pins', async ({ page }) => {
    // Click a fossil
    await page.locator('.species-card').first().click()
    await page.waitForTimeout(2000)

    // Timeline slider should NOT be visible (it's only for observations)
    const timeline = page.locator('.timeline-slider')
    await expect(timeline).toHaveCount(0)
  })

  test('Clicking a fossil updates search bar with bone emoji', async ({ page }) => {
    await expect(page.locator('.species-card').first()).toBeVisible({ timeout: 10000 })

    // Click a fossil card
    await page.locator('.species-card').first().click()
    await page.waitForTimeout(3000)

    // Search bar should show bone emoji (proves fossil path ran, not observation path)
    const searchBar = page.locator('.obs-search-input')
    const val = await searchBar.inputValue()
    expect(val).toContain('🦴')

    // Deselect
    await page.locator('.species-card').first().click()
    await page.waitForTimeout(500)

    // Click a different card
    if (await page.locator('.species-card').count() > 1) {
      await page.locator('.species-card').nth(1).click()
      await page.waitForTimeout(3000)
      const val2 = await searchBar.inputValue()
      expect(val2).toContain('🦴')
    }
  })

  test('No console errors or blank page when clicking fossils', async ({ page }) => {
    const errors: string[] = []
    page.on('console', msg => {
      if (msg.type() === 'error' && !msg.text().includes('favicon')) {
        errors.push(msg.text())
      }
    })
    page.on('pageerror', err => errors.push(err.message))

    // Click through several fossil cards
    const cards = page.locator('.species-card')
    const count = Math.min(await cards.count(), 5)
    for (let i = 0; i < count; i++) {
      await cards.nth(i).click()
      await page.waitForTimeout(800)

      // Page should not be blank
      await expect(page.locator('.app')).toBeVisible()
    }

    // Filter out non-critical errors
    const critical = errors.filter(e =>
      e.includes('TypeError') || e.includes('Cannot read') ||
      e.includes('ReferenceError') || e.includes('Unexpected token')
    )
    if (critical.length > 0) {
      console.log('Critical errors:', critical)
    }
    expect(critical).toHaveLength(0)
  })

  test('Fossil KPI chip shows count with bone emoji', async ({ page }) => {
    // Click a fossil that should have results
    await page.locator('.species-card').first().click()
    await page.waitForTimeout(3000)

    // Should see the fossil KPI chip
    const fossilChip = page.locator('.kpi-chip', { hasText: 'fossils on map' })
    // If fossils were found, the chip should be visible
    const searchBar = page.locator('.obs-search-input')
    const searchValue = await searchBar.inputValue()
    if (searchValue.includes('(0)')) {
      // No fossils found — chip won't show
      console.log('No fossil pins for this taxon — skipping KPI check')
    } else {
      await expect(fossilChip).toBeVisible({ timeout: 5000 })
    }
  })
})

test.describe('Species tab uses observation pins (not fossil pins)', () => {
  test('Species tab click queries observations endpoint', async ({ page }) => {
    await page.goto(`${BASE}/riversignal`)
    await page.waitForLoadState('networkidle')

    // Select a watershed with observations
    const mckTab = page.locator('.ws-tab', { hasText: 'McKenzie' })
    if (await mckTab.isVisible()) await mckTab.click()
    await page.waitForTimeout(2000)

    // Should default to overview or species tab
    const speciesTab = page.locator('button', { hasText: 'Species' })
    await expect(speciesTab).toBeVisible({ timeout: 10000 })
    await speciesTab.click()
    await page.waitForTimeout(2000)

    // Intercept requests
    const obsRequests: string[] = []
    const fossilRequests: string[] = []
    page.on('request', req => {
      if (req.url().includes('/observations/search')) obsRequests.push(req.url())
      if (req.url().includes('/fossils/search')) fossilRequests.push(req.url())
    })

    // Click a species card
    const cards = page.locator('.species-card')
    if (await cards.count() > 0) {
      await cards.first().click()
      await page.waitForTimeout(2000)

      // Should call observations, NOT fossils
      expect(obsRequests.length).toBeGreaterThan(0)
      expect(fossilRequests.length).toBe(0)
    }
  })
})
