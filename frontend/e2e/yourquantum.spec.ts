import { test, expect } from '@playwright/test'

test.describe('YourQuantum Calm Decision Studio E2E Suite', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('1. Smoke Test: Verifies brand identity, quantum badge, and Quantum Terminal', async ({ page }) => {
    await expect(page.getByText('YourQuantum').first()).toBeVisible()
    await expect(page.getByText('MECHANIZM KWANTOWY ZAMIAST ZGADYWANIA CZATU AI')).toBeVisible()
    await expect(page.getByText('Wprowadź swój dylemat lub zadanie decyzyjne')).toBeVisible()
    await expect(page.getByPlaceholder(/Np. Stoję przed wyborem między/).first()).toBeVisible()
    await expect(page.getByRole('button', { name: /OBLICZ ROZWIĄZANIE KWANTOWE/ }).first()).toBeVisible()
  })

  test('2. Human Decision Dilemma Flow: Analyzes dilemma and shows options & clarification', async ({ page }) => {
    const input = page.locator('#hero-problem-input')
    await input.fill('Nie wiem, czy zmienić pracę, czy zostać w obecnej firmie')
    await page.getByRole('button', { name: /OBLICZ ROZWIĄZANIE KWANTOWE/ }).first().click()

    // Expect Case Workspace
    await expect(page.getByText(/Rozważane opcje/)).toBeVisible({ timeout: 15000 })
    await expect(page.getByRole('button', { name: /Wygląda dobrze — szukaj najlepszej opcji/ })).toBeVisible()
  })

  test('3. Full Decision & Solving Flow with Independent Verification', async ({ page }) => {
    const input = page.locator('#hero-problem-input')
    await input.fill('Wybierz maksymalnie 2 projekty spośród A, B i C')
    await page.getByRole('button', { name: /OBLICZ ROZWIĄZANIE KWANTOWE/ }).first().click()

    // In Case Workspace
    const proceedBtn = page.getByRole('button', { name: /Wygląda dobrze — szukaj najlepszej opcji/ })
    await expect(proceedBtn).toBeVisible({ timeout: 15000 })
    await proceedBtn.click()

    // In Model Approval Gate
    await expect(page.getByRole('button', { name: /Oblicz najlepszą opcję/ })).toBeVisible({ timeout: 15000 })
    await page.getByRole('button', { name: /Oblicz najlepszą opcję/ }).click()

    // Expect Recommendation View
    await expect(page.getByText(/Wynik niezależnie zweryfikowany/)).toBeVisible({ timeout: 15000 })
    await expect(page.getByText('Odpowiedź')).toBeVisible()
    await expect(page.getByText(/To nie opinia — to wynik obliczeń/)).toBeVisible()
  })
})
