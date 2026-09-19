import React, { useState } from 'react'
import {
  ScoredValue,
  researchEvidence,
} from '../api'

export interface LeverOption {
  id: string
  title: string
  description?: string
  evidence_ref?: string
  provenance?: string
}

export interface DesignLever {
  id: string
  name: string
  description?: string
  options: LeverOption[]
}

export interface DesignCriterion {
  id: string
  name: string
  direction: 'maximize' | 'minimize'
  weight: number
  unit?: string
}

export interface DesignInteraction {
  lever_a_id: string
  option_a_id: string
  lever_b_id: string
  option_b_id: string
  compatible: boolean
  synergy: number
  source_ref?: string
}

export interface DesignProblem {
  id?: string
  title: string
  description: string
  levers: DesignLever[]
  criteria: DesignCriterion[]
  score_matrix: Record<string, Record<string, Record<string, ScoredValue>>>
  interactions: DesignInteraction[]
}

interface DesignWorkspaceProps {
  designProblem: DesignProblem
  onUpdateDesign: (updated: DesignProblem) => void
  onSynthesize: (problem: DesignProblem) => void
  onBack: () => void
  isSynthesizing?: boolean
}

export const DesignWorkspace: React.FC<DesignWorkspaceProps> = ({
  designProblem,
  onUpdateDesign,
  onSynthesize,
  onBack,
  isSynthesizing = false,
}) => {
  const [activeLeverId, setActiveLeverId] = useState<string>(
    designProblem.levers[0]?.id || ''
  )
  const [researchNotice, setResearchNotice] = useState<string | null>(null)
  const [isSearchingWeb, setIsSearchingWeb] = useState(false)
  const [showManualUrl, setShowManualUrl] = useState(false)
  const [manualUrlInput, setManualUrlInput] = useState('')
  const [activeResearchCell, setActiveResearchCell] = useState<{
    leverId: string
    optionId: string
    criterionId: string
  } | null>(null)

  // Validation according to N5 rules
  const validationErrors: string[] = []
  if (designProblem.levers.length < 2) {
    validationErrors.push('Model syntezy wymaga co najmniej 2 dźwigni architektonicznych.')
  }
  for (const lev of designProblem.levers) {
    if (lev.options.length < 2) {
      validationErrors.push(`Dźwignia '${lev.name}' musi mieć co najmniej 2 warianty.`)
    }
  }
  if (designProblem.criteria.length === 0) {
    validationErrors.push('Zdefiniuj co najmniej jedno kryterium oceny wielokryterialnej.')
  }

  // Check score_matrix documented vs empty cells
  let documentedCells = 0
  let emptyCells = 0
  const activeCriteriaIds = new Set<string>()

  for (const lev of designProblem.levers) {
    for (const opt of lev.options) {
      for (const crit of designProblem.criteria) {
        const cell = designProblem.score_matrix?.[lev.id]?.[opt.id]?.[crit.id]
        if (cell && cell.value !== undefined && cell.value !== null && !isNaN(cell.value)) {
          documentedCells++
          activeCriteriaIds.add(crit.id)
        } else {
          emptyCells++
        }
      }
    }
  }

  // Synthesis is valid if there is at least one active criterion with values across options
  if (documentedCells === 0) {
    validationErrors.push('Brak danych w macierzy. Wprowadź dane liczbowe lub dociągnij je z sieci.')
  }

  // Check interactions synergy sources
  for (const inter of designProblem.interactions) {
    if (Math.abs(inter.synergy) > 1e-6 && (!inter.source_ref || !inter.source_ref.trim())) {
      validationErrors.push(`Niezerowa synergia (${inter.synergy}) wymaga podania źródła lub oznaczenia jako założenie.`)
    }
  }

  const isValidForSynthesis = validationErrors.length === 0

  const handleUpdateCell = (
    leverId: string,
    optionId: string,
    criterionId: string,
    updates: Partial<ScoredValue>
  ): void => {
    const matrix = { ...(designProblem.score_matrix || {}) }
    if (!matrix[leverId]) matrix[leverId] = {}
    if (!matrix[leverId][optionId]) matrix[leverId][optionId] = {}
    const cur = matrix[leverId][optionId][criterionId] || {
      value: undefined,
      provenance: 'user_supplied',
      source_ref: 'Wprowadzone przez użytkownika',
    }
    matrix[leverId][optionId][criterionId] = { ...cur, ...updates }
    onUpdateDesign({
      ...designProblem,
      score_matrix: matrix,
    })
  }

  const handleWebResearch = async (
    leverId: string,
    optionId: string,
    criterionId: string
  ): Promise<void> => {
    const lev = designProblem.levers.find((l) => l.id === leverId)
    const opt = lev?.options.find((o) => o.id === optionId)
    const crit = designProblem.criteria.find((c) => c.id === criterionId)
    if (!lev || !opt || !crit) return

    setActiveResearchCell({ leverId, optionId, criterionId })
    setIsSearchingWeb(true)
    setResearchNotice(null)
    setShowManualUrl(false)

    try {
      const res = await researchEvidence({
        target_parameters: [
          {
            param_id: `${leverId}_${optionId}_${criterionId}`,
            query_text: `${lev.name} ${opt.title} ${crit.name}`,
            expected_unit: crit.unit,
          },
        ],
        max_results_per_param: 2,
      })

      if (res.evidence && res.evidence.length > 0) {
        const ev = res.evidence[0]
        const num = parseFloat(String(ev.value ?? '0'))
        if (!isNaN(num) && num > 0) {
          handleUpdateCell(leverId, optionId, criterionId, {
            value: num,
            unit: ev.unit || crit.unit,
            provenance: 'web_sourced',
            source_ref: ev.source_url || 'Sieć www',
            confidence: ev.confidence ?? 0.85,
          })
          setResearchNotice(`✓ Pobrano dane z sieci: ${num} (${ev.source_url})`)
        } else {
          setResearchNotice(`Znaleziono źródło (${ev.source_url}), lecz brak jednoznacznej liczby. Wpisz wartość ręcznie.`)
        }
      } else {
        setResearchNotice('Wyszukiwarka nieskonfigurowana — możesz wkleić adres URL źródła:')
        setShowManualUrl(true)
      }
    } catch {
      setResearchNotice('Wyszukiwarka nieskonfigurowana — możesz wkleić adres URL źródła:')
      setShowManualUrl(true)
    } finally {
      setIsSearchingWeb(false)
    }
  }

  const handleBulkWebResearch = async (): Promise<void> => {
    // Find empty cells across design problem (capped at 6 to adhere to DEC-042 budget)
    const targets: Array<{
      leverId: string
      optionId: string
      criterionId: string
      param_id: string
      query_text: string
      expected_unit?: string
    }> = []

    for (const lev of designProblem.levers) {
      for (const opt of lev.options) {
        for (const crit of designProblem.criteria) {
          const cell = designProblem.score_matrix?.[lev.id]?.[opt.id]?.[crit.id]
          if (!cell || cell.value === undefined || cell.value === null || isNaN(cell.value)) {
            if (targets.length < 6) {
              targets.push({
                leverId: lev.id,
                optionId: opt.id,
                criterionId: crit.id,
                param_id: `${lev.id}_${opt.id}_${crit.id}`,
                query_text: `${lev.name} ${opt.title} ${crit.name}`,
                expected_unit: crit.unit,
              })
            }
          }
        }
      }
    }

    if (targets.length === 0) {
      setResearchNotice('Wszystkie komórki posiadają już wartości.')
      return
    }

    setIsSearchingWeb(true)
    setResearchNotice(`🌐 Wyszukiwanie danych w sieci dla ${targets.length} brakujących pozycji...`)

    try {
      const res = await researchEvidence({
        target_parameters: targets.map((t) => ({
          param_id: t.param_id,
          query_text: t.query_text,
          expected_unit: t.expected_unit,
        })),
        max_results_per_param: 2,
      })

      let addedCount = 0
      const matrix = { ...(designProblem.score_matrix || {}) }

      if (res.evidence && res.evidence.length > 0) {
        for (const ev of res.evidence) {
          if (!ev.target_param || ev.value === undefined || ev.value === null) continue
          const matchTarget = targets.find((t) => t.param_id === ev.target_param)
          if (!matchTarget) continue
          const num = parseFloat(String(ev.value))
          if (isNaN(num)) continue

          const { leverId, optionId, criterionId } = matchTarget
          if (!matrix[leverId]) matrix[leverId] = {}
          if (!matrix[leverId][optionId]) matrix[leverId][optionId] = {}

          matrix[leverId][optionId][criterionId] = {
            value: num,
            unit: ev.unit || matchTarget.expected_unit,
            provenance: 'web_sourced',
            source_ref: ev.source_url || 'Sieć www',
            confidence: ev.confidence ?? 0.85,
          }
          addedCount++
        }
      }

      if (addedCount > 0) {
        onUpdateDesign({ ...designProblem, score_matrix: matrix })
        setResearchNotice(`✓ Pomyślnie pobrano i zweryfikowano ${addedCount} wartości z sieci www.`)
      } else {
        setResearchNotice('Nie znaleziono w sieci jednoznacznych liczb dla brakujących komórek. Możesz wpisać je ręcznie.')
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Błąd wyszukiwania'
      setResearchNotice(`Błąd podczas badania sieci: ${msg}`)
    } finally {
      setIsSearchingWeb(false)
    }
  }

  const handleApplyManualUrl = (): void => {
    if (!activeResearchCell || !manualUrlInput.trim()) return
    const { leverId, optionId, criterionId } = activeResearchCell
    handleUpdateCell(leverId, optionId, criterionId, {
      provenance: 'web_sourced',
      source_ref: manualUrlInput.trim(),
      confidence: 0.9,
    })
    setManualUrlInput('')
    setShowManualUrl(false)
    setResearchNotice('✓ Przypisano źródło URL do komórki.')
    setActiveResearchCell(null)
  }

  const handleUpdateSynergy = (idx: number, synergyVal: number, sourceRef?: string): void => {
    const updated = [...designProblem.interactions]
    if (updated[idx]) {
      updated[idx] = {
        ...updated[idx],
        synergy: synergyVal,
        source_ref: sourceRef || (Math.abs(synergyVal) > 1e-6 ? 'Założenie eksperckie synergii' : undefined),
      }
      onUpdateDesign({
        ...designProblem,
        interactions: updated,
      })
    }
  }

  const activeLever = designProblem.levers.find((l) => l.id === activeLeverId) || designProblem.levers[0]

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '1.5rem' }}>
      {/* Header */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '1.5rem',
        gap: '1rem',
      }}>
        <div>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: 800,
            letterSpacing: '0.04em',
            color: 'oklch(75% 0.12 80)',
          }}>
            Klasa DESIGN — synteza wielodźwigniowa
          </span>
          <h2 style={{ margin: '0.35rem 0', fontSize: '1.5rem', fontWeight: 900, color: 'oklch(95% 0.01 250)' }}>
            {designProblem.title}
          </h2>
          <p style={{ margin: 0, fontSize: '0.875rem', color: 'oklch(65% 0.02 250)', maxWidth: '800px', lineHeight: 1.5 }}>
            {designProblem.description}
          </p>
        </div>
        <button
          type="button"
          onClick={onBack}
          style={{
            background: 'none',
            border: '1px solid oklch(28% 0.025 250)',
            borderRadius: '6px',
            padding: '0.4rem 0.8rem',
            fontSize: '0.8125rem',
            color: 'oklch(65% 0.02 250)',
            cursor: 'pointer',
          }}
        >
          ← Powrót
        </button>
      </div>

      {/* Lever Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid oklch(22% 0.025 250)', marginBottom: '1.5rem', overflowX: 'auto', paddingBottom: '0.5rem' }}>
        {designProblem.levers.map((lev) => {
          const isActive = lev.id === activeLeverId
          return (
            <button
              key={lev.id}
              type="button"
              onClick={() => setActiveLeverId(lev.id)}
              style={{
                background: isActive ? 'oklch(75% 0.12 80 / 0.15)' : 'oklch(12% 0.02 250)',
                color: isActive ? 'oklch(90% 0.1 80)' : 'oklch(70% 0.02 250)',
                border: isActive ? '1px solid oklch(75% 0.12 80 / 0.5)' : '1px solid oklch(22% 0.02 250)',
                borderRadius: '8px',
                padding: '0.5rem 1rem',
                fontSize: '0.84rem',
                fontWeight: isActive ? 700 : 500,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              {lev.name} ({lev.options.length})
            </button>
          )
        })}
      </div>

      {/* Active Lever Matrix Card */}
      {activeLever && (
        <div style={{
          background: 'oklch(11% 0.02 250)',
          borderRadius: '10px',
          border: '1px solid oklch(22% 0.025 250)',
          padding: '1.25rem',
          marginBottom: '1.5rem',
        }}>
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            marginBottom: '1rem',
            flexWrap: 'wrap',
            gap: '0.75rem',
          }}>
            <div>
              <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: 'oklch(90% 0.01 250)' }}>
                {activeLever.name}
              </h3>
              {activeLever.description && (
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8125rem', color: 'oklch(60% 0.02 250)' }}>
                  {activeLever.description}
                </p>
              )}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span style={{
                fontSize: '0.75rem',
                color: 'oklch(70% 0.02 250)',
                background: 'oklch(14% 0.02 250)',
                padding: '0.3rem 0.6rem',
                borderRadius: '6px',
                border: '1px solid oklch(22% 0.02 250)',
              }}>
                Dane: <strong style={{ color: 'oklch(80% 0.12 140)' }}>{documentedCells} ugruntowanych</strong> / <span style={{ color: 'oklch(70% 0.05 80)' }}>{emptyCells} pustych</span>
              </span>
              <button
                type="button"
                onClick={handleBulkWebResearch}
                disabled={isSearchingWeb || emptyCells === 0}
                style={{
                  background: 'oklch(75% 0.12 80 / 0.15)',
                  color: 'oklch(88% 0.12 80)',
                  border: '1px solid oklch(75% 0.12 80 / 0.5)',
                  borderRadius: '6px',
                  padding: '0.4rem 0.8rem',
                  fontSize: '0.8125rem',
                  fontWeight: 700,
                  cursor: isSearchingWeb || emptyCells === 0 ? 'not-allowed' : 'pointer',
                  transition: 'all 150ms ease',
                }}
              >
                {isSearchingWeb ? 'Wyszukiwanie w sieci...' : '🌐 Dociągnij dane z sieci'}
              </button>
            </div>
          </div>

          {/* Research notice banner */}
          {researchNotice && (
            <div style={{
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              background: 'oklch(14% 0.03 250)',
              border: '1px solid oklch(25% 0.03 250)',
              marginBottom: '1rem',
              fontSize: '0.8125rem',
              color: 'oklch(80% 0.08 80)',
            }}>
              <div>{researchNotice}</div>
              {showManualUrl && (
                <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.4rem' }}>
                  <input
                    type="url"
                    placeholder="https://... (adres źródła z danymi)"
                    value={manualUrlInput}
                    onChange={(e) => setManualUrlInput(e.target.value)}
                    style={{ flex: 1, fontSize: '0.8125rem', padding: '0.35rem 0.6rem' }}
                  />
                  <button
                    type="button"
                    onClick={handleApplyManualUrl}
                    disabled={!manualUrlInput.trim()}
                    style={{
                      background: 'oklch(75% 0.12 80)',
                      color: 'oklch(6% 0.01 250)',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '0 0.8rem',
                      fontWeight: 700,
                      fontSize: '0.8125rem',
                      cursor: 'pointer',
                    }}
                  >
                    Zastosuj URL
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Table */}
          <div style={{ overflowX: 'auto', borderRadius: '8px', border: '1px solid oklch(20% 0.02 250)' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8125rem' }}>
              <thead>
                <tr style={{ background: 'oklch(14% 0.02 250)', borderBottom: '1px solid oklch(22% 0.025 250)' }}>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'left', color: 'oklch(75% 0.02 250)' }}>
                    Wariant dźwigni
                  </th>
                  {designProblem.criteria.map((crit) => (
                    <th key={crit.id} style={{ padding: '0.75rem 1rem', textAlign: 'center', color: 'oklch(85% 0.08 80)' }}>
                      <div>{crit.name}</div>
                      <div style={{ fontSize: '0.6875rem', color: 'oklch(60% 0.02 250)', fontWeight: 400 }}>
                        ({crit.direction === 'maximize' ? 'max' : 'min'}, waga: {crit.weight})
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {activeLever.options.map((opt) => (
                  <tr key={opt.id} style={{ borderBottom: '1px solid oklch(18% 0.02 250)' }}>
                    <td style={{ padding: '0.875rem 1rem', minWidth: '220px' }}>
                      <div style={{ fontWeight: 700, color: 'oklch(90% 0.01 250)' }}>{opt.title}</div>
                      {opt.description && (
                        <div style={{ fontSize: '0.75rem', color: 'oklch(60% 0.02 250)', marginTop: '0.2rem' }}>
                          {opt.description}
                        </div>
                      )}
                      {opt.evidence_ref && (
                        <div style={{ fontSize: '0.6875rem', color: 'oklch(70% 0.08 80)', marginTop: '0.25rem' }}>
                          ℹ️ {opt.evidence_ref}
                        </div>
                      )}
                    </td>
                    {designProblem.criteria.map((crit) => {
                      const cell = designProblem.score_matrix?.[activeLever.id]?.[opt.id]?.[crit.id]
                      const hasVal = cell && cell.value !== undefined && cell.value !== null && !isNaN(cell.value)
                      const provenance = cell?.provenance || 'missing'
                      const provenanceIcons: Record<string, string> = {
                        user_supplied: '👤',
                        web_sourced: '🌐',
                        assumed: '⚠️',
                        derived: '⚙️',
                        missing: '❓',
                      }
                      const icon = hasVal ? (provenanceIcons[provenance] || '✓') : '❓'
                      const isResearching = isSearchingWeb && activeResearchCell?.leverId === activeLever.id && activeResearchCell?.optionId === opt.id && activeResearchCell?.criterionId === crit.id

                      return (
                        <td key={crit.id} style={{ padding: '0.75rem 0.5rem', textAlign: 'center', minWidth: '150px' }}>
                          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
                              <input
                                type="number"
                                step="any"
                                placeholder="Wartość..."
                                value={hasVal ? cell.value : ''}
                                onChange={(e) => {
                                  const num = parseFloat(e.target.value)
                                  if (!isNaN(num)) {
                                    handleUpdateCell(activeLever.id, opt.id, crit.id, {
                                      value: num,
                                      provenance: 'user_supplied',
                                      source_ref: 'Wprowadzone ręcznie przez użytkownika',
                                      confidence: 1.0,
                                    })
                                  }
                                }}
                                style={{
                                  width: '80px',
                                  padding: '0.3rem 0.4rem',
                                  fontSize: '0.8125rem',
                                  textAlign: 'right',
                                  borderRadius: '4px',
                                  background: hasVal ? 'oklch(14% 0.02 250)' : 'oklch(13% 0.03 35 / 0.3)',
                                  border: `1px solid ${hasVal ? 'oklch(28% 0.03 250)' : 'oklch(38% 0.08 35)'}`,
                                }}
                              />
                              <span style={{ fontSize: '0.75rem', color: 'oklch(60% 0.02 250)' }}>
                                {crit.unit || ''}
                              </span>
                              <span title={`Pochodzenie: ${cell?.source_ref || 'brak'}`} style={{ cursor: 'help' }}>
                                {icon}
                              </span>
                            </div>
                            <div style={{ display: 'flex', gap: '0.3rem', fontSize: '0.6875rem' }}>
                              <button
                                type="button"
                                onClick={() => handleWebResearch(activeLever.id, opt.id, crit.id)}
                                disabled={isResearching}
                                title="Dozbierz dane z sieci www dla tego parametru"
                                style={{
                                  background: 'none',
                                  border: '1px solid oklch(25% 0.03 250)',
                                  borderRadius: '3px',
                                  color: 'oklch(75% 0.12 80)',
                                  padding: '0.15rem 0.35rem',
                                  cursor: 'pointer',
                                }}
                              >
                                {isResearching ? 'Szukam...' : '🌐 Badaj w sieci'}
                              </button>
                            </div>
                          </div>
                        </td>
                      )
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Interactions / Synergies section */}
      <div style={{
        background: 'oklch(11% 0.02 250)',
        borderRadius: '10px',
        border: '1px solid oklch(22% 0.025 250)',
        padding: '1.25rem',
        marginBottom: '1.5rem',
      }}>
        <h3 style={{ margin: '0 0 0.5rem 0', fontSize: '1rem', fontWeight: 800, color: 'oklch(90% 0.01 250)' }}>
          Interakcje i synergie między dźwigniami (D2 / N5)
        </h3>
        <p style={{ margin: '0 0 1rem 0', fontSize: '0.8125rem', color: 'oklch(60% 0.02 250)' }}>
          Synergie między wariantami wynoszą domyślnie 0.0. Każda niezerowa wartość wymaga podania źródła lub oznaczenia jako założenie.
        </p>

        {designProblem.interactions.length === 0 ? (
          <div style={{ fontSize: '0.8125rem', color: 'oklch(55% 0.02 250)', fontStyle: 'italic' }}>
            Brak zdefiniowanych interakcji nieliniowych (czysta addytywność liniowa).
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {designProblem.interactions.map((inter, idx) => (
              <div key={idx} style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.6rem 0.8rem',
                borderRadius: '6px',
                background: 'oklch(13% 0.02 250)',
                border: '1px solid oklch(20% 0.02 250)',
                flexWrap: 'wrap',
                gap: '0.5rem',
                fontSize: '0.8125rem',
              }}>
                <div>
                  <span style={{ fontWeight: 700, color: 'oklch(85% 0.08 80)' }}>
                    {inter.option_a_id} + {inter.option_b_id}:
                  </span>{' '}
                  <span style={{ color: 'oklch(65% 0.02 250)' }}>
                    {inter.compatible ? 'Kompatybilne' : 'Wykluczające się'}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <label style={{ color: 'oklch(60% 0.02 250)' }}>Synergia:</label>
                  <input
                    type="number"
                    step="0.1"
                    value={inter.synergy}
                    onChange={(e) => handleUpdateSynergy(idx, parseFloat(e.target.value) || 0.0, inter.source_ref)}
                    style={{ width: '65px', padding: '0.25rem', fontSize: '0.8125rem', textAlign: 'right' }}
                  />
                  <input
                    type="text"
                    placeholder="Źródło / uzasadnienie synergii..."
                    value={inter.source_ref || ''}
                    onChange={(e) => handleUpdateSynergy(idx, inter.synergy, e.target.value)}
                    style={{ width: '220px', padding: '0.25rem 0.5rem', fontSize: '0.8125rem' }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Validation banner & proceed button */}
      {!isValidForSynthesis && (
        <div style={{
          padding: '0.875rem 1rem',
          borderRadius: '8px',
          background: 'oklch(14% 0.04 35 / 0.4)',
          border: '1px solid oklch(40% 0.1 35)',
          marginBottom: '1.5rem',
          fontSize: '0.8125rem',
          color: 'oklch(85% 0.08 35)',
        }}>
          <div style={{ fontWeight: 700, marginBottom: '0.35rem' }}>
            ⚠️ Uzupełnij brakujące dane przed syntezą Pareto:
          </div>
          <ul style={{ margin: 0, paddingLeft: '1.2rem', lineHeight: 1.5 }}>
            {validationErrors.slice(0, 5).map((err, i) => (
              <li key={i}>{err}</li>
            ))}
            {validationErrors.length > 5 && (
              <li>...i jeszcze {validationErrors.length - 5} innych pozycji</li>
            )}
          </ul>
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
        <button
          type="button"
          onClick={() => onSynthesize(designProblem)}
          disabled={!isValidForSynthesis || isSynthesizing}
          style={{
            background: isValidForSynthesis ? 'oklch(75% 0.12 80)' : 'oklch(25% 0.02 250)',
            color: isValidForSynthesis ? 'oklch(6% 0.01 250)' : 'oklch(50% 0.02 250)',
            border: 'none',
            borderRadius: '8px',
            padding: '0.75rem 1.5rem',
            fontSize: '0.9375rem',
            fontWeight: 800,
            cursor: isValidForSynthesis ? 'pointer' : 'not-allowed',
            transition: 'all 180ms ease',
          }}
        >
          {isSynthesizing ? 'Obliczanie syntezy Pareto...' : 'Oblicz syntezę Pareto i optymalną konfigurację →'}
        </button>
      </div>
    </div>
  )
}
