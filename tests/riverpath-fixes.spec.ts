/**
 * Playwright e2e for the RiverPath fixes #3 (°F), #4 (species label/tooltip),
 * #5 (Time Machine renders when enabled), #6 (Saved share recipient flow).
 *
 *   BASE_URL=http://localhost:5173 API_BASE=http://localhost:8001/api/v1 \
 *     npx playwright test tests/riverpath-fixes.spec.ts
 */
import { test, expect } from '@playwright/test'

const BASE = process.env.BASE_URL || 'http://localhost:5173'
const API = process.env.API_BASE || 'http://localhost:8001/api/v1'
const WS = 'clinch_river_va'
const SETTLE = 4500

// #3 — temperatures display in °F, never °C
test('#3 water temperature shows °F, not °C', async ({ page }) => {
  await page.goto(`${BASE}/path/now/${WS}`)
  await page.waitForTimeout(SETTLE)
  const body = (await page.locator('body').textContent()) || ''
  expect(body, 'no raw Celsius should appear').not.toContain('°C')
  // Clinch has a temp-reporting gauge, so a °F reading should render somewhere.
  expect(body).toContain('°F')
})

// #4 — "species" count is clarified as observed-across-all-taxa
test('#4 species count relabeled to "species observed"', async ({ page }) => {
  await page.goto(`${BASE}/path`)
  await page.waitForTimeout(SETTLE)
  const body = (await page.locator('body').textContent()) || ''
  expect(body.toLowerCase()).toContain('species observed')
})

// #5 — Time Machine renders content (data or graceful note) when enabled
test('#5 Time Machine renders when enabled', async ({ page }) => {
  // Seed card settings so time_machine is visible before the app loads.
  await page.addInitScript(() => {
    localStorage.setItem('riverpath-card-settings', JSON.stringify([{ id: 'time_machine', visible: true }]))
  })
  await page.goto(`${BASE}/path/now/${WS}`)
  await page.waitForTimeout(SETTLE)
  const card = page.locator('[data-card="time_machine"]')
  await expect(card).toBeVisible()
  const txt = (await card.textContent()) || ''
  // Either the slider/data view OR the graceful "needs more history" note —
  // but NOT an empty card.
  expect(txt.toLowerCase()).toContain('time machine')
  expect(
    txt.includes('species') || txt.toLowerCase().includes('more history'),
    'time machine should show data or a needs-more-history note, not be blank'
  ).toBeTruthy()
})

// #6 — a shared link drops items into the recipient's Saved
test('#6 shared link lands items in recipient Saved', async ({ page, request }) => {
  // Create a share via the API.
  const resp = await request.post(`${API}/saved/share`, {
    data: {
      watershed: WS,
      sections: ['species'],
      items: [{ type: 'species', id: 'pw-share-smallmouth', data: { label: 'PW Share Smallmouth', watershed: WS } }],
    },
  })
  expect(resp.ok()).toBeTruthy()
  const { token, url } = await resp.json()
  expect(token).toBeTruthy()

  // Open the recipient link → should ingest + redirect to /path/saved.
  await page.goto(`${BASE}${url}`)
  await page.waitForTimeout(SETTLE)
  await expect(page).toHaveURL(/\/path\/saved/)
  const body = (await page.locator('body').textContent()) || ''
  expect(body).toContain('PW Share Smallmouth')          // the shared item landed
  expect(body.toLowerCase()).toContain('shared item')     // the "sign in to keep" banner
})

// #6c — a shared link carrying an observation renders it on the recipient's Saved
test('#6c shared observation lands in recipient Saved', async ({ page, request }) => {
  const resp = await request.post(`${API}/saved/share`, {
    data: {
      watershed: WS,
      sections: ['observation'],
      items: [{
        type: 'observation', id: 'pw-obs-42',
        data: { watershed: WS, label: 'PW Shared Otter', sublabel: 'Lontra canadensis' },
      }],
    },
  })
  expect(resp.ok()).toBeTruthy()
  const { url } = await resp.json()
  await page.goto(`${BASE}${url}`)
  await page.waitForTimeout(SETTLE)
  await expect(page).toHaveURL(/\/path\/saved/)
  const body = (await page.locator('body').textContent()) || ''
  expect(body).toContain('PW Shared Otter')        // the observation rendered
  expect(body).toContain('shared with you')         // shared-observation affordance
})

// #6d — a shared private observation keeps photographer + visibility on the detail screen
test('#6d shared observation keeps photographer + private visibility', async ({ page, request }) => {
  const resp = await request.post(`${API}/saved/share`, {
    data: {
      watershed: WS,
      sections: ['observation'],
      items: [{
        type: 'observation', id: 'pw-attrib-1',
        data: {
          watershed: WS, label: 'PW Heron', sublabel: 'Ardea herodias',
          thumbnail: 'https://storage.googleapis.com/riversignal-assets-riversignal-prod/favicon.png',
          observer: 'Original Photographer', source: 'RiverPath', visibility: 'private',
          observedAt: '2026-05-01T12:00:00Z',
        },
      }],
    },
  })
  expect(resp.ok()).toBeTruthy()
  const { url } = await resp.json()
  await page.goto(`${BASE}${url}`)
  await page.waitForTimeout(SETTLE)
  await expect(page).toHaveURL(/\/path\/saved/)
  // the row shows the original photographer + a private marker
  const body = (await page.locator('body').textContent()) || ''
  expect(body).toContain('Original Photographer')
  expect(body).toContain('private')
  // tap the shared observation → detail screen
  await page.getByText('PW Heron').first().click()
  await page.waitForTimeout(1500)
  await expect(page).toHaveURL(/\/photo/)
  const detail = (await page.locator('body').textContent()) || ''
  expect(detail).toContain('Photographer')
  expect(detail).toContain('Original Photographer')
  expect(detail).toContain('Visibility')
  expect(detail).toContain('Private')
})

// #6b — expired/invalid link shows a friendly message
test('#6b invalid share link shows friendly error', async ({ page }) => {
  await page.goto(`${BASE}/path/shared/totally-bogus-token`)
  await page.waitForTimeout(SETTLE)
  const body = (await page.locator('body').textContent()) || ''
  expect(body.toLowerCase()).toContain('unavailable')
})
