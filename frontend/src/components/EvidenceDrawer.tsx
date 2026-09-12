import React, { useState } from 'react'
import { JobResult } from '../api'

interface EvidenceDrawerProps {
  result: JobResult
  comparisonResult?: JobResult | null
}

export const EvidenceDrawer: React.FC<EvidenceDrawerProps> = ({ result, comparisonResult }) => {
  const [isOpen, setIsOpen] = useState(false)

  const verification = result.verification
  const isVerified = result.publication_status === 'PUBLISHED_VERIFIED'

  return (
    <div style={{
      marginTop: '2rem',
      background: 'var(--bg-canvas)',
      borderRadius: 'var(--radius-md)',
      border: '1px solid var(--border-subtle)',
      overflow: 'hidden',
    }}>
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '1rem 1.25rem',
          background: 'var(--bg-subtle)',
          border: 'none',
          cursor: 'pointer',
          textAlign: 'left',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{
            fontSize: '0.8125rem',
            fontWeight: 700,
            color: 'var(--text-secondary)',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}>
            Dowody obliczeniowe i weryfikacja niezależna
          </span>
          <span style={{
            fontSize: '0.75rem',
            padding: '0.2rem 0.5rem',
            borderRadius: 'var(--radius-full)',
            background: isVerified ? 'var(--status-verified-bg)' : 'var(--status-unverified-bg)',
            color: isVerified ? 'var(--status-verified-text)' : 'var(--status-unverified-text)',
            border: `1px solid ${isVerified ? 'var(--status-verified-border)' : 'var(--status-unverified-border)'}`,
            fontWeight: 600,
          }}>
            {isVerified ? 'Weryfikacja pomyślna' : 'Wymaga uwagi'}
          </span>
        </div>
        <span style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          {isOpen ? 'Zwiń szczegóły ▲' : 'Rozwiń dowody techniczne ▼'}
        </span>
      </button>

      {isOpen && (
        <div style={{ padding: '1.25rem', borderTop: '1px solid var(--border-subtle)' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '1rem',
            marginBottom: '1.25rem',
          }}>
            <div style={{ background: 'var(--bg-surface)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Silnik obliczeniowy</div>
              <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                {result.source || 'Solver klasyczny'}
              </div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Status matematyczny</div>
              <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                {result.math_status || 'Nieznany'}
              </div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Czas obliczeń</div>
              <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                {result.solve_time_seconds ? `${result.solve_time_seconds.toFixed(3)} s` : 'Brak danych'}
              </div>
            </div>

            <div style={{ background: 'var(--bg-surface)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Wartość funkcji celu</div>
              <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'var(--text-primary)', marginTop: '0.25rem' }}>
                {result.objective_value !== null ? result.objective_value : '—'}
              </div>
            </div>

            {verification?.optimality_gap_percent !== undefined && verification.optimality_gap_percent !== null && (
              <div style={{ background: 'var(--bg-surface)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Luka optymalności (Dual Gap)</div>
                <div style={{ fontWeight: 700, fontSize: '0.9375rem', color: 'oklch(75% 0.15 80)', marginTop: '0.25rem' }}>
                  ≤ {verification.optimality_gap_percent}%
                </div>
              </div>
            )}

            {verification?.sha256_hash && (
              <div style={{ background: 'var(--bg-surface)', padding: '0.75rem', borderRadius: 'var(--radius-sm)', border: '1px solid var(--border-subtle)' }}>
                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>Certyfikat SHA-256</div>
                <div style={{ fontWeight: 600, fontSize: '0.75rem', fontFamily: 'ui-monospace, monospace', color: 'var(--text-secondary)', marginTop: '0.25rem' }}>
                  {verification.sha256_hash.slice(0, 16)}...
                </div>
              </div>
            )}
          </div>

          {/* Quantum Circuit & Physics analysis if QAOA was run */}
          {(() => {
            const qRecord = result.solver_result?.metadata?.qaoa_run_record ||
              comparisonResult?.solver_result?.metadata?.qaoa_run_record

            if (!qRecord) return null

            const totalShots = qRecord.shots || 1024
            const dist = qRecord.sample_distribution || {}
            const sortedSamples = Object.entries(dist)
              .sort(([, a], [, b]) => (b as number) - (a as number))
              .slice(0, 4)

            return (
              <div style={{
                marginBottom: '1.25rem',
                padding: '1.125rem',
                background: 'oklch(14% 0.025 250)',
                borderRadius: 'var(--radius-sm)',
                border: '1px solid oklch(26% 0.04 250)',
              }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{ fontSize: '1rem' }}>⚛️</span>
                    <span style={{ fontSize: '0.875rem', fontWeight: 700, color: 'oklch(96% 0.01 250)' }}>
                      Fizyka obwodu kwantowego (QAOA Qiskit Aer)
                    </span>
                  </div>
                  {qRecord.amplification_factor && (
                    <span style={{
                      fontSize: '0.75rem',
                      padding: '0.2rem 0.6rem',
                      borderRadius: 'var(--radius-full)',
                      background: 'oklch(22% 0.06 150)',
                      color: 'oklch(82% 0.16 150)',
                      border: '1px solid oklch(35% 0.1 150)',
                      fontWeight: 700,
                    }}>
                      Wzmocnienie kwantowe: {qRecord.amplification_factor}x
                    </span>
                  )}
                </div>

                {/* Physics metrics grid */}
                <div style={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
                  gap: '0.75rem',
                  marginBottom: '1rem',
                }}>
                  <div style={{ background: 'oklch(11% 0.02 250)', padding: '0.625rem 0.75rem', borderRadius: '6px', border: '1px solid oklch(20% 0.02 250)' }}>
                    <div style={{ fontSize: '0.6875rem', color: 'oklch(60% 0.02 250)', textTransform: 'uppercase' }}>Bramki splątujące (2-qubit)</div>
                    <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'oklch(92% 0.01 250)', marginTop: '0.2rem' }}>
                      {qRecord.two_qubit_gate_count || 0} bramek CNOT
                    </div>
                  </div>

                  <div style={{ background: 'oklch(11% 0.02 250)', padding: '0.625rem 0.75rem', borderRadius: '6px', border: '1px solid oklch(20% 0.02 250)' }}>
                    <div style={{ fontSize: '0.6875rem', color: 'oklch(60% 0.02 250)', textTransform: 'uppercase' }}>Głębokość obwodu (Depth)</div>
                    <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'oklch(92% 0.01 250)', marginTop: '0.2rem' }}>
                      {qRecord.circuit_depth || 0} warstw logicznych
                    </div>
                  </div>

                  <div style={{ background: 'oklch(11% 0.02 250)', padding: '0.625rem 0.75rem', borderRadius: '6px', border: '1px solid oklch(20% 0.02 250)' }}>
                    <div style={{ fontSize: '0.6875rem', color: 'oklch(60% 0.02 250)', textTransform: 'uppercase' }}>Trafienie stanu optymalnego</div>
                    <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'oklch(82% 0.16 150)', marginTop: '0.2rem' }}>
                      {qRecord.ground_state_prob ? `${(qRecord.ground_state_prob * 100).toFixed(1)}%` : '—'}
                      <span style={{ fontSize: '0.6875rem', color: 'oklch(60% 0.02 250)', fontWeight: 400, marginLeft: '0.35rem' }}>
                        (vs {qRecord.random_guess_prob ? `${(qRecord.random_guess_prob * 100).toFixed(1)}%` : '—'} losowo)
                      </span>
                    </div>
                  </div>

                  <div style={{ background: 'oklch(11% 0.02 250)', padding: '0.625rem 0.75rem', borderRadius: '6px', border: '1px solid oklch(20% 0.02 250)' }}>
                    <div style={{ fontSize: '0.6875rem', color: 'oklch(60% 0.02 250)', textTransform: 'uppercase' }}>Inicjalizacja i przeszukiwanie</div>
                    <div style={{ fontSize: '0.9375rem', fontWeight: 700, color: 'oklch(92% 0.01 250)', marginTop: '0.2rem' }}>
                      TQA Adiabatic Ramp ({qRecord.n_evaluations} prób)
                    </div>
                  </div>
                </div>

                {/* State measurement distribution bar */}
                {sortedSamples.length > 0 && (
                  <div>
                    <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'oklch(65% 0.02 250)', marginBottom: '0.5rem' }}>
                      Rozkład interferencji kwantowej (pomiary stanów końcowych):
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.375rem' }}>
                      {sortedSamples.map(([bits, cnt], idx) => {
                        const pct = ((cnt as number) / totalShots) * 100
                        const isBest = idx === 0
                        return (
                          <div key={bits} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '0.75rem' }}>
                            <span style={{ fontFamily: 'monospace', width: '50px', color: isBest ? 'oklch(85% 0.15 150)' : 'oklch(70% 0.02 250)', fontWeight: isBest ? 700 : 400 }}>
                              |{bits}⟩
                            </span>
                            <div style={{ flex: 1, height: '8px', background: 'oklch(18% 0.02 250)', borderRadius: '4px', overflow: 'hidden' }}>
                              <div style={{
                                width: `${pct}%`,
                                height: '100%',
                                background: isBest ? 'oklch(68% 0.18 150)' : 'oklch(45% 0.08 240)',
                                borderRadius: '4px',
                              }} />
                            </div>
                            <span style={{ width: '45px', textAlign: 'right', color: 'oklch(80% 0.02 250)', fontWeight: 600 }}>
                              {pct.toFixed(1)}%
                            </span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            )
          })()}

          {/* Benchmark comparison if available */}
          {comparisonResult && (
            <div style={{
              marginBottom: '1.25rem',
              padding: '1rem',
              background: 'var(--bg-surface)',
              borderRadius: 'var(--radius-sm)',
              border: '1px solid var(--border-subtle)',
            }}>
              <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.5rem' }}>
                Porównanie solverów (Benchmark)
              </div>
              <table style={{ width: '100%', fontSize: '0.8125rem', borderCollapse: 'collapse' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-subtle)', color: 'var(--text-muted)', textAlign: 'left' }}>
                    <th style={{ padding: '0.375rem 0' }}>Solver</th>
                    <th style={{ padding: '0.375rem 0' }}>Cel</th>
                    <th style={{ padding: '0.375rem 0' }}>Czas</th>
                    <th style={{ padding: '0.375rem 0' }}>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style={{ padding: '0.375rem 0', fontWeight: 600 }}>{result.source || 'Główny'}</td>
                    <td style={{ padding: '0.375rem 0' }}>{result.objective_value}</td>
                    <td style={{ padding: '0.375rem 0' }}>{result.solve_time_seconds?.toFixed(3)}s</td>
                    <td style={{ padding: '0.375rem 0' }}>{result.math_status}</td>
                  </tr>
                  <tr>
                    <td style={{ padding: '0.375rem 0', fontWeight: 600 }}>{comparisonResult.source || 'Drugi'}</td>
                    <td style={{ padding: '0.375rem 0' }}>{comparisonResult.objective_value}</td>
                    <td style={{ padding: '0.375rem 0' }}>{comparisonResult.solve_time_seconds?.toFixed(3)}s</td>
                    <td style={{ padding: '0.375rem 0' }}>{comparisonResult.math_status}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          )}

          {/* Verification details */}
          {verification && (
            <div>
              <div style={{ fontSize: '0.8125rem', fontWeight: 700, color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                Raport niezależnego audytu ograniczeń
              </div>
              <p style={{ fontSize: '0.8125rem', color: 'var(--text-muted)', margin: '0 0 0.75rem 0' }}>
                Weryfikator przelicza funkcję celu i wszystkie ograniczenia od zera, bez zaufania do solvera.
              </p>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {verification.constraint_results.map((c) => (
                  <div
                    key={c.constraint_id}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.5rem 0.75rem',
                      borderRadius: 'var(--radius-sm)',
                      background: c.satisfied ? 'var(--status-verified-bg)' : 'var(--status-rejected-bg)',
                      border: `1px solid ${c.satisfied ? 'var(--status-verified-border)' : 'var(--status-rejected-border)'}`,
                      fontSize: '0.8125rem',
                    }}
                  >
                    <span style={{ fontWeight: 500, color: 'var(--text-primary)' }}>
                      Ograniczenie: {c.constraint_id} {c.note ? `(${c.note})` : ''}
                    </span>
                    <span style={{
                      fontWeight: 600,
                      color: c.satisfied ? 'var(--status-verified-text)' : 'var(--status-rejected-text)',
                    }}>
                      {c.satisfied ? 'Spełnione' : 'Naruszone'}
                    </span>
                  </div>
                ))}
              </div>

              {verification.limitations && verification.limitations.length > 0 && (
                <div style={{ marginTop: '1rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase' }}>
                    Ograniczenia i uwagi metodologiczne
                  </div>
                  <ul style={{ margin: '0.25rem 0 0 1.25rem', fontSize: '0.8125rem', color: 'var(--text-secondary)' }}>
                    {verification.limitations.map((lim, idx) => (
                      <li key={idx}>{lim}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
