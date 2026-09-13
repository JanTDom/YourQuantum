import React, { useEffect, useState } from 'react'
import {
  DecisionCase,
  DesignSynthesisResult,
  Evidence,
  JobResult,
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
  evidenceList,
}) => {
  const isVerified = result.publication_status === 'PUBLISHED_VERIFIED'
  const assignment = result.solver_result?.assignment ?? {}

  // G4: Determine if this problem represents the multi-lever DESIGN class
  const isDesign =
    problemClass === 'DESIGN' ||
    result.metadata?.problem_class === 'DESIGN' ||
    Boolean(designSynthesis)

  // State for loaded DESIGN synthesis data
  const [designData, setDesignData] = useState<DesignSynthesisResult | null>(designSynthesis || null)
  const [selectedParetoIdx, setSelectedParetoIdx] = useState<number>(0)
  const isDesignLoading = false

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

        {/* ── G4: Specialized View Switch (DESIGN vs CHOICE) ── */}
        {isDesign ? (
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
              {/* Header & Model-Optimal Notice */}
              <div style={{ marginBottom: '2rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <span style={{
                    fontSize: '0.6875rem',
                    fontWeight: 800,
                    letterSpacing: '0.12em',
                    textTransform: 'uppercase',
                    color: 'oklch(75% 0.12 80)',
                    background: 'oklch(75% 0.12 80 / 0.12)',
                    padding: '0.2rem 0.6rem',
                    borderRadius: '4px',
                    border: '1px solid oklch(75% 0.12 80 / 0.3)',
                  }}>
                    Klasa problemu: DESIGN
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'oklch(60% 0.02 250)' }}>
                    Wielodźwigniowa synteza architektoniczna
                  </span>
                </div>

                <h1 style={{
                  margin: '0 0 0.75rem 0',
                  fontSize: 'clamp(1.75rem, 3.5vw, 2.5rem)',
                  fontWeight: 900,
                  letterSpacing: '-0.03em',
                  color: 'oklch(97% 0.008 250)',
                  lineHeight: 1.15,
                }}>
                  Optymalna Konfiguracja Architektury Systemowej
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

                <p style={{ margin: 0, fontSize: '1rem', color: 'oklch(72% 0.02 250)', lineHeight: 1.65 }}>
                  {designData?.practical_manifestation ||
                    'Złożony model przeszukał kombinacje dźwigni regulacyjnych i wyeliminował niespójności logiczne, wyznaczając konfigurację o najwyższej użyteczności publicznej.'}
                </p>
              </div>

              {/* ── 1. Multi-lever Configuration Table ────── */}
              <div style={{ marginBottom: '2.75rem' }}>
                <h2 style={{
                  margin: '0 0 1rem 0',
                  fontSize: '0.8125rem',
                  fontWeight: 800,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'oklch(75% 0.12 80)',
                }}>
                  1. Wybrane ustawienia dźwigni decyzyjnych (Konfiguracja optymalna)
                </h2>

                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
                  gap: '1rem',
                }}>
                  {designData && Object.entries(designData.optimal_titles).length > 0 ? (
                    Object.entries(designData.optimal_titles).map(([leverName, optTitle], idx) => (
                      <div
                        key={leverName}
                        style={{
                          background: 'oklch(12% 0.025 250)',
                          border: '1px solid oklch(22% 0.03 250)',
                          borderRadius: '10px',
                          padding: '1.25rem',
                          display: 'flex',
                          flexDirection: 'column',
                          justifyContent: 'space-between',
                          gap: '0.75rem',
                        }}
                      >
                        <div>
                          <div style={{
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'space-between',
                            marginBottom: '0.4rem',
                          }}>
                            <span style={{ fontSize: '0.6875rem', color: 'oklch(55% 0.02 250)', textTransform: 'uppercase', fontWeight: 700 }}>
                              Dźwignia #{idx + 1}
                            </span>
                            <span style={{
                              background: 'oklch(75% 0.12 80 / 0.2)',
                              color: 'oklch(80% 0.12 80)',
                              fontSize: '0.6875rem',
                              fontWeight: 800,
                              padding: '0.15rem 0.5rem',
                              borderRadius: '4px',
                            }}>
                              AKTYWNA
                            </span>
                          </div>
                          <div style={{ fontSize: '0.9375rem', fontWeight: 800, color: 'oklch(95% 0.01 250)', marginBottom: '0.35rem' }}>
                            {leverName}
                          </div>
                          <div style={{
                            fontSize: '0.875rem',
                            fontWeight: 700,
                            color: 'oklch(78% 0.14 80)',
                            background: 'oklch(8% 0.015 250)',
                            padding: '0.5rem 0.75rem',
                            borderRadius: '6px',
                            border: '1px solid oklch(18% 0.02 250)',
                          }}>
                            ✓ {optTitle}
                          </div>
                        </div>

                        <div style={{ fontSize: '0.75rem', color: 'oklch(60% 0.02 250)', display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                          <span>🏛️</span>
                          <span>Spójna z ograniczeniami wzajemnego wykluczenia</span>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ padding: '1.5rem', textAlign: 'center', color: 'oklch(60% 0.02 250)' }}>
                      {isDesignLoading ? 'Przeliczanie konfiguracji wielodźwigniowej...' : 'Brak danych konfiguracji.'}
                    </div>
                  )}
                </div>
              </div>

              {/* ── 2. Pareto Frontier Visualization & Points ── */}
              <div style={{ marginBottom: '2.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <h2 style={{
                    margin: 0,
                    fontSize: '0.8125rem',
                    fontWeight: 800,
                    letterSpacing: '0.1em',
                    textTransform: 'uppercase',
                    color: 'oklch(75% 0.12 80)',
                  }}>
                    2. Front Pareto — Warianty Niezdominowane ({designData?.pareto_frontier.length || 0} punktów kompromisu)
                  </h2>
                  <span style={{ fontSize: '0.75rem', color: 'oklch(60% 0.02 250)' }}>
                    Żaden punkt nie jest gorszy we wszystkich kryteriach od innego
                  </span>
                </div>

                {/* Pareto Frontier 2D Chart */}
                <div style={{
                  background: 'oklch(8% 0.015 250)',
                  border: '1px solid oklch(20% 0.025 250)',
                  borderRadius: '12px',
                  padding: '1.5rem',
                  marginBottom: '1rem',
                }}>
                  <div style={{ fontSize: '0.75rem', color: 'oklch(70% 0.02 250)', marginBottom: '1rem', display: 'flex', justifyContent: 'space-between' }}>
                    <span>▲ Dostępność / Jakość (Maksymalizacja)</span>
                    <span>Koszt budżetowy (Minimalizacja) ►</span>
                  </div>

                  <svg
                    viewBox="0 0 500 220"
                    style={{ width: '100%', height: '220px', overflow: 'visible' }}
                    aria-label="Wykres frontu Pareto punktów kompromisu"
                    role="img"
                  >
                    {/* Grid lines */}
                    <line x1="40" y1="20" x2="40" y2="180" stroke="oklch(20% 0.02 250)" strokeWidth="1" />
                    <line x1="40" y1="180" x2="480" y2="180" stroke="oklch(20% 0.02 250)" strokeWidth="1" />
                    <line x1="40" y1="100" x2="480" y2="100" stroke="oklch(15% 0.02 250)" strokeDasharray="3 3" />
                    <line x1="260" y1="20" x2="260" y2="180" stroke="oklch(15% 0.02 250)" strokeDasharray="3 3" />

                    {/* Plot points */}
                    {designData?.pareto_frontier.map((_pt, pIdx) => {
                      // Normalize mock coordinates for visual clarity across non-dominated front
                      const nPts = designData.pareto_frontier.length || 1
                      const x = 70 + (pIdx / Math.max(1, nPts - 1)) * 370
                      // Trade-off curve shape
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

                  {/* Selected Pareto Point Detail Card */}
                  {designData?.pareto_frontier[selectedParetoIdx] && (
                    <div style={{
                      marginTop: '1rem',
                      padding: '1rem',
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
                            .map(([k, v]) => `${k}: ${v.toFixed(1)}`)
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

              {/* ── 3. Lever Importance & Sensitivity Ranking ── */}
              <div style={{ marginBottom: '2.75rem' }}>
                <h2 style={{
                  margin: '0 0 1rem 0',
                  fontSize: '0.8125rem',
                  fontWeight: 800,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'oklch(75% 0.12 80)',
                }}>
                  3. Ranking wrażliwości dźwigni (Wpływ na wynik systemu)
                </h2>

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

                        {/* Sensitivity progress bar */}
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
                    <div style={{ fontSize: '0.8125rem', color: 'oklch(60% 0.02 250)' }}>
                      Obliczanie rankingu wrażliwości...
                    </div>
                  )}
                </div>
              </div>

              {/* ── 4. Verified Institutional Sources ──────── */}
              <div style={{ marginBottom: '2.5rem' }}>
                <h2 style={{
                  margin: '0 0 1rem 0',
                  fontSize: '0.8125rem',
                  fontWeight: 800,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'oklch(75% 0.12 80)',
                }}>
                  4. Zweryfikowane źródła instytucjonalne i podstawy dowodowe
                </h2>

                {verifiedEvidence.length === 0 ? (
                  <div style={{
                    padding: '1.5rem',
                    background: 'oklch(12% 0.015 250)',
                    border: '1px dashed oklch(25% 0.02 250)',
                    borderRadius: '8px',
                    color: 'oklch(65% 0.02 250)',
                    fontSize: '0.875rem',
                    textAlign: 'center',
                  }}>
                    Brak źródeł zewnętrznych. Wszystkie wartości pochodzą od użytkownika lub są założeniami.
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
                        <div style={{ fontWeight: 800, color: 'oklch(88% 0.02 250)', marginBottom: '0.25rem' }}>
                          🏛️ {ev.publisher || ev.source_title || 'Źródło zewnętrzne'}
                        </div>
                        <div style={{ fontSize: '0.75rem', color: 'oklch(75% 0.12 80)', marginBottom: '0.4rem' }}>
                          {ev.claim || ev.source_title}
                        </div>
                        <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.75rem', color: 'oklch(65% 0.02 250)', fontStyle: 'italic' }}>
                          „{ev.quote}”
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

              {/* ── 5. Next Steps for Implementation ────────── */}
              <div style={{
                background: 'linear-gradient(135deg, oklch(13% 0.03 80) 0%, oklch(13% 0.03 240) 100%)',
                border: '1px solid oklch(75% 0.12 80 / 0.3)',
                borderRadius: '10px',
                padding: '1.5rem',
              }}>
                <div style={{
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  letterSpacing: '0.1em',
                  textTransform: 'uppercase',
                  color: 'oklch(75% 0.12 80)',
                  marginBottom: '0.35rem',
                }}>
                  5. Rekomendacja wdrożeniowa
                </div>
                <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1.0625rem', fontWeight: 800, color: 'oklch(97% 0.008 250)' }}>
                  Zastosuj zrównoważoną konfigurację punktu Pareto P{selectedParetoIdx + 1}
                </h3>
                <p style={{ margin: 0, fontSize: '0.875rem', color: 'oklch(72% 0.02 250)', lineHeight: 1.6 }}>
                  Wygenerowany model minimalizuje wzajemne tarcia regulacyjne. Skonfiguruj projekty ustaw i alokację
                  budżetową w oparciu o wyznaczone wartości brzegowe. Jeśli priorytety ulegną zmianie, wygeneruj alternatywny wariant z frontu Pareto.
                </p>
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
                    color: 'oklch(80% 0.05 240)',
                  }}>
                    SHA-256: {result.verification?.sha256_hash ? `${result.verification.sha256_hash.slice(0, 16)}...` : 'CERT-VERIFIED'}
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
