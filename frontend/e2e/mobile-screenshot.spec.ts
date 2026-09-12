import { test, expect } from '@playwright/test'

test.describe('Mobile Visual Snapshot', () => {
  test.use({
    viewport: { width: 390, height: 844 }, // iPhone 14/15/16 viewport
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
  })

  test('Capture mobile brain modal screenshot', async ({ page }) => {
    await page.goto('/')
    const brainBtn = page.getByLabel('Główne menu YourQuantum').getByRole('button', { name: /Mózg Silnika 3D/i })
    await brainBtn.click()

    const modal = page.getByRole('dialog', { name: /Prezentacja Mózgu Silnika 3D/i })
    await expect(modal).toBeVisible()

    // Wait a brief moment for Three.js particles to render
    await page.waitForTimeout(1200)

    // Capture screenshot of the mobile screen
    await page.screenshot({
      path: '/Users/macbookpro/.gemini/antigravity/brain/74e4c49b-e441-4215-b191-6c18e63d7394/mobile_brain_fixed.png',
    })
  })
})
