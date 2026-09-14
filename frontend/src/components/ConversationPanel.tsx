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
        background: 'oklch(8% 0.025 250 / 0.95)',
        borderRadius: '12px',
        border: '1.5px solid oklch(75% 0.12 80 / 0.38)',
        boxShadow: '0 0 45px oklch(75% 0.12 80 / 0.18), 0 20px 40px oklch(5% 0.01 250 / 0.85)',
        padding: '2rem',
        backdropFilter: 'blur(20px)',
      }}>
        {/* Terminal Header Bar */}
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          paddingBottom: '1rem',
          marginBottom: '1.5rem',
          borderBottom: '1px solid oklch(75% 0.12 80 / 0.2)',
          flexWrap: 'wrap',
          gap: '0.75rem',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: 'oklch(75% 0.18 150)',
              boxShadow: '0 0 10px oklch(75% 0.18 150)',
              display: 'inline-block',
            }} />
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 800,
              letterSpacing: '0.04em',
              color: 'oklch(80% 0.10 80)',
            }}>
              Terminal obliczeń kwantowych
            </span>
          </div>
          <div style={{
            fontSize: '0.6875rem',
            fontWeight: 700,
            letterSpacing: '0.04em',
            padding: '0.2rem 0.625rem',
            borderRadius: '4px',
            background: 'oklch(62% 0.18 240 / 0.18)',
            border: '1px solid oklch(62% 0.18 240 / 0.4)',
            color: 'oklch(85% 0.09 240)',
          }}>
            QAOA + CP-SAT · ścisły dowód i weryfikacja
          </div>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <h2 style={{
            fontSize: '1.5rem',
            fontWeight: 800,
            color: 'oklch(97% 0.01 250)',
            letterSpacing: '-0.02em',
            margin: '0 0 0.5rem 0',
          }}>
            Wprowadź swój dylemat lub problem decyzyjny
          </h2>
          <p style={{
            fontSize: '0.9375rem',
            color: 'oklch(75% 0.02 250)',
            margin: 0,
            lineHeight: 1.6,
          }}>
            Opisz sytuację zwykłymi słowami. Silnik formalizuje model matematyczny, sprawdza wszystkie ograniczenia i oblicza globalne optimum — bez zgadywania czatów AI.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ position: 'relative', marginBottom: '1.25rem' }}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Np. Stoję przed wyborem między dwiema ofertami pracy... albo: Muszę wybrać 2 z 4 projektów dla zespołu przy twardym budżecie..."
              rows={4}
              style={{
                width: '100%',
                padding: '1.125rem',
                fontSize: '1.0625rem',
                lineHeight: 1.6,
                borderRadius: '8px',
                border: '1.5px solid oklch(30% 0.035 250)',
                background: 'oklch(11% 0.02 250)',
                color: 'oklch(98% 0.01 250)',
                resize: 'vertical',
                boxSizing: 'border-box',
                outline: 'none',
                fontFamily: 'inherit',
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
            <span style={{ fontSize: '0.8125rem', color: 'oklch(60% 0.025 250)' }}>
              Bez żargonu. Deterministyczny model matematyczny z niezależnym dowodem.
            </span>

            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              style={{
                background: !input.trim() || isLoading
                  ? 'oklch(20% 0.02 250)'
                  : 'linear-gradient(135deg, oklch(75% 0.12 80) 0%, oklch(82% 0.14 85) 100%)',
                color: !input.trim() || isLoading ? 'oklch(50% 0.02 250)' : 'oklch(5% 0.01 250)',
                padding: '0.875rem 1.75rem',
                borderRadius: '6px',
                border: 'none',
                fontWeight: 900,
                fontSize: '1rem',
                cursor: !input.trim() || isLoading ? 'not-allowed' : 'pointer',
                boxShadow: !input.trim() || isLoading ? 'none' : '0 0 30px oklch(75% 0.12 80 / 0.5)',
                transition: 'all 200ms ease',
                letterSpacing: '-0.01em',
              }}
            >
              {isLoading ? 'Uruchamianie silnika kwantowego...' : '⚡ OBLICZ ROZWIĄZANIE KWANTOWE →'}
            </button>
          </div>
        </form>

        <div style={{
          marginTop: '2rem',
          paddingTop: '1.5rem',
          borderTop: '1px solid oklch(75% 0.12 80 / 0.18)',
        }}>
          <p style={{
            fontSize: '0.8125rem',
            fontWeight: 700,
            color: 'oklch(80% 0.10 80)',
            marginBottom: '0.75rem',
            letterSpacing: '0.02em',
          }}>
            Przykładowe codzienne dylematy
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
                  background: 'oklch(13% 0.02 250)',
                  border: '1px solid oklch(28% 0.035 250)',
                  borderRadius: '6px',
                  padding: '0.875rem',
                  cursor: 'pointer',
                  transition: 'all 180ms ease',
                }}
              >
                <div style={{ fontSize: '0.75rem', color: 'oklch(75% 0.12 80)', fontWeight: 700 }}>
                  {ex.label}
                </div>
                <div style={{ fontSize: '0.875rem', color: 'oklch(95% 0.01 250)', fontWeight: 500, marginTop: '0.2rem' }}>
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
