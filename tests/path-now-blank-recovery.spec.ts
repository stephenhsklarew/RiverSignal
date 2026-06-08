/**
 * Regression: /path/now rendered a blank page (header only, no retry) when the
 * backbone `/sites/{ws}` fetch failed — common after the PWA resumed from
 * background and the SW resolved a cache-cold failed request to `undefined`.
 * Now it must show a Retry state and recover without a remount.
 */
import { test, expect } from '@playwright/test'

const BASE = process.env.BASE_URL || 'http://localhost:5173'
const WS = 'clinch_river_va'
// Matches the backbone /sites/<ws> only — NOT its sub-resources (/sites/<ws>/...).
const backbone = (u: URL) => /\/api\/v1\/sites\/clinch_river_va(\?|$)/.test(u.toString())

test('failed backbone fetch shows Retry (not blank) and recovers', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 740 })

  // 1. Make the backbone request fail (simulate the flaky post-resume network).
  await page.route(backbone, route => route.abort())
  await page.goto(`${BASE}/path/now/${WS}`)
  await page.waitForTimeout(3500)

  // The page must NOT be blank — it shows a retry affordance.
  const retry = page.getByTestId('rnow-retry')
  await expect(retry).toBeVisible()
  await expect(retry).toContainText(/couldn't load/i)

  // 2. Heal the network, tap Retry → content loads, retry block gone.
  await page.unroute(backbone)
  await retry.getByRole('button', { name: 'Retry' }).click()
  await page.waitForTimeout(3500)
  await expect(page.getByTestId('rnow-retry')).toHaveCount(0)
  // a card that only renders inside the `{site && (...)}` block
  await expect(page.locator('[data-card="catch_probability"], .rnow-story-card').first()).toBeVisible()
})
