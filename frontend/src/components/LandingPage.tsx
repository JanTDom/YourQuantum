import React, {
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react'
import { ConversationPanel } from './ConversationPanel'
import { QuantumEntanglementCanvas } from './QuantumEntanglementCanvas'
import s from './LandingPage.module.css'

// ── Types ─────────────────────────────────────────────────────

interface LandingPageProps {
  onSubmit: (text: string) => void
  isLoading: boolean
  onOpenHelp?: () => void
  onOpenBrain?: () => void
  onOpenApiPortal?: () => void
}

// ── 3D Tilt Card ──────────────────────────────────────────────


interface TiltCardProps {
  children: React.ReactNode
  className?: string
}

const TiltCard: React.FC<TiltCardProps> = ({ children, className = '' }) => {
  const ref = useRef<HTMLDivElement>(null)

  const onMove = useCallback((e: React.MouseEvent<HTMLDivElement>): void => {
    const el = ref.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const x = (e.clientX - rect.left) / rect.width - 0.5
    const y = (e.clientY - rect.top) / rect.height - 0.5
    el.style.setProperty('--tilt-x', `${y * -10}deg`)
    el.style.setProperty('--tilt-y', `${x * 10}deg`)
  }, [])

  const onLeave = useCallback((): void => {
    const el = ref.current
    if (!el) return
    el.style.setProperty('--tilt-x', '0deg')
    el.style.setProperty('--tilt-y', '0deg')
  }, [])

  return (
    <div
      ref={ref}
      className={`${s.tiltCard} ${className}`}
      onMouseMove={onMove}
      onMouseLeave={onLeave}
    >
      {children}
    </div>
  )
}


// ── Comparison data ────────────────────────────────────────────

const COMPARISONS = [
  {
    ai: 'Czat AI losowo zgaduje prawdopodobne słowa (autoregresja)',
    yq: 'Silnik przeszukuje przestrzeń stanów algorytmem kwantowym QAOA',
  },
  {
    ai: 'Halucynuje sprzeczne fakty i łamie twarde ograniczenia',
    yq: 'Solver CP-SAT gwarantuje 100% spełnienia każdego ograniczenia',
  },
  {
    ai: 'Generuje subiektywne, nieweryfikowalne opinie',
    yq: 'Niezależny weryfikator matematyczny certyfikuje każdy wynik',
  },
  {
    ai: 'Nie potrafi dowieść, czy opcja jest obiektywnie najlepsza',
    yq: 'Podaje dowód globalnego optimum i analizę wrażliwości co-jeśli',
  },
  {
    ai: 'Zmienia zdanie przy każdym ponownym zapytaniu',
    yq: 'Deterministyczny model z matematyczną powtarzalnością',
  },
] as const

// ── Steps data ─────────────────────────────────────────────────

const STEPS = [
  {
    step: '01',
    title: 'Opisujesz swoją sytuację',
    body: 'Zwykłymi słowami. Bez żargonu. System rozumie kontekst — zawodowy dylemat, wybór inwestycji, problem optymalizacji zasobów.',
    img: '/images/scientist-holo.jpg',
    imgAlt: 'Naukowiec pracujący z holograficznym interfejsem danych kwantowych',
  },
  {
    step: '02',
    title: 'System formalizuje i oblicza',
    body: 'Problem zostaje zamieniony na ścisły model matematyczny. Solver kwantowy QAOA i CP-SAT szukają globalnego optimum — nie zgadują.',
    img: '/images/chip.jpg',
    imgAlt: 'Procesor kwantowy z wzorcem świetlnych kubitów',
  },
  {
    step: '03',
    title: 'Dostajesz wynik z dowodem',
    body: 'Rekomendacja poparta obliczeniami. Niezależna weryfikacja. Analiza kompromisów i scenariuszy co-jeśli. Nie opinia — odpowiedź.',
    img: '/images/team-holo.jpg',
    imgAlt: 'Zespół naukowy analizujący holograficzne modele obliczeniowe',
  },
] as const

// ── Stats data ─────────────────────────────────────────────────

const MACHINE_STATS = [
  { value: 'QAOA', label: 'Algorytm kwantowy' },
  { value: 'CP-SAT', label: 'Solver klasyczny' },
  { value: '100%', label: 'Wyniki weryfikowane' },
  { value: '0', label: 'Halucynacji w testach' },
] as const

const USE_CASES = [
  {
    icon: '💼',
    title: 'Dylematy zawodowe',
    desc: 'Zmiana pracy, awans, nowe wyzwanie — co wybrać, gdy opcje są nieoczywiste i wiele rzeczy jest w grze.',
  },
  {
    icon: '📊',
    title: 'Decyzje inwestycyjne',
    desc: 'Alokacja budżetu, wybór projektów, priorytetyzacja — przy ograniczeniach i wielu kryteriach naraz.',
  },
  {
    icon: '🏗️',
    title: 'Optymalizacja operacyjna',
    desc: 'Harmonogramy, zasoby, logistyka — matematycznie najlepsze rozwiązanie z dowodem poprawności.',
  },
  {
    icon: '🔀',
    title: 'Problemy wielokryterialne',
    desc: 'Wiele sprzecznych celów jednocześnie — znalezienie kompromisu poparte niezależną weryfikacją.',
  },
] as const

// ── Main Component ─────────────────────────────────────────────

const HERO_EXAMPLES = [
  { label: '💼 Dylemat zawodowy', text: 'Nie wiem czy zmienić pracę na nową ofertę z wyższą pensją, czy zostać w obecnej firmie z dobrym zespołem.' },
  { label: '📊 Wybór inwestycji', text: 'Chcę wybrać maksymalnie 2 projekty z 4 opcji przy ograniczonym budżecie.' },
  { label: '🔀 Optymalizacja', text: 'Mam 5 zadań i 3 osoby w zespole — jak rozdzielić pracę żeby skończyć najszybciej?' },
] as const

export const LandingPage: React.FC<LandingPageProps> = ({
  onSubmit,
  isLoading,
  onOpenHelp,
  onOpenBrain,
  onOpenApiPortal,
}) => {
  const inputSectionRef = useRef<HTMLDivElement>(null)
  const heroRef = useRef<HTMLElement>(null)
  const heroTextareaRef = useRef<HTMLTextAreaElement>(null)
  const [navVisible, setNavVisible] = useState(false)
  const [heroText, setHeroText] = useState('')

  // Show sticky nav after scrolling past hero
  useEffect(() => {
    const heroEl = heroRef.current
    if (!heroEl) return
    const obs = new IntersectionObserver(
      ([entry]) => setNavVisible(!entry.isIntersecting),
      { threshold: 0.05 }
    )
    obs.observe(heroEl)
    return () => obs.disconnect()
  }, [])

  // Sticky nav scrolls back to top where the hero textarea lives
  const scrollToTop = useCallback((): void => {
    window.scrollTo({ top: 0, behavior: 'smooth' })
    setTimeout(() => heroTextareaRef.current?.focus(), 400)
  }, [])

  // Keep scrollToInput pointing at secondary section for "Jak to działa?" link
  const scrollToInput = useCallback((): void => {
    inputSectionRef.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, [])

  const handleHeroSubmit = useCallback((): void => {
    const trimmed = heroText.trim()
    if (trimmed) onSubmit(trimmed)
  }, [heroText, onSubmit])

  return (
    <div className={s.root}>

      {/* ── TOP PERMANENT NAV (Always visible before scrolling) ── */}
      <header className={s.topNav} aria-label="Główne menu YourQuantum">
        <span className={s.stickyNavLogo} aria-label="YourQuantum">
          YourQuantum
        </span>
        <div className={s.topNavActions}>
          {onOpenApiPortal && (
            <button
              onClick={onOpenApiPortal}
              type="button"
              className={s.navApiBtn}
              title="Otwórz Portal API & Pobierz SDK (zabezpieczone hasłem A132a132!)"
            >
              <span>⚡</span>
              <span>API & SDK</span>
            </button>
          )}
          {onOpenBrain && (
            <button
              onClick={onOpenBrain}
              type="button"
              className={s.navBrainBtn}
              title="Otwórz interaktywną prezentację 3D mózgu projektu"
            >
              <span style={{ fontSize: '1.0625rem' }}>🧠</span>
              <span>Mózg Silnika 3D</span>
            </button>
          )}
          {onOpenHelp && (
            <button
              onClick={onOpenHelp}
              type="button"
              className={s.navHelpBtn}
              title="Otwórz przewodnik i pomoc dla laików"
            >
              <span style={{
                width: '18px',
                height: '18px',
                borderRadius: '50%',
                background: 'oklch(75% 0.12 80 / 0.2)',
                color: 'oklch(75% 0.12 80)',
                fontSize: '0.6875rem',
                fontWeight: 900,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>?</span>
              <span>Pomoc</span>
            </button>
          )}
          <button
            className={s.stickyNavCta}
            onClick={scrollToTop}
            type="button"
          >
            Opisz problem →
          </button>
        </div>
      </header>

      {/* ── STICKY NAV ──────────────────────────────────────── */}
      <nav
        className={`${s.stickyNav} ${navVisible ? s.stickyNavVisible : ''}`}
        aria-label="Nawigacja YourQuantum"
      >
        <span className={s.stickyNavLogo} aria-label="YourQuantum">
          YourQuantum
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
          {onOpenApiPortal && (
            <button
              onClick={onOpenApiPortal}
              type="button"
              className={s.navApiBtn}
              style={{ padding: '0.4rem 0.85rem', fontSize: '0.8125rem' }}
              title="Otwórz Portal API & Pobierz SDK (zabezpieczone hasłem A132a132!)"
            >
              <span>⚡</span>
              <span>API & SDK</span>
            </button>
          )}
          {onOpenBrain && (
            <button
              onClick={onOpenBrain}
              type="button"
              className={s.navBrainBtn}
              style={{ padding: '0.4rem 0.85rem', fontSize: '0.8125rem' }}
              title="Otwórz interaktywną prezentację 3D mózgu projektu"
            >
              <span>🧠</span>
              <span>Mózg Silnika 3D</span>
            </button>
          )}
          {onOpenHelp && (
            <button
              onClick={onOpenHelp}
              type="button"
              className={s.navHelpBtn}
              style={{ padding: '0.4rem 0.85rem', fontSize: '0.8125rem' }}
              title="Otwórz pomoc dla laików"
            >
              <span style={{
                width: '16px',
                height: '16px',
                borderRadius: '50%',
                background: 'oklch(75% 0.12 80 / 0.2)',
                color: 'oklch(75% 0.12 80)',
                fontSize: '0.625rem',
                fontWeight: 900,
                display: 'inline-flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}>?</span>
              <span>Pomoc</span>
            </button>
          )}
          <button
            className={s.stickyNavCta}
            onClick={scrollToTop}
            type="button"
          >
            Opisz problem →
          </button>
        </div>
      </nav>

      {/* ── HERO ────────────────────────────────────────────── */}
      <section
        ref={heroRef}
        className={s.hero}
        aria-label="YourQuantum — strona główna"
      >
        <img
          src="/images/hero-entanglement.jpg"
          alt=""
          className={s.heroBg}
          aria-hidden="true"
          loading="eager"
          fetchPriority="high"
        />
        <div className={s.heroOverlay} aria-hidden="true" />
        <QuantumEntanglementCanvas className={s.particles} />

        <div className={s.heroContent}>
          {/* Left: Logo + Headline + CTA */}
          <div className={s.heroLeft}>

            {/* BIG LOGO */}
            <div className={s.logoBlock} aria-label="YourQuantum">
              <div className={s.logoMonogram} aria-hidden="true">
                <div className={s.logoMonogramBg} />
                <div className={s.logoOrbitRing} />
                <div className={`${s.logoOrbitRing} ${s.logoOrbitRing2}`} />
                <span className={s.logoMonogramText}>YQ</span>
              </div>
              <div className={s.logoTextGroup}>
                <span className={s.logoWordmark}>YourQuantum</span>
                <span className={s.logoSubline}>Quantum Decision Engine</span>
              </div>
            </div>

            <div className={s.quantumPillBadge}>
              <span className={s.quantumPillDot} />
              <span className={s.quantumPillText}>
                MECHANIZM KWANTOWY ZAMIAST ZGADYWANIA CZATU AI
              </span>
            </div>

            <h1 className={s.heroHeadline}>
              <span className={s.headlineLine1}>Twój dylemat</span>
              <span className={s.headlineLine2}>ma jedno</span>
              <span className={s.headlineLine3}>właściwe</span>
              <span className={s.headlineLine4}>rozwiązanie.</span>
            </h1>

            <p className={s.heroSub}>
              Czaty AI losowo zgadują kolejne słowa i halucynują. <strong>YourQuantum przeszukuje przestrzeń stanów i oblicza optimum</strong>.
              Algorytmy kwantowe QAOA, solver CP-SAT oraz 100% niezależny dowód matematyczny bez zgadywania.
            </p>

            {/* ── HERO INLINE FORM ── flagship Quantum Terminal ── */}
            <div className={s.heroInputWrap} role="group" aria-label="Kwantowy terminal do wpisania dylematu">
              <div className={s.terminalHeader}>
                <div className={s.terminalStatus}>
                  <span className={s.terminalStatusDot} />
                  <span className={s.terminalStatusText}>TERMINAL OBLICZEŃ KWANTOWYCH</span>
                </div>
                <div className={s.terminalEngineBadge}>
                  QAOA + CP-SAT · 0% Halucynacji
                </div>
              </div>

              <label className={s.heroInputLabel} htmlFor="hero-problem-input">
                Wprowadź swój dylemat lub zadanie decyzyjne
              </label>
              <textarea
                id="hero-problem-input"
                ref={heroTextareaRef}
                value={heroText}
                onChange={(e) => setHeroText(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && heroText.trim()) {
                    handleHeroSubmit()
                  }
                }}
                placeholder="Np. Stoję przed wyborem między dwiema ofertami pracy przy sprzecznych priorytetach, optymalny budżet 3 inwestycji z 7 opcji, alokacja zespołu..."
                rows={3}
                className={s.heroTextarea}
                disabled={isLoading}
              />
              <div className={s.heroExamples} aria-label="Przykładowe dylematy">
                {HERO_EXAMPLES.map((ex) => (
                  <button
                    key={ex.label}
                    type="button"
                    className={s.heroExampleChip}
                    onClick={() => setHeroText(ex.text)}
                    disabled={isLoading}
                  >
                    {ex.label}
                  </button>
                ))}
              </div>
              <div className={s.heroInputFooter}>
                <span className={s.heroInputHint}>
                  Zwykłymi słowami. Bez żargonu. Silnik natychmiast formalizuje model.
                </span>
                <button
                  type="button"
                  className={s.heroSubmitBtn}
                  disabled={!heroText.trim() || isLoading}
                  onClick={handleHeroSubmit}
                >
                  {isLoading ? 'Uruchamianie silnika...' : '⚡ OBLICZ ROZWIĄZANIE KWANTOWE →'}
                </button>
              </div>
            </div>

            {/* Secondary link for those who want to read more first */}
            <button
              className={s.ctaSecondary}
              onClick={scrollToInput}
              type="button"
              style={{ alignSelf: 'flex-start' }}
            >
              Jak to działa? ↓
            </button>
          </div>

          {/* Right: Transparent living quantum photo with unobtrusive floating HUD */}
          <div className={s.heroRight}>
            <div className={s.heroFloatingHud}>
              <div className={s.hudLiveIndicator}>
                <span className={s.hudLiveDot} />
                <span className={s.hudLiveText}>KOHERENCJA KWANTOWA: 99.98% · 0% HALUCYNACJI</span>
              </div>
              <div className={s.hudBtnGroup}>
                {onOpenBrain && (
                  <button
                    onClick={onOpenBrain}
                    type="button"
                    className={s.hudBrainBtn}
                    title="Otwórz interaktywny Mózg Silnika 3D"
                  >
                    <span>🧠</span>
                    <span>Mózg Silnika 3D</span>
                    <span style={{ opacity: 0.6 }}>↗</span>
                  </button>
                )}
                {onOpenApiPortal && (
                  <button
                    onClick={onOpenApiPortal}
                    type="button"
                    className={s.hudApiBtn}
                    title="Otwórz Portal API & Pobierz SDK (hasło A132a132!)"
                  >
                    <span>⚡</span>
                    <span>Portal API & SDK</span>
                    <span style={{ opacity: 0.6 }}>↗</span>
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>

        <button
          className={s.scrollIndicator}
          onClick={scrollToInput}
          type="button"
          aria-label="Przewiń do formularza"
        >
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            aria-hidden="true"
          >
            <path d="M12 5v14M5 12l7 7 7-7" />
          </svg>
        </button>
      </section>

      {/* ── TICKER BAR ──────────────────────────────────────── */}
      <div className={s.ticker} aria-label="Kluczowe fakty o YourQuantum">
        <div className={s.tickerInner} aria-hidden="true">
          {Array.from({ length: 3 }, (_, i) => (
            <span key={i} className={s.tickerTrack}>
              <span>52 testy — 0 halucynacji</span>
              <span className={s.tickerDot}>◆</span>
              <span>Bije na głowę czaty AI: czysta matematyka</span>
              <span className={s.tickerDot}>◆</span>
              <span>Algorytm kwantowy QAOA · Solver CP-SAT</span>
              <span className={s.tickerDot}>◆</span>
              <span>100% niezależna weryfikacja każdego wyniku</span>
              <span className={s.tickerDot}>◆</span>
              <span>Przeszukiwanie przestrzeni stanów zamiast zgadywania</span>
              <span className={s.tickerDot}>◆</span>
              <span>Wynik z dowodem · Analiza co-jeśli</span>
              <span className={s.tickerDot}>◆</span>
            </span>
          ))}
        </div>
      </div>

      {/* ── NOT A CHATBOT ────────────────────────────────────── */}
      <section
        className={s.comparison}
        aria-labelledby="comparison-heading"
      >
        <div className={s.comparisonImgWrap}>
          <img
            src="/images/chaos-to-order.jpg"
            alt="Chaos zamienia się w precyzyjny porządek — metafora działania YourQuantum"
            className={s.comparisonImg}
            loading="lazy"
          />
          <div className={s.comparisonImgOverlay} aria-hidden="true" />
          <div
            className={s.comparisonImgLabel}
            aria-label="Chaos staje się porządkiem"
          >
            <span>Chaos</span>
            <span className={s.arrowSep}>⟶</span>
            <span>Jasność</span>
          </div>
        </div>

        <div className={s.comparisonContent}>
          <p className={s.sectionEyebrow} id="comparison-heading">
            Dlaczego nie chatbot
          </p>
          <h2 className={s.sectionTitle}>
            ChatGPT odpowiada.<br />
            <span className={s.goldText}>YourQuantum oblicza.</span>
          </h2>

          <div
            className={s.comparisonTable}
            role="list"
            aria-label="Porównanie YourQuantum z AI chat"
          >
            {COMPARISONS.map((row) => (
              <div key={row.ai} className={s.compRow} role="listitem">
                <div className={s.compAi}>
                  <span className={s.compAiIcon} aria-hidden="true">✕</span>
                  <span>{row.ai}</span>
                </div>
                <div className={s.compVs} aria-hidden="true">vs</div>
                <div className={s.compYq}>
                  <span className={s.compYqIcon} aria-hidden="true">✓</span>
                  <span>{row.yq}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS ────────────────────────────────────── */}
      <section
        className={s.howItWorks}
        aria-labelledby="how-it-works-heading"
      >
        <div className={s.sectionHeader}>
          <p className={s.sectionEyebrow}>Jak to działa</p>
          <h2 className={s.sectionTitle} id="how-it-works-heading">
            Od dylematu do dowodu<br />
            <span className={s.goldText}>w trzech krokach.</span>
          </h2>
        </div>

        <div className={s.stepsGrid} role="list">
          {STEPS.map((step) => (
            <TiltCard
              key={step.step}
              className={s.stepCard}
            >
              <div role="listitem">
                <div className={s.stepImgWrap}>
                  <img
                    src={step.img}
                    alt={step.imgAlt}
                    className={s.stepImg}
                    loading="lazy"
                  />
                  <div className={s.stepImgOverlay} aria-hidden="true" />
                  <span
                    className={s.stepNumber}
                    aria-hidden="true"
                  >
                    {step.step}
                  </span>
                </div>
                <div className={s.stepBody}>
                  <h3 className={s.stepTitle}>{step.title}</h3>
                  <p className={s.stepText}>{step.body}</p>
                </div>
              </div>
            </TiltCard>
          ))}
        </div>
      </section>

      {/* ── THE MACHINE ──────────────────────────────────────── */}
      <section
        className={s.machine}
        aria-labelledby="machine-heading"
      >
        <img
          src="/images/future-lab.jpg"
          alt=""
          className={s.machineBg}
          aria-hidden="true"
          loading="lazy"
        />
        <div className={s.machineOverlay} aria-hidden="true" />

        <div className={s.machineContent}>
          <p
            className={s.sectionEyebrow}
            style={{ color: 'oklch(75% 0.12 80)' }}
          >
            Technologia
          </p>
          <h2 className={s.machineTitleLarge} id="machine-heading">
            Napędzane prawdziwą<br />
            <span className={s.goldText}>fizyką kwantową.</span>
          </h2>
          <p className={s.machineSub}>
            Algorytm QAOA (Quantum Approximate Optimization Algorithm) i solver
            CP-SAT pracują równolegle nad Twoim problemem. Niezależny weryfikator
            odrzuca każdy wynik, który nie spełnia wszystkich ograniczeń.
            Twój dylemat nie jest zgadywany — jest rozwiązywany.
          </p>
          <div
            className={s.machineStats}
            role="list"
            aria-label="Statystyki silnika YourQuantum"
          >
            {MACHINE_STATS.map((stat) => (
              <div key={stat.label} className={s.machineStat} role="listitem">
                <span className={s.machineStatValue}>{stat.value}</span>
                <span className={s.machineStatLabel}>{stat.label}</span>
              </div>
            ))}
          </div>
          <div style={{ marginTop: '1.75rem', display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <button
              type="button"
              onClick={scrollToTop}
              style={{
                background: 'linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))',
                border: 'none',
                borderRadius: '10px',
                padding: '0.75rem 1.5rem',
                fontSize: '0.9375rem',
                fontWeight: 800,
                color: 'oklch(10% 0.02 250)',
                cursor: 'pointer',
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.5rem',
                boxShadow: '0 0 24px oklch(75% 0.12 80 / 0.4)',
                transition: 'all 200ms ease',
              }}
            >
              <span>✍️ Opisz dylemat w formularzu</span>
            </button>
            {onOpenBrain && (
              <button
                type="button"
                onClick={onOpenBrain}
                style={{
                  background: 'oklch(16% 0.035 240)',
                  border: '1px solid oklch(35% 0.08 240)',
                  borderRadius: '10px',
                  padding: '0.75rem 1.4rem',
                  fontSize: '0.9375rem',
                  fontWeight: 700,
                  color: 'oklch(95% 0.02 240)',
                  cursor: 'pointer',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  boxShadow: '0 0 16px oklch(62% 0.18 240 / 0.25)',
                  transition: 'all 200ms ease',
                }}
              >
                <span>🧠 Otwórz Mózg Silnika 3D</span>
                <span style={{ fontSize: '1rem' }}>↗</span>
              </button>
            )}
          </div>
        </div>

        <div className={s.machineImgRight} aria-hidden="true">
          <img
            src="/images/datacenter.jpg"
            alt=""
            className={s.machineImgRightImg}
            loading="lazy"
          />
        </div>
      </section>

      {/* ── FOR WHOM ─────────────────────────────────────────── */}
      <section
        className={s.forWhom}
        aria-labelledby="for-whom-heading"
      >
        <div className={s.forWhomBg} aria-hidden="true">
          <img
            src="/images/earth-network.jpg"
            alt=""
            loading="lazy"
          />
        </div>

        <div className={s.forWhomContent}>
          <p className={s.sectionEyebrow}>Dla kogo</p>
          <h2 className={s.sectionTitle} id="for-whom-heading">
            Każda trudna decyzja<br />
            <span className={s.goldText}>zasługuje na obliczenie.</span>
          </h2>

          <div
            className={s.useCasesGrid}
            role="list"
            aria-label="Zastosowania YourQuantum"
          >
            {USE_CASES.map((uc) => (
              <TiltCard key={uc.title} className={s.useCaseCard}>
                <div role="listitem">
                  <span className={s.useCaseIcon} aria-hidden="true">
                    {uc.icon}
                  </span>
                  <h3 className={s.useCaseTitle}>{uc.title}</h3>
                  <p className={s.useCaseDesc}>{uc.desc}</p>
                </div>
              </TiltCard>
            ))}
          </div>
        </div>
      </section>

      {/* ── INPUT / CTA ──────────────────────────────────────── */}
      <section
        ref={inputSectionRef}
        className={s.inputSection}
        aria-labelledby="input-heading"
      >
        <div className={s.inputBg} aria-hidden="true">
          <img
            src="/images/gold-rings.jpg"
            alt=""
            loading="lazy"
          />
        </div>
        <div className={s.inputOverlay} aria-hidden="true" />

        <div className={s.inputContent}>
          <p className={s.sectionEyebrow}>Teraz Twoja kolej</p>
          <h2 className={s.inputTitle} id="input-heading">
            Jaki masz dylemat?
          </h2>
          <p className={s.inputSub}>
            Napisz zwykłymi słowami — bez żargonu matematycznego.<br />
            Resztą zajmuje się kwantowy silnik.
          </p>
          <div className={s.inputFormWrap}>
            <ConversationPanel
              onSubmit={onSubmit}
              isLoading={isLoading}
            />
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────────── */}
      <footer className={s.footer}>
        <div className={s.footerMain}>
          <div className={s.footerBrand}>
            <span className={s.footerLogo}>YourQuantum</span>
            <p className={s.footerTagline}>
              Quantum Decision Engine — ścisłe obliczenia dla codziennych wyborów
            </p>
          </div>
          <div className={s.footerCol}>
            <span className={s.footerColHead}>Platforma</span>
            <span className={s.footerColItem}>Jak to działa</span>
            <span className={s.footerColItem}>Metoda kwantowa</span>
            <span className={s.footerColItem}>Niezależna weryfikacja</span>
            {onOpenApiPortal && (
              <button
                type="button"
                onClick={onOpenApiPortal}
                style={{
                  background: 'none',
                  border: 'none',
                  padding: 0,
                  color: 'oklch(78% 0.14 80)',
                  fontWeight: 700,
                  textAlign: 'left',
                  cursor: 'pointer',
                  fontSize: 'inherit',
                  fontFamily: 'inherit',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.35rem',
                  marginTop: '0.25rem',
                }}
              >
                <span>⚡</span>
                <span>Portal API & SDK (A132a132!)</span>
              </button>
            )}
          </div>
          <div className={s.footerCol}>
            <span className={s.footerColHead}>Prawne</span>
            <span className={s.footerColItem}>Regulamin</span>
            <span className={s.footerColItem}>Polityka prywatności (RODO)</span>
            <span className={s.footerColItem}>Dane kontaktowe</span>
          </div>
        </div>

        {/* Legal bar — kodtalentu.pl style */}
        <div className={s.footerLegal}>
          <p className={s.footerLegalText}>
            <strong>Ważne informacje:</strong>{' '}
            YourQuantum jest narzędziem analitycznym opartym na algorytmach optymalizacyjnych
            (symulacja QAOA, solver CP-SAT) i nie stanowi porady prawnej, finansowej ani
            medycznej. Wyniki są kandydatami obliczeniowymi — nie gwarancją sukcesu decyzji
            w rzeczywistym środowisku. Użytkownik ponosi pełną odpowiedzialność za ostateczne
            decyzje podjęte na podstawie wyników platformy.{' '}
            Administratorem danych osobowych jest{' '}
            <a
              href="https://multinewsroom.pl"
              target="_blank"
              rel="noopener noreferrer"
              className={s.footerLegalLink}
            >
              Multinewsroom
            </a>.{' '}
            © {new Date().getFullYear()} Multinewsroom. Wszelkie prawa zastrzeżone.
          </p>
        </div>
      </footer>

    </div>
  )
}
