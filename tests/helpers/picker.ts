import type { Page } from '@playwright/test'

/** Open the watershed picker pill. */
export async function openPicker(page: Page) {
  await page.waitForSelector('.wp-pill', { timeout: 10000 })
  await page.locator('.wp-pill').click()
}

/** Select the first available watershed (first state → first river). */
export async function selectFirstWatershed(page: Page) {
  await openPicker(page)
  await page.locator('.wp-state').first().click()
  await page.locator('.wp-river').first().click()
}

/** Select a watershed by its short river name (e.g. "McKenzie"), scanning states for it. */
export async function selectWatershed(page: Page, riverName: string) {
  await openPicker(page)
  const states = page.locator('.wp-state')
  const n = await states.count()
  for (let i = 0; i < n; i++) {
    await states.nth(i).click()
    const river = page.locator('.wp-river', { hasText: riverName })
    if (await river.count() > 0) {
      await river.first().click()
      return
    }
  }
  throw new Error(`Watershed not found in picker: ${riverName}`)
}
