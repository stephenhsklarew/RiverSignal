/**
 * Drives the real /admin/photos UI with a forged admin session:
 *  - watersheds listed alphabetically
 *  - Splash Card: choosing a .png uploads AND auto-saves (persists)
 *
 * Orchestrated by tests/run-admin-splash.sh (creates the admin user + token).
 */
import { test, expect } from '@playwright/test'

const BASE = 'http://localhost:5173'
const API = 'http://localhost:8001/api/v1'
const TOKEN = process.env.RP_ADMIN_TOKEN || ''
const PNG = process.env.RP_PNG_PATH || ''
const WS = 'deschutes'

// Needs a forged admin session + a png on disk — provided by the local setup
// (create an is_admin user, mint a dev-secret JWT). Skips otherwise so a plain
// `playwright test` run stays green.
test.beforeEach(async ({ context }) => {
  test.skip(!TOKEN || !PNG, 'set RP_ADMIN_TOKEN + RP_PNG_PATH to run (admin-only UI)')
  await context.addCookies([{ name: 'rs_token', value: TOKEN, domain: 'localhost', path: '/' }])
})

test('watershed picker is alphabetical', async ({ page }) => {
  await page.goto(`${BASE}/admin/photos`)
  await page.waitForTimeout(3000)
  const names = await page.locator('.admin-card-name').allTextContents()
  const watershedNames = names.filter(n => n && n !== 'Global defaults')
  const sorted = [...watershedNames].sort((a, b) => a.localeCompare(b))
  expect(watershedNames.length).toBeGreaterThan(5)
  expect(watershedNames).toEqual(sorted)
})

test('Splash Card: choosing a .png uploads and auto-saves', async ({ page, request }) => {
  await page.goto(`${BASE}/admin/photos?watershed=${WS}&type=splash`)
  await page.waitForTimeout(3000)
  await expect(page.getByText('Upload a new image')).toBeVisible()

  // choose the file → triggers upload + auto-save
  await page.locator('input[type="file"]').setInputFiles(PNG)
  await expect(page.locator('.admin-msg')).toContainText('uploaded and saved', { timeout: 15000 })

  // verify it actually persisted server-side (no manual Save click)
  const res = await request.get(`${API}/admin/watershed-splash/${WS}`, {
    headers: { cookie: `rs_token=${TOKEN}` },
  })
  const body = await res.json()
  expect(body.splash.exists).toBe(true)
  expect(body.splash.image_url).toContain('/images/uploads/watershed_splash/')
  console.log('persisted image_url:', body.splash.image_url)
})
