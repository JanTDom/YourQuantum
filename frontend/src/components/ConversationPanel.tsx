import React, { useState } from 'react'

interface ConversationPanelProps {
  onSubmit: (text: string) => void
  isLoading: boolean
}

const QUICK_EXAMPLES = [
  {
    label: 'Dylemat zawodowy',
    title: 'Zmiana pracy czy obecna firma',
    text: 'Nie wiem, czy zmienić pracę na nową ofertę z wyższą pensją, czy zostać w obecnej firmie ze stabilnym zespołem.',
  },
  {
    label: 'Wybór inwestycji',
    title: 'Wybór projektów firmowych',
    text: 'Chcę wybrać maksymalnie 2 projekty inwestycyjne spośród A, B i C przy ograniczonym budżecie.',
  },
  {
    label: 'Optymalizacja plecaka',
    title: 'Ekwipunek na wyprawę',
    text: 'Chcę rozwiązać problem plecakowy o udźwigu 7 kg dla 4 przedmiotów.',
  },
]

export const ConversationPanel: React.FC<ConversationPanelProps> = ({ onSubmit, isLoading }) => {
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return
    onSubmit(input.trim())
  }

  const handleSelectExample = (text: string) => {
    setInput(text)
  }

  return (
    <div style={{
      maxWidth: '760px',
      margin: '2.5rem auto',
      padding: '0 1rem',
    }}>
      <div style={{
        background: 'var(--bg-surface)',
        borderRadius: 'var(--radius-lg)',
        border: '1px solid var(--border-subtle)',
        boxShadow: 'var(--shadow-md)',
        padding: '2rem',
      }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <h1 style={{
            fontSize: '1.5rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            letterSpacing: '-0.02em',
            margin: '0 0 0.5rem 0',
          }}>
            Przedstaw swój problem lub dylemat
          </h1>
          <p style={{
            fontSize: '0.9375rem',
            color: 'var(--text-muted)',
            margin: 0,
            lineHeight: 1.5,
          }}>
            Napisz zwykłymi słowami, przed jaką decyzją stoisz. System pomoże zmapować opcje, zapyta o brakujące kryteria i przeprowadzi bezstronną analizę.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ position: 'relative', marginBottom: '1.25rem' }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Np. Stoję przed wyborem między dwiema ofertami pracy... albo: Muszę wybrać 2 z 4 projektów dla zespołu..."
              rows={4}
              style={{
                width: '100%',
                padding: '1rem',
                fontSize: '1rem',
                lineHeight: 1.5,
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border-strong)',
                background: 'var(--bg-canvas)',
                color: 'var(--text-primary)',
                resize: 'vertical',
                boxSizing: 'border-box',
              }}
              disabled={isLoading}
            />
          </div>

          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '1rem',
          }}>
            <span style={{ fontSize: '0.8125rem', color: 'var(--text-muted)' }}>
              Bez żargonu matematycznego. Pełna kontrola nad kryteriami.
            </span>

            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              style={{
                background: 'var(--accent-primary)',
                color: 'var(--text-inverse)',
                padding: '0.75rem 1.5rem',
                borderRadius: 'var(--radius-md)',
                border: 'none',
                fontWeight: 600,
                fontSize: '0.9375rem',
                cursor: !input.trim() || isLoading ? 'not-allowed' : 'pointer',
                opacity: !input.trim() || isLoading ? 0.6 : 1,
                transition: 'background var(--transition-fast)',
              }}
            >
              {isLoading ? 'Analizowanie sytuacji...' : 'Przeanalizuj sytuację'}
            </button>
          </div>
        </form>

        <div style={{
          marginTop: '2rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid var(--border-subtle)',
        }}>
          <p style={{
            fontSize: '0.8125rem',
            fontWeight: 600,
            color: 'var(--text-muted)',
            marginBottom: '0.75rem',
            textTransform: 'uppercase',
            letterSpacing: '0.04em',
          }}>
            Przykładowe codzienne sytuacje
          </p>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
            gap: '0.75rem',
          }}>
            {QUICK_EXAMPLES.map((ex) => (
              <button
                key={ex.title}
                type="button"
                onClick={() => handleSelectExample(ex.text)}
                style={{
                  textAlign: 'left',
                  background: 'var(--bg-subtle)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                  padding: '0.75rem',
                  cursor: 'pointer',
                  transition: 'background var(--transition-fast), border-color var(--transition-fast)',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'var(--accent-blue)', fontWeight: 600 }}>
                  {ex.label}
                </div>
                <div style={{ fontSize: '0.875rem', color: 'var(--text-primary)', fontWeight: 500, marginTop: '0.125rem' }}>
                  {ex.title}
                </div>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
