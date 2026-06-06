/**
 * River Story page-turn scroll reset.
 *
 * The story body (.rnow-story-text) is a height-clipped, internally-scrollable
 * box. After reading to the bottom of a page and tapping Next, the new page
 * must start at the top of that box (inner scrollTop === 0).
 *
 *   BASE_URL=http://localhost:5173 npx playwright test tests/riverpath-story-scroll.spec.ts
 */
import { test, expect } from '@playwright/test'

const BASE = process.env.BASE_URL || 'http://localhost:5173'
const WS = 'clinch_river_va' // multi-page story
const SETTLE = 4500

test('story page-turn resets the inner text box to the top', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 740 }) // mobile
  await page.goto(`${BASE}/path/now/${WS}`)
  await page.waitForTimeout(SETTLE)

  const text = page.locator('.rnow-story-text')
  await expect(text).toBeVisible()

  // The box must actually be scrollable for this test to mean anything.
  const scrollable = await text.evaluate((el) => el.scrollHeight - el.clientHeight)
  expect(scrollable, 'story text box should overflow (be internally scrollable)').toBeGreaterThan(5)

  // Simulate a reader scrolling to the bottom of the current page.
  await text.evaluate((el) => { el.scrollTop = el.scrollHeight })
  await page.waitForTimeout(150)
  const beforeTop = await text.evaluate((el) => el.scrollTop)
  expect(beforeTop, 'inner scroll should be > 0 after scrolling down').toBeGreaterThan(0)

  // Tap Next.
  await page.getByRole('button', { name: 'Next →' }).first().click()
  await page.waitForTimeout(600) // rAF + smooth settle

  const afterTop = await page.locator('.rnow-story-text').evaluate((el) => el.scrollTop)
  const pageInfo = await page.locator('.rnow-story-page-info').textContent()
  console.log(`beforeTop=${beforeTop} afterTop=${afterTop} now on ${pageInfo}`)
  expect(afterTop, 'inner scroll should reset to top on the new page').toBe(0)

  // And going back (Prev) should also land at the top.
  await page.locator('.rnow-story-text').evaluate((el) => { el.scrollTop = el.scrollHeight })
  await page.getByRole('button', { name: '← Prev' }).first().click()
  await page.waitForTimeout(600)
  const prevTop = await page.locator('.rnow-story-text').evaluate((el) => el.scrollTop)
  expect(prevTop, 'Prev should also reset to top').toBe(0)
})
