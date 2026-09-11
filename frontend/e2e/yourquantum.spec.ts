import { test, expect } from '@playwright/test'

test.describe('YourQuantum Calm Decision Studio E2E Suite', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('1. Smoke Test: Verifies brand identity, calm header, and conversation prompt', async ({ page }) => {
    await expect(page.getByText('YourQuantum').first()).toBeVisible()
    await expect(page.getByText('Studio decyzji').first()).toBeVisible()
    await expect(page.getByText('Przedstaw swój problem lub dylemat')).toBeVisible()
    await expect(page.getByPlaceholder(/Np. Stoję przed wyborem między/)).toBeVisible()
    await expect(page.getByRole('button', { name: 'Przeanalizuj sytuację' })).toBeVisible()
  })

  test('2. Human Decision Dilemma Flow: Analyzes dilemma and shows options & clarification', async ({ page }) => {
    const input = page.getByPlaceholder(/Np. Stoję przed wyborem między/)
    await input.fill('Nie wiem, czy zmienić pracę, czy zostać w obecnej firmie')
    await page.getByRole('button', { name: 'Przeanalizuj sytuację' }).click()

    // Expect Case Workspace
    await expect(page.getByText('Zrozumienie sytuacji decyzyjnej')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('Rozważane warianty wyboru')).toBeVisible()
    await expect(page.getByText('Kwestie do doprecyzowania')).toBeVisible()
    await expect(page.getByRole('button', { name: 'Zatwierdź założenia i przejdź do weryfikacji' })).toBeVisible()
  })

  test('3. Full Decision & Solving Flow with Independent Verification', async ({ page }) => {
    const input = page.getByPlaceholder(/Np. Stoję przed wyborem między/)
    await input.fill('Wybierz maksymalnie 2 projekty spośród A, B i C')
    await page.getByRole('button', { name: 'Przeanalizuj sytuację' }).click()

    // In Case Workspace
    await expect(page.getByText('Zrozumienie sytuacji decyzyjnej')).toBeVisible({ timeout: 10000 })
    await page.getByRole('button', { name: 'Zatwierdź założenia i przejdź do weryfikacji' }).click()

    // In Model Approval Gate
    await expect(page.getByText('Przejrzystość obliczeń (bramka weryfikacyjna)')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('Zatwierdzenie modelu przed uruchomieniem silnika')).toBeVisible()
    await expect(page.getByText('Zmienne wyboru')).toBeVisible()

    // Click Approve and Solve
    await page.getByRole('button', { name: 'Zatwierdź model i rozwiąż' }).click()

    // Expect Recommendation View with 5 sections
    await expect(page.getByText('1. Co z tego wynika dla Ciebie')).toBeVisible({ timeout: 15000 })
    await expect(page.getByText('2. Kluczowe powody takiego wyboru')).toBeVisible()
    await expect(page.getByText('3. Kompromisy i koszty wyboru')).toBeVisible()
    await expect(page.getByText('4. Analiza wrażliwości („Co-jeśli”)')).toBeVisible()
    await expect(page.getByText('5. Bezpośredni następny krok')).toBeVisible()

    // Check publication verification badge
    await expect(page.getByText(/Rekomendacja niezależnie zweryfikowana/)).toBeVisible()

    // Expand Evidence Drawer
    await page.getByText('Rozwiń dowody techniczne ▼').click()
    await expect(page.getByText('Silnik obliczeniowy')).toBeVisible()
    await expect(page.getByText('Raport niezależnego audytu ograniczeń')).toBeVisible()
  })
})
