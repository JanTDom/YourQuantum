import React, { useState, useEffect, useMemo } from 'react'
import { api, HelpResponse } from '../api'

interface HelpCenterModalProps {
  isOpen: boolean
  onClose: () => void
  currentStage: 'INTAKE' | 'CASE_WORKSPACE' | 'MODEL_APPROVAL' | 'RECOMMENDATION'
  onSelectExample?: (exampleText: string) => void
}

export const HelpCenterModal: React.FC<HelpCenterModalProps> = ({
  isOpen,
  onClose,
  currentStage,
  onSelectExample,
}) => {
  const [data, setData] = useState<HelpResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [activeCategory, setActiveCategory] = useState<string>('ALL')
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<'GUIDE' | 'EXAMPLES' | 'FAQ' | 'GLOSSARY' | 'ENGINE'>('GUIDE')

  useEffect(() => {
    if (isOpen && !data) {
      setIsLoading(true)
      api.getHelpKnowledge()
        .then((res) => {
          setData(res)
          // Default to a contextually relevant topic
          const relevant = res.topics.find((t) => t.target_stages.includes(currentStage))
          if (relevant) {
            setSelectedTopicId(relevant.id)
          } else if (res.topics.length > 0) {
            setSelectedTopicId(res.topics[0].id)
          }
        })
        .catch((err) => console.error('Failed to load help knowledge', err))
        .finally(() => setIsLoading(false))
    }
  }, [isOpen, data, currentStage])

  // ESC key to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  const stageLabel = useMemo(() => {
    switch (currentStage) {
      case 'INTAKE':
        return 'Wpisywanie problemu'
      case 'CASE_WORKSPACE':
        return 'Doprecyzowywanie i wagi'
      case 'MODEL_APPROVAL':
        return 'Zatwierdzanie reguł matematycznych'
      case 'RECOMMENDATION':
        return 'Analiza optymalnego wyniku'
    }
  }, [currentStage])

  // Filter topics
  const filteredTopics = useMemo(() => {
    if (!data) return []
    return data.topics.filter((t) => {
      const matchesSearch =
        searchQuery.trim() === '' ||
        t.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.short_desc.toLowerCase().includes(searchQuery.toLowerCase()) ||
        t.content_markdown.toLowerCase().includes(searchQuery.toLowerCase())
      const matchesCategory = activeCategory === 'ALL' || t.category === activeCategory
      return matchesSearch && matchesCategory
    })
  }, [data, searchQuery, activeCategory])

  const activeTopic = useMemo(() => {
    if (!data) return null
    return data.topics.find((t) => t.id === selectedTopicId) || data.topics[0] || null
  }, [data, selectedTopicId])

  if (!isOpen) return null

  return (
    <div
      className="help-modal-overlay"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'oklch(0% 0 0 / 0.75)',
        backdropFilter: 'blur(12px)',
        WebkitBackdropFilter: 'blur(12px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '1rem',
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Centrum Pomocy YourQuantum"
    >
      <div
        className="help-modal-panel"
        style={{
          width: '100%',
          maxWidth: '1100px',
          height: 'min(880px, 92vh)',
          maxHeight: '96dvh',
          background: 'oklch(11% 0.015 250)',
          border: '1px solid oklch(26% 0.03 250)',
          borderRadius: '20px',
          boxShadow: '0 24px 80px oklch(0% 0 0 / 0.8), 0 0 40px oklch(75% 0.12 80 / 0.1)',
          display: 'flex',
          flexDirection: 'column',
          overflow: 'hidden',
        }}
      >
        <style>{`
          @media (max-width: 768px) {
            .help-modal-overlay {
              padding: 0 !important;
              align-items: stretch !important;
              justify-content: stretch !important;
            }
            .help-modal-panel {
              width: 100vw !important;
              max-width: 100vw !important;
              height: 100dvh !important;
              max-height: 100dvh !important;
              border-radius: 0 !important;
              border: none !important;
            }
            .help-modal-header {
              padding: max(env(safe-area-inset-top, 0px), 0.75rem) 1rem 0.625rem 1rem !important;
            }
            .help-modal-desc {
              display: none !important;
            }
            .help-modal-tabs {
              padding: 0.5rem 0.75rem 0 !important;
              overflow-x: auto !important;
              scrollbar-width: none !important;
              -webkit-overflow-scrolling: touch !important;
            }
            .help-modal-tabs button {
              white-space: nowrap !important;
              flex-shrink: 0 !important;
              font-size: 0.75rem !important;
              padding: 0.5rem 0.75rem !important;
            }
            .help-modal-split {
              flex-direction: column !important;
            }
            .help-modal-sidebar {
              width: 100% !important;
              max-height: 38vh !important;
              border-right: none !important;
              border-bottom: 1px solid oklch(20% 0.02 250) !important;
            }
          }
        `}</style>

        {/* Top Header */}
        <div
          className="help-modal-header"
          style={{
            padding: '1.25rem 1.75rem',
            borderBottom: '1px solid oklch(20% 0.025 250)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            background: 'oklch(13% 0.02 250)',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <div
              style={{
                width: '38px',
                height: '38px',
                borderRadius: '10px',
                background: 'oklch(75% 0.12 80)',
                color: 'oklch(10% 0.02 250)',
                fontWeight: 900,
                fontSize: '1.125rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: '0 0 16px oklch(75% 0.12 80 / 0.4)',
              }}
            >
              ?
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
                <h2 style={{ fontSize: '1.125rem', fontWeight: 800, margin: 0, color: 'oklch(96% 0.01 250)' }}>
                  Centrum Pomocy dla Laików
                </h2>
                {data && (
                  <span
                    style={{
                      fontSize: '0.6875rem',
                      fontWeight: 700,
                      padding: '0.2rem 0.5rem',
                      borderRadius: '100px',
                      background: 'oklch(22% 0.05 170)',
                      color: 'oklch(78% 0.16 168)',
                      border: '1px solid oklch(35% 0.09 168)',
                    }}
                  >
                    Silnik {data.engine_status.engine_version} • Samoaktywujący
                  </span>
                )}
              </div>
              <p className="help-modal-desc" style={{ margin: '2px 0 0 0', fontSize: '0.8125rem', color: 'oklch(65% 0.02 250)' }}>
                Wszystko, co musisz wiedzieć o rozwiązywaniu dylematów — prostym, ludzkim językiem.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: 'oklch(20% 0.02 250)',
              border: '1px solid oklch(28% 0.03 250)',
              color: 'oklch(80% 0.01 250)',
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer',
              fontSize: '1.25rem',
              lineHeight: 1,
              transition: 'all 150ms ease',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'oklch(28% 0.03 250)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'oklch(20% 0.02 250)')}
            title="Zamknij (ESC)"
          >
            ×
          </button>
        </div>

        {/* Dynamic Context Banner */}
        <div
          style={{
            padding: '0.625rem 1.75rem',
            background: 'oklch(16% 0.03 240)',
            borderBottom: '1px solid oklch(22% 0.03 240)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: '0.8125rem',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span style={{ color: 'oklch(75% 0.12 80)', fontWeight: 700 }}>Aktualny etap:</span>
            <span
              style={{
                background: 'oklch(22% 0.04 250)',
                padding: '0.15rem 0.5rem',
                borderRadius: '4px',
                color: 'oklch(90% 0.02 250)',
                fontWeight: 600,
              }}
            >
              {stageLabel}
            </span>
          </div>
          <span style={{ color: 'oklch(60% 0.02 250)', fontSize: '0.75rem' }}>
            Auto-aktualizacja: {data?.engine_status.last_updated || 'Synchronizowanie...'}
          </span>
        </div>

        {/* Tab Navigation */}
        <div
          className="help-modal-tabs"
          style={{
            display: 'flex',
            gap: '0.5rem',
            padding: '0.75rem 1.75rem 0',
            borderBottom: '1px solid oklch(20% 0.02 250)',
            background: 'oklch(12% 0.015 250)',
          }}
        >
          {[
            { id: 'GUIDE', label: 'Przewodnik krok po kroku' },
            { id: 'EXAMPLES', label: 'Przykłady dylematów' },
            { id: 'FAQ', label: 'Częste pytania (FAQ)' },
            { id: 'GLOSSARY', label: 'Słowniczek pojęć' },
            { id: 'ENGINE', label: 'Stan Silnika (Live)' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              style={{
                background: 'none',
                border: 'none',
                padding: '0.625rem 1rem',
                fontSize: '0.84375rem',
                fontWeight: activeTab === tab.id ? 700 : 500,
                color: activeTab === tab.id ? 'oklch(75% 0.12 80)' : 'oklch(65% 0.02 250)',
                borderBottom: activeTab === tab.id ? '2px solid oklch(75% 0.12 80)' : '2px solid transparent',
                cursor: 'pointer',
                transition: 'all 150ms ease',
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Main Content Area */}
        <div className="help-modal-split" style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
          {isLoading && (
            <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'oklch(75% 0.12 80)' }}>
              Ładowanie bazy wiedzy...
            </div>
          )}

          {!isLoading && data && activeTab === 'GUIDE' && (
            <>
              {/* Sidebar list */}
              <div
                className="help-modal-sidebar"
                style={{
                  width: '340px',
                  borderRight: '1px solid oklch(20% 0.02 250)',
                  display: 'flex',
                  flexDirection: 'column',
                  background: 'oklch(12% 0.015 250)',
                }}
              >
                {/* Search */}
                <div style={{ padding: '1rem', borderBottom: '1px solid oklch(18% 0.02 250)' }}>
                  <input
                    type="text"
                    placeholder="Szukaj w przewodniku..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    style={{
                      width: '100%',
                      padding: '0.5rem 0.75rem',
                      borderRadius: '8px',
                      background: 'oklch(16% 0.02 250)',
                      border: '1px solid oklch(24% 0.03 250)',
                      color: 'oklch(95% 0.01 250)',
                      fontSize: '0.8125rem',
                      outline: 'none',
                    }}
                  />
                {data && (
                  <div style={{ display: 'flex', gap: '0.35rem', overflowX: 'auto', marginTop: '0.625rem', paddingBottom: '0.25rem' }}>
                    <button
                      type="button"
                      onClick={() => setActiveCategory('ALL')}
                      style={{
                        background: activeCategory === 'ALL' ? 'oklch(24% 0.04 80)' : 'oklch(16% 0.02 250)',
                        border: '1px solid',
                        borderColor: activeCategory === 'ALL' ? 'oklch(75% 0.12 80)' : 'oklch(22% 0.025 250)',
                        color: activeCategory === 'ALL' ? 'oklch(95% 0.01 250)' : 'oklch(65% 0.01 250)',
                        borderRadius: '4px',
                        padding: '0.15rem 0.5rem',
                        fontSize: '0.6875rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        whiteSpace: 'nowrap',
                      }}
                    >
                      Wszystkie
                    </button>
                    {data.categories.map((cat) => (
                      <button
                        key={cat}
                        type="button"
                        onClick={() => setActiveCategory(cat)}
                        style={{
                          background: activeCategory === cat ? 'oklch(24% 0.04 80)' : 'oklch(16% 0.02 250)',
                          border: '1px solid',
                          borderColor: activeCategory === cat ? 'oklch(75% 0.12 80)' : 'oklch(22% 0.025 250)',
                          color: activeCategory === cat ? 'oklch(95% 0.01 250)' : 'oklch(65% 0.01 250)',
                          borderRadius: '4px',
                          padding: '0.15rem 0.5rem',
                          fontSize: '0.6875rem',
                          fontWeight: 600,
                          cursor: 'pointer',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {cat}
                      </button>
                    ))}
                  </div>
                )}
              </div>

                {/* Topics list */}
                <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
                  {filteredTopics.map((topic) => {
                    const isSelected = activeTopic?.id === topic.id
                    const isCurrentStage = topic.target_stages.includes(currentStage)
                    return (
                      <div
                        key={topic.id}
                        onClick={() => setSelectedTopicId(topic.id)}
                        style={{
                          padding: '0.75rem 0.875rem',
                          borderRadius: '8px',
                          marginBottom: '0.25rem',
                          cursor: 'pointer',
                          background: isSelected ? 'oklch(20% 0.03 80 / 0.3)' : 'transparent',
                          border: isSelected ? '1px solid oklch(75% 0.12 80 / 0.5)' : '1px solid transparent',
                          transition: 'all 150ms ease',
                        }}
                      >
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
                          <span style={{ fontSize: '0.875rem', fontWeight: 700, color: isSelected ? 'oklch(95% 0.01 250)' : 'oklch(80% 0.01 250)' }}>
                            {topic.title}
                          </span>
                          {isCurrentStage && (
                            <span style={{ fontSize: '0.625rem', background: 'oklch(75% 0.12 80 / 0.2)', color: 'oklch(75% 0.12 80)', padding: '0.1rem 0.35rem', borderRadius: '3px' }}>
                              Teraz
                            </span>
                          )}
                        </div>
                        <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: 'oklch(60% 0.01 250)', lineClamp: 2 }}>
                          {topic.short_desc}
                        </p>
                      </div>
                    )
                  })}
                </div>
              </div>

              {/* Topic Detail */}
              <div style={{ flex: 1, overflowY: 'auto', padding: '2rem 2.5rem' }}>
                {activeTopic && (
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                      <span
                        style={{
                          fontSize: '0.75rem',
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          letterSpacing: '0.08em',
                          color: 'oklch(75% 0.12 80)',
                        }}
                      >
                        {activeTopic.category}
                      </span>
                      <span style={{ color: 'oklch(40% 0.01 250)' }}>•</span>
                      <span style={{ fontSize: '0.75rem', color: 'oklch(60% 0.01 250)' }}>
                        {activeTopic.read_time_minutes} min czytania
                      </span>
                      {activeTopic.badge && (
                        <span
                          style={{
                            fontSize: '0.6875rem',
                            fontWeight: 700,
                            padding: '0.15rem 0.45rem',
                            borderRadius: '4px',
                            background: 'oklch(22% 0.04 250)',
                            color: 'oklch(90% 0.01 250)',
                          }}
                        >
                          {activeTopic.badge}
                        </span>
                      )}
                    </div>

                    <h1 style={{ fontSize: '1.625rem', fontWeight: 900, margin: '0 0 1.25rem 0', color: 'oklch(98% 0.005 250)' }}>
                      {activeTopic.title}
                    </h1>

                    <div
                      style={{
                        lineHeight: 1.7,
                        fontSize: '0.9375rem',
                        color: 'oklch(82% 0.015 250)',
                      }}
                    >
                      {activeTopic.content_markdown.split('\n\n').map((paragraph, idx) => {
                        if (paragraph.startsWith('### ')) {
                          return (
                            <h3 key={idx} style={{ fontSize: '1.1875rem', fontWeight: 800, margin: '1.5rem 0 0.5rem 0', color: 'oklch(95% 0.01 250)' }}>
                              {paragraph.replace('### ', '')}
                            </h3>
                          )
                        }
                        if (paragraph.startsWith('#### ')) {
                          return (
                            <h4 key={idx} style={{ fontSize: '1rem', fontWeight: 700, margin: '1.25rem 0 0.5rem 0', color: 'oklch(75% 0.12 80)' }}>
                              {paragraph.replace('#### ', '')}
                            </h4>
                          )
                        }
                        if (paragraph.startsWith('* ') || paragraph.startsWith('- ')) {
                          const items = paragraph.split('\n').map((i) => i.replace(/^[*\\-]\s+/, ''))
                          return (
                            <ul key={idx} style={{ margin: '0.5rem 0 1rem 1.25rem', padding: 0 }}>
                              {items.map((item, itemIdx) => (
                                <li key={itemIdx} style={{ marginBottom: '0.375rem' }}>
                                  {item}
                                </li>
                              ))}
                            </ul>
                          )
                        }
                        return (
                          <p key={idx} style={{ margin: '0 0 1rem 0' }}>
                            {paragraph}
                          </p>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}

          {/* Tab 2: Examples */}
          {!isLoading && data && activeTab === 'EXAMPLES' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '0 0 0.5rem 0', color: 'oklch(95% 0.01 250)' }}>
                Szablony i Prawdziwe Scenariusze
              </h3>
              <p style={{ margin: '0 0 1.5rem 0', fontSize: '0.875rem', color: 'oklch(65% 0.02 250)' }}>
                Kliknij dowolny przykład, aby natychmiast załadować go do silnika i zobaczyć jak YourQuantum przeprowadzi Cię przez proces decyzyjny.
              </p>

              <div style={{ display: 'grid', gap: '1rem' }}>
                {[
                  {
                    title: 'Dwie Oferty Pracy (Kariera vs Spokój)',
                    category: 'Kariera',
                    text: 'Pracuję w firmie A jako Senior Developer za 16 000 zł na rękę, praca zdalna, zero stresu. Dostałem ofertę od prestiżowej korporacji B: 24 000 zł, ale praca hybrydowa (3 dni w biurze w innym mieście, dojazd 1.5h w jedną stronę) i duża presja na wyniki. Mam dwójkę małych dzieci. Nie wiem czy poświęcić wygodę dla 50% wyższych zarobków.',
                  },
                  {
                    title: 'Wybór Ścieżki Biznesowej (Bezpieczna Marża vs Duży Kontrakt)',
                    category: 'Biznes',
                    text: 'Prowadzę małe studio projektowe. Mamy 4 stałych klientów generujących 35 000 zł zysku miesięcznie. Otrzymałem propozycję rocznego kontraktu od giganta technologicznego: gwarancja 90 000 zł miesięcznie, ale muszę zrezygnować z dotychczasowych klientów i zatrudnić 3 osoby. Klient ma termin płatności 60 dni.',
                  },
                  {
                    title: 'Dylemat Mieszkaniowy (Kredyt na Obrzeżach vs Wynajem w Centrum)',
                    category: 'Życie Osobiste',
                    text: 'Kończy mi się umowa najmu kawalerki w centrum. Mogę wziąć kredyt hipoteczny na 30 lat i kupić dom na przedmieściach (120 m2, spokój, ogród, ale 50 minut do pracy i raty 4200 zł), albo wynająć 3-pokojowe mieszkanie 10 minut od pracy (koszt 4500 zł, elastyczność, ale bez własności).',
                  },
                ].map((ex, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'oklch(14% 0.02 250)',
                      border: '1px solid oklch(22% 0.03 250)',
                      borderRadius: '12px',
                      padding: '1.25rem 1.5rem',
                      display: 'flex',
                      flexDirection: 'column',
                      gap: '0.75rem',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                      <span style={{ fontSize: '0.9375rem', fontWeight: 800, color: 'oklch(95% 0.01 250)' }}>
                        {ex.title}
                      </span>
                      <span
                        style={{
                          fontSize: '0.6875rem',
                          fontWeight: 700,
                          padding: '0.15rem 0.5rem',
                          borderRadius: '100px',
                          background: 'oklch(22% 0.04 80)',
                          color: 'oklch(75% 0.12 80)',
                        }}
                      >
                        {ex.category}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.84375rem', color: 'oklch(75% 0.015 250)', lineHeight: 1.6, fontStyle: 'italic' }}>
                      „{ex.text}”
                    </p>
                    {onSelectExample && (
                      <div style={{ alignSelf: 'flex-end' }}>
                        <button
                          onClick={() => {
                            onSelectExample(ex.text)
                            onClose()
                          }}
                          style={{
                            background: 'oklch(75% 0.12 80)',
                            border: 'none',
                            padding: '0.4rem 0.875rem',
                            borderRadius: '6px',
                            fontSize: '0.75rem',
                            fontWeight: 800,
                            color: 'oklch(10% 0.02 250)',
                            cursor: 'pointer',
                            transition: 'all 150ms ease',
                          }}
                        >
                          Przetestuj ten dylemat →
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 3: FAQ */}
          {!isLoading && data && activeTab === 'FAQ' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '0 0 1rem 0', color: 'oklch(95% 0.01 250)' }}>
                Najczęściej Zadawane Pytania
              </h3>
              <div style={{ display: 'grid', gap: '1rem' }}>
                {data.faq.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'oklch(14% 0.02 250)',
                      border: '1px solid oklch(22% 0.03 250)',
                      borderRadius: '12px',
                      padding: '1.25rem 1.5rem',
                    }}
                  >
                    <h4 style={{ margin: '0 0 0.5rem 0', fontSize: '0.9375rem', fontWeight: 800, color: 'oklch(75% 0.12 80)' }}>
                      {item.q}
                    </h4>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: 'oklch(80% 0.01 250)', lineHeight: 1.6 }}>
                      {item.a}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 4: Glossary */}
          {!isLoading && data && activeTab === 'GLOSSARY' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
              <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: '0 0 1rem 0', color: 'oklch(95% 0.01 250)' }}>
                Słowniczek Pojęć (Bez Żargonu)
              </h3>
              <div style={{ display: 'grid', gap: '1rem' }}>
                {data.glossary.map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      background: 'oklch(14% 0.02 250)',
                      border: '1px solid oklch(22% 0.03 250)',
                      borderRadius: '12px',
                      padding: '1.25rem 1.5rem',
                    }}
                  >
                    <span style={{ fontSize: '1rem', fontWeight: 800, color: 'oklch(96% 0.01 250)', display: 'block', marginBottom: '0.375rem' }}>
                      {item.term}
                    </span>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: 'oklch(75% 0.02 250)', lineHeight: 1.6 }}>
                      {item.meaning}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tab 5: Live Engine State */}
          {!isLoading && data && activeTab === 'ENGINE' && (
            <div style={{ flex: 1, overflowY: 'auto', padding: '2rem', maxWidth: '900px', margin: '0 auto' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                <div>
                  <h3 style={{ fontSize: '1.25rem', fontWeight: 800, margin: 0, color: 'oklch(95% 0.01 250)' }}>
                    Aktywny Status Silnika Obliczeniowego
                  </h3>
                  <p style={{ margin: '4px 0 0 0', fontSize: '0.8125rem', color: 'oklch(65% 0.02 250)' }}>
                    Ta sekcja aktualizuje się w czasie rzeczywistym bezpośrednio z kodu produkcyjnego.
                  </p>
                </div>
                <span
                  style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    padding: '0.25rem 0.625rem',
                    borderRadius: '6px',
                    background: 'oklch(20% 0.05 170)',
                    color: 'oklch(78% 0.16 168)',
                    border: '1px solid oklch(35% 0.08 168)',
                  }}
                >
                  Połączono z bazą wiedzy
                </span>
              </div>

              <div style={{ display: 'grid', gap: '1rem', marginTop: '1.25rem' }}>
                <div style={{ background: 'oklch(14% 0.02 250)', border: '1px solid oklch(22% 0.03 250)', borderRadius: '12px', padding: '1.25rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'oklch(75% 0.12 80)', marginBottom: '0.75rem' }}>
                    Zarejestrowane Solvery i Moduły Obliczeniowe ({data.engine_status.active_solvers_count})
                  </div>
                  {data.engine_status.solvers.map((s, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        padding: '0.75rem 0',
                        borderBottom: idx < data.engine_status.solvers.length - 1 ? '1px solid oklch(20% 0.02 250)' : 'none',
                      }}
                    >
                      <div>
                        <span style={{ fontWeight: 800, fontSize: '0.9375rem', color: 'oklch(95% 0.01 250)' }}>
                          {s.name}
                        </span>
                        <span style={{ marginLeft: '0.625rem', fontSize: '0.75rem', color: 'oklch(60% 0.01 250)' }}>
                          {s.kind}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'oklch(78% 0.14 168)' }}>
                        {s.status}
                      </span>
                    </div>
                  ))}
                </div>

                <div style={{ background: 'oklch(14% 0.02 250)', border: '1px solid oklch(22% 0.03 250)', borderRadius: '12px', padding: '1.25rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'oklch(75% 0.12 80)', marginBottom: '0.75rem' }}>
                    Obsługiwane Klasy Dylematów
                  </div>
                  <ul style={{ margin: 0, paddingLeft: '1.25rem', color: 'oklch(80% 0.015 250)', fontSize: '0.84375rem', lineHeight: 1.8 }}>
                    {data.engine_status.supported_dilemma_types.map((type, idx) => (
                      <li key={idx}>{type}</li>
                    ))}
                  </ul>
                </div>

                <div style={{ background: 'oklch(14% 0.02 250)', border: '1px solid oklch(22% 0.03 250)', borderRadius: '12px', padding: '1.25rem' }}>
                  <div style={{ fontSize: '0.75rem', fontWeight: 700, textTransform: 'uppercase', color: 'oklch(75% 0.12 80)', marginBottom: '0.375rem' }}>
                    Protokół Weryfikacji
                  </div>
                  <p style={{ margin: 0, fontSize: '0.84375rem', color: 'oklch(80% 0.015 250)', lineHeight: 1.6 }}>
                    {data.engine_status.verification_mode}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
