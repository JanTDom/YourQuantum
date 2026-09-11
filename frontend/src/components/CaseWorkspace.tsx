import React, { useState } from 'react'
import { DecisionCase, CaseUnknown, CaseOption } from '../api'

interface CaseWorkspaceProps {
  decisionCase: DecisionCase
  onAnswerUnknown: (unknownId: string, answer: string) => void
  onUpdateCase: (updatedCase: DecisionCase) => void
  onProceedToModeling: () => void
  onBackToEdit: () => void
  isLoading: boolean
}

const DEFAULT_PRIORITY_TOKENS = [
  '💰 Niższy koszt / Finanse',
  '🌿 Spokój i komfort psychiczny',
  '🛡️ Bezpieczeństwo i stabilność',
  '⏱️ Oszczędność czasu i wygoda',
  '🚀 Rozwój i perspektywy na przyszłość',
  '⚖️ Balans życiowy i swoboda',
]

export const CaseWorkspace: React.FC<CaseWorkspaceProps> = ({
  decisionCase,
  onAnswerUnknown,
  onUpdateCase,
  onProceedToModeling,
  onBackToEdit,
  isLoading,
}) => {
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [showAddOption, setShowAddOption] = useState(false)
  const [newOptionTitle, setNewOptionTitle] = useState('')
  const [newOptionDesc, setNewOptionDesc] = useState('')
  const [showAddPriority, setShowAddPriority] = useState(false)
  const [customPriority, setCustomPriority] = useState('')

  const handleAnswerChange = (id: string, text: string): void => {
    setAnswers((prev) => ({ ...prev, [id]: text }))
  }

  const handleSaveAnswer = (unk: CaseUnknown): void => {
    const val = answers[unk.id] || ''
    if (val.trim()) onAnswerUnknown(unk.id, val.trim())
  }

  const selectedTokens = decisionCase.selected_priority_tokens || []
  const availableTokens =
    decisionCase.priority_tokens && decisionCase.priority_tokens.length > 0
      ? decisionCase.priority_tokens
      : DEFAULT_PRIORITY_TOKENS

  const handleTogglePriority = (token: string): void => {
    const next = selectedTokens.includes(token)
      ? selectedTokens.filter((t) => t !== token)
      : [...selectedTokens, token]
    onUpdateCase({
      ...decisionCase,
      selected_priority_tokens: next,
    })
  }

  const handleAddCustomPriority = (): void => {
    const trimmed = customPriority.trim()
    if (!trimmed) return
    const formattedToken = trimmed.startsWith('🎯') || trimmed.startsWith('✨') ? trimmed : `🎯 ${trimmed}`
    const updatedAvailable = availableTokens.includes(formattedToken)
      ? availableTokens
      : [...availableTokens, formattedToken]
    const updatedSelected = selectedTokens.includes(formattedToken)
      ? selectedTokens
      : [...selectedTokens, formattedToken]

    onUpdateCase({
      ...decisionCase,
      priority_tokens: updatedAvailable,
      selected_priority_tokens: updatedSelected,
    })
    setCustomPriority('')
    setShowAddPriority(false)
  }

  const handleAddOptionSubmit = (): void => {
    const trimmedTitle = newOptionTitle.trim()
    if (!trimmedTitle) return
    const newOpt: CaseOption = {
      id: `opt_${Date.now()}`,
      title: trimmedTitle,
      description: newOptionDesc.trim() || 'Dodatkowa opcja wprowadzona przez użytkownika',
      pros: [],
      cons: [],
      attributes: {},
    }
    onUpdateCase({
      ...decisionCase,
      options: [...decisionCase.options, newOpt],
    })
    setNewOptionTitle('')
    setNewOptionDesc('')
    setShowAddOption(false)
  }

  const handleRemoveOption = (optId: string): void => {
    if (decisionCase.options.length <= 2) return
    onUpdateCase({
      ...decisionCase,
      options: decisionCase.options.filter((o) => o.id !== optId),
    })
  }

  const unresolvedCount = decisionCase.unknowns.filter((u) => !u.is_resolved).length

  return (
    <div style={{ minHeight: '100vh', background: 'oklch(6% 0.01 250)', position: 'relative', overflow: 'hidden' }}>

      {/* ── Background photo ──────────────────────────────────── */}
      <img
        src="/images/scientist-holo.jpg"
        alt=""
        aria-hidden="true"
        style={{
          position: 'absolute', inset: 0, width: '100%', height: '100%',
          objectFit: 'cover', objectPosition: 'center right',
          opacity: 0.12, filter: 'saturate(0.6) brightness(0.55)',
          pointerEvents: 'none', zIndex: 0,
        }}
      />
      {/* Gradient overlay: dark on left for readability */}
      <div aria-hidden="true" style={{
        position: 'absolute', inset: 0, zIndex: 0,
        background: 'linear-gradient(to right, oklch(6% 0.01 250 / 0.97) 50%, oklch(6% 0.01 250 / 0.75) 100%)',
      }} />

      {/* ── Content ───────────────────────────────────────────── */}
      <div style={{
        position: 'relative', zIndex: 1,
        maxWidth: '900px', margin: '0 auto',
        padding: 'clamp(1.5rem, 4vw, 3rem) clamp(1rem, 3vw, 2rem)',
        animation: 'wsPageIn 0.55s cubic-bezier(0.22,1,0.36,1) both',
      }}>

        {/* Step indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '2rem' }}>
          {['Sytuacja opisana', 'Zatwierdź i oblicz', 'Wynik'].map((label, i) => (
            <React.Fragment key={label}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: '0.5rem',
                fontSize: '0.8125rem',
                fontWeight: i === 0 ? 700 : 500,
                color: i === 0 ? 'oklch(75% 0.12 80)' : 'oklch(38% 0.015 250)',
              }}>
                <span style={{
                  width: '24px', height: '24px', borderRadius: '50%',
                  background: i === 0 ? 'oklch(75% 0.12 80)' : 'oklch(17% 0.025 250)',
                  border: i === 0 ? 'none' : '1px solid oklch(26% 0.03 250)',
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  fontSize: '0.6875rem', fontWeight: 900,
                  color: i === 0 ? 'oklch(6% 0.01 250)' : 'oklch(38% 0.015 250)',
                  flexShrink: 0,
                }}>{i + 1}</span>
                {label}
              </div>
              {i < 2 && <div style={{ flex: 1, height: '1px', background: 'oklch(22% 0.025 250)' }} />}
            </React.Fragment>
          ))}
        </div>

        {/* Main card */}
        <div style={{
          background: 'oklch(10% 0.02 250 / 0.88)',
          backdropFilter: 'blur(20px) saturate(1.3)',
          WebkitBackdropFilter: 'blur(20px) saturate(1.3)',
          borderRadius: '14px',
          border: '1px solid oklch(20% 0.025 250)',
          boxShadow: '0 0 80px oklch(0% 0 0 / 0.5), 0 0 160px oklch(62% 0.18 240 / 0.04)',
          overflow: 'hidden',
        }}>
          <div style={{ height: '2px', background: 'linear-gradient(to right, transparent, oklch(75% 0.12 80) 30%, oklch(62% 0.18 240) 70%, transparent)' }} />

          <div style={{ padding: 'clamp(1.5rem, 3vw, 2.5rem)' }}>

            {/* Header */}
            <div style={{
              display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
              marginBottom: '2rem', gap: '1rem',
            }}>
              <div>
                <p style={{ margin: '0 0 0.375rem 0', fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.12em', textTransform: 'uppercase', color: 'oklch(75% 0.12 80)' }}>
                  Krok 1 z 2 — Twoja sytuacja
                </p>
                <h2 style={{ margin: '0 0 0.5rem 0', fontSize: 'clamp(1.25rem, 3vw, 1.75rem)', fontWeight: 900, color: 'oklch(97% 0.008 250)', letterSpacing: '-0.03em', lineHeight: 1.1 }}>
                  {decisionCase.title}
                </h2>
                <p style={{ margin: 0, fontSize: '0.9375rem', color: 'oklch(62% 0.02 250)', lineHeight: 1.6 }}>
                  System zrozumiał Twoją sytuację. Sprawdź opcje, zaznacz priorytety i odpowiedz na ewentualne pytania.
                </p>
              </div>
              <button
                onClick={onBackToEdit}
                style={{
                  background: 'none', border: '1px solid oklch(28% 0.025 250)',
                  borderRadius: '6px', padding: '0.4375rem 0.875rem',
                  fontSize: '0.8125rem', color: 'oklch(60% 0.018 250)',
                  cursor: 'pointer', flexShrink: 0, whiteSpace: 'nowrap',
                  transition: 'border-color 200ms, color 200ms',
                }}
              >
                ← Zmień opis
              </button>
            </div>

            {/* Options grid with photo accents */}
            <div style={{ marginBottom: '2.25rem' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.875rem' }}>
                <h3 style={{ fontSize: '0.875rem', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'oklch(54% 0.018 250)', margin: 0 }}>
                  {decisionCase.options.length > 1
                    ? `Rozważane opcje (${decisionCase.options.length})`
                    : 'Opcja do zbadania'}
                </h3>
                {!showAddOption && (
                  <button
                    type="button"
                    onClick={() => setShowAddOption(true)}
                    style={{
                      background: 'none',
                      border: '1px dashed oklch(35% 0.03 250)',
                      color: 'oklch(75% 0.12 80)',
                      fontSize: '0.8125rem',
                      fontWeight: 600,
                      borderRadius: '6px',
                      padding: '0.3rem 0.65rem',
                      cursor: 'pointer',
                      transition: 'border-color 200ms, color 200ms',
                    }}
                  >
                    + Dodaj kolejną opcję / alternatywę
                  </button>
                )}
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(230px, 1fr))', gap: '1rem' }}>
                {decisionCase.options.map((opt, i) => (
                  <div key={opt.id} style={{
                    background: 'oklch(13% 0.022 250)',
                    border: '1px solid oklch(22% 0.025 250)',
                    borderRadius: '10px', overflow: 'hidden',
                    transition: 'border-color 250ms ease',
                    position: 'relative',
                  }}>
                    {/* Mini color accent per option */}
                    <div style={{ height: '3px', background: i === 0 ? 'oklch(75% 0.12 80)' : i === 1 ? 'oklch(62% 0.18 240)' : 'oklch(72% 0.18 152)' }} />
                    <div style={{ padding: '1.125rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.375rem' }}>
                        <div style={{ fontSize: '0.6875rem', fontWeight: 700, color: 'oklch(54% 0.018 250)', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                          Opcja {i + 1}
                        </div>
                        {decisionCase.options.length > 2 && (
                          <button
                            type="button"
                            title="Usuń tę opcję z porównania"
                            onClick={() => handleRemoveOption(opt.id)}
                            style={{
                              background: 'none',
                              border: 'none',
                              color: 'oklch(45% 0.02 250)',
                              cursor: 'pointer',
                              fontSize: '1rem',
                              lineHeight: 1,
                              padding: '0.1rem 0.3rem',
                            }}
                          >
                            ×
                          </button>
                        )}
                      </div>
                      <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '1.0625rem', fontWeight: 700, color: 'oklch(97% 0.008 250)', letterSpacing: '-0.02em' }}>
                        {opt.title}
                      </h4>
                      {opt.description && (
                        <p style={{ margin: 0, fontSize: '0.875rem', color: 'oklch(60% 0.018 250)', lineHeight: 1.55 }}>
                          {opt.description}
                        </p>
                      )}
                    </div>
                  </div>
                ))}

                {/* Add Option Box (when open) */}
                {showAddOption && (
                  <div style={{
                    background: 'oklch(15% 0.03 250)',
                    border: '1px dashed oklch(75% 0.12 80 / 0.5)',
                    borderRadius: '10px',
                    padding: '1.125rem',
                  }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'oklch(75% 0.12 80)', marginBottom: '0.5rem' }}>
                      Nowa opcja lub alternatywa (np. odrzucenie obu, trzecia droga):
                    </div>
                    <input
                      type="text"
                      placeholder="Nazwa opcji (np. Pozostanie na starym miejscu)..."
                      value={newOptionTitle}
                      onChange={(e) => setNewOptionTitle(e.target.value)}
                      style={{ marginBottom: '0.5rem', fontSize: '0.875rem' }}
                      autoFocus
                    />
                    <textarea
                      placeholder="Krótki opis / założenia (opcjonalnie)..."
                      value={newOptionDesc}
                      onChange={(e) => setNewOptionDesc(e.target.value)}
                      rows={2}
                      style={{ marginBottom: '0.75rem', fontSize: '0.8125rem', resize: 'none' }}
                    />
                    <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
                      <button
                        type="button"
                        onClick={() => { setShowAddOption(false); setNewOptionTitle(''); setNewOptionDesc(''); }}
                        style={{
                          background: 'none', border: '1px solid oklch(30% 0.025 250)',
                          borderRadius: '6px', padding: '0.35rem 0.75rem', fontSize: '0.8125rem',
                          color: 'oklch(65% 0.02 250)', cursor: 'pointer',
                        }}
                      >
                        Anuluj
                      </button>
                      <button
                        type="button"
                        onClick={handleAddOptionSubmit}
                        style={{
                          background: 'oklch(75% 0.12 80)', color: 'oklch(6% 0.01 250)',
                          border: 'none', borderRadius: '6px', padding: '0.35rem 0.85rem',
                          fontSize: '0.8125rem', fontWeight: 700, cursor: 'pointer',
                        }}
                      >
                        Dodaj do porównania
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* ── PRIORITY PILLS (Token selection) ─────────────────────────── */}
            <div style={{
              marginBottom: '2.25rem',
              padding: '1.25rem',
              borderRadius: '10px',
              background: 'oklch(12% 0.025 250)',
              border: '1px solid oklch(24% 0.03 250)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: '0.375rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <h3 style={{
                  fontSize: '0.875rem',
                  fontWeight: 800,
                  letterSpacing: '0.08em',
                  textTransform: 'uppercase',
                  color: 'oklch(75% 0.12 80)',
                  margin: 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                }}>
                  <span>🎯</span> Na czym zależy Ci najbardziej w tej decyzji?
                </h3>
                <span style={{ fontSize: '0.75rem', color: 'oklch(58% 0.02 250)' }}>
                  {selectedTokens.length > 0
                    ? `Aktywne priorytety: ${selectedTokens.length}`
                    : 'Kliknij, aby nadać wybranym wagę decydującą'}
                </span>
              </div>
              <p style={{ margin: '0 0 1rem 0', fontSize: '0.8125rem', color: 'oklch(65% 0.02 250)', lineHeight: 1.55 }}>
                Wybierz najważniejsze wartości dla tego dylematu. Algorytm optymalizacyjny uwzględni je z najwyższą wagą podczas formalnego modelowania i szukania rozwiązania.
              </p>

              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.625rem', alignItems: 'center' }}>
                {availableTokens.map((tok) => {
                  const isSelected = selectedTokens.includes(tok)
                  return (
                    <button
                      key={tok}
                      type="button"
                      onClick={() => handleTogglePriority(tok)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        padding: '0.5rem 0.9rem',
                        borderRadius: '20px',
                        fontSize: '0.84rem',
                        fontWeight: isSelected ? 700 : 500,
                        background: isSelected ? 'oklch(75% 0.12 80 / 0.16)' : 'oklch(16% 0.025 250)',
                        border: isSelected
                          ? '1px solid oklch(75% 0.12 80)'
                          : '1px solid oklch(26% 0.025 250)',
                        color: isSelected ? 'oklch(95% 0.05 80)' : 'oklch(75% 0.02 250)',
                        cursor: 'pointer',
                        transition: 'all 180ms ease',
                        boxShadow: isSelected ? '0 0 16px oklch(75% 0.12 80 / 0.25)' : 'none',
                      }}
                    >
                      <span>{tok}</span>
                      {isSelected ? (
                        <span style={{
                          width: '18px', height: '18px', borderRadius: '50%',
                          background: 'oklch(75% 0.12 80)', color: 'oklch(6% 0.01 250)',
                          display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                          fontSize: '0.68rem', fontWeight: 900,
                        }}>✓</span>
                      ) : (
                        <span style={{ color: 'oklch(45% 0.02 250)', fontSize: '0.8rem' }}>+</span>
                      )}
                    </button>
                  )
                })}

                {/* Button to add custom priority */}
                {!showAddPriority ? (
                  <button
                    type="button"
                    onClick={() => setShowAddPriority(true)}
                    style={{
                      background: 'none',
                      border: '1px dashed oklch(34% 0.025 250)',
                      borderRadius: '20px',
                      padding: '0.45rem 0.8rem',
                      fontSize: '0.78rem',
                      color: 'oklch(60% 0.02 250)',
                      cursor: 'pointer',
                    }}
                  >
                    + Wpisz własny priorytet
                  </button>
                ) : (
                  <div style={{ display: 'inline-flex', gap: '0.35rem', alignItems: 'center' }}>
                    <input
                      type="text"
                      placeholder="Np. Bliskość rodziny..."
                      value={customPriority}
                      onChange={(e) => setCustomPriority(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && handleAddCustomPriority()}
                      style={{
                        padding: '0.4rem 0.75rem',
                        fontSize: '0.8125rem',
                        borderRadius: '20px',
                        width: '180px',
                      }}
                      autoFocus
                    />
                    <button
                      type="button"
                      onClick={handleAddCustomPriority}
                      style={{
                        background: 'oklch(75% 0.12 80)', color: 'oklch(6% 0.01 250)',
                        border: 'none', borderRadius: '20px', padding: '0.4rem 0.75rem',
                        fontSize: '0.75rem', fontWeight: 700, cursor: 'pointer',
                      }}
                    >
                      Dodaj
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowAddPriority(false)}
                      style={{
                        background: 'none', border: 'none', color: 'oklch(50% 0.02 250)',
                        fontSize: '1rem', cursor: 'pointer', padding: '0 0.3rem',
                      }}
                    >
                      ×
                    </button>
                  </div>
                )}
              </div>
            </div>

            {/* Clarification questions */}
            {decisionCase.unknowns.length > 0 && (
              <div style={{
                marginBottom: '2rem',
                background: 'oklch(16% 0.04 70 / 0.5)',
                border: '1px solid oklch(36% 0.09 72 / 0.5)',
                borderRadius: '10px', padding: '1.375rem',
              }}>
                <h3 style={{ fontSize: '0.9375rem', fontWeight: 800, color: 'oklch(80% 0.14 72)', margin: '0 0 0.375rem 0' }}>
                  {unresolvedCount > 0
                    ? `Mam ${unresolvedCount} ${unresolvedCount === 1 ? 'pytanie' : 'pytania'} — żeby trafniej policzyć:`
                    : '✓ Wszystkie pytania uzupełnione — gotowe do obliczenia'}
                </h3>
                <p style={{ fontSize: '0.8125rem', color: 'oklch(66% 0.02 250)', margin: '0 0 1rem 0' }}>
                  Im dokładniej odpiszesz, tym lepszy wynik. Możesz też pominąć.
                </p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                  {decisionCase.unknowns.map((unk) => (
                    <div key={unk.id} style={{
                      background: 'oklch(10% 0.02 250 / 0.7)',
                      border: '1px solid oklch(22% 0.025 250)',
                      borderRadius: '8px', padding: '1rem',
                    }}>
                      <div style={{ fontWeight: 600, fontSize: '0.9375rem', color: 'oklch(88% 0.015 250)', marginBottom: '0.25rem' }}>
                        {unk.question}
                      </div>
                      {unk.impact_description && (
                        <div style={{ fontSize: '0.75rem', color: 'oklch(54% 0.018 250)', marginBottom: '0.625rem' }}>
                          Dlaczego pytam: {unk.impact_description}
                        </div>
                      )}
                      {unk.answer ? (
                        <div style={{
                          padding: '0.375rem 0.75rem',
                          background: 'oklch(16% 0.04 170)', border: '1px solid oklch(35% 0.08 168)',
                          borderRadius: '6px', fontSize: '0.8125rem', color: 'oklch(78% 0.14 168)',
                        }}>
                          ✓ {unk.answer}
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                          <input
                            type="text"
                            placeholder="Twoja odpowiedź..."
                            value={answers[unk.id] || ''}
                            onChange={(e) => handleAnswerChange(unk.id, e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSaveAnswer(unk)}
                            style={{ flex: 1, fontSize: '0.875rem' }}
                          />
                          <button
                            type="button"
                            onClick={() => handleSaveAnswer(unk)}
                            style={{
                              background: 'oklch(75% 0.12 80)', color: 'oklch(6% 0.01 250)',
                              border: 'none', borderRadius: '6px', padding: '0 1rem',
                              fontSize: '0.875rem', fontWeight: 700, cursor: 'pointer', whiteSpace: 'nowrap',
                            }}
                          >OK</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Tradeoffs */}
            {decisionCase.tradeoffs.length > 0 && (
              <div style={{ marginBottom: '2rem' }}>
                <h3 style={{ fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.1em', textTransform: 'uppercase', color: 'oklch(54% 0.018 250)', marginBottom: '0.75rem' }}>
                  Na co warto zwrócić uwagę:
                </h3>
                {decisionCase.tradeoffs.map((tr, idx) => (
                  <div key={idx} style={{
                    padding: '0.875rem 1rem', borderRadius: '8px',
                    background: 'oklch(13% 0.022 250)', border: '1px solid oklch(22% 0.025 250)',
                    fontSize: '0.875rem', color: 'oklch(68% 0.02 250)', marginBottom: '0.5rem', lineHeight: 1.5,
                  }}>
                    ⚖️ {tr.description} — zyskujesz <strong style={{ color: 'oklch(88% 0.015 250)' }}>{tr.gain}</strong>, rezygnujesz z <strong style={{ color: 'oklch(88% 0.015 250)' }}>{tr.sacrifice}</strong>.
                  </div>
                ))}
              </div>
            )}

            {/* Action */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', paddingTop: '1.25rem', borderTop: '1px solid oklch(18% 0.022 250)' }}>
              <button
                type="button"
                onClick={onProceedToModeling}
                disabled={isLoading}
                style={{
                  background: isLoading ? 'oklch(50% 0.08 80)' : 'oklch(75% 0.12 80)',
                  color: 'oklch(5% 0.01 250)', border: 'none',
                  padding: '0.9375rem 2rem', borderRadius: '8px',
                  fontWeight: 800, fontSize: '1rem', cursor: isLoading ? 'not-allowed' : 'pointer',
                  letterSpacing: '-0.015em', display: 'inline-flex', alignItems: 'center', gap: '0.5rem',
                  boxShadow: isLoading ? 'none' : '0 0 28px oklch(75% 0.12 80 / 0.4)',
                  transition: 'background 200ms, box-shadow 200ms',
                }}
              >
                {isLoading ? 'Przygotowuję...' : 'Wygląda dobrze — szukaj najlepszej opcji →'}
              </button>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        @keyframes wsPageIn {
          from { opacity: 0; transform: translateY(28px); }
          to   { opacity: 1; transform: translateY(0); }
        }
      `}</style>
    </div>
  )
}
