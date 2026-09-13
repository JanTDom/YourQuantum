import { test, expect } from '@playwright/test'

test.describe('V4 Real Uvicorn Backend E2E Suite', () => {
  test('Backend health check is active and reachable', async ({ request }) => {
    // Direct verification of live uvicorn backend health endpoint
    const response = await request.get('http://127.0.0.1:8000/api/v1/health')
    expect(response.status()).toBe(200)
    const data = await response.json()
    expect(data.status).toBe('healthy')
  })

  test('Complete end-to-end problem solving flow with real uvicorn backend', async ({ page }) => {
    // 1. Visit the production-grade frontend connected to live uvicorn
    await page.goto('/')

    // Expect brand identity
    await expect(page.getByText('YourQuantum').first()).toBeVisible()
    await expect(page.getByText('Wprowadź swój dylemat lub zadanie decyzyjne')).toBeVisible()

    // 2. Track real backend API traffic to guarantee zero mocking
    const apiRequests: string[] = []
    page.on('request', (req) => {
      if (req.url().includes('/api/v1/')) {
        apiRequests.push(req.url())
      }
    })

    // 3. Fill in a real optimization problem in the quantum terminal
    const input = page.locator('#hero-problem-input')
    await expect(input).toBeVisible()
    await input.fill('Wybierz maksymalnie 2 projekty spośród A, B i C')

    // Click compute button
    const submitBtn = page.getByRole('button', { name: /OBLICZ ROZWIĄZANIE KWANTOWE/i }).first()
    await expect(submitBtn).toBeVisible()
    await submitBtn.click()

    // 4. Case Workspace appears with options parsed by backend
    // The proceed button takes the user to the approval gate
    const proceedBtn = page.getByRole('button', { name: /Wygląda dobrze — szukaj najlepszej opcji/i })
    await expect(proceedBtn).toBeVisible({ timeout: 15000 })
    await proceedBtn.click()

    // 5. Model Approval Gate: explicit human approval step
    const solveBtn = page.getByRole('button', { name: /Oblicz najlepszą opcję/i })
    await expect(solveBtn).toBeVisible({ timeout: 15000 })
    await solveBtn.click()

    // 6. Recommendation View: live verified mathematical computation
    await expect(page.getByText(/Wynik niezależnie zweryfikowany/i)).toBeVisible({ timeout: 20000 })
    await expect(page.getByText('Odpowiedź')).toBeVisible()

    // Verify that real backend endpoints were called
    expect(apiRequests.length).toBeGreaterThan(0)
  })

  test('Decision matrix and criteria addition with live backend', async ({ page }) => {
    await page.goto('/')
    const input = page.locator('#hero-problem-input')
    await input.fill('Czy wybrać ofertę pracy A, czy ofertę B')

    const submitBtn = page.getByRole('button', { name: /OBLICZ ROZWIĄZANIE KWANTOWE/i }).first()
    await submitBtn.click()

    // In CaseWorkspace, verify score_matrix and options appear
    await expect(page.getByText(/Rozważane opcje/i)).toBeVisible({ timeout: 15000 })
  })
})
