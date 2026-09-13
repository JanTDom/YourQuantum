import React, { useState } from 'react'
import { DecisionCase, FormalizeResponse } from '../api'

interface ModelApprovalGateProps {
  formalized: FormalizeResponse
  decisionCase?: DecisionCase | null
  onApproveAndSolve: (solver: 'cp_sat' | 'qaoa_aer' | 'both', editedWeights?: Record<string, number>) => void
  onBack: () => void
  isSolving: boolean
}

const DIRECTION_LABEL: Record<string, string> = {
  maximize: 'Znalezienie najlepszego wyniku',
  minimize: 'Znalezienie najmniejszego kosztu / najkrótszej drogi',
}

const SOLVER_OPTIONS = [
  {
    id: 'cp_sat' as const,
    name: 'Analiza dokładna',
    tagline: 'Zalecana',
    desc: 'System sprawdza wszystkie możliwości i wybiera matematycznie najlepszą. Daje pewny wynik — nie przybliżony.',
    icon: '🎯',
  },
  {
    id: 'qaoa_aer' as const,
    name: 'Analiza kwantowa',
    tagline: 'Eksperymentalna',
    desc: 'Metoda inspirowana mechaniką kwantową — przydatna przy bardzo dużej liczbie możliwości. Może dać nieznacznie inny wynik niż analiza dokładna.',
    icon: '⚛️',
  },
  {
    id: 'both' as const,
    name: 'Obie metody',
    tagline: 'Porównawcza',
    desc: 'System uruchamia obie metody i zestawia wyniki. Możesz zobaczyć, czy się zgadzają — i wybrać pewniejszy.',
    icon: '⚖️',
  },
] as const

export const ModelApprovalGate: React.FC<ModelApprovalGateProps> = ({
  formalized,
  decisionCase,
  onApproveAndSolve,
  onBack,
  isSolving,
}) => {
  const [selectedSolver, setSelectedSolver] = useState<'cp_sat' | 'qaoa_aer' | 'both'>('cp_sat')
  const [weights, setWeights] = useState<Record<string, number>>(() => ({
    ...formalized.objective_coefficients,
  }))

  const handleWeightChange = (varName: string, val: number) => {
    setWeights((prev) => ({
      ...prev,
      [varName]: val,
    }))
  }

  // G3: Check if there are any blocking missing information items
  const blockingUnknowns = (decisionCase?.unknowns || []).filter(
    (u) => !u.is_resolved && (
      u.impact_description?.toLowerCase().includes('blok') ||
      u.impact_description?.toLowerCase().includes('krytycz') ||
      u.id?.includes('block')
    )
  )

  const blockingMissingInfo = (formalized.missing_information || []).filter(
    (m) => m.toLowerCase().includes('blok') || m.toLowerCase().includes('krytycz')
  )

  const hasBlockingMissingInfo =
    blockingUnknowns.length > 0 ||
    blockingMissingInfo.length > 0 ||
    decisionCase?.input_quality?.level === 'too_vague'

  const optionCount = formalized.binary_variables?.length || 0
  const constraintCount =
    (formalized.equality_constraints?.length || 0) + (formalized.inequality_constraints?.length || 0)
  const direction = formalized.objective_direction === 'maximize' ? 'maximize' : 'minimize'

  return (
    <div style={{ minHeight: '100vh', background: 'oklch(6% 0.01 250)', position: 'relative', overflow: 'hidden' }}>

      {/* ── Background photo — quantum chip ─────────────── */}
      <img
        src="/images/chip.jpg"
        alt=""
        aria-hidden="true"
        style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%',
          objectFit: 'cover', objectPosition: 'center',
          opacity: 0.1, filter: 'saturate(0.5) brightness(0.45)',
          pointerEvents: 'none', zIndex: 0,
        }}
      />

      {/* ── Gradient overlay ─────────────────────────────── */}
      <div
        aria-hidden="true"
        style={{
          position: 'absolute', inset: 0, zIndex: 0,
          background: [
            'radial-gradient(ellipse 80% 70% at 70% 40%, oklch(62% 0.18 240 / 0.07) 0%, transparent 60%)',
            'linear-gradient(to bottom, oklch(6% 0.01 250 / 0.65) 0%, oklch(6% 0.01 250 / 0.95) 100%)',
          ].join(', '),
        }}
      />

      {/* ── Floating decorative particles ─────────────────── */}
      <div aria-hidden="true" style={{ position: 'absolute', inset: 0, zIndex: 0, overflow: 'hidden', pointerEvents: 'none' }}>
        {([
          { sz: 6,  left: '10%', top: '18%', color: 'oklch(75% 0.12 80 / 0.3)',  glow: 'oklch(75% 0.12 80 / 0.5)',  delay: 0,    dur: 4.2 },
          { sz: 9,  left: '22%', top: '72%', color: 'oklch(62% 0.18 240 / 0.25)', glow: 'oklch(62% 0.18 240 / 0.5)', delay: 0.6,  dur: 5.8 },
          { sz: 5,  left: '55%', top: '14%', color: 'oklch(75% 0.12 80 / 0.2)',  glow: 'oklch(75% 0.12 80 / 0.4)',  delay: 1.1,  dur: 3.9 },
          { sz: 8,  left: '78%', top: '35%', color: 'oklch(62% 0.18 240 / 0.2)', glow: 'oklch(62% 0.18 240 / 0.4)', delay: 0.3,  dur: 6.3 },
          { sz: 10, left: '88%', top: '65%', color: 'oklch(75% 0.12 80 / 0.15)', glow: 'oklch(75% 0.12 80 / 0.35)', delay: 1.8,  dur: 4.7 },
          { sz: 7,  left: '42%', top: '82%', color: 'oklch(62% 0.18 240 / 0.22)', glow: 'oklch(62% 0.18 240 / 0.45)', delay: 0.9, dur: 5.2 },
        ] as const).map((p, i) => (
          <div
            key={i}
            style={{
              position: 'absolute',
              width: `${p.sz}px`, height: `${p.sz}px`,
              borderRadius: '50%',
              background: p.color,
              boxShadow: `0 0 ${p.sz * 2}px ${p.glow}`,
              left: p.left, top: p.top,
              animation: `magFloat ${p.dur}s ease-in-out ${p.delay}s infinite`,
            }}
          />
        ))}
      </div>

      {/* ── Main content ──────────────────────────────────── */}
      <div
        style={{
          position: 'relative', zIndex: 1,
          maxWidth: '900px', margin: '0 auto',
          padding: 'clamp(1.5rem, 4vw, 3rem) clamp(1rem, 3vw, 2rem)',
          animation: 'magPageIn 0.55s cubic-bezier(0.22,1,0.36,1) both',
        }}
      >

        {/* ── Step indicator ──────────────────────────────── */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
          {[
            { label: 'Sytuacja opisana', done: true },
            { label: 'Zatwierdź i oblicz', active: true },
            { label: 'Wynik', pending: true },
          ].map((step, i) => (
            <React.Fragment key={step.label}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                fontSize: '0.8125rem',
                fontWeight: step.active ? 700 : 500,
                color: step.active
                  ? 'oklch(75% 0.12 80)'
                  : step.done
                    ? 'oklch(54% 0.018 250)'
                    : 'oklch(34% 0.015 250)',
              }}>
                <span style={{
                  width: '24px', height: '24px', borderRadius: '50%',
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.6875rem', fontWeight: 900, flexShrink: 0,
                  background: step.active
                    ? 'oklch(75% 0.12 80)'
                    : step.done
                      ? 'oklch(35% 0.08 168)'
                      : 'oklch(17% 0.025 250)',
                  border: step.pending ? '1px solid oklch(26% 0.03 250)' : 'none',
                  color: step.active
                    ? 'oklch(6% 0.01 250)'
                    : step.done
                      ? 'oklch(78% 0.14 168)'
                      : 'oklch(38% 0.015 250)',
                }}>
                  {step.done ? '✓' : i + 1}
                </span>
                {step.label}
              </div>
              {i < 2 && (
                <div style={{
                  flex: 1, height: '1px',
                  background: step.done
                    ? 'oklch(75% 0.12 80 / 0.35)'
                    : 'oklch(22% 0.025 250)',
                }} />
              )}
            </React.Fragment>
          ))}
        </div>

        {/* ── Main card ───────────────────────────────────── */}
        <div style={{
          background: 'oklch(10% 0.02 250 / 0.85)',
          backdropFilter: 'blur(20px) saturate(1.4)',
          WebkitBackdropFilter: 'blur(20px) saturate(1.4)',
          borderRadius: '14px',
          border: '1px solid oklch(20% 0.025 250)',
          boxShadow: '0 0 80px oklch(0% 0 0 / 0.5), 0 0 160px oklch(62% 0.18 240 / 0.04)',
          overflow: 'hidden',
        }}>
          {/* Gold accent line */}
          <div style={{
            height: '2px',
            background: 'linear-gradient(to right, transparent, oklch(75% 0.12 80) 30%, oklch(62% 0.18 240) 70%, transparent)',
          }} />

          <div style={{ padding: 'clamp(1.5rem, 3vw, 2.5rem)' }}>

            {/* ── Header ────────────────────────────────────── */}
            <div style={{ marginBottom: '2.25rem' }}>
              <p style={{
                margin: '0 0 0.5rem 0',
                fontSize: '0.75rem', fontWeight: 800,
                letterSpacing: '0.12em', textTransform: 'uppercase',
                color: 'oklch(75% 0.12 80)',
              }}>
                Krok 2 z 2 — Gotowe do obliczenia
              </p>
              <h2 style={{
                margin: '0 0 0.75rem 0',
                fontSize: 'clamp(1.5rem, 3vw, 2rem)',
                fontWeight: 900,
                color: 'oklch(97% 0.008 250)',
                letterSpacing: '-0.03em', lineHeight: 1.1,
              }}>
                System rozumie Twój dylemat.{' '}
                <span style={{ color: 'oklch(75% 0.12 80)' }}>Czy możemy zacząć obliczenia?</span>
              </h2>
              <p style={{ margin: 0, fontSize: '1rem', color: 'oklch(66% 0.02 250)', lineHeight: 1.65 }}>
                Sprawdź podsumowanie. Jeśli coś się nie zgadza — wróć i popraw opis.
                Jeśli wygląda dobrze — kliknij{' '}
                <strong style={{ color: 'oklch(88% 0.015 250)' }}>„Oblicz najlepszą opcję"</strong>.
              </p>
            </div>

            {/* ── Summary cards ─────────────────────────────── */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
              gap: '1rem', marginBottom: '2rem',
            }}>
              <div style={{ background: 'oklch(13% 0.022 250)', borderRadius: '10px', border: '1px solid oklch(22% 0.025 250)', padding: '1.25rem' }}>
                <div style={{ fontSize: '2.25rem', fontWeight: 900, color: 'oklch(75% 0.12 80)', lineHeight: 1, letterSpacing: '-0.03em' }}>
                  {optionCount || '—'}
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'oklch(78% 0.02 250)', marginTop: '0.375rem' }}>
                  {optionCount === 1 ? 'opcja do zbadania' : 'opcje do zbadania'}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'oklch(54% 0.018 250)', marginTop: '0.25rem' }}>
                  System porówna każdą i wybierze najlepszą.
                </div>
              </div>

              <div style={{ background: 'oklch(13% 0.022 250)', borderRadius: '10px', border: '1px solid oklch(22% 0.025 250)', padding: '1.25rem' }}>
                <div style={{ fontSize: '1.5rem', lineHeight: 1, marginBottom: '0.375rem' }}>
                  {direction === 'maximize' ? '📈' : '📉'}
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'oklch(78% 0.02 250)' }}>
                  Cel analizy
                </div>
                <div style={{ fontSize: '0.8125rem', color: 'oklch(66% 0.02 250)', marginTop: '0.25rem', lineHeight: 1.4 }}>
                  {DIRECTION_LABEL[direction] ?? 'Optymalizacja'}
                </div>
              </div>

              <div style={{ background: 'oklch(13% 0.022 250)', borderRadius: '10px', border: '1px solid oklch(22% 0.025 250)', padding: '1.25rem' }}>
                <div style={{
                  fontSize: '2.25rem', fontWeight: 900, lineHeight: 1, letterSpacing: '-0.03em',
                  color: constraintCount > 0 ? 'oklch(62% 0.18 240)' : 'oklch(54% 0.018 250)',
                }}>
                  {constraintCount}
                </div>
                <div style={{ fontSize: '0.875rem', fontWeight: 700, color: 'oklch(78% 0.02 250)', marginTop: '0.375rem' }}>
                  {constraintCount === 1 ? 'reguła do spełnienia' : 'reguły do spełnienia'}
                </div>
                <div style={{ fontSize: '0.75rem', color: 'oklch(54% 0.018 250)', marginTop: '0.25rem' }}>
                  {constraintCount > 0
                    ? 'System sprawdzi je niezależnie przed wynikiem.'
                    : 'Brak ograniczeń — pełna swoboda wyboru.'}
                </div>
              </div>
            </div>

            {/* ── What system understood ────────────────────── */}
            <div style={{
              background: 'oklch(8% 0.015 250)',
              border: '1px solid oklch(20% 0.025 250)',
              borderLeft: '3px solid oklch(75% 0.12 80 / 0.6)',
              borderRadius: '10px', padding: '1.25rem', marginBottom: '1.5rem',
            }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                marginBottom: '0.625rem',
              }}>
                <div style={{
                  fontSize: '0.75rem', fontWeight: 800,
                  letterSpacing: '0.1em', textTransform: 'uppercase',
                  color: 'oklch(75% 0.12 80)',
                }}>
                  Co system zrozumiał z Twojego opisu
                </div>
                <button
                  type="button"
                  onClick={onBack}
                  disabled={isSolving}
                  style={{
                    background: 'none', border: 'none', padding: 0,
                    color: 'oklch(75% 0.12 80)', fontSize: '0.75rem', fontWeight: 700,
                    cursor: 'pointer', textDecoration: 'underline',
                  }}
                >
                  Popraw opis
                </button>
              </div>
              <p style={{
                margin: 0, fontSize: '0.9375rem',
                color: 'oklch(78% 0.02 250)', lineHeight: 1.65,
                whiteSpace: 'pre-wrap', fontFamily: 'var(--font-sans)',
              }}>
                {formalized.description_formalised}
              </p>
            </div>

            {/* ── Mathematical model: Objective & Coefficients ── */}
            <div style={{
              background: 'oklch(11% 0.02 250)',
              border: '1px solid oklch(22% 0.025 250)',
              borderRadius: '10px', padding: '1.25rem', marginBottom: '2rem',
            }}>
              <div style={{
                display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                marginBottom: '1rem',
              }}>
                <div>
                  <div style={{
                    fontSize: '0.75rem', fontWeight: 800,
                    letterSpacing: '0.1em', textTransform: 'uppercase',
                    color: 'oklch(62% 0.18 240)',
                  }}>
                    Model matematyczny — Funkcja celu i wagi kryteriów
                  </div>
                  <div style={{ fontSize: '0.8125rem', color: 'oklch(56% 0.018 250)', marginTop: '0.2rem' }}>
                    Kierunek: <strong style={{ color: 'oklch(85% 0.02 250)' }}>{direction === 'maximize' ? 'Maksymalizacja' : 'Minimalizacja'}</strong>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={onBack}
                  disabled={isSolving}
                  style={{
                    background: 'oklch(16% 0.025 250)',
                    border: '1px solid oklch(28% 0.03 250)',
                    borderRadius: '6px', padding: '0.35rem 0.75rem',
                    fontSize: '0.75rem', fontWeight: 600,
                    color: 'oklch(75% 0.12 80)', cursor: isSolving ? 'not-allowed' : 'pointer',
                  }}
                >
                  ✎ Popraw formalizację
                </button>
              </div>

              {/* Decision Matrix Table with Cell Provenance (G3 / C6) */}
              {decisionCase?.score_matrix && Object.keys(decisionCase.score_matrix).length > 0 && (
                <div style={{ marginBottom: '1.5rem', overflowX: 'auto' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'oklch(62% 0.18 240)', marginBottom: '0.5rem' }}>
                    Macierz Decyzyjna ze Źródłami i Pochodzeniem Danych (C6)
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.75rem', textAlign: 'left' }}>
                    <thead>
                      <tr style={{ background: 'oklch(14% 0.025 250)', borderBottom: '1px solid oklch(24% 0.03 250)' }}>
                        <th style={{ padding: '0.6rem 0.75rem', color: 'oklch(80% 0.02 250)', fontWeight: 700 }}>Opcja / Wariant</th>
                        {decisionCase.criteria.map((crit) => (
                          <th key={crit.id} style={{ padding: '0.6rem 0.75rem', color: 'oklch(80% 0.02 250)', fontWeight: 700 }}>
                            {crit.name} {crit.unit ? `(${crit.unit})` : ''}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {decisionCase.options.map((opt) => (
                        <tr key={opt.id} style={{ borderBottom: '1px solid oklch(18% 0.02 250)' }}>
                          <td style={{ padding: '0.6rem 0.75rem', fontWeight: 600, color: 'oklch(88% 0.02 250)' }}>
                            {opt.title}
                          </td>
                          {decisionCase.criteria.map((crit) => {
                            const cell = decisionCase.score_matrix?.[opt.id]?.[crit.id]
                            const prov = cell?.provenance || 'assumed'
                            const provColor = prov === 'user_supplied' ? 'oklch(75% 0.12 80)' : prov === 'web_sourced' ? 'oklch(65% 0.18 240)' : 'oklch(60% 0.02 250)'
                            return (
                              <td key={crit.id} style={{ padding: '0.6rem 0.75rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', flexWrap: 'wrap' }}>
                                  <span style={{ fontWeight: 700, color: 'oklch(90% 0.01 250)' }}>
                                    {cell?.value !== undefined ? cell.value : '—'}
                                  </span>
                                  <span style={{
                                    fontSize: '0.625rem', padding: '0.1rem 0.35rem', borderRadius: '3px',
                                    background: 'oklch(18% 0.025 250)', color: provColor, fontWeight: 700,
                                  }}>
                                    {prov}
                                  </span>
                                </div>
                                {cell?.source_ref && (
                                  <div style={{ fontSize: '0.625rem', color: 'oklch(55% 0.02 250)', marginTop: '0.15rem' }}>
                                    źródło: {cell.source_ref.slice(0, 30)}...
                                  </div>
                                )}
                              </td>
                            )
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}

              {/* Formula badge */}
              <div style={{
                background: 'oklch(7% 0.012 250)',
                border: '1px solid oklch(18% 0.02 250)',
                borderRadius: '8px', padding: '0.75rem 1rem',
                fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace',
                fontSize: '0.8125rem', color: 'oklch(80% 0.08 80)',
                marginBottom: '1rem', overflowX: 'auto',
              }}>
                {direction.toUpperCase()}(Z) ={' '}
                {formalized.binary_variables.map((v, idx) => {
                  const val = weights[v] ?? 1.0
                  return `${idx > 0 && val >= 0 ? '+ ' : ''}${val.toFixed(1)} · ${v}`
                }).join(' ')}
              </div>

              {/* Editable weights grid (G3) */}
              <div style={{ marginBottom: '1.25rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'oklch(75% 0.12 80)', marginBottom: '0.5rem' }}>
                  Edytowalne wagi zmiennych decyzyjnych (możesz dostosować priorytety):
                </div>
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                  gap: '0.625rem',
                }}>
                  {formalized.binary_variables.map((varName) => {
                    const currentWeight = weights[varName] ?? 1.0
                    return (
                      <div
                        key={varName}
                        style={{
                          background: 'oklch(13% 0.02 250)',
                          border: '1px solid oklch(22% 0.022 250)',
                          borderRadius: '8px', padding: '0.625rem 0.875rem',
                          display: 'flex', flexDirection: 'column', gap: '0.35rem',
                        }}
                      >
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <span style={{ fontSize: '0.8125rem', color: 'oklch(85% 0.02 250)', fontWeight: 600 }}>
                            {varName}
                          </span>
                          <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', fontWeight: 700, color: 'oklch(75% 0.12 80)' }}>
                            waga: {currentWeight.toFixed(1)}
                          </span>
                        </div>
                        <input
                          type="range"
                          min="-10"
                          max="20"
                          step="0.5"
                          value={currentWeight}
                          onChange={(e) => handleWeightChange(varName, parseFloat(e.target.value) || 0)}
                          disabled={isSolving}
                          style={{ width: '100%', accentColor: 'oklch(75% 0.12 80)', cursor: isSolving ? 'not-allowed' : 'pointer' }}
                        />
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Constraints review if any */}
              {constraintCount > 0 && (
                <div style={{ borderTop: '1px solid oklch(18% 0.02 250)', paddingTop: '0.75rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'oklch(60% 0.02 250)', marginBottom: '0.5rem' }}>
                    Twarde reguły matematyczne:
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                    {formalized.equality_constraints?.map((c, idx) => (
                      <div key={`eq-${idx}`} style={{ fontSize: '0.75rem', color: 'oklch(70% 0.02 250)', fontFamily: 'monospace' }}>
                        • {Object.entries(c.lhs).map(([k, v]) => `${v}·${k}`).join(' + ')} = {c.rhs} (równość)
                      </div>
                    ))}
                    {formalized.inequality_constraints?.map((c, idx) => (
                      <div key={`ineq-${idx}`} style={{ fontSize: '0.75rem', color: 'oklch(70% 0.02 250)', fontFamily: 'monospace' }}>
                        • {Object.entries(c.lhs).map(([k, v]) => `${v}·${k}`).join(' + ')} ≤ {c.rhs} (ograniczenie zasobu)
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Założenia i Czego nie wiemy (G3) */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
              {/* Założenia */}
              <div style={{ background: 'oklch(10% 0.018 250)', border: '1px solid oklch(20% 0.025 250)', borderRadius: '10px', padding: '1.25rem' }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'oklch(75% 0.12 80)', marginBottom: '0.5rem' }}>
                  Założenia modelowe ({formalized.assumptions?.length || decisionCase?.facts?.length || 0})
                </div>
                {formalized.assumptions && formalized.assumptions.length > 0 ? (
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8125rem', color: 'oklch(75% 0.02 250)', lineHeight: 1.6 }}>
                    {formalized.assumptions.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                ) : (
                  <div style={{ fontSize: '0.8125rem', color: 'oklch(55% 0.02 250)' }}>Brak ukrytych założeń — model oparty wyłącznie na faktach użytkownika.</div>
                )}
              </div>

              {/* Czego nie wiemy */}
              <div style={{
                background: hasBlockingMissingInfo ? 'oklch(14% 0.04 25)' : 'oklch(10% 0.018 250)',
                border: `1px solid ${hasBlockingMissingInfo ? 'oklch(40% 0.15 25)' : 'oklch(20% 0.025 250)'}`,
                borderRadius: '10px', padding: '1.25rem'
              }}>
                <div style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.08em', color: hasBlockingMissingInfo ? 'oklch(75% 0.15 25)' : 'oklch(62% 0.18 240)', marginBottom: '0.5rem' }}>
                  Czego nie wiemy ({blockingUnknowns.length + blockingMissingInfo.length > 0 ? `${blockingUnknowns.length + blockingMissingInfo.length} blokujących` : 'Brak luk'})
                </div>
                {hasBlockingMissingInfo ? (
                  <div>
                    <div style={{ fontSize: '0.75rem', color: 'oklch(85% 0.1 25)', fontWeight: 700, marginBottom: '0.5rem' }}>
                      ⚠️ Wykryto luki uniemożliwiające rozwiązanie (BLOCKS_SOLVING):
                    </div>
                    <ul style={{ margin: 0, paddingLeft: '1.25rem', fontSize: '0.8125rem', color: 'oklch(80% 0.02 25)', lineHeight: 1.6 }}>
                      {blockingUnknowns.map((u) => (
                        <li key={u.id}><strong>{u.question}</strong> — {u.impact_description}</li>
                      ))}
                      {blockingMissingInfo.map((m, i) => (
                        <li key={`bm-${i}`}>{m}</li>
                      ))}
                    </ul>
                  </div>
                ) : (
                  <div style={{ fontSize: '0.8125rem', color: 'oklch(70% 0.04 168)' }}>
                    ✓ Wszystkie krytyczne dane wejściowe zostały zweryfikowane. Model gotowy do obliczeń.
                  </div>
                )}
              </div>
            </div>

            {/* ── Solver selection ──────────────────────────── */}
            <div style={{ marginBottom: '2rem' }}>
              <div style={{
                fontSize: '0.875rem', fontWeight: 700,
                color: 'oklch(78% 0.02 250)', marginBottom: '0.875rem',
              }}>
                Jak chcesz żeby system szukał odpowiedzi?
              </div>
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                gap: '0.75rem',
              }}>
                {SOLVER_OPTIONS.map((opt) => {
                  const isSelected = selectedSolver === opt.id
                  return (
                    <button
                      key={opt.id}
                      type="button"
                      onClick={() => setSelectedSolver(opt.id)}
                      style={{
                        textAlign: 'left', padding: '1.125rem',
                        borderRadius: '10px',
                        border: `2px solid ${isSelected ? 'oklch(75% 0.12 80)' : 'oklch(22% 0.025 250)'}`,
                        background: isSelected ? 'oklch(14% 0.03 80)' : 'oklch(13% 0.022 250)',
                        cursor: 'pointer',
                        transition: 'all 200ms ease',
                        boxShadow: isSelected ? '0 0 20px oklch(75% 0.12 80 / 0.15)' : 'none',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.375rem' }}>
                        <span style={{ fontSize: '1.375rem', lineHeight: 1 }}>{opt.icon}</span>
                        <span style={{
                          fontSize: '0.6875rem', fontWeight: 800,
                          letterSpacing: '0.08em', textTransform: 'uppercase',
                          color: isSelected ? 'oklch(75% 0.12 80)' : 'oklch(42% 0.02 250)',
                          padding: '0.125rem 0.5rem', borderRadius: '3px',
                          background: isSelected ? 'oklch(75% 0.12 80 / 0.12)' : 'oklch(17% 0.025 250)',
                        }}>
                          {opt.tagline}
                        </span>
                      </div>
                      <div style={{
                        fontWeight: 700, fontSize: '0.9375rem',
                        color: isSelected ? 'oklch(97% 0.008 250)' : 'oklch(78% 0.02 250)',
                        marginBottom: '0.3125rem',
                      }}>
                        {opt.name}
                      </div>
                      <div style={{ fontSize: '0.8125rem', color: 'oklch(58% 0.018 250)', lineHeight: 1.5 }}>
                        {opt.desc}
                      </div>
                    </button>
                  )
                })}
              </div>
            </div>

            {/* ── Footer actions ────────────────────────────── */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'center',
              paddingTop: '1.5rem',
              borderTop: '1px solid oklch(18% 0.022 250)',
              gap: '1rem', flexWrap: 'wrap',
            }}>
              <button
                type="button"
                onClick={onBack}
                disabled={isSolving}
                style={{
                  background: 'none',
                  border: '1px solid oklch(28% 0.025 250)',
                  borderRadius: '8px', padding: '0.75rem 1.25rem',
                  fontSize: '0.875rem', color: 'oklch(60% 0.018 250)',
                  cursor: isSolving ? 'not-allowed' : 'pointer',
                  opacity: isSolving ? 0.5 : 1,
                  transition: 'border-color 200ms, color 200ms',
                }}
              >
                ← Wróć i zmień opis
              </button>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                {hasBlockingMissingInfo && (
                  <div style={{
                    background: 'oklch(16% 0.04 25)',
                    border: '1px solid oklch(35% 0.12 25)',
                    borderRadius: '6px', padding: '0.35rem 0.75rem',
                    fontSize: '0.75rem', color: 'oklch(80% 0.12 25)', fontWeight: 700,
                  }}>
                    ⛔ Zatwierdzenie zablokowane: rozwiąż luki BLOCKS_SOLVING przed solverem
                  </div>
                )}
                <button
                  type="button"
                  onClick={() => onApproveAndSolve(selectedSolver, weights)}
                  disabled={isSolving || hasBlockingMissingInfo}
                  style={{
                    background: (isSolving || hasBlockingMissingInfo) ? 'oklch(30% 0.02 250)' : 'oklch(75% 0.12 80)',
                    color: (isSolving || hasBlockingMissingInfo) ? 'oklch(60% 0.02 250)' : 'oklch(5% 0.01 250)',
                    border: 'none',
                    borderRadius: '8px', padding: '0.9375rem 2rem',
                    fontSize: '1rem', fontWeight: 800,
                    cursor: (isSolving || hasBlockingMissingInfo) ? 'not-allowed' : 'pointer',
                    transition: 'background 200ms ease, box-shadow 200ms ease',
                    boxShadow: (isSolving || hasBlockingMissingInfo) ? 'none' : '0 0 30px oklch(75% 0.12 80 / 0.45)',
                    letterSpacing: '-0.015em',
                    display: 'inline-flex', alignItems: 'center', gap: '0.625rem',
                  }}
                >
                  {isSolving ? (
                    <>
                      <span style={{
                        display: 'inline-block', width: '16px', height: '16px',
                        border: '2px solid oklch(5% 0.01 250 / 0.3)',
                        borderTopColor: 'oklch(5% 0.01 250)',
                        borderRadius: '50%',
                        animation: 'magSpin 0.9s linear infinite',
                      }} />
                      Obliczam i weryfikuję...
                    </>
                  ) : (
                    <>
                      Oblicz najlepszą opcję
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2.5" aria-hidden="true">
                        <path d="M5 12h14M12 5l7 7-7 7" />
                      </svg>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes magPageIn {
          from { opacity: 0; transform: translateY(28px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes magSpin {
          from { transform: rotate(0deg); }
          to   { transform: rotate(360deg); }
        }
        @keyframes magFloat {
          0%, 100% { transform: translateY(0)   scale(1); }
          50%       { transform: translateY(-20px) scale(1.15); }
        }
      `}</style>
    </div>
  )
}
