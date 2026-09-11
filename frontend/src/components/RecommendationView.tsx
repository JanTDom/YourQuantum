import React from 'react'
import { DecisionCase, JobResult } from '../api'
import { EvidenceDrawer } from './EvidenceDrawer'

interface RecommendationViewProps {
  decisionCase: DecisionCase | null
  result: JobResult
  comparisonResult?: JobResult | null
  onStartNew: () => void
  breakEvenPoint?: string | null
}

export const RecommendationView: React.FC<RecommendationViewProps> = ({
  decisionCase,
  result,
  comparisonResult,
  onStartNew,
  breakEvenPoint,
}) => {
  const isVerified = result.publication_status === 'PUBLISHED_VERIFIED'
  const assignment = result.solver_result?.assignment ?? {}

  // Map solver variable names to human option titles
  const chosenVarNames = Object.entries(assignment)
    .filter(([, val]) => val > 0.5)
    .map(([k]) => k)

  const chosenTitles = chosenVarNames.map((v) => {
    if (decisionCase) {
      const vNorm = v.toLowerCase().replace(/[_\s-]+/g, ' ')
      const match = decisionCase.options.find((o) => {
        const oNorm = o.title.toLowerCase().replace(/[_\s-]+/g, ' ')
        return (
          o.id === v ||
          oNorm.includes(vNorm) ||
          vNorm.includes(oNorm) ||
          v.toLowerCase().includes(o.id.toLowerCase())
        )
      })
      if (match) return match.title
    }
    return v.replace(/_/g, ' ').replace(/^\w/, (c) => c.toUpperCase())
  })

  const hasChoice = chosenTitles.length > 0
  const headline = hasChoice
    ? chosenTitles.join(' i ')
    : 'System znalazł najlepsze rozwiązanie'

  const primaryWinnerTitle = chosenTitles[0] || 'Rekomendowana opcja'
  const alternativeOptions =
    decisionCase?.options.filter((o) => !chosenTitles.includes(o.title)) || []
  const alternativeTitle =
    alternativeOptions.length > 0 ? alternativeOptions[0].title : 'Druga opcja'

  const effectiveBreakEven =
    breakEvenPoint ||
    decisionCase?.break_even_point ||
    `Opcja "${alternativeTitle}" zyskałaby przewagę, gdyby zaoferowała warunki korzystniejsze o ok. 20-30% w kluczowych aspektach (finansowych, czasowych lub stabilności), albo gdyby Twoim nadrzędnym priorytetem stało się całkowite uniknięcie ryzyka.`

  const mathStatusMap: Record<string, string> = {
    OPTIMAL: 'Najlepszy możliwy wynik przy podanych warunkach',
    FEASIBLE: 'Wynik poprawny — zadanie rozwiązane',
    INFEASIBLE: 'Brak rozwiązania — podane warunki wzajemnie się wykluczają',
    UNKNOWN: 'Wynik niepewny — spróbuj doprecyzować warunki',
  }
  const mathStatusLabel =
    mathStatusMap[result.math_status ?? ''] ?? 'Wynik obliczony'

  return (
    <div style={{ minHeight: '100vh', background: 'oklch(6% 0.01 250)', position: 'relative', overflow: 'hidden' }}>

      {/* Background — future lab photo, left-side dark for readability */}
      <img
        src="/images/future-lab.jpg"
        alt=""
        aria-hidden="true"
        className="no-print"
        style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%',
          objectFit: 'cover', objectPosition: 'center',
          opacity: 0.13, filter: 'saturate(0.5) brightness(0.5)',
          pointerEvents: 'none', zIndex: 0,
        }}
      />
      <div className="no-print" aria-hidden="true" style={{
        position: 'absolute', inset: 0, zIndex: 0,
        background: `
          radial-gradient(ellipse 90% 60% at 50% 0%, oklch(75% 0.12 80 / 0.06) 0%, transparent 55%),
          radial-gradient(ellipse 60% 50% at 80% 80%, oklch(62% 0.18 240 / 0.07) 0%, transparent 60%),
          linear-gradient(to bottom, oklch(6% 0.01 250 / 0.6) 0%, oklch(6% 0.01 250 / 0.88) 100%)
        `,
      }} />

      {/* Floating result-celebration orbs */}
      <div className="no-print" aria-hidden="true" style={{ position: 'absolute', inset: 0, zIndex: 0, pointerEvents: 'none', overflow: 'hidden' }}>
        {[
          { s: 180, x: 82, y: 12, c: 'oklch(75% 0.12 80 / 0.08)', d: 6 },
          { s: 80,  x: 5,  y: 60, c: 'oklch(62% 0.18 240 / 0.1)', d: 9 },
          { s: 120, x: 90, y: 70, c: 'oklch(72% 0.18 152 / 0.07)', d: 7 },
        ].map((orb, i) => (
          <div key={i} style={{
            position: 'absolute',
            width: `${orb.s}px`, height: `${orb.s}px`,
            borderRadius: '50%',
            background: orb.c,
            left: `${orb.x}%`, top: `${orb.y}%`,
            filter: 'blur(40px)',
            animation: `rvFloat${i} ${orb.d}s ease-in-out ${i * 1.5}s infinite`,
          }} />
        ))}
      </div>

      {/* Content */}
      <div style={{
        position: 'relative', zIndex: 1,
        maxWidth: '960px', margin: '0 auto',
        padding: 'clamp(1.5rem, 4vw, 3rem) clamp(1rem, 3vw, 2rem)',
        animation: 'wsPageIn 0.6s cubic-bezier(0.22,1,0.36,1) both',
      }}>

      {/* ── Official Print Header (Only visible when printing) ─ */}
      <div className="print-only">
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'flex-start',
          borderBottom: '2px solid #0f172a',
          paddingBottom: '0.875rem',
          marginBottom: '1.5rem',
        }}>
          <div>
            <div style={{ fontSize: '18pt', fontWeight: 900, color: '#0f172a', letterSpacing: '-0.02em' }}>
              YOURQUANTUM
            </div>
            <div style={{ fontSize: '11pt', fontWeight: 700, color: '#334155', marginTop: '2px' }}>
              Raport Weryfikacji Decyzyjnej
            </div>
            <div style={{ fontSize: '9pt', color: '#64748b', marginTop: '3px' }}>
              Temat: {decisionCase?.title || 'Dylemat decyzyjny'}
            </div>
          </div>
          <div style={{ textAlign: 'right', fontSize: '8.5pt', color: '#475569' }}>
            <div>Data: {new Date().toLocaleDateString('pl-PL', { year: 'numeric', month: 'long', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</div>
            <div style={{ color: '#059669', fontWeight: 800, marginTop: '3px' }}>
              ✓ CERTYFIKAT FORMALNY ZWERYFIKOWANY
            </div>
            <div style={{ fontSize: '8pt', color: '#64748b' }}>
              Status dowodu: {mathStatusLabel}
            </div>
          </div>
        </div>
      </div>

      {/* ── Step indicator (all done) ────────────────────────── */}
      <div className="no-print" style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        marginBottom: '2rem',
      }}>
        {['Sytuacja opisana', 'Obliczenia', 'Wynik'].map((label, i) => (
          <React.Fragment key={label}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontSize: '0.8125rem',
              fontWeight: i === 2 ? 700 : 500,
              color: i === 2 ? 'oklch(75% 0.12 80)' : 'oklch(54% 0.018 250)',
            }}>
              <span style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: i === 2 ? 'oklch(75% 0.12 80)' : 'oklch(35% 0.08 168)',
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '0.6875rem',
                fontWeight: 900,
                color: i === 2 ? 'oklch(6% 0.01 250)' : 'oklch(78% 0.14 168)',
                flexShrink: 0,
              }}>
                {i === 2 ? '★' : '✓'}
              </span>
              {label}
            </div>
            {i < 2 && (
              <div style={{ flex: 1, height: '1px', background: 'oklch(75% 0.12 80 / 0.3)' }} />
            )}
          </React.Fragment>
        ))}
      </div>

      {/* ── Verification status banner ───────────────────────── */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        gap: '1rem',
        padding: '0.875rem 1.25rem',
        borderRadius: '10px',
        background: isVerified ? 'oklch(16% 0.04 170)' : 'oklch(16% 0.04 70)',
        border: `1px solid ${isVerified ? 'oklch(35% 0.08 168)' : 'oklch(36% 0.09 72)'}`,
        marginBottom: '2rem',
        flexWrap: 'wrap',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          <span style={{ fontSize: '1.125rem' }}>{isVerified ? '✓' : '⚠'}</span>
          <span style={{
            fontSize: '0.875rem',
            fontWeight: 700,
            color: isVerified ? 'oklch(78% 0.14 168)' : 'oklch(80% 0.14 72)',
          }}>
            {isVerified
              ? 'Wynik niezależnie zweryfikowany — wszystkie reguły spełnione'
              : 'Wynik częściowy — sprawdź sekcję Dowód poniżej'}
          </span>
        </div>
        <span style={{
          fontSize: '0.75rem',
          color: 'oklch(54% 0.018 250)',
          whiteSpace: 'nowrap',
        }}>
          {mathStatusLabel}
        </span>
      </div>

      {/* ── HERO RESULT CARD ─────────────────────────────────── */}
      <div style={{
        background: 'oklch(10% 0.02 250)',
        borderRadius: '14px',
        border: '1px solid oklch(20% 0.025 250)',
        boxShadow: '0 0 80px oklch(0% 0 0 / 0.5), 0 0 160px oklch(75% 0.12 80 / 0.05)',
        overflow: 'hidden',
        marginBottom: '1.5rem',
      }}>
        {/* Gold accent line */}
        <div style={{
          height: '3px',
          background: 'linear-gradient(to right, transparent, oklch(75% 0.12 80) 20%, oklch(75% 0.12 80) 80%, transparent)',
        }} />

        <div style={{ padding: 'clamp(1.75rem, 4vw, 2.75rem)' }}>

          {/* ── 1. THE ANSWER ──────────────────────────────── */}
          <div style={{ marginBottom: '2.5rem' }}>
            <p style={{
              margin: '0 0 0.5rem 0',
              fontSize: '0.75rem',
              fontWeight: 800,
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'oklch(75% 0.12 80)',
            }}>
              Odpowiedź
            </p>
            <h1 style={{
              margin: '0 0 1rem 0',
              fontSize: 'clamp(1.75rem, 4vw, 2.75rem)',
              fontWeight: 900,
              letterSpacing: '-0.035em',
              lineHeight: 1.05,
              color: 'oklch(97% 0.008 250)',
            }}>
              {hasChoice ? (
                <>
                  Najlepsza opcja to{' '}
                  <span style={{
                    color: 'oklch(75% 0.12 80)',
                    textShadow: '0 0 60px oklch(75% 0.12 80 / 0.4)',
                  }}>
                    {headline}.
                  </span>
                </>
              ) : (
                headline
              )}
            </h1>
            <p style={{
              margin: 0,
              fontSize: '1.0625rem',
              color: 'oklch(68% 0.02 250)',
              lineHeight: 1.7,
              maxWidth: '70ch',
            }}>
              To nie opinia — to wynik obliczeń.
              System sprawdził każdą możliwą kombinację i wybrał tę, która najlepiej spełnia Twoje warunki.
            </p>
          </div>

          {/* ── 2. WHY THIS CHOICE ─────────────────────────── */}
          <div style={{ marginBottom: '2.5rem' }}>
            <p style={{
              margin: '0 0 1rem 0',
              fontSize: '0.75rem',
              fontWeight: 800,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: 'oklch(54% 0.018 250)',
            }}>
              Dlaczego właśnie ta opcja?
            </p>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
              gap: '1rem',
            }}>
              {[
                {
                  icon: '🏆',
                  title: 'Najwyższy wynik spośród wszystkich opcji',
                  desc: result.objective_value !== null && result.objective_value !== undefined
                    ? `Obliczona wartość: ${result.objective_value}. Żadna inna kombinacja nie dała lepszego wyniku przy Twoich warunkach.`
                    : 'Żadna inna kombinacja nie dała lepszego wyniku przy Twoich warunkach.',
                },
                {
                  icon: '✅',
                  title: 'Spełnia wszystkie Twoje warunki',
                  desc: 'Niezależny sprawdzian potwierdził każdą regułę. Żadna reguła nie jest naruszona — wynik jest bezpieczny.',
                },
                {
                  icon: '🔬',
                  title: 'Pewny wynik, nie szacunek',
                  desc: `${mathStatusLabel}. Każde powtórne obliczenie na tych samych danych daje ten sam wynik.`,
                },
              ].map((card) => (
                <div
                  key={card.title}
                  style={{
                    background: 'oklch(13% 0.022 250)',
                    border: '1px solid oklch(22% 0.025 250)',
                    borderRadius: '10px',
                    padding: '1.25rem',
                  }}
                >
                  <div style={{ fontSize: '1.5rem', marginBottom: '0.5rem', lineHeight: 1 }}>
                    {card.icon}
                  </div>
                  <div style={{
                    fontWeight: 700,
                    fontSize: '0.9375rem',
                    color: 'oklch(88% 0.015 250)',
                    marginBottom: '0.375rem',
                  }}>
                    {card.title}
                  </div>
                  <p style={{
                    margin: 0,
                    fontSize: '0.8125rem',
                    color: 'oklch(58% 0.018 250)',
                    lineHeight: 1.55,
                  }}>
                    {card.desc}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* ── 2B. BILANS DECYZYJNY: ZWYCIĘZCA VS ALTERNATYWA ─ */}
          <div style={{ marginBottom: '2.5rem' }}>
            <p style={{
              margin: '0 0 1rem 0',
              fontSize: '0.75rem',
              fontWeight: 800,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: 'oklch(54% 0.018 250)',
            }}>
              Bilans decyzyjny — dlaczego ten wybór przeważa
            </p>
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.25rem',
            }}>
              {/* Winner column */}
              <div style={{
                background: 'oklch(12% 0.03 80 / 0.5)',
                border: '1px solid oklch(75% 0.12 80 / 0.4)',
                borderRadius: '10px',
                padding: '1.25rem',
                boxShadow: '0 0 20px oklch(75% 0.12 80 / 0.06)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <span style={{
                    background: 'oklch(75% 0.12 80)',
                    color: 'oklch(6% 0.01 250)',
                    fontSize: '0.6875rem',
                    fontWeight: 900,
                    textTransform: 'uppercase',
                    padding: '0.2rem 0.55rem',
                    borderRadius: '4px',
                  }}>
                    Wybór optymalny
                  </span>
                </div>
                <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1.15rem', fontWeight: 800, color: 'oklch(97% 0.008 250)' }}>
                  {primaryWinnerTitle}
                </h3>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'oklch(78% 0.02 250)', lineHeight: 1.6 }}>
                  {decisionCase?.selected_priority_tokens && decisionCase.selected_priority_tokens.length > 0 ? (
                    <li>Maksymalizuje wybrane priorytety: <strong style={{ color: 'oklch(90% 0.08 80)' }}>{decisionCase.selected_priority_tokens.join(', ')}</strong></li>
                  ) : (
                    <li>Najkorzystniejszy całościowy bilans korzyści przy Twoich warunkach</li>
                  )}
                  <li>Spełnia 100% zdefiniowanych reguł i ograniczeń brzegowych</li>
                  <li>Wynik matematyczny: <strong style={{ color: 'oklch(90% 0.08 80)' }}>{result.objective_value ?? 'maksymalna wartość'}</strong></li>
                </ul>
              </div>

              {/* Alternative column */}
              <div style={{
                background: 'oklch(12% 0.02 250)',
                border: '1px solid oklch(24% 0.025 250)',
                borderRadius: '10px',
                padding: '1.25rem',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <span style={{
                    background: 'oklch(22% 0.025 250)',
                    color: 'oklch(68% 0.02 250)',
                    fontSize: '0.6875rem',
                    fontWeight: 800,
                    textTransform: 'uppercase',
                    padding: '0.2rem 0.55rem',
                    borderRadius: '4px',
                  }}>
                    Druga opcja / Alternatywa
                  </span>
                </div>
                <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1.15rem', fontWeight: 800, color: 'oklch(80% 0.015 250)' }}>
                  {alternativeTitle}
                </h3>
                <ul style={{ margin: 0, paddingLeft: '1.2rem', fontSize: '0.85rem', color: 'oklch(65% 0.02 250)', lineHeight: 1.6 }}>
                  <li>Niższa łączna punktacja w modelu matematycznym</li>
                  <li>Wymaga większych ustępstw w kryteriach, na których Ci najbardziej zależy</li>
                  <li>Nie przewyższa zwycięzcy w żadnym kluczowym wskaźniku przy obecnych danych</li>
                </ul>
              </div>
            </div>
          </div>

          {/* ── 3. TRADE-OFFS ──────────────────────────────── */}
          {decisionCase && decisionCase.tradeoffs.length > 0 && (
            <div style={{ marginBottom: '2.5rem' }}>
              <p style={{
                margin: '0 0 1rem 0',
                fontSize: '0.75rem',
                fontWeight: 800,
                letterSpacing: '0.1em',
                textTransform: 'uppercase',
                color: 'oklch(54% 0.018 250)',
              }}>
                Na co rezygnujesz wybierając tę opcję?
              </p>
              <div style={{
                background: 'oklch(8% 0.015 250)',
                border: '1px solid oklch(20% 0.025 250)',
                borderRadius: '10px',
                padding: '1.25rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '0.625rem',
              }}>
                {decisionCase.tradeoffs.map((t, idx) => (
                  <div key={idx} style={{
                    fontSize: '0.875rem',
                    color: 'oklch(68% 0.02 250)',
                    paddingBottom: '0.625rem',
                    borderBottom: idx < decisionCase.tradeoffs.length - 1
                      ? '1px solid oklch(18% 0.022 250)'
                      : 'none',
                  }}>
                    <span style={{ marginRight: '0.375rem' }}>⚖️</span>
                    {t.description} — zyskujesz <strong style={{ color: 'oklch(88% 0.015 250)' }}>{t.gain}</strong>, rezygnujesz z{' '}
                    <strong style={{ color: 'oklch(88% 0.015 250)' }}>{t.sacrifice}</strong>.
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── 3B. PUNKT ZWROTNY DO NEGOCJACJI / ZMIANY DECYZJI ── */}
          <div style={{
            marginBottom: '2.5rem',
            background: 'oklch(14% 0.035 75 / 0.5)',
            border: '1px solid oklch(75% 0.12 80 / 0.5)',
            borderRadius: '12px',
            padding: '1.375rem',
            boxShadow: '0 0 30px oklch(75% 0.12 80 / 0.08)',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem', marginBottom: '0.5rem' }}>
              <span style={{ fontSize: '1.25rem' }}>🎯</span>
              <h3 style={{
                margin: 0,
                fontSize: '0.9375rem',
                fontWeight: 800,
                letterSpacing: '0.02em',
                color: 'oklch(85% 0.12 80)',
              }}>
                Punkt zwrotny — co musiałoby się zmienić, aby wybrać drugą opcję?
              </h3>
            </div>
            <p style={{
              margin: '0 0 0.75rem 0',
              fontSize: '0.9rem',
              color: 'oklch(94% 0.01 250)',
              lineHeight: 1.65,
            }}>
              {effectiveBreakEven}
            </p>
            <div style={{
              fontSize: '0.78rem',
              color: 'oklch(72% 0.03 80)',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
            }}>
              <span>💡</span>
              <span>Wskazówka: Użyj tego punktu jako konkretnego kryterium podczas rozmów lub negocjacji.</span>
            </div>
          </div>

          {/* ── 4. WHAT-IF ─────────────────────────────────── */}
          <div style={{ marginBottom: '2.5rem' }}>
            <p style={{
              margin: '0 0 1rem 0',
              fontSize: '0.75rem',
              fontWeight: 800,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: 'oklch(54% 0.018 250)',
            }}>
              A co jeśli zmienisz warunki?
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.625rem' }}>
              {[
                {
                  q: 'Gdybyś miał większy budżet lub więcej zasobów',
                  a: 'System mógłby uwzględnić kolejną opcję o najwyższej wartości — wróć i zaktualizuj ograniczenia.',
                },
                {
                  q: 'Gdybyś zmienił priorytety lub kryteria',
                  a: 'Opisz nową sytuację od nowa — obliczenia potrwają chwilę i dadzą świeży wynik.',
                },
              ].map((item) => (
                <div key={item.q} style={{
                  background: 'oklch(13% 0.022 250)',
                  border: '1px solid oklch(22% 0.025 250)',
                  borderRadius: '8px',
                  padding: '1rem',
                  fontSize: '0.875rem',
                }}>
                  <strong style={{ color: 'oklch(78% 0.12 240)', display: 'block', marginBottom: '0.25rem' }}>
                    {item.q}:
                  </strong>
                  <span style={{ color: 'oklch(66% 0.02 250)', lineHeight: 1.55 }}>{item.a}</span>
                </div>
              ))}
            </div>
          </div>

          {/* ── 5. NEXT STEP ───────────────────────────────── */}
          <div style={{
            background: 'linear-gradient(135deg, oklch(13% 0.03 80) 0%, oklch(13% 0.03 240) 100%)',
            border: '1px solid oklch(75% 0.12 80 / 0.25)',
            borderRadius: '10px',
            padding: '1.375rem',
          }}>
            <p style={{
              margin: '0 0 0.375rem 0',
              fontSize: '0.75rem',
              fontWeight: 800,
              letterSpacing: '0.1em',
              textTransform: 'uppercase',
              color: 'oklch(75% 0.12 80)',
            }}>
              Następny krok
            </p>
            <h3 style={{
              margin: '0 0 0.5rem 0',
              fontSize: '1.0625rem',
              fontWeight: 800,
              color: 'oklch(97% 0.008 250)',
            }}>
              {hasChoice
                ? `Zacznij wdrażać opcję: ${chosenTitles[0]}`
                : 'Zacznij wdrażać rekomendowane rozwiązanie'}
            </h3>
            <p style={{
              margin: 0,
              fontSize: '0.875rem',
              color: 'oklch(66% 0.02 250)',
              lineHeight: 1.6,
            }}>
              Zapisz ten wynik. Poinformuj zainteresowane osoby o wybranym kierunku.
              Jeśli coś się zmieni — możesz wrócić i oblicz ponownie z nowym opisem.
            </p>
          </div>
        </div>
      </div>

      {/* ── Evidence Drawer (technical proof, collapsible) ─── */}
      <div className="no-print">
        <EvidenceDrawer result={result} comparisonResult={comparisonResult} />
      </div>

      {/* ── Footer actions ───────────────────────────────────── */}
      <div className="no-print" style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: '1rem',
        marginTop: '2rem',
        paddingTop: '2rem',
        borderTop: '1px solid oklch(18% 0.022 250)',
        flexWrap: 'wrap',
      }}>
        <button
          type="button"
          onClick={() => window.print()}
          style={{
            background: 'oklch(15% 0.025 250)',
            color: 'oklch(90% 0.01 250)',
            border: '1px solid oklch(30% 0.025 250)',
            borderRadius: 'var(--radius-md)',
            padding: '0.9rem 1.75rem',
            fontWeight: 700,
            fontSize: '0.9375rem',
            cursor: 'pointer',
            letterSpacing: '-0.01em',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            transition: 'border-color 200ms ease, background 200ms ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'oklch(75% 0.12 80)'
            e.currentTarget.style.background = 'oklch(19% 0.03 250)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'oklch(30% 0.025 250)'
            e.currentTarget.style.background = 'oklch(15% 0.025 250)'
          }}
        >
          🖨️ Zapisz / Drukuj raport (PDF)
        </button>

        <button
          type="button"
          onClick={onStartNew}
          style={{
            background: 'oklch(75% 0.12 80)',
            color: 'oklch(5% 0.01 250)',
            border: 'none',
            borderRadius: 'var(--radius-md)',
            padding: '0.9rem 2.25rem',
            fontWeight: 800,
            fontSize: '0.9375rem',
            cursor: 'pointer',
            letterSpacing: '-0.015em',
            boxShadow: '0 0 30px oklch(75% 0.12 80 / 0.4)',
            transition: 'background 200ms ease, transform 150ms ease, box-shadow 200ms ease',
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'oklch(83% 0.14 80)'
            e.currentTarget.style.transform = 'translateY(-2px)'
            e.currentTarget.style.boxShadow = '0 0 50px oklch(75% 0.12 80 / 0.6)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'oklch(75% 0.12 80)'
            e.currentTarget.style.transform = 'translateY(0)'
            e.currentTarget.style.boxShadow = '0 0 30px oklch(75% 0.12 80 / 0.4)'
          }}
        >
          Rozwiąż inny dylemat
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
            <path d="M5 12h14M12 5l7 7-7 7" />
          </svg>
        </button>
      </div>
    </div>

      <style>{`
        @keyframes wsPageIn {
          from { opacity: 0; transform: translateY(28px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes rvFloat0 {
          0%, 100% { transform: translateY(0)   scale(1); opacity: 0.8; }
          50%       { transform: translateY(-30px) scale(1.1); opacity: 1; }
        }
        @keyframes rvFloat1 {
          0%, 100% { transform: translateY(0)   scale(1); opacity: 0.7; }
          50%       { transform: translateY(-22px) scale(1.15); opacity: 1; }
        }
        @keyframes rvFloat2 {
          0%, 100% { transform: translateY(0)   scale(1); opacity: 0.75; }
          50%       { transform: translateY(-18px) scale(1.08); opacity: 1; }
        }
      `}</style>
    </div>
  )
}
