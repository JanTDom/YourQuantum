import { test, expect } from '@playwright/test'

test.describe('Mobile Viewport & 3D Brain Modal Tests', () => {
  test.use({
    viewport: { width: 390, height: 844 }, // iPhone 14/15/16 viewport
    userAgent: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1',
  })

  test('Mobile: landing page loads, top nav fits, opens 3D brain modal cleanly', async ({ page }) => {
    await page.goto('/')

    // Verify brand logo and top navigation
    await expect(page.getByText('YourQuantum').first()).toBeVisible()
    const brainBtn = page.getByLabel('Główne menu YourQuantum').getByRole('button', { name: /Mózg Silnika 3D/i })
    await expect(brainBtn).toBeVisible()

    // Open Brain Modal
    await brainBtn.click()

    // Verify modal dialog is open and visible
    const modal = page.getByRole('dialog', { name: /Prezentacja Mózgu Silnika 3D/i })
    await expect(modal).toBeVisible()

    // Check compact mobile header title
    await expect(modal.getByRole('heading', { name: /Mózg 3D/i })).toBeVisible()
    const closeBtn = modal.getByRole('button', { name: /Zamknij/i })
    await expect(closeBtn).toBeVisible()

    // Verify 4-lobe selector tabs are present and visible
    await expect(modal.getByRole('button', { name: 'Płat Czołowy' })).toBeVisible()
    await expect(modal.getByRole('button', { name: 'Płat Lewy' })).toBeVisible()
    await expect(modal.getByRole('button', { name: 'Płat Prawy' })).toBeVisible()
    await expect(modal.getByRole('button', { name: 'Rdzeń Centralny' })).toBeVisible()

    // Verify explanation details card is visible with content
    await expect(modal.getByRole('heading', { name: /Płat Czołowy: Ekstrakcja Faktów/i })).toBeVisible()
    await expect(modal.getByText('Zasada Działania w Twoim Dylemacie')).toBeVisible()

    // Switch to another lobe (Płat Lewy)
    await modal.getByRole('button', { name: 'Płat Lewy' }).click()
    await expect(modal.getByRole('heading', { name: /Płat Lewy: Filtr Ograniczeń Twardych/i })).toBeVisible()

    // Switch to Quantum lobe
    await modal.getByRole('button', { name: 'Płat Prawy' }).click()
    await expect(modal.getByRole('heading', { name: /Płat Prawy: Splątanie Kwantowe/i })).toBeVisible()

    // Close modal
    await closeBtn.click()
    await expect(modal).not.toBeVisible()
  })
})
