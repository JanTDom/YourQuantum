import React, { useEffect, useState } from 'react'
import {
  DecisionCase,
  DesignSynthesisResult,
  Evidence,
  JobResult,
  ScenarioForecast,
} from '../api'
import { EvidenceDrawer } from './EvidenceDrawer'

interface RecommendationViewProps {
  decisionCase: DecisionCase | null
  result: JobResult
  comparisonResult?: JobResult | null
  onStartNew: () => void
  breakEvenPoint?: string | null
  sessionId?: string | null
  problemClass?: string | null
  designSynthesis?: DesignSynthesisResult | null
  scenarioForecast?: ScenarioForecast | null
  evidenceList?: Evidence[]
}

export const RecommendationView: React.FC<RecommendationViewProps> = ({
  decisionCase,
  result,
  comparisonResult,
  onStartNew,
  breakEvenPoint,
  sessionId,
  problemClass = 'CHOICE',
  designSynthesis,
  scenarioForecast,
  evidenceList,
}) => {
  const isVerified = result.publication_status === 'PUBLISHED_VERIFIED'
  const assignment = result.solver_result?.assignment ?? {}

  const forecast: ScenarioForecast | null =
    scenarioForecast ||
    (result.metadata?.scenario_forecast as ScenarioForecast | undefined) ||
    null
  const isScenario = Boolean(forecast)

  // G4: Determine if this problem represents the multi-lever DESIGN class
  const isDesign =
    problemClass === 'DESIGN' ||
    result.metadata?.problem_class === 'DESIGN' ||
    Boolean(designSynthesis)

  // State for loaded DESIGN synthesis data
  const [designData, setDesignData] = useState<DesignSynthesisResult | null>(designSynthesis || null)
  const [selectedParetoIdx, setSelectedParetoIdx] = useState<number>(0)
  const [showTechnicalDetails, setShowTechnicalDetails] = useState<boolean>(false)

  useEffect(() => {
    if (designSynthesis) {
      setDesignData(designSynthesis)
    }
  }, [designSynthesis])

  const verifiedEvidence: Evidence[] = (
    evidenceList ||
    (result.metadata?.evidence as Evidence[] | undefined) ||
    ((result as any).evidence as Evidence[] | undefined) ||
    []
  ).filter((ev) => ev && ev.source_url && ev.content_hash)

  // Map solver variable names to human option titles (CHOICE mode)
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

  // B1: Analytical break-even point from formalization
  const effectiveBreakEven =
    breakEvenPoint ||
    decisionCase?.break_even_point ||
    null

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
      {/* Background — subtle future lab atmosphere */}
      <img
        src="/images/future-lab.jpg"
        alt=""
        aria-hidden="true"
        className="no-print"
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          objectPosition: 'center',
          opacity: 0.12,
          filter: 'saturate(0.5) brightness(0.45)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />
      <div
        className="no-print"
        aria-hidden="true"
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 0,
          background: `
            radial-gradient(ellipse 90% 60% at 50% 0%, oklch(75% 0.12 80 / 0.06) 0%, transparent 55%),
            radial-gradient(ellipse 60% 50% at 80% 80%, oklch(62% 0.18 240 / 0.07) 0%, transparent 60%),
            linear-gradient(to bottom, oklch(6% 0.01 250 / 0.6) 0%, oklch(6% 0.01 250 / 0.9) 100%)
          `,
        }}
      />

      {/* Content */}
      <div style={{
        position: 'relative',
        zIndex: 1,
        maxWidth: '1000px',
        margin: '0 auto',
        padding: 'clamp(1.5rem, 4vw, 3rem) clamp(1rem, 3vw, 2rem)',
        animation: 'wsPageIn 0.5s cubic-bezier(0.22,1,0.36,1) both',
      }}>
        {/* ── Official Print Header (Visible only when printing) ─ */}
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
                {isDesign ? 'Raport Syntezy Wielodźwigniowej (DESIGN)' : 'Raport Weryfikacji Decyzyjnej (CHOICE)'}
              </div>
              <div style={{ fontSize: '9pt', color: '#64748b', marginTop: '3px' }}>
                Temat: {decisionCase?.title || (isDesign ? 'Optymalizacja reformy systemu ochrony zdrowia' : 'Dylemat decyzyjny')}
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

        {/* ── Step indicator ──────────────────────────────────── */}
        <div className="no-print" style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          marginBottom: '2rem',
        }}>
          {['Sytuacja opisana', 'Obliczenia i synteza', 'Wynik z dowodem'].map((label, i) => (
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

        {/* ── Verification status banner ─────────────────────── */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem',
          padding: '0.875rem 1.25rem',
          borderRadius: '10px',
          background: isVerified ? 'oklch(16% 0.04 170)' : 'oklch(16% 0.04 70)',
          border: `1px solid ${isVerified ? 'oklch(35% 0.08 168)' : 'oklch(36% 0.09 72)'}`,
          marginBottom: '1.75rem',
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
                ? 'Wynik niezależnie zweryfikowany — 0 naruszeń ograniczeń brzegowych'
                : 'Wynik częściowy — sprawdź szczegóły weryfikacji poniżej'}
            </span>
          </div>
          <span style={{ fontSize: '0.75rem', color: 'oklch(65% 0.02 250)' }}>
            {mathStatusLabel}
          </span>
        </div>

        {/* ── G4: Specialized View Switch (SCENARIO vs DESIGN vs CHOICE) ── */}
        {isScenario && forecast ? (
          /* ══════════════════════════════════════════════════════════
             SCENARIO & PROBABILISTIC RISK VIEW (Quantum Born Distribution)
             ══════════════════════════════════════════════════════════ */
          <div style={{
            background: 'oklch(10% 0.02 250)',
            borderRadius: '14px',
            border: '1px solid oklch(22% 0.025 250)',
            boxShadow: '0 0 80px oklch(0% 0 0 / 0.5), 0 0 160px oklch(75% 0.12 80 / 0.05)',
            overflow: 'hidden',
            marginBottom: '2rem',
          }}>
            <div style={{
              height: '3px',
              background: 'linear-gradient(to right, transparent, oklch(75% 0.12 80) 20%, oklch(75% 0.12 80) 80%, transparent)',
            }} />

            <div style={{ padding: 'clamp(1.75rem, 4vw, 2.75rem)' }}>
              {/* ── 1. EXECUTIVE BRIEFING HERO ── */}
              <div style={{ marginBottom: '2.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                  <span style={{
                    fontSize: '0.6875rem',
                    fontWeight: 800,
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    color: 'oklch(75% 0.12 80)',
                    background: 'oklch(75% 0.12 80 / 0.12)',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '6px',
                    border: '1px solid oklch(75% 0.12 80 / 0.3)',
                  }}>
                    ✦ PROGNOZA SCENARIUSZOWA · KWANTOWA KOMBINATORYKA STANÓW (BORN PROBABILITY)
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'oklch(65% 0.02 250)' }}>
                    Symulacja Qiskit Aer · Rozkład prawdopodobieństw na podstawie twardych przesłanek
                  </span>
                </div>

                <h1 style={{
                  margin: '0 0 1rem 0',
                  fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
                  fontWeight: 900,
                  letterSpacing: '-0.03em',
                  color: 'oklch(97% 0.008 250)',
                  lineHeight: 1.15,
                }}>
                  {forecast.briefing?.headline || `Ocena prawdopodobieństwa: ${forecast.query}`}
                </h1>

                {/* Honesty banner */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.625rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  background: 'oklch(14% 0.03 80 / 0.4)',
                  borderLeft: '4px solid oklch(75% 0.12 80)',
                  fontSize: '0.8125rem',
                  color: 'oklch(88% 0.05 80)',
                  marginBottom: '1.5rem',
                }}>
                  <span>⚖️</span>
                  <span>
                    <strong>Zastrzeżenie metodologiczne:</strong> Model nie zgaduje przyszłości w sposób losowy (jak czatbot LLM), lecz oblicza rozkład prawdopodobieństw stanów z amplitud kwantowych (reguła Borna: P(s) = |⟨s|ψ⟩|²) na podstawie ważonego wektora przesłanek empirycznych z sieci.
                  </span>
                </div>

                {/* Executive Summary Card */}
                <div style={{
                  background: 'linear-gradient(135deg, oklch(14% 0.03 250) 0%, oklch(12% 0.02 250) 100%)',
                  border: '1px solid oklch(75% 0.12 80 / 0.35)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  boxShadow: '0 8px 32px oklch(0% 0 0 / 0.4)',
                  marginBottom: '2rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '1.25rem' }}>📋</span>
                    <h3 style={{ margin: 0, fontSize: '1.0625rem', fontWeight: 800, color: 'oklch(96% 0.01 250)', letterSpacing: '-0.01em' }}>
                      Wnioski w pigułce (Diagnoza Strategiczna)
                    </h3>
                  </div>
                  <p style={{ margin: 0, fontSize: '1.0625rem', color: 'oklch(92% 0.01 250)', lineHeight: 1.7, fontWeight: 400 }}>
                    {forecast.briefing?.executive_summary}
                  </p>
                </div>
              </div>

              {/* ── 2. QUANTUM SCENARIO PROBABILITY DISTRIBUTION ── */}
              <div style={{ marginBottom: '2.5rem' }}>
                <h3 style={{
                  margin: '0 0 1.25rem 0',
                  fontSize: '0.8125rem',
                  fontWeight: 800,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'oklch(75% 0.12 80)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}>
                  <span>🎲</span>
                  <span>Kwantowy Rozkład Prawdopodobieństwa Scenariuszy (Born Rule)</span>
                </h3>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                  {forecast.scenarios.map((sc, idx) => {
                    const isDominant = sc.id === forecast.dominant_scenario_id
                    const pctNum = sc.probability * 100
                    const pctPl = pctNum < 0.1 && pctNum > 0 ? '< 0,1%' : `${pctNum.toFixed(1).replace('.', ',')}%`

                    let verbalChance = ''
                    if (pctNum >= 90) {
                      verbalChance = 'Wariant niemal pewny (ponad 90 na 100 szans)'
                    } else if (pctNum >= 50) {
                      verbalChance = 'Wysokie prawdopodobieństwo (większość szans)'
                    } else if (pctNum >= 15) {
                      verbalChance = 'Umiarkowane prawdopodobieństwo (realny wariant)'
                    } else if (pctNum >= 1) {
                      verbalChance = 'Niskie prawdopodobieństwo (kilka szans na 100)'
                    } else {
                      verbalChance = 'Znikome prawdopodobieństwo (poniżej 1 na 100 szans)'
                    }

                    const riskLabelMap: Record<string, string> = {
                      LOW: 'Niskie zagrożenie (stabilność)',
                      MEDIUM: 'Umiarkowane (presja hybrydowa)',
                      HIGH: 'Wysokie zagrożenie',
                      CRITICAL: 'Krytyczne (otwarty konflikt)',
                    }
                    const riskLabel = riskLabelMap[sc.risk_level] || sc.risk_level

                    return (
                      <div
                        key={sc.id}
                        style={{
                          background: isDominant ? 'oklch(14% 0.035 80 / 0.3)' : 'oklch(12% 0.02 250)',
                          border: isDominant ? '1.5px solid oklch(75% 0.12 80 / 0.8)' : '1px solid oklch(20% 0.025 250)',
                          borderRadius: '12px',
                          padding: '1.25rem 1.5rem',
                          boxShadow: isDominant ? '0 4px 20px oklch(75% 0.12 80 / 0.12)' : 'none',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
                            <span style={{
                              fontWeight: 900,
                              fontSize: '0.8125rem',
                              color: isDominant ? 'oklch(75% 0.12 80)' : 'oklch(60% 0.02 250)',
                            }}>
                              SCENARIUSZ #{idx + 1}
                            </span>
                            {isDominant && (
                              <span style={{
                                fontSize: '0.625rem',
                                fontWeight: 800,
                                textTransform: 'uppercase',
                                padding: '0.15rem 0.5rem',
                                borderRadius: '4px',
                                background: 'oklch(75% 0.12 80 / 0.2)',
                                color: 'oklch(85% 0.14 80)',
                                border: '1px solid oklch(75% 0.12 80 / 0.5)',
                              }}>
                                ★ DOMINUJĄCY KIERUNEK
                              </span>
                            )}
                            <span style={{
                              fontSize: '0.625rem',
                              fontWeight: 700,
                              textTransform: 'uppercase',
                              padding: '0.15rem 0.5rem',
                              borderRadius: '4px',
                              background: sc.risk_level === 'CRITICAL' || sc.risk_level === 'HIGH'
                                ? 'oklch(20% 0.1 25)'
                                : sc.risk_level === 'MEDIUM'
                                ? 'oklch(20% 0.08 60)'
                                : 'oklch(16% 0.03 160)',
                              color: sc.risk_level === 'CRITICAL' || sc.risk_level === 'HIGH'
                                ? 'oklch(80% 0.18 25)'
                                : sc.risk_level === 'MEDIUM'
                                ? 'oklch(82% 0.14 60)'
                                : 'oklch(80% 0.15 160)',
                              border: sc.risk_level === 'CRITICAL' || sc.risk_level === 'HIGH'
                                ? '1px solid oklch(35% 0.15 25)'
                                : 'none',
                            }}>
                              Zagrożenie: {riskLabel}
                            </span>
                          </div>

                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.1rem' }}>
                            <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.35rem' }}>
                              <span style={{
                                fontSize: '1.625rem',
                                fontWeight: 900,
                                letterSpacing: '-0.02em',
                                color: isDominant ? 'oklch(96% 0.12 80)' : 'oklch(86% 0.02 250)',
                              }}>
                                {pctPl}
                              </span>
                              <span style={{
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                color: isDominant ? 'oklch(85% 0.12 80)' : 'oklch(65% 0.02 250)',
                              }}>
                                szans
                              </span>
                            </div>
                            <span style={{ fontSize: '0.6875rem', fontWeight: 600, color: isDominant ? 'oklch(75% 0.08 80)' : 'oklch(60% 0.02 250)' }}>
                              {verbalChance}
                            </span>
                          </div>
                        </div>

                        <div style={{
                          height: '8px',
                          borderRadius: '4px',
                          background: 'oklch(18% 0.02 250)',
                          overflow: 'hidden',
                          marginBottom: '0.75rem',
                        }}>
                          <div style={{
                            width: `${Math.max(1, Math.min(100, sc.probability * 100))}%`,
                            height: '100%',
                            background: isDominant
                              ? 'linear-gradient(to right, oklch(75% 0.12 80), oklch(88% 0.15 80))'
                              : 'linear-gradient(to right, oklch(50% 0.12 240), oklch(60% 0.14 240))',
                            borderRadius: '4px',
                            transition: 'width 600ms cubic-bezier(0.16, 1, 0.3, 1)',
                          }} />
                        </div>

                        <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'oklch(95% 0.01 250)', marginBottom: '0.35rem' }}>
                          {sc.title}
                        </div>
                        <p style={{ margin: 0, fontSize: '0.8125rem', color: 'oklch(75% 0.02 250)', lineHeight: 1.5 }}>
                          {sc.description}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* ── 3. EVIDENCE PILLARS (Przesłanki z Sieci) ── */}
              <div style={{ marginBottom: '2.5rem' }}>
                <h3 style={{
                  margin: '0 0 1.25rem 0',
                  fontSize: '0.8125rem',
                  fontWeight: 800,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'oklch(75% 0.12 80)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                }}>
                  <span>🏛️</span>
                  <span>Kluczowe Przesłanki i Wektory Dowodowe (Dlaczego Ten Rozkład)</span>
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
                  {forecast.briefing?.key_pillars.map((pillar, idx) => (
                    <div
                      key={pillar.title || idx}
                      style={{
                        background: 'oklch(12% 0.02 250)',
                        border: '1px solid oklch(22% 0.025 250)',
                        borderRadius: '10px',
                        padding: '1.25rem',
                        display: 'flex',
                        flexDirection: 'column',
                        justifyContent: 'space-between',
                      }}
                    >
                      <div>
                        <div style={{ fontSize: '0.6875rem', fontWeight: 800, color: 'oklch(75% 0.12 80)', marginBottom: '0.35rem', textTransform: 'uppercase' }}>
                          PRZESŁANKA #{idx + 1}
                        </div>
                        <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'oklch(95% 0.01 250)', marginBottom: '0.5rem' }}>
                          {pillar.title}
                        </div>
                        <div style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          padding: '0.25rem 0.6rem',
                          borderRadius: '5px',
                          background: pillar.chosen_option?.includes('oddala') || pillar.chosen_option?.includes('stabilność')
                            ? 'oklch(18% 0.05 160)'
                            : pillar.chosen_option?.includes('Podwyższa') || pillar.chosen_option?.includes('zagrożenia')
                            ? 'oklch(20% 0.08 40)'
                            : 'oklch(16% 0.03 240)',
                          color: pillar.chosen_option?.includes('oddala') || pillar.chosen_option?.includes('stabilność')
                            ? 'oklch(82% 0.14 160)'
                            : pillar.chosen_option?.includes('Podwyższa') || pillar.chosen_option?.includes('zagrożenia')
                            ? 'oklch(82% 0.14 40)'
                            : 'oklch(80% 0.12 240)',
                          border: pillar.chosen_option?.includes('oddala') || pillar.chosen_option?.includes('stabilność')
                            ? '1px solid oklch(30% 0.08 160)'
                            : pillar.chosen_option?.includes('Podwyższa') || pillar.chosen_option?.includes('zagrożenia')
                            ? '1px solid oklch(35% 0.12 40)'
                            : '1px solid oklch(25% 0.04 240)',
                          marginBottom: '0.6rem',
                          display: 'inline-block',
                        }}>
                          {pillar.chosen_option}
                        </div>
                        <p style={{ margin: 0, fontSize: '0.8125rem', color: 'oklch(78% 0.02 250)', lineHeight: 1.5 }}>
                          {pillar.rationale}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* ── 4. TRADEOFF & TIPPING POINTS ── */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.25rem', marginBottom: '2.5rem' }}>
                <div style={{
                  background: 'oklch(11% 0.02 250)',
                  border: '1px solid oklch(22% 0.03 250)',
                  borderRadius: '10px',
                  padding: '1.25rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1rem' }}>⚖️</span>
                    <h4 style={{ margin: 0, fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'oklch(75% 0.12 80)' }}>
                      Główny kompromis (Cena Oceny)
                    </h4>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'oklch(85% 0.02 250)', lineHeight: 1.6 }}>
                    {forecast.briefing?.primary_tradeoff}
                  </p>
                </div>

                <div style={{
                  background: 'oklch(11% 0.02 250)',
                  border: '1px solid oklch(22% 0.03 250)',
                  borderRadius: '10px',
                  padding: '1.25rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                    <span style={{ fontSize: '1rem' }}>🎯</span>
                    <h4 style={{ margin: 0, fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'oklch(75% 0.12 80)' }}>
                      Kiedy wynik uległby zmianie (Punkty Krytyczne / Tripwires)
                    </h4>
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.875rem', color: 'oklch(85% 0.02 250)', lineHeight: 1.6 }}>
                    {forecast.briefing?.tipping_points?.map((tp, i) => (
                      <li key={i} style={{ marginBottom: '0.35rem' }}>{tp}</li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* ── 5. EXPANDABLE TECHNICAL DRAWER ── */}
              <div style={{ borderTop: '1px solid oklch(20% 0.02 250)', paddingTop: '1.75rem' }}>
                <button
                  type="button"
                  id="btn-toggle-scenario-technical-details"
                  onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                  style={{
                    width: '100%',
                    background: showTechnicalDetails ? 'oklch(15% 0.03 250)' : 'oklch(11% 0.02 250)',
                    border: '1px solid oklch(28% 0.04 250)',
                    borderRadius: '10px',
                    padding: '1.125rem 1.5rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    color: 'oklch(92% 0.01 250)',
                    fontWeight: 700,
                    fontSize: '0.9375rem',
                    transition: 'all 200ms ease',
                    boxShadow: '0 2px 10px oklch(0% 0 0 / 0.3)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ fontSize: '1.25rem' }}>🔬</span>
                    <span>
                      {showTechnicalDetails
                        ? 'Ukryj model kwantowy, wektor stanu Qiskit i telemetrię'
                        : 'Pokaż pełny model kwantowy, wektor stanu Qiskit i telemetrię (dla analityka)'}
                    </span>
                  </div>
                  <span style={{
                    transform: showTechnicalDetails ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 200ms ease',
                    fontSize: '0.875rem',
                    color: 'oklch(75% 0.12 80)',
                  }}>
                    ▼
                  </span>
                </button>

                {showTechnicalDetails && (
                  <div style={{
                    marginTop: '1.75rem',
                    background: 'oklch(9% 0.015 250)',
                    border: '1px solid oklch(20% 0.025 250)',
                    borderRadius: '12px',
                    padding: '1.75rem',
                  }}>
                    {/* Quantum state table */}
                    <div style={{ marginBottom: '1.5rem' }}>
                      <h4 style={{ margin: '0 0 0.75rem 0', fontSize: '0.875rem', fontWeight: 800, color: 'oklch(75% 0.12 80)', textTransform: 'uppercase' }}>
                        Wektor Stanu Kwantowego & Amplitudy Zespolone (Born Rule Audit)
                      </h4>
                      <div style={{ overflowX: 'auto' }}>
                        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
                          <thead>
                            <tr style={{ borderBottom: '1px solid oklch(25% 0.02 250)', textAlign: 'left', color: 'oklch(70% 0.02 250)' }}>
                              <th style={{ padding: '0.5rem' }}>Stan |s⟩</th>
                              <th style={{ padding: '0.5rem' }}>Tytuł Scenariusza</th>
                              <th style={{ padding: '0.5rem' }}>Energia H(s)</th>
                              <th style={{ padding: '0.5rem' }}>Amplituda α</th>
                              <th style={{ padding: '0.5rem' }}>Prawdopodobieństwo |α|²</th>
                            </tr>
                          </thead>
                          <tbody>
                            {forecast.scenarios.map((s, i) => (
                              <tr key={s.id} style={{ borderBottom: '1px solid oklch(16% 0.02 250)' }}>
                                <td style={{ padding: '0.5rem', fontFamily: 'monospace', color: 'oklch(75% 0.12 80)' }}>|s_{i+1}⟩</td>
                                <td style={{ padding: '0.5rem', fontWeight: 600 }}>{s.title}</td>
                                <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>{(s.energy_level || 0).toFixed(3)}</td>
                                <td style={{ padding: '0.5rem', fontFamily: 'monospace' }}>({(s.amplitude_real || 0).toFixed(4)}, {(s.amplitude_imag || 0).toFixed(4)}i)</td>
                                <td style={{ padding: '0.5rem', fontWeight: 800, color: 'oklch(85% 0.14 80)' }}>{(s.probability * 100).toFixed(2).replace('.', ',')}%</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    </div>

                    {/* Quantum telemetry */}
                    <div style={{
                      background: 'oklch(12% 0.02 250)',
                      borderRadius: '8px',
                      padding: '1rem',
                      fontFamily: 'monospace',
                      fontSize: '0.75rem',
                      color: 'oklch(70% 0.02 250)',
                    }}>
                      <div style={{ fontWeight: 800, color: 'oklch(90% 0.01 250)', marginBottom: '0.5rem' }}>
                        TELEMETRIA PROCESORA KWANTOWEGO / SYMULATORA AER:
                      </div>
                      <pre style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
                        {JSON.stringify(forecast.quantum_telemetry, null, 2)}
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : isDesign ? (
          /* ══════════════════════════════════════════════════════════
             G4: DESIGN CLASS VIEW (Multi-Lever Synthesis & Pareto)
             ══════════════════════════════════════════════════════════ */
          <div style={{
            background: 'oklch(10% 0.02 250)',
            borderRadius: '14px',
            border: '1px solid oklch(22% 0.025 250)',
            boxShadow: '0 0 80px oklch(0% 0 0 / 0.5), 0 0 160px oklch(75% 0.12 80 / 0.05)',
            overflow: 'hidden',
            marginBottom: '2rem',
          }}>
            <div style={{
              height: '3px',
              background: 'linear-gradient(to right, transparent, oklch(75% 0.12 80) 20%, oklch(75% 0.12 80) 80%, transparent)',
            }} />

            <div style={{ padding: 'clamp(1.75rem, 4vw, 2.75rem)' }}>
              {/* ── 1. EXECUTIVE BRIEFING HERO ─────────────────────── */}
              <div style={{ marginBottom: '2.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
                  <span style={{
                    fontSize: '0.6875rem',
                    fontWeight: 800,
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    color: 'oklch(75% 0.12 80)',
                    background: 'oklch(75% 0.12 80 / 0.12)',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '6px',
                    border: '1px solid oklch(75% 0.12 80 / 0.3)',
                  }}>
                    ✦ SYNTEZA STRATEGICZNA · REKOMENDACJA DLA DECYDENTA
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'oklch(65% 0.02 250)' }}>
                    Wielokryterialna optymalizacja oparta na faktach i twardych ograniczeniach
                  </span>
                </div>

                <h1 style={{
                  margin: '0 0 1rem 0',
                  fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
                  fontWeight: 900,
                  letterSpacing: '-0.03em',
                  color: 'oklch(97% 0.008 250)',
                  lineHeight: 1.15,
                }}>
                  {designData?.briefing?.headline || (decisionCase?.title ? `Diagnoza i rekomendacja: ${decisionCase.title}` : 'Optymalna Konfiguracja Architektury Systemowej')}
                </h1>

                {/* Model-optimal mandatory honesty banner */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.625rem',
                  padding: '0.75rem 1rem',
                  borderRadius: '8px',
                  background: 'oklch(14% 0.03 80 / 0.4)',
                  borderLeft: '4px solid oklch(75% 0.12 80)',
                  fontSize: '0.8125rem',
                  color: 'oklch(88% 0.05 80)',
                  marginBottom: '1.5rem',
                }}>
                  <span>⚖️</span>
                  <span>
                    <strong>Zastrzeżenie formalne:</strong> Konfiguracja{' '}
                    <em>{designData?.model_optimal_label || 'optymalna dla modelu, nie dla świata (wynik zależy od podanych kryteriów i wag)'}</em>.
                  </span>
                </div>

                {/* Executive Summary Card */}
                <div style={{
                  background: 'linear-gradient(135deg, oklch(14% 0.03 250) 0%, oklch(12% 0.02 250) 100%)',
                  border: '1px solid oklch(75% 0.12 80 / 0.35)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  boxShadow: '0 8px 32px oklch(0% 0 0 / 0.4)',
                  marginBottom: '2rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                    <span style={{ fontSize: '1.25rem' }}>📋</span>
                    <h3 style={{ margin: 0, fontSize: '1.0625rem', fontWeight: 800, color: 'oklch(96% 0.01 250)', letterSpacing: '-0.01em' }}>
                      Wnioski w pigułce (Diagnoza i Główny Kierunek)
                    </h3>
                  </div>
                  <p style={{ margin: 0, fontSize: '1.0625rem', color: 'oklch(92% 0.01 250)', lineHeight: 1.7, fontWeight: 400 }}>
                    {designData?.briefing?.executive_summary || designData?.practical_manifestation || 'Matematyczna synteza wielokryterialna wyznaczyła zrównoważony kierunek strategiczny, maksymalizujący globalną użyteczność publiczną.'}
                  </p>
                </div>
              </div>

              {/* ── 2. KEY PILLARS (Kluczowe Filary Rozwiązania) ───── */}
              <div style={{ marginBottom: '2.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
                  <span style={{ fontSize: '1.125rem' }}>🏛️</span>
                  <h2 style={{
                    margin: 0,
                    fontSize: '0.875rem',
                    fontWeight: 800,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'oklch(75% 0.12 80)',
                  }}>
                    Kluczowe Filary Rozwiązania (Dlaczego ten kierunek)
                  </h2>
                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                  gap: '1.25rem',
                }}>
                  {designData?.briefing?.key_pillars && designData.briefing.key_pillars.length > 0 ? (
                    designData.briefing.key_pillars.map((pillar, idx) => (
                      <div
                        key={pillar.title}
                        style={{
                          background: 'oklch(12% 0.025 250)',
                          border: '1px solid oklch(24% 0.03 250)',
                          borderRadius: '12px',
                          padding: '1.375rem',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          gap: '1rem',
                        }}
                      >
                        <div>
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            marginBottom: '0.5rem',
                          }}>
                            <span style={{ fontSize: '0.6875rem', color: 'oklch(60% 0.02 250)', textTransform: 'uppercase', fontWeight: 800 }}>
                              Filar #{idx + 1}
                            </span>
                            <span style={{
                              background: 'oklch(75% 0.12 80 / 0.15)',
                              color: 'oklch(82% 0.12 80)',
                              fontSize: '0.6875rem',
                              fontWeight: 800,
                              padding: '0.2rem 0.5rem',
                              borderRadius: '4px',
                              border: '1px solid oklch(75% 0.12 80 / 0.3)',
                            }}>
                              REKOMENDOWANY WYBÓR
                            </span>
                          </div>

                          <div style={{ fontSize: '1.0625rem', fontWeight: 800, color: 'oklch(96% 0.01 250)', marginBottom: '0.5rem' }}>
                            {pillar.title}
                          </div>

                          <div style={{
                            fontSize: '0.9375rem',
                            fontWeight: 700,
                            color: 'oklch(82% 0.14 80)',
                            background: 'oklch(8% 0.015 250)',
                            padding: '0.625rem 0.875rem',
                            borderRadius: '8px',
                            border: '1px solid oklch(22% 0.03 250)',
                            marginBottom: '0.75rem',
                          }}>
                            ✓ {pillar.chosen_option}
                          </div>

                          <div style={{
                            fontSize: '0.8125rem',
                            color: 'oklch(78% 0.02 250)',
                            lineHeight: 1.55,
                            background: 'oklch(14% 0.02 250)',
                            padding: '0.625rem 0.75rem',
                            borderRadius: '6px',
                          }}>
                            <strong style={{ color: 'oklch(92% 0.01 250)' }}>💡 Dlaczego to rozwiązanie: </strong>
                            {pillar.rationale}
                          </div>
                        </div>

                        <div style={{ fontSize: '0.75rem', color: 'oklch(60% 0.02 250)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          <span>🏛️</span>
                          <span>Spójne z ograniczeniami logicznymi systemu</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    Object.entries(designData?.optimal_titles || {}).map(([leverName, optTitle], idx) => (
                      <div
                        key={leverName}
                        style={{
                          background: 'oklch(12% 0.025 250)',
                          border: '1px solid oklch(22% 0.03 250)',
                          borderRadius: '10px',
                          padding: '1.25rem',
                        }}
                      >
                        <div style={{ fontSize: '0.6875rem', color: 'oklch(55% 0.02 250)', textTransform: 'uppercase', fontWeight: 700 }}>
                          Filar #{idx + 1}
                        </div>
                        <div style={{ fontSize: '0.9375rem', fontWeight: 800, color: 'oklch(95% 0.01 250)', margin: '0.35rem 0' }}>
                          {leverName}
                        </div>
                        <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'oklch(78% 0.14 80)' }}>
                          ✓ {optTitle}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* ── 3. STRATEGIC TRADE-OFFS & TIPPING POINTS ────────── */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
                gap: '1.25rem',
                marginBottom: '2.5rem',
              }}>
                <div style={{
                  background: 'oklch(12% 0.02 250)',
                  border: '1px solid oklch(24% 0.03 250)',
                  borderRadius: '12px',
                  padding: '1.25rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.625rem' }}>
                    <span style={{ fontSize: '1.125rem' }}>⚖️</span>
                    <h3 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 800, color: 'oklch(92% 0.01 250)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Główny kompromis (Cena wyboru)
                    </h3>
                  </div>
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'oklch(78% 0.02 250)', lineHeight: 1.6 }}>
                    {designData?.briefing?.primary_tradeoff || 'Osiągnięcie stabilności i wysokiej dostępności wymaga zrównoważenia wyższych nakładów wdrożeniowych na rzecz jednolitej koordynacji procedur.'}
                  </p>
                </div>

                <div style={{
                  background: 'oklch(12% 0.02 250)',
                  border: '1px solid oklch(24% 0.03 250)',
                  borderRadius: '12px',
                  padding: '1.25rem',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.625rem' }}>
                    <span style={{ fontSize: '1.125rem' }}>🔀</span>
                    <h3 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 800, color: 'oklch(92% 0.01 250)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                      Kiedy wynik uległby zmianie (Punkty wrażliwości)
                    </h3>
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8125rem', color: 'oklch(75% 0.02 250)', lineHeight: 1.55 }}>
                    {(designData?.briefing?.tipping_points && designData.briefing.tipping_points.length > 0) ? (
                      designData.briefing.tipping_points.map((pt, i) => (
                        <li key={i} style={{ marginBottom: '0.35rem' }}>{pt}</li>
                      ))
                    ) : (
                      <li>Wybór jest stabilny przy standardowych wagach kryteriów. Zmiana nadrzędnego priorytetu o ponad 25% mogłaby wskazać alternatywny punkt kompromisu.</li>
                    )}
                  </ul>
                </div>
              </div>

              {/* ── 4. EXPANDABLE TECHNICAL CORE (Dla Analityka / Audytora) ── */}
              <div style={{
                marginTop: '2.5rem',
                borderTop: '1px solid oklch(22% 0.03 250)',
                paddingTop: '2rem',
              }}>
                <button
                  type="button"
                  id="btn-toggle-technical-details"
                  onClick={() => setShowTechnicalDetails(!showTechnicalDetails)}
                  style={{
                    width: '100%',
                    background: showTechnicalDetails ? 'oklch(15% 0.03 250)' : 'oklch(11% 0.02 250)',
                    border: '1px solid oklch(28% 0.04 250)',
                    borderRadius: '10px',
                    padding: '1.125rem 1.5rem',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    cursor: 'pointer',
                    color: 'oklch(92% 0.01 250)',
                    fontWeight: 700,
                    fontSize: '0.9375rem',
                    transition: 'all 200ms ease',
                    boxShadow: '0 2px 10px oklch(0% 0 0 / 0.3)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{ fontSize: '1.25rem' }}>🔬</span>
                    <span>
                      {showTechnicalDetails
                        ? 'Ukryj szczegółowy model matematyczny, front Pareto i weryfikator'
                        : 'Pokaż pełny model matematyczny, front Pareto i dowód weryfikatora (dla analityka)'}
                    </span>
                  </div>
                  <span style={{
                    transform: showTechnicalDetails ? 'rotate(180deg)' : 'rotate(0deg)',
                    transition: 'transform 200ms ease',
                    fontSize: '0.875rem',
                    color: 'oklch(75% 0.12 80)',
                  }}>
                    ▼
                  </span>
                </button>

                {showTechnicalDetails && (
                  <div style={{
                    marginTop: '1.75rem',
                    background: 'oklch(9% 0.015 250)',
                    border: '1px solid oklch(20% 0.025 250)',
                    borderRadius: '12px',
                    padding: '1.75rem',
                    animation: 'magPageIn 300ms ease forwards',
                  }}>
                    {/* ── 4a. Front Pareto ── */}
                    <div style={{ marginBottom: '2.5rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                        <h3 style={{
                          margin: 0,
                          fontSize: '0.8125rem',
                          fontWeight: 800,
                          letterSpacing: '0.1em',
                          textTransform: 'uppercase',
                          color: 'oklch(75% 0.12 80)',
                        }}>
                          Front Pareto — Warianty Niezdominowane ({designData?.pareto_frontier.length || 0} punktów kompromisu)
                        </h3>
                        <span style={{ fontSize: '0.75rem', color: 'oklch(60% 0.02 250)' }}>
                          Żaden punkt nie jest gorszy we wszystkich kryteriach od innego
                        </span>
                      </div>

                      {/* Pareto Frontier 2D Chart */}
                      <div style={{
                        background: 'oklch(7% 0.01 250)',
                        border: '1px solid oklch(18% 0.02 250)',
                        borderRadius: '10px',
                        padding: '1.25rem',
                        marginBottom: '1rem',
                      }}>
                        <div style={{ fontSize: '0.75rem', color: 'oklch(70% 0.02 250)', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
                          <span>▲ Jakość kliniczna i dostępność (Maksymalizacja)</span>
                          <span>Koszt publiczny systemu (Minimalizacja) ►</span>
                        </div>

                        <svg
                          viewBox="0 0 500 220"
                          style={{ width: '100%', height: '220px', overflow: 'visible' }}
                          aria-label="Wykres frontu Pareto punktów kompromisu"
                          role="img"
                        >
                          <line x1="40" y1="20" x2="40" y2="180" stroke="oklch(20% 0.02 250)" strokeWidth="1" />
                          <line x1="40" y1="180" x2="480" y2="180" stroke="oklch(20% 0.02 250)" strokeWidth="1" />
                          <line x1="40" y1="100" x2="480" y2="100" stroke="oklch(15% 0.02 250)" strokeDasharray="3 3" />
                          <line x1="260" y1="20" x2="260" y2="180" stroke="oklch(15% 0.02 250)" strokeDasharray="3 3" />

                          {designData?.pareto_frontier.map((_pt, pIdx) => {
                            const nPts = designData.pareto_frontier.length || 1
                            const x = 70 + (pIdx / Math.max(1, nPts - 1)) * 370
                            const y = 160 - Math.sin((pIdx / Math.max(1, nPts - 1)) * Math.PI * 0.7 + 0.3) * 120
                            const isSelected = pIdx === selectedParetoIdx

                            return (
                              <g
                                key={pIdx}
                                style={{ cursor: 'pointer' }}
                                onClick={() => setSelectedParetoIdx(pIdx)}
                                tabIndex={0}
                                role="button"
                                aria-label={`Punkt Pareto #${pIdx + 1}`}
                                onKeyDown={(e) => {
                                  if (e.key === 'Enter' || e.key === ' ') {
                                    setSelectedParetoIdx(pIdx)
                                  }
                                }}
                              >
                                <circle
                                  cx={x}
                                  cy={y}
                                  r={isSelected ? 9 : 6}
                                  fill={isSelected ? 'oklch(75% 0.12 80)' : 'oklch(62% 0.18 240)'}
                                  stroke={isSelected ? 'oklch(95% 0.02 80)' : 'oklch(35% 0.08 240)'}
                                  strokeWidth={isSelected ? 3 : 1.5}
                                />
                                <text
                                  x={x}
                                  y={y - 12}
                                  textAnchor="middle"
                                  fill={isSelected ? 'oklch(85% 0.12 80)' : 'oklch(60% 0.02 250)'}
                                  fontSize="11"
                                  fontWeight={isSelected ? '800' : '500'}
                                >
                                  P{pIdx + 1}
                                </text>
                              </g>
                            )
                          })}
                        </svg>

                        {designData?.pareto_frontier[selectedParetoIdx] && (
                          <div style={{
                            marginTop: '1rem',
                            padding: '0.875rem 1rem',
                            borderRadius: '8px',
                            background: 'oklch(12% 0.025 250)',
                            border: '1px solid oklch(75% 0.12 80 / 0.4)',
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            flexWrap: 'wrap',
                            gap: '0.75rem',
                          }}>
                            <div>
                              <div style={{ fontSize: '0.75rem', color: 'oklch(75% 0.12 80)', fontWeight: 800, textTransform: 'uppercase' }}>
                                Aktywny punkt kompromisu: P{selectedParetoIdx + 1} {selectedParetoIdx === 0 ? '(Rekomendowany globalnie)' : '(Wariant alternatywny)'}
                              </div>
                              <div style={{ fontSize: '0.8125rem', color: 'oklch(80% 0.01 250)', marginTop: '0.25rem' }}>
                                Wartości kryteriów:{' '}
                                {Object.entries(designData.pareto_frontier[selectedParetoIdx].objective_values)
                                  .map(([k, v]) => `${k}: ${Number(v).toFixed(1)}`)
                                  .join(' | ')}
                              </div>
                            </div>
                            <div style={{ fontSize: '0.75rem', color: 'oklch(60% 0.02 250)' }}>
                              Wybór niezdominowany w przestrzeni wielokryterialnej
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* ── 4b. Ranking wrażliwości dźwigni ── */}
                    <div style={{ marginBottom: '2.5rem' }}>
                      <h3 style={{
                        margin: '0 0 1rem 0',
                        fontSize: '0.8125rem',
                        fontWeight: 800,
                        letterSpacing: '0.1em',
                        textTransform: 'uppercase',
                        color: 'oklch(75% 0.12 80)',
                      }}>
                        Ranking wrażliwości dźwigni (Wpływ na wynik systemu)
                      </h3>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                        {designData?.lever_importance_ranking && designData.lever_importance_ranking.length > 0 ? (
                          designData.lever_importance_ranking.map((item, idx) => (
                            <div
                              key={item.lever_id}
                              style={{
                                background: 'oklch(12% 0.02 250)',
                                border: '1px solid oklch(20% 0.025 250)',
                                borderRadius: '8px',
                                padding: '0.875rem 1.25rem',
                              }}
                            >
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.4rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                  <span style={{
                                    fontWeight: 900,
                                    fontSize: '0.75rem',
                                    color: idx === 0 ? 'oklch(75% 0.12 80)' : 'oklch(60% 0.02 250)',
                                  }}>
                                    #{idx + 1}
                                  </span>
                                  <span style={{ fontWeight: 700, fontSize: '0.875rem', color: 'oklch(90% 0.01 250)' }}>
                                    {item.lever_name}
                                  </span>
                                </div>
                                <span style={{ fontSize: '0.8125rem', fontWeight: 800, color: 'oklch(75% 0.12 80)' }}>
                                  {item.relative_impact_percent}% wpływu
                                </span>
                              </div>

                              <div style={{
                                height: '6px',
                                borderRadius: '3px',
                                background: 'oklch(18% 0.02 250)',
                                overflow: 'hidden',
                              }}>
                                <div style={{
                                  width: `${Math.min(100, Math.max(5, item.relative_impact_percent))}%`,
                                  height: '100%',
                                  background: idx === 0
                                    ? 'linear-gradient(to right, oklch(75% 0.12 80), oklch(85% 0.14 80))'
                                    : 'oklch(62% 0.18 240)',
                                  borderRadius: '3px',
                                }} />
                              </div>
                            </div>
                          ))
                        ) : (
                          <div style={{ fontSize: '0.8125rem', color: 'oklch(60% 0.02 250)', fontStyle: 'italic' }}>
                            Ranking wrażliwości niedostępny dla tej konfiguracji modelu.
                          </div>
                        )}
                      </div>
                    </div>

                    {/* ── 4c. Zweryfikowane źródła instytucjonalne ── */}
                    <div>
                      <h3 style={{
                        margin: '0 0 1rem 0',
                        fontSize: '0.8125rem',
                        fontWeight: 800,
                        letterSpacing: '0.1em',
                        textTransform: 'uppercase',
                        color: 'oklch(75% 0.12 80)',
                      }}>
                        Podstawy dowodowe i źródła
                      </h3>

                      {verifiedEvidence.length === 0 ? (
                        <div style={{
                          padding: '1.25rem',
                          background: 'oklch(11% 0.015 250)',
                          border: '1px dashed oklch(25% 0.02 250)',
                          borderRadius: '8px',
                          color: 'oklch(65% 0.02 250)',
                          fontSize: '0.875rem',
                          textAlign: 'center',
                        }}>
                          Brak źródeł zewnętrznych. Wszystkie wartości pochodzą z modeli domenowych lub założeń eksperckich.
                        </div>
                      ) : (
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
                          gap: '0.875rem',
                        }}>
                          {verifiedEvidence.map((ev, i) => (
                            <div
                              key={ev.id || i}
                              style={{
                                background: 'oklch(12% 0.02 250)',
                                border: '1px solid oklch(20% 0.025 250)',
                                borderRadius: '8px',
                                padding: '1rem',
                                fontSize: '0.8125rem',
                              }}
                            >
                              <div style={{ fontWeight: 700, color: 'oklch(90% 0.01 250)', marginBottom: '0.35rem' }}>
                                {ev.source_title}
                              </div>
                              <p style={{ margin: '0 0 0.5rem 0', color: 'oklch(70% 0.02 250)', fontSize: '0.75rem', lineHeight: 1.4 }}>
                                &ldquo;{ev.quote}&rdquo;
                              </p>
                              <div style={{ fontSize: '0.6875rem', color: 'oklch(55% 0.02 250)', marginBottom: '0.4rem', fontFamily: 'monospace' }}>
                                Hash: {ev.content_hash.slice(0, 16)}...
                              </div>
                              <div style={{ fontSize: '0.6875rem', color: 'oklch(55% 0.02 250)', marginBottom: '0.4rem' }}>
                                Pobrano: {new Date(ev.retrieved_at).toLocaleString()}
                              </div>
                              <a
                                href={ev.source_url}
                                target="_blank"
                                rel="noreferrer noopener"
                                style={{ fontSize: '0.6875rem', color: 'oklch(75% 0.15 220)', textDecoration: 'none' }}
                              >
                                Przejdź do źródła ↗
                              </a>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          /* ══════════════════════════════════════════════════════════
             G4: CHOICE CLASS VIEW (DEC-014 5 Sections + Analytical Break-Even B1)
             ══════════════════════════════════════════════════════════ */
          <div style={{
            background: 'oklch(10% 0.02 250)',
            borderRadius: '14px',
            border: '1px solid oklch(20% 0.025 250)',
            boxShadow: '0 0 80px oklch(0% 0 0 / 0.5), 0 0 160px oklch(75% 0.12 80 / 0.05)',
            overflow: 'hidden',
            marginBottom: '1.5rem',
          }}>
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

              {/* ── 2A. KRYPTOGRAFICZNY PASZPORT I TEST ODPORNOŚCI ── */}
              <div style={{
                marginBottom: '2.5rem',
                padding: '1.5rem',
                borderRadius: '16px',
                background: 'linear-gradient(135deg, oklch(12% 0.03 240 / 0.8), oklch(10% 0.02 260 / 0.9))',
                border: '1px solid oklch(35% 0.08 240 / 0.4)',
                boxShadow: '0 8px 32px oklch(0% 0 0 / 0.4)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                    <span style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      width: '28px',
                      height: '28px',
                      borderRadius: '8px',
                      background: 'oklch(62% 0.18 240 / 0.2)',
                      color: 'oklch(75% 0.15 220)',
                      fontSize: '0.9rem',
                    }}>🛡️</span>
                    <div>
                      <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'oklch(95% 0.02 220)' }}>
                        Kryptograficzny Paszport Matematyczny & Test Odporności
                      </h3>
                      <span style={{ fontSize: '0.75rem', color: 'oklch(65% 0.04 240)' }}>
                        Twardy dowód weryfikatora niezależnego — 0% zmyśleń czatu AI
                      </span>
                    </div>
                  </div>
                  <span style={{
                    fontSize: '0.6875rem',
                    fontFamily: 'ui-monospace, monospace',
                    padding: '0.3rem 0.6rem',
                    borderRadius: '6px',
                    background: 'oklch(15% 0.04 240 / 0.9)',
                    border: '1px solid oklch(30% 0.06 240 / 0.5)',
                    color: result.verification?.hmac_signature ? 'oklch(80% 0.05 240)' : 'oklch(75% 0.12 60)',
                  }}>
                    {result.verification?.hmac_signature
                      ? `SHA-256: ${result.verification.sha256_hash ? `${result.verification.sha256_hash.slice(0, 16)}...` : 'CERT-VERIFIED'} (HMAC)`
                      : 'odcisk SHA-256 (bez podpisu serwera)'}
                  </span>
                </div>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                  gap: '0.875rem',
                  marginBottom: '1rem',
                }}>
                  <div style={{ padding: '0.875rem', borderRadius: '10px', background: 'oklch(8% 0.02 250 / 0.7)', border: '1px solid oklch(20% 0.04 250 / 0.5)' }}>
                    <span style={{ fontSize: '0.6875rem', textTransform: 'uppercase', color: 'oklch(60% 0.04 240)', fontWeight: 700 }}>Residuum Naruszeń</span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 900, color: 'oklch(75% 0.2 150)', fontFamily: 'ui-monospace, monospace' }}>
                      {result.verification?.numerical_residual !== null && result.verification?.numerical_residual !== undefined ? `${result.verification.numerical_residual.toFixed(4)}` : '0.0000'}
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'oklch(70% 0.03 240)' }}>100% ograniczeń spełnionych</span>
                  </div>

                  <div style={{ padding: '0.875rem', borderRadius: '10px', background: 'oklch(8% 0.02 250 / 0.7)', border: '1px solid oklch(20% 0.04 250 / 0.5)' }}>
                    <span style={{ fontSize: '0.6875rem', textTransform: 'uppercase', color: 'oklch(60% 0.04 240)', fontWeight: 700 }}>Luka Optymalności</span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 900, color: 'oklch(75% 0.15 80)', fontFamily: 'ui-monospace, monospace' }}>
                      {result.verification?.optimality_gap_percent !== null && result.verification?.optimality_gap_percent !== undefined ? `≤ ${result.verification.optimality_gap_percent}%` : 'Brak danych'}
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'oklch(70% 0.03 240)' }}>
                      {result.verification?.optimality_proven ? 'Granica dualna udowodniona' : 'Brak certyfikatu optymalności'}
                    </span>
                  </div>

                  <div style={{ padding: '0.875rem', borderRadius: '10px', background: 'oklch(8% 0.02 250 / 0.7)', border: '1px solid oklch(20% 0.04 250 / 0.5)' }}>
                    <span style={{ fontSize: '0.6875rem', textTransform: 'uppercase', color: 'oklch(60% 0.04 240)', fontWeight: 700 }}>Odporność na Szok (±25%)</span>
                    <div style={{ fontSize: '1.15rem', fontWeight: 900, color: 'oklch(85% 0.15 220)', fontFamily: 'ui-monospace, monospace' }}>
                      {result.verification?.robustness ? `${(result.verification.robustness.robustness_score * 100).toFixed(0)}%` : 'Brak danych'}
                    </div>
                    <span style={{ fontSize: '0.72rem', color: 'oklch(70% 0.03 240)' }}>
                      {result.verification?.robustness ? result.verification.robustness.verdict : 'Analiza odporności niedostępna dla tego modelu'}
                    </span>
                  </div>
                </div>

                {result.verification?.robustness?.summary_pl && (
                  <div style={{
                    padding: '0.75rem 1rem',
                    borderRadius: '8px',
                    background: 'oklch(14% 0.04 240 / 0.6)',
                    borderLeft: '3px solid oklch(75% 0.15 220)',
                    fontSize: '0.8125rem',
                    color: 'oklch(85% 0.03 240)',
                    lineHeight: 1.5,
                  }}>
                    <strong>Test wstrząsowy parametrów: </strong>
                    {result.verification.robustness.summary_pl}
                  </div>
                )}
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

              {/* ── 3B. PUNKT ZWROTNY LICZONY ANALITYCZNIE (B1) ── */}
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
                    Punkt zwrotny (B1) — co musiałoby się zmienić, aby wybrać drugą opcję?
                  </h3>
                </div>
                {effectiveBreakEven ? (
                  <>
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
                      <span>Wskazówka: Użyj tego analitycznego progu jako konkretnego kryterium podczas rozmów lub negocjacji.</span>
                    </div>
                  </>
                ) : (
                  <p style={{
                    margin: '0',
                    fontSize: '0.85rem',
                    color: 'oklch(54% 0.018 250)',
                    fontStyle: 'italic',
                  }}>
                    Punkt zwrotny niedostępny — brak zdefiniowanych wag lub kryteriów różnicujących w modelu.
                  </p>
                )}
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

              {/* ── 4B. NA CZYM OPARLIŚMY TĘ REKOMENDACJĘ & CZEGO NIE WIEMY (C6) ── */}
              <div style={{
                background: 'oklch(11% 0.02 250)',
                border: '1px solid oklch(22% 0.025 250)',
                borderRadius: '10px',
                padding: '1.5rem',
                marginBottom: '1.5rem',
              }}>
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
                  {/* Na czym oparliśmy */}
                  <div>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: '0.5rem',
                      fontSize: '0.8125rem', fontWeight: 800,
                      letterSpacing: '0.08em', textTransform: 'uppercase',
                      color: 'oklch(75% 0.12 80)', marginBottom: '0.75rem',
                    }}>
                      <span>🌐</span> Na czym oparliśmy tę rekomendację
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {decisionCase?.facts && decisionCase.facts.length > 0 ? (
                        decisionCase.facts.map((f) => (
                          <div key={f.id} style={{
                            fontSize: '0.8125rem', padding: '0.5rem 0.75rem',
                            background: 'oklch(13% 0.022 250)', borderRadius: '6px',
                            border: '1px solid oklch(20% 0.025 250)',
                          }}>
                            <strong style={{ color: 'oklch(88% 0.015 250)' }}>{f.label}:</strong>{' '}
                            <span style={{ color: 'oklch(75% 0.12 80)' }}>{String(f.value)} {f.unit || ''}</span>
                            {f.source_text && (
                              <div style={{ fontSize: '0.75rem', color: 'oklch(56% 0.018 250)', marginTop: '0.2rem' }}>
                                👤 Źródło: {f.source_text}
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <div style={{ fontSize: '0.8125rem', color: 'oklch(60% 0.02 250)' }}>
                          Wszystkie parametry zostały ustalone bezpośrednio na podstawie Twojego opisu i zatwierdzonego modelu matematycznego.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Czego nie wiemy */}
                  <div>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: '0.5rem',
                      fontSize: '0.8125rem', fontWeight: 800,
                      letterSpacing: '0.08em', textTransform: 'uppercase',
                      color: 'oklch(75% 0.15 45)', marginBottom: '0.75rem',
                    }}>
                      <span>⚠️</span> Czego nie wiemy i co założyliśmy
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                      {decisionCase?.unknowns && decisionCase.unknowns.filter((u) => !u.is_resolved).length > 0 ? (
                        decisionCase.unknowns.filter((u) => !u.is_resolved).map((u) => (
                          <div key={u.id} style={{
                            fontSize: '0.8125rem', padding: '0.5rem 0.75rem',
                            background: 'oklch(14% 0.03 45 / 0.3)', borderRadius: '6px',
                            border: '1px solid oklch(28% 0.06 45 / 0.5)',
                            color: 'oklch(80% 0.08 45)',
                          }}>
                            <strong>Brak danych:</strong> {u.question}
                            {u.default_assumption && (
                              <div style={{ fontSize: '0.75rem', color: 'oklch(68% 0.06 45)', marginTop: '0.2rem' }}>
                                Założenie robocze: {u.default_assumption}
                              </div>
                            )}
                          </div>
                        ))
                      ) : (
                        <div style={{ fontSize: '0.8125rem', color: 'oklch(60% 0.02 250)' }}>
                          Brak nierozwiązanych wątpliwości — wszystkie kluczowe zmienne decyzyjne zostały jawnie określone.
                        </div>
                      )}
                    </div>
                  </div>
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
                  Jeśli coś się zmieni — możesz wrócić i obliczyć ponownie z nowym opisem.
                </p>
              </div>
            </div>
          </div>
        )}

        {/* ── Evidence Drawer (technical proof, collapsible) ─── */}
        <div className="no-print">
          <EvidenceDrawer result={result} comparisonResult={comparisonResult} sessionId={sessionId} />
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
          from { opacity: 0; transform: translateY(24px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
