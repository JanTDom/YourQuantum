import { test, expect } from '@playwright/test'

test.describe('YourQuantum V2 Honest Engine E2E Suite (Phase I)', () => {

  test('I1. CHOICE path with web-sourced evidence & break-even calculation', async ({ page }) => {
    // 1. Mock Cognitive Intake for CHOICE problem
    await page.route('**/api/v1/cognitive/intake', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'sess_e2e_choice',
          status: 'success',
          problem_class: 'CHOICE',
          problem_class_reason: 'Dylemat wyboru między dwiema ofertami pracy z wielokryterialnymi wagami.',
          decision_case: {
            title: 'Wybór oferty: Korporacja A vs Startup B',
            domain: 'HR / Kariera',
            facts: [
              {
                id: 'fact_sal_a',
                label: 'Wynagrodzenie Korporacja A',
                value: 22000,
                unit: 'PLN',
                confidence: 1.0,
                provenance: 'user_supplied',
                source_ref: 'Użytkownik',
              },
              {
                id: 'fact_bench_b',
                label: 'Mediana rynkowa Software House',
                value: 28500,
                unit: 'PLN',
                confidence: 0.95,
                provenance: 'web_sourced',
                source_ref: 'https://stat.gov.pl/wynagrodzenia-it-2024',
              },
            ],
            options: [
              {
                id: 'opt_corp_a',
                title: 'Korporacja A (Stabilność)',
                description: 'Stabilna korporacja z kontraktem B2B, 100% pracy zdalnej i prywatną opieką.',
                pros: ['Stabilność zatrudnienia', '100% remote', 'Spokój operacyjny'],
                cons: ['Niższa dynamika wzrostu wynagrodzenia'],
                attributes: { wynagrodzenie: 22000, stabilnosc: 9, stres: 3 },
              },
              {
                id: 'opt_start_b',
                title: 'Startup B (Dynamika)',
                description: 'Szybko rosnący software house, wyższa pensja, wymagane częste wyjazdy.',
                pros: ['Wyższe wynagrodzenie rynkowe', 'Szybki awans'],
                cons: ['Większy stres', 'Konieczność dojazdów'],
                attributes: { wynagrodzenie: 28500, stabilnosc: 5, stres: 8 },
              },
            ],
            criteria: [
              {
                id: 'crit_finance',
                name: 'Finanse i Wynagrodzenie',
                direction: 'maximize',
                weight: 0.35,
                unit: 'PLN',
                is_mandatory: false,
              },
              {
                id: 'crit_peace',
                name: 'Stabilność i Spokój',
                direction: 'maximize',
                weight: 0.65,
                unit: 'pkt',
                is_mandatory: false,
              },
            ],
            unknowns: [],
            tradeoffs: [],
            score_matrix: {
              opt_corp_a: {
                crit_finance: { value: 22000, provenance: 'user_supplied', source_ref: 'Użytkownik' },
                crit_peace: { value: 9, provenance: 'user_supplied', source_ref: 'Użytkownik' },
              },
              opt_start_b: {
                crit_finance: { value: 28500, provenance: 'web_sourced', source_ref: 'https://stat.gov.pl/wynagrodzenia-it-2024' },
                crit_peace: { value: 5, provenance: 'assumed', source_ref: 'Szacunek' },
              },
            },
            provenance_map: {
              'fact_sal_a': 'user_supplied',
              'fact_bench_b': 'web_sourced',
            },
            break_even_point: 'Gdyby waga spokoju spadła poniżej 42%, optymalnym wyborem stałby się Startup B.',
          },
          formalized: {
            problem_id: 'prob_choice_e2e',
            description_raw: 'Wybór między Korporacją A a Startupem B',
            binary_variables: ['choose_corp_a', 'choose_start_b'],
            objective_coefficients: {
              choose_corp_a: 7.8,
              choose_start_b: 6.9,
            },
            objective_direction: 'maximize',
            equality_constraints: [
              { lhs: { choose_corp_a: 1, choose_start_b: 1 }, rhs: 1 },
            ],
            n_variables: 2,
            n_constraints: 1,
            assumptions: ['Wybór dokładnie jednego wariantu zatrudnienia.'],
            provenance_map: {
              choose_corp_a: 'derived',
              choose_start_b: 'derived',
            },
            source_attribution: {
              'fact_bench_b': 'https://stat.gov.pl/wynagrodzenia-it-2024',
            },
            break_even_point: 'Gdyby waga spokoju spadła poniżej 42%, optymalnym wyborem stałby się Startup B.',
          },
        }),
      })
    })

    // Mock Formalize Case
    await page.route('**/api/v1/cases/formalize', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          problem_id: 'prob_choice_e2e',
          description_raw: 'Wybór między Korporacją A a Startupem B',
          binary_variables: ['choose_corp_a', 'choose_start_b'],
          objective_coefficients: {
            choose_corp_a: 7.8,
            choose_start_b: 6.9,
          },
          objective_direction: 'maximize',
          equality_constraints: [
            { lhs: { choose_corp_a: 1, choose_start_b: 1 }, rhs: 1 },
          ],
          n_variables: 2,
          n_constraints: 1,
          assumptions: ['Wybór dokładnie jednego wariantu zatrudnienia.'],
          provenance_map: {
            'fact_sal_a': 'user_supplied',
            'fact_bench_b': 'web_sourced',
          },
          source_attribution: {
            'fact_bench_b': 'https://stat.gov.pl/wynagrodzenia-it-2024',
          },
          break_even_point: 'Gdyby waga spokoju spadła poniżej 42%, optymalnym wyborem stałby się Startup B.',
        }),
      })
    })

    // Mock Create Problem
    await page.route('**/api/v1/problems', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            problem_id: 'prob_choice_e2e',
            description_formalised: 'Wybór wariantu',
            n_variables: 2,
            n_constraints: 1,
            n_objectives: 1,
            approved: false,
            missing_blocking: 0,
            ir_summary: {
              variables: ['choose_corp_a', 'choose_start_b'],
              objective_direction: 'maximize',
              n_equality_constraints: 1,
            },
          }),
        })
      }
    })

    // Mock Approve Problem
    await page.route('**/api/v1/problems/prob_choice_e2e/approve', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          problem_id: 'prob_choice_e2e',
          status: 'APPROVED',
          approved_at: new Date().toISOString(),
        }),
      })
    })

    // Mock Create Job
    await page.route('**/api/v1/jobs', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: 'job_choice_e2e',
            problem_id: 'prob_choice_e2e',
            solver_name: 'cp_sat',
            execution_status: 'QUEUED',
            math_status: null,
            source: null,
            created_at: new Date().toISOString(),
            started_at: null,
            completed_at: null,
            solve_time_seconds: null,
            objective_value: null,
            error_message: null,
          }),
        })
      }
    })

    // Mock Job Status
    await page.route('**/api/v1/jobs/job_choice_e2e', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: 'job_choice_e2e',
            problem_id: 'prob_choice_e2e',
            solver_name: 'cp_sat',
            execution_status: 'COMPLETED',
            publication_status: 'PUBLISHED_VERIFIED',
            math_status: 'OPTIMAL',
            source: 'EXACT_CLASSICAL_SOLVER',
            created_at: new Date().toISOString(),
            started_at: new Date().toISOString(),
            completed_at: new Date().toISOString(),
            solve_time_seconds: 0.042,
            objective_value: 7.8,
            error_message: null,
          }),
        })
      }
    })

    // Mock Job Result with DEC-014 sections, break-even point, and SHA-256 passport
    await page.route('**/api/v1/jobs/job_choice_e2e/result', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'job_choice_e2e',
          problem_id: 'prob_choice_e2e',
          solver_name: 'cp_sat',
          execution_status: 'COMPLETED',
          publication_status: 'PUBLISHED_VERIFIED',
          is_verified_recommendation: true,
          math_status: 'OPTIMAL',
          source: 'EXACT_CLASSICAL_SOLVER',
          objective_value: 7.8,
          solve_time_seconds: 0.042,
          solver_result: {
            assignment: {
              choose_corp_a: 1.0,
              choose_start_b: 0.0,
            },
          },
          verification: {
            verified: true,
            verdict_reason: 'Wszystkie ograniczenia spełnione w 100%',
            feasible: true,
            objective_value: 7.8,
            objective_recomputed: true,
            solver_claimed_objective: 7.8,
            constraint_results: [],
            domain_violations: [],
            numerical_residual: 0.0,
            limitations: [
              'Model zakłada niezmienność stawek podatkowych w 2025/2026 r.',
            ],
            sha256_hash: '3f78b12d59a0f4e91244ac5e982143dc587211bf65342a382dfc700142b93eef',
          },
          metadata: {
            effective_break_even: 'Gdyby waga spokoju spadła poniżej 42%, optymalnym wyborem stałby się Startup B.',
          },
        }),
      })
    })

    // Navigate to Landing Page
    await page.goto('/')

    // Input problem
    const input = page.locator('#hero-problem-input')
    await input.fill('Wybór oferty: Korporacja A ze spokojem czy Startup B z wyższą pensją')
    await page.getByRole('button', { name: /OBLICZ ROZWIĄZANIE KWANTOWE/ }).first().click()

    // 2. Case Workspace Stage
    await expect(page.getByText('Wybór oferty: Korporacja A vs Startup B')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('Korporacja A (Stabilność)')).toBeVisible()
    await expect(page.getByText('Startup B (Dynamika)')).toBeVisible()

    const proceedBtn = page.getByRole('button', { name: /Wygląda dobrze — szukaj najlepszej opcji/ })
    await expect(proceedBtn).toBeVisible()
    await proceedBtn.click()

    // 3. Model Approval Gate Stage
    await expect(page.getByText(/System rozumie Twój dylemat/i)).toBeVisible({ timeout: 10000 })
    await expect(page.getByText(/Macierz Decyzyjna ze Źródłami i Pochodzeniem Danych/i)).toBeVisible()
    await expect(page.getByText(/stat\.gov\.pl/i)).toBeVisible()
    await expect(page.getByText(/web_sourced/i).first()).toBeVisible()

    const solveBtn = page.getByRole('button', { name: /Oblicz najlepszą opcję/i })
    await expect(solveBtn).toBeVisible()
    await solveBtn.click()

    // 4. Recommendation View Stage (DEC-014 format)
    await expect(page.getByText(/Wynik niezależnie zweryfikowany/i)).toBeVisible({ timeout: 10000 })
    await expect(page.getByText(/Odpowiedź/i)).toBeVisible()
    await expect(page.getByText(/Punkt zwrotny/i)).toBeVisible()
    await expect(page.getByText(/Gdyby waga spokoju spadła poniżej 42%/i)).toBeVisible()
    await expect(page.getByText(/3f78b12d59a0f4e9/i)).toBeVisible()
  })

  test('I1. DESIGN path with multi-lever Pareto frontier & sensitivity ranking', async ({ page }) => {
    // 1. Mock Cognitive Intake for DESIGN problem
    await page.route('**/api/v1/cognitive/intake', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          session_id: 'sess_e2e_design',
          status: 'success',
          problem_class: 'DESIGN',
          problem_class_reason: 'Równoczesny dobór spójnej konfiguracji 5 dźwigni architektonicznych.',
          decision_case: {
            title: 'Synteza dźwigni: Optymalizacja systemu ochrony zdrowia',
            domain: 'Healthcare System Design',
            facts: [],
            options: [
              {
                id: 'opt_design_1',
                title: 'Konfiguracja Zintegrowana (POZ + AOS)',
                description: 'Koordynacja podstawowej opieki zdrowotnej i centralizacja chirurgii jednego dnia.',
                pros: ['Skrócenie kolejek', 'Optymalizacja kosztów'],
                cons: ['Wymaga nakładów integracyjnych'],
                attributes: {},
              },
              {
                id: 'opt_design_2',
                title: 'Konfiguracja Tradycyjna',
                description: 'Utrzymanie rozproszonych oddziałów szpitalnych.',
                pros: ['Brak kosztów transformacji'],
                cons: ['Wysokie koszty stałe'],
                attributes: {},
              },
            ],
            criteria: [],
            unknowns: [],
            tradeoffs: [],
            missing_info: [],
            provenance_map: {},
          },
          formalized: {
            problem_id: 'prob_design_e2e',
            description_raw: 'Dobór 5 dźwigni systemowych dla skrócenia kolejek i bilansu NFZ',
            binary_variables: ['L1_opt_a', 'L1_opt_b', 'L2_opt_a', 'L2_opt_b'],
            objective_coefficients: {
              L1_opt_a: 1.0,
              L2_opt_b: 2.5,
            },
            objective_direction: 'minimize',
            equality_constraints: [],
            inequality_constraints: [],
            n_variables: 4,
            n_constraints: 2,
            assumptions: ['Każda dźwignia przyjmuje dokładnie jedną opcję.'],
            provenance_map: {},
          },
        }),
      })
    })

    // Mock Formalize Case
    await page.route('**/api/v1/cases/formalize', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          problem_id: 'prob_design_e2e',
          description_raw: 'Dobór 5 dźwigni systemowych dla skrócenia kolejek i bilansu NFZ',
          binary_variables: ['L1_opt_a', 'L1_opt_b', 'L2_opt_a', 'L2_opt_b'],
          objective_coefficients: {
            L1_opt_a: 1.0,
            L2_opt_b: 2.5,
          },
          objective_direction: 'minimize',
          equality_constraints: [],
          inequality_constraints: [],
          n_variables: 4,
          n_constraints: 2,
          assumptions: ['Każda dźwignia przyjmuje dokładnie jedną opcję.'],
          provenance_map: {},
        }),
      })
    })

    // Mock Create Problem
    await page.route('**/api/v1/problems', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            problem_id: 'prob_design_e2e',
            description_formalised: 'DESIGN Synthesis',
            n_variables: 4,
            n_constraints: 2,
            n_objectives: 2,
            approved: false,
            missing_blocking: 0,
            ir_summary: {
              variables: ['L1_opt_a', 'L1_opt_b', 'L2_opt_a', 'L2_opt_b'],
              objective_direction: 'minimize',
              n_equality_constraints: 2,
            },
          }),
        })
      }
    })

    // Mock Approve Problem
    await page.route('**/api/v1/problems/prob_design_e2e/approve', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          problem_id: 'prob_design_e2e',
          status: 'APPROVED',
          approved_at: new Date().toISOString(),
        }),
      })
    })

    // Mock Create Job
    await page.route('**/api/v1/jobs', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: 'job_design_e2e',
            problem_id: 'prob_design_e2e',
            solver_name: 'cp_sat',
            execution_status: 'QUEUED',
            created_at: new Date().toISOString(),
          }),
        })
      }
    })

    // Mock Job Status
    await page.route('**/api/v1/jobs/job_design_e2e', async (route) => {
      if (route.request().method() === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            job_id: 'job_design_e2e',
            problem_id: 'prob_design_e2e',
            solver_name: 'cp_sat',
            execution_status: 'COMPLETED',
            publication_status: 'PUBLISHED_VERIFIED',
            math_status: 'OPTIMAL',
            source: 'EXACT_CLASSICAL_SOLVER',
            created_at: new Date().toISOString(),
            started_at: new Date().toISOString(),
            completed_at: new Date().toISOString(),
            solve_time_seconds: 0.089,
            objective_value: 3.5,
            error_message: null,
          }),
        })
      }
    })

    // Mock Job Result with DESIGN Pareto frontier synthesis
    await page.route('**/api/v1/jobs/job_design_e2e/result', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          job_id: 'job_design_e2e',
          problem_id: 'prob_design_e2e',
          solver_name: 'cp_sat',
          execution_status: 'COMPLETED',
          publication_status: 'PUBLISHED_VERIFIED',
          is_verified_recommendation: true,
          math_status: 'OPTIMAL',
          source: 'EXACT_CLASSICAL_SOLVER',
          objective_value: 3.5,
          solve_time_seconds: 0.089,
          solver_result: {
            assignment: {
              L1_opt_a: 1.0,
              L2_opt_b: 1.0,
            },
          },
          verification: {
            verified: true,
            verdict_reason: 'Wszystkie ograniczenia spełnione w 100%',
            feasible: true,
            objective_value: 3.5,
            objective_recomputed: true,
            solver_claimed_objective: 3.5,
            constraint_results: [],
            domain_violations: [],
            numerical_residual: 0.0,
            limitations: [
              'Front Pareto wyznaczony metodą ważonych sum celów (weighted-sum method).',
            ],
            sha256_hash: '7a11bb02030405060708090a0b0c0d0e0f101112131415161718192021222324',
          },
          metadata: {
            problem_class: 'DESIGN',
          },
        }),
      })
    })

    // Mock DESIGN Fixture and Synthesize endpoints
    await page.route('**/api/v1/design/fixtures/healthcare_pl', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          problem_id: 'healthcare_pl',
          domain: 'healthcare',
        }),
      })
    })

    await page.route('**/api/v1/design/synthesize', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          synthesis: {
            problem_id: 'healthcare_pl',
            model_optimal_label: 'optymalna dla modelu, nie dla świata (wynik zależy od podanych kryteriów i wag)',
            practical_manifestation: 'Model wyznaczył konfigurację o najwyższej użyteczności publicznej.',
            optimal_configuration: {
              'Model POZ': 'Koordynacja opieki z budżetem powierzonym',
              'Sieć Szpitali i AOS': 'Centralizacja chirurgii jednego dnia',
            },
            optimal_titles: {
              'Model POZ': 'Koordynacja opieki z budżetem powierzonym',
              'Sieć Szpitali i AOS': 'Centralizacja chirurgii jednego dnia',
            },
            pareto_frontier: [
              {
                configuration: { 'Model POZ': 'Koordynacja opieki' },
                objective_values: { 'Koszty mld zł': 45.0, 'Czas oczekiwania dni': 24.0 },
                is_pareto_optimal: true,
              },
              {
                configuration: { 'Model POZ': 'Dostęp swobodny' },
                objective_values: { 'Koszty mld zł': 62.0, 'Czas oczekiwania dni': 12.0 },
                is_pareto_optimal: true,
              },
            ],
            lever_importance_ranking: [
              {
                lever_id: 'L1',
                lever_name: 'Model POZ',
                sensitivity_impact: 0.42,
                options_count: 3,
                relative_impact_percent: 42,
              },
              {
                lever_id: 'L2',
                lever_name: 'Sieć Szpitali i AOS',
                sensitivity_impact: 0.31,
                options_count: 2,
                relative_impact_percent: 31,
              },
            ],
            unknowns_and_decisive_assumptions: [],
            practical_manifestation_steps: [],
          },
        }),
      })
    })

    // Navigate to Landing Page
    await page.goto('/')

    // Input problem
    const input = page.locator('#hero-problem-input')
    await input.fill('Synteza 5 dźwigni systemowych dla optymalizacji ochrony zdrowia')
    await page.getByRole('button', { name: /OBLICZ ROZWIĄZANIE KWANTOWE/ }).first().click()

    // Workspace & Proceed
    await expect(page.getByText('Synteza dźwigni: Optymalizacja systemu ochrony zdrowia')).toBeVisible({ timeout: 10000 })
    await expect(page.getByText('Konfiguracja Zintegrowana (POZ + AOS)')).toBeVisible()
    const proceedBtn = page.getByRole('button', { name: /Wygląda dobrze — szukaj najlepszej opcji/ })
    await expect(proceedBtn).toBeVisible({ timeout: 10000 })
    await proceedBtn.click()

    // Model Approval Gate & Solve
    await expect(page.getByText(/System rozumie Twój dylemat/i)).toBeVisible({ timeout: 10000 })
    const solveBtn = page.getByRole('button', { name: /Oblicz najlepszą opcję/i })
    await expect(solveBtn).toBeVisible({ timeout: 10000 })
    await solveBtn.click()

    // Verify DESIGN Recommendation View
    await expect(page.getByText(/Klasa problemu: DESIGN/i)).toBeVisible({ timeout: 10000 })
    await expect(page.getByText(/Optymalna Konfiguracja Architektury Systemowej/i)).toBeVisible()
    await expect(page.getByText('Koordynacja opieki z budżetem powierzonym')).toBeVisible()
    await expect(page.getByText(/Front Pareto — Warianty Niezdominowane/i)).toBeVisible()
    await expect(page.getByText(/Ranking wrażliwości dźwigni/i)).toBeVisible()
    await expect(page.getByText(/Zweryfikowane źródła instytucjonalne/i)).toBeVisible()
    await expect(page.getByText(/Zastrzeżenie formalne/i)).toBeVisible()
  })
})
