import React, { useState, useEffect, useMemo } from 'react'
import { api, UniversalComputeRequest, UniversalComputeResponse } from '../api'
import s from './ApiPortalModal.module.css'

interface ApiPortalModalProps {
  isOpen: boolean
  onClose: () => void
}

type DomainTab = 'FINANCE' | 'LOGISTICS' | 'HR' | 'GENERAL'
type LangTab = 'PYTHON' | 'TYPESCRIPT' | 'CURL'

const PRESET_REQUESTS: Record<DomainTab, UniversalComputeRequest> = {
  FINANCE: {
    domain: 'finance',
    title: 'Optymalizacja Alokacji Kapitału B+R',
    variables: [
      { id: 'proj_1', name: 'Nowa linia technologiczna', cost: 150000, value: 420000 },
      { id: 'proj_2', name: 'Rozbudowa magazynu e-commerce', cost: 90000, value: 230000 },
      { id: 'proj_3', name: 'Wdrożenie automatyzacji AI', cost: 60000, value: 195000 },
      { id: 'proj_4', name: 'Modernizacja floty pojazdów', cost: 120000, value: 180000 },
    ],
    objective_direction: 'maximize',
    objective_attribute: 'value',
    constraints: [
      {
        name: 'Sztywny limit budżetu inwestycyjnego',
        type: 'budget',
        attribute: 'cost',
        limit: 220000,
      },
    ],
    solver: 'auto',
    include_stress_test: true,
  },
  LOGISTICS: {
    domain: 'logistics',
    title: 'Wybór Korytarzy Transportowych',
    variables: [
      { id: 'route_A', name: 'Trasa Północna A (Gdańsk-Warszawa)', cost: 4000, value: 120 },
      { id: 'route_B', name: 'Trasa Północna B (Gdynia-Łódź)', cost: 3800, value: 110 },
      { id: 'route_C', name: 'Trasa Południowa (Kraków-Katowice)', cost: 2500, value: 85 },
      { id: 'route_D', name: 'Trasa Zachodnia (Poznań-Wrocław)', cost: 3200, value: 95 },
    ],
    objective_direction: 'maximize',
    objective_attribute: 'value',
    constraints: [
      {
        name: 'Wybór dokładnie 2 głównych tras',
        type: 'cardinality_exact',
        count: 2,
      },
      {
        name: 'Wykluczenie wzajemne tras A i B (konflikt zasobów)',
        type: 'incompatible',
        var_ids: ['route_A', 'route_B'],
      },
    ],
    solver: 'auto',
    include_stress_test: true,
  },
  HR: {
    domain: 'hr',
    title: 'Kompletowanie Zespołu Projektowego',
    variables: [
      { id: 'emp_1', name: 'Senior Quantum Architect', cost: 35000, value: 98 },
      { id: 'emp_2', name: 'Lead Fullstack Engineer', cost: 28000, value: 92 },
      { id: 'emp_3', name: 'Data Scientist / ML Lead', cost: 26000, value: 88 },
      { id: 'emp_4', name: 'DevOps Cloud Specialist', cost: 22000, value: 80 },
    ],
    objective_direction: 'maximize',
    objective_attribute: 'value',
    constraints: [
      {
        name: 'Limit miesięcznego budżetu wynagrodzeń',
        type: 'budget',
        attribute: 'cost',
        limit: 65000,
      },
      {
        name: 'Minimum 2 specjalistów w zespole',
        type: 'cardinality_min',
        count: 2,
      },
    ],
    solver: 'auto',
    include_stress_test: true,
  },
  GENERAL: {
    domain: 'general',
    title: 'Wielokryterialna Selekcja Opcji Decyzyjnych',
    variables: [
      { id: 'opt_alpha', name: 'Wariant Alpha (Wysoki zysk, wysokie ryzyko)', cost: 80, value: 95 },
      { id: 'opt_beta', name: 'Wariant Beta (Zrównoważony)', cost: 50, value: 75 },
      { id: 'opt_gamma', name: 'Wariant Gamma (Konserwatywny)', cost: 30, value: 50 },
    ],
    objective_direction: 'maximize',
    objective_attribute: 'value',
    constraints: [
      {
        name: 'Maksymalny łączny koszt ryzyka',
        type: 'budget',
        attribute: 'cost',
        limit: 100,
      },
    ],
    solver: 'auto',
    include_stress_test: true,
  },
}

export const ApiPortalModal: React.FC<ApiPortalModalProps> = ({ isOpen, onClose }) => {
  const [password, setPassword] = useState('')
  const [authToken, setAuthToken] = useState<string>(() => {
    return localStorage.getItem('yq_api_token') || ''
  })
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return !!localStorage.getItem('yq_api_token')
  })
  const [isLoadingAuth, setIsLoadingAuth] = useState(false)
  const [authError, setAuthError] = useState<string | null>(null)

  // Portal tabs
  const [activeDomain, setActiveDomain] = useState<DomainTab>('FINANCE')
  const [activeLang, setActiveLang] = useState<LangTab>('PYTHON')
  const [copiedKey, setCopiedKey] = useState(false)
  const [copiedCode, setCopiedCode] = useState(false)

  // Interactive Live Tester
  const [isComputing, setIsComputing] = useState(false)
  const [computeResult, setComputeResult] = useState<UniversalComputeResponse | null>(null)
  const [computeError, setComputeError] = useState<string | null>(null)

  // Close on ESC
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose()
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const handleVerifyPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!password.trim()) return
    setIsLoadingAuth(true)
    setAuthError(null)

    try {
      const res = await api.verifyApiAccess(password.trim())
      if (res.valid) {
        setIsAuthenticated(true)
        setAuthToken(res.token)
        localStorage.setItem('yq_api_token', res.token)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Nieprawidłowe hasło dostępu.'
      setAuthError(msg)
    } finally {
      setIsLoadingAuth(false)
    }
  }

  const handleCopyKey = () => {
    const keyToCopy = authToken || ''
    if (!keyToCopy) return
    navigator.clipboard.writeText(keyToCopy)
    setCopiedKey(true)
    setTimeout(() => setCopiedKey(false), 2000)
  }

  const activePreset = useMemo(() => PRESET_REQUESTS[activeDomain], [activeDomain])

  // Generate code snippet according to language and active domain
  const generatedCode = useMemo(() => {
    const key = authToken || 'YOUR_API_TOKEN'
    const reqJson = JSON.stringify(activePreset, null, 2)

    if (activeLang === 'PYTHON') {
      return `from yourquantum_sdk import YourQuantumClient

client = YourQuantumClient(api_key="${key}", base_url="https://yourquantum.pl")

# Wielozadaniowe wywołanie w dziedzinie: ${activeDomain.toLowerCase()}
result = client.solve(
    title="${activePreset.title}",
    domain="${activePreset.domain}",
    variables=${JSON.stringify(activePreset.variables, null, 4)},
    constraints=${JSON.stringify(activePreset.constraints, null, 4)},
    objective_direction="${activePreset.objective_direction}",
    objective_attribute="${activePreset.objective_attribute}",
    solver="auto",
    include_stress_test=True,
)

print("Wybrane elementy:", result["optimal_selection"])
print("Wartość funkcji celu:", result["total_objective_value"])
print("Paszport kryptograficzny SHA-256:", result["sha256_passport"])
print("Luka optymalności:", result["optimality_gap_percent"], "%")`
    }

    if (activeLang === 'TYPESCRIPT') {
      return `import { YourQuantumClient } from './yourquantum_client';

const client = new YourQuantumClient({ apiKey: '${key}' });

async function runOptimization() {
  const result = await client.solve({
    domain: '${activePreset.domain}',
    title: '${activePreset.title}',
    variables: ${JSON.stringify(activePreset.variables, null, 4)},
    constraints: ${JSON.stringify(activePreset.constraints, null, 4)},
    objective_direction: '${activePreset.objective_direction}',
    objective_attribute: '${activePreset.objective_attribute}',
    solver: 'auto',
    include_stress_test: true,
  });

  console.log('Optymalny podzbiór:', result.optimal_selection);
  console.log('Zysk / Wartość:', result.total_objective_value);
  console.log('Paszport SHA-256:', result.sha256_passport);
}

runOptimization();`
    }

    // cURL
    return `curl -X POST https://yourquantum.pl/api/v1/universal/compute \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer ${key}" \\
  -d '${reqJson.replace(/'/g, "'\\''")}'`
  }, [activeLang, activePreset, authToken])

  const handleCopyCode = () => {
    navigator.clipboard.writeText(generatedCode)
    setCopiedCode(true)
    setTimeout(() => setCopiedCode(false), 2000)
  }

  const handleRunLiveTest = async () => {
    setIsComputing(true)
    setComputeError(null)
    setComputeResult(null)

    try {
      if (!authToken) {
        setComputeError('Wymagane uwierzytelnienie: wprowadź hasło dostępu')
        return
      }
      const res = await api.runUniversalCompute(activePreset, authToken)
      setComputeResult(res)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Błąd podczas obliczeń API'
      setComputeError(msg)
    } finally {
      setIsComputing(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className={s.overlay} onClick={onClose} role="dialog" aria-modal="true">
      <div className={s.modal} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className={s.header}>
          <div className={s.headerLeft}>
            <span className={s.headerBadge}>B2B & DEV PORTAL</span>
            <h2 className={s.title}>Kwantowe API & Oficjalne SDK</h2>
          </div>
          <button className={s.closeBtn} onClick={onClose} title="Zamknij (Esc)">
            ✕
          </button>
        </div>

        {/* Modal Body */}
        <div className={s.body}>
          {!isAuthenticated ? (
            /* PASSWORD GATE */
            <div className={s.gateContainer}>
              <div className={s.gateIconWrap}>🔒</div>
              <h3 className={s.gateHeading}>Dostęp Chroniony do Kwantowego API</h3>
              <p className={s.gateDesc}>
                Wprowadź hasło deweloperskie, aby odblokować uniwersalny endpoint obliczeniowy,
                pobrać gotowe pliki SDK (Python, TypeScript) oraz zintegrować optymalizację
                YourQuantum w swoich systemach zewnętrznych.
              </p>
              <form className={s.gateForm} onSubmit={handleVerifyPassword}>
                <div className={s.inputGroup}>
                  <input
                    type="password"
                    className={s.passwordInput}
                    placeholder="Wprowadź hasło dostępu..."
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    autoFocus
                  />
                </div>
                <button
                  type="submit"
                  className={s.gateBtn}
                  disabled={isLoadingAuth || !password.trim()}
                >
                  {isLoadingAuth ? 'Weryfikowanie...' : '⚡ Odblokuj Dostęp do API'}
                </button>
                {authError && <div className={s.errorBox}>{authError}</div>}
              </form>
            </div>
          ) : (
            /* UNLOCKED DEVELOPER DASHBOARD */
            <>
              {/* API Key Banner */}
              <div className={s.keyBanner}>
                 <div>
                   <div className={s.keyLabel}>Twój Klucz Autoryzacyjny API</div>
                   <div className={s.keyValue}>{authToken || 'Brak aktywnego tokenu'}</div>
                 </div>
                 <button className={s.copyBtn} onClick={handleCopyKey} disabled={!authToken}>
                   {copiedKey ? '✓ Skopiowano' : '📋 Kopiuj Klucz API'}
                 </button>
               </div>

               {/* SDK Download Section */}
               <div>
                 <h3 className={s.sectionTitle}>
                   <span>📥</span> Pobierz Gotowe Biblioteki SDK (Zero-Dependency)
                 </h3>
                 <div className={s.sdkGrid} style={{ marginTop: '0.75rem' }}>
                   {/* Python SDK */}
                   <div className={s.sdkCard}>
                     <div className={s.sdkCardTop}>
                       <div className={s.sdkName}>
                         <span>🐍 Python SDK</span>
                         <span className={s.sdkBadge}>v1.0.0</span>
                       </div>
                       <div className={s.sdkDesc}>
                         Oficjalny klient zero-dependency dla Pythona. Działa z biblioteką standardową
                         (urllib/json), gotowy do wdrożenia w FastAPI, Django, skryptach Data Science
                         i potokach agentów AI.
                       </div>
                     </div>
                     <a
                       href={api.getSdkDownloadUrl('python', authToken || '')}
                       download="yourquantum_sdk.py"
                       className={s.downloadBtn}
                     >
                       <span>📥</span> Pobierz yourquantum_sdk.py
                     </a>
                   </div>

                   {/* TypeScript SDK */}
                   <div className={s.sdkCard}>
                     <div className={s.sdkCardTop}>
                       <div className={s.sdkName}>
                         <span>⚡ TypeScript / Node.js</span>
                         <span className={s.sdkBadge}>v1.0.0</span>
                       </div>
                       <div className={s.sdkDesc}>
                         Oficjalny silnie typowany klient zero-dependency. Działa z natywnym fetch
                         w środowiskach Node.js 18+, Bun, Deno oraz bezpośrednio w aplikacjach
                         przeglądarkowych React, Vue, Next.js.
                       </div>
                     </div>
                     <a
                       href={api.getSdkDownloadUrl('typescript', authToken || '')}
                       download="yourquantum_client.ts"
                       className={s.downloadBtn}
                     >
                       <span>📥</span> Pobierz yourquantum_client.ts
                     </a>
                   </div>
                 </div>
               </div>

              {/* Multi-Domain Code Examples */}
              <div>
                <h3 className={s.sectionTitle}>
                  <span>🌐</span> Wielozadaniowe Przykłady Integracji
                </h3>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem' }}>
                  <div className={s.tabNav}>
                    <button
                      className={`${s.tabBtn} ${activeDomain === 'FINANCE' ? s.tabBtnActive : ''}`}
                      onClick={() => setActiveDomain('FINANCE')}
                    >
                      💼 Finanse & Portfele
                    </button>
                    <button
                      className={`${s.tabBtn} ${activeDomain === 'LOGISTICS' ? s.tabBtnActive : ''}`}
                      onClick={() => setActiveDomain('LOGISTICS')}
                    >
                      🚚 Logistyka & Trasy
                    </button>
                    <button
                      className={`${s.tabBtn} ${activeDomain === 'HR' ? s.tabBtnActive : ''}`}
                      onClick={() => setActiveDomain('HR')}
                    >
                      👥 HR & Zespoły
                    </button>
                    <button
                      className={`${s.tabBtn} ${activeDomain === 'GENERAL' ? s.tabBtnActive : ''}`}
                      onClick={() => setActiveDomain('GENERAL')}
                    >
                      ⚙️ Dowolna Selekcja
                    </button>
                  </div>

                  <div className={s.langToggle}>
                    <button
                      className={`${s.langBtn} ${activeLang === 'PYTHON' ? s.langBtnActive : ''}`}
                      onClick={() => setActiveLang('PYTHON')}
                    >
                      Python
                    </button>
                    <button
                      className={`${s.langBtn} ${activeLang === 'TYPESCRIPT' ? s.langBtnActive : ''}`}
                      onClick={() => setActiveLang('TYPESCRIPT')}
                    >
                      TypeScript
                    </button>
                    <button
                      className={`${s.langBtn} ${activeLang === 'CURL' ? s.langBtnActive : ''}`}
                      onClick={() => setActiveLang('CURL')}
                    >
                      cURL
                    </button>
                  </div>
                </div>

                <div style={{ position: 'relative', marginTop: '0.5rem' }}>
                  <pre className={s.codeBlock}>
                    <code>{generatedCode}</code>
                  </pre>
                  <button
                    className={s.copyBtn}
                    onClick={handleCopyCode}
                    style={{ position: 'absolute', top: '10px', right: '10px' }}
                  >
                    {copiedCode ? '✓ Skopiowano' : '📋 Kopiuj Kod'}
                  </button>
                </div>
              </div>

              {/* Interactive Live Tester */}
              <div className={s.testerCard}>
                <div className={s.testerHeader}>
                  <div>
                    <h4 style={{ margin: '0 0 0.25rem 0', fontSize: '0.98rem', color: 'oklch(98% 0.01 240)' }}>
                      ⚡ Interaktywny Tester na Żywo
                    </h4>
                    <span style={{ fontSize: '0.8125rem', color: 'oklch(65% 0.02 240)' }}>
                      Wykonaj natychmiastowe zapytanie do API dla aktywnego presetu: <strong>{activePreset.title}</strong>
                    </span>
                  </div>
                  <button
                    className={s.testerActionBtn}
                    onClick={handleRunLiveTest}
                    disabled={isComputing}
                  >
                    {isComputing ? 'Obliczanie...' : '⚡ Uruchom Obliczenie Przez API'}
                  </button>
                </div>

                {computeError && <div className={s.errorBox}>{computeError}</div>}

                {computeResult && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                    <div className={s.metricsRow}>
                      <div className={s.metricBadge}>
                        <span className={s.metricBadgeTitle}>Status Solwera</span>
                        <span className={s.metricBadgeVal} style={{ color: 'oklch(80% 0.16 145)' }}>
                          ● {computeResult.status} ({computeResult.solver_used})
                        </span>
                      </div>
                      <div className={s.metricBadge}>
                        <span className={s.metricBadgeTitle}>Wartość Optymalna</span>
                        <span className={s.metricBadgeVal}>
                          {computeResult.total_objective_value.toLocaleString('pl-PL')}
                        </span>
                      </div>
                      <div className={s.metricBadge}>
                        <span className={s.metricBadgeTitle}>Luka Optymalności</span>
                        <span className={s.metricBadgeVal}>
                          {computeResult.optimality_gap_percent !== null ? `${computeResult.optimality_gap_percent}%` : '0.00%'}
                        </span>
                      </div>
                      <div className={s.metricBadge}>
                        <span className={s.metricBadgeTitle}>Czas Obliczeń</span>
                        <span className={s.metricBadgeVal}>{computeResult.compute_time_ms} ms</span>
                      </div>
                    </div>

                    <div className={s.testerResultBox}>
                      <div style={{ color: 'oklch(78% 0.14 80)', fontWeight: 700, marginBottom: '0.4rem' }}>
                        ✦ Wybrana Alokacja Decyzyjna:
                      </div>
                      <ul style={{ margin: '0 0 0.75rem 1.25rem', padding: 0 }}>
                        {computeResult.optimal_selection.map((item) => (
                          <li key={item.id} style={{ color: 'oklch(95% 0.01 240)' }}>
                            <strong>{item.name}</strong> (id: {item.id}
                            {item.cost ? `, koszt: ${item.cost}` : ''}
                            {item.value ? `, wartość: ${item.value}` : ''})
                          </li>
                        ))}
                      </ul>
                      <div style={{ color: 'oklch(70% 0.02 240)', fontSize: '0.75rem', wordBreak: 'break-all' }}>
                        Paszport SHA-256: <code>{computeResult.sha256_passport}</code>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
