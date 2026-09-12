import { test } from '@playwright/test'

test('Capture Desktop Quantum Terminal and Comparison', async ({ page }) => {
  await page.setViewportSize({ width: 1440, height: 900 })
  await page.goto('/')
  await page.waitForTimeout(2000)

  // 1. Capture Desktop Hero with Quantum Terminal
  await page.screenshot({
    path: '/Users/macbookpro/.gemini/antigravity/brain/74e4c49b-e441-4215-b191-6c18e63d7394/desktop_quantum_terminal.png',
    fullPage: false,
  })

  // 2. Capture the isolated Quantum Terminal box
  const terminal = page.locator('div[aria-label="Kwantowy terminal do wpisania dylematu"]')
  await terminal.screenshot({
    path: '/Users/macbookpro/.gemini/antigravity/brain/74e4c49b-e441-4215-b191-6c18e63d7394/quantum_terminal_card.png',
  })

  // 3. Scroll to and capture Comparison section
  const comparison = page.locator('section[aria-labelledby="comparison-heading"]')
  await comparison.scrollIntoViewIfNeeded()
  await page.waitForTimeout(600)
  await page.screenshot({
    path: '/Users/macbookpro/.gemini/antigravity/brain/74e4c49b-e441-4215-b191-6c18e63d7394/comparison_quantum_vs_ai.png',
    fullPage: false,
  })
})

test('Capture Mobile Quantum Terminal', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await page.waitForTimeout(2000)

  await page.screenshot({
    path: '/Users/macbookpro/.gemini/antigravity/brain/74e4c49b-e441-4215-b191-6c18e63d7394/mobile_quantum_terminal.png',
    fullPage: false,
  })
})
