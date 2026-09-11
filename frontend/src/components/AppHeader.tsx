import React from 'react'

interface AppHeaderProps {
  onReset: () => void
  isBusy: boolean
  onOpenHelp?: () => void
  onOpenBrain?: () => void
}

export const AppHeader: React.FC<AppHeaderProps> = ({ onReset, isBusy, onOpenHelp, onOpenBrain }) => {
  return (
    <header
      className="no-print"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 clamp(1rem, 4vw, 2.5rem)',
        background: 'oklch(6% 0.01 250 / 0.94)',
        backdropFilter: 'blur(18px) saturate(1.4)',
        WebkitBackdropFilter: 'blur(18px) saturate(1.4)',
        borderBottom: '1px solid oklch(18% 0.022 250)',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        height: '64px',
        flexShrink: 0,
        boxShadow: '0 1px 0 oklch(75% 0.12 80 / 0.06), 0 4px 24px oklch(0% 0 0 / 0.4)',
      }}
    >
      {/* Logo — big and visible */}
      <button
        onClick={onReset}
        style={{
          background: 'none',
          border: 'none',
          padding: 0,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}
        aria-label="YourQuantum — wróć do strony głównej"
        title="Wróć do strony głównej"
      >
        {/* Logo badge */}
        <div style={{
          position: 'relative',
          width: '40px',
          height: '40px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'oklch(75% 0.12 80)',
            borderRadius: '10px',
            boxShadow: '0 0 20px oklch(75% 0.12 80 / 0.6), 0 0 40px oklch(75% 0.12 80 / 0.25)',
          }} />
          <span style={{
            position: 'relative',
            fontSize: '1.0625rem',
            fontWeight: 900,
            color: 'oklch(6% 0.01 250)',
            letterSpacing: '-0.04em',
            lineHeight: 1,
          }}>
            YQ
          </span>
        </div>

        {/* Wordmark */}
        <div>
          <div style={{
            fontSize: '1.1875rem',
            fontWeight: 900,
            letterSpacing: '-0.035em',
            lineHeight: 1,
            background: 'linear-gradient(125deg, oklch(97% 0.008 250) 45%, oklch(75% 0.12 80) 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text',
          }}>
            YourQuantum
          </div>
          <div style={{
            fontSize: '0.625rem',
            fontWeight: 700,
            letterSpacing: '0.14em',
            textTransform: 'uppercase',
            color: 'oklch(62% 0.18 240 / 0.8)',
            marginTop: '1px',
          }}>
            Quantum Decision Engine
          </div>
        </div>
      </button>

      {/* Right side */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.625rem' }}>
        {/* 3D Brain Button */}
        {onOpenBrain && (
          <button
            onClick={onOpenBrain}
            style={{
              background: 'oklch(14% 0.025 250)',
              border: '1px solid oklch(28% 0.04 250)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.45rem 0.875rem',
              fontSize: '0.8125rem',
              color: 'oklch(90% 0.02 250)',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              transition: 'all 200ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'oklch(18% 0.035 250)'
              e.currentTarget.style.borderColor = 'oklch(40% 0.08 240)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'oklch(14% 0.025 250)'
              e.currentTarget.style.borderColor = 'oklch(28% 0.04 250)'
            }}
            title="Otwórz interaktywną wizualizację 3D mózgu silnika"
          >
            <span style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#4df0ff',
              boxShadow: '0 0 8px #4df0ff',
            }} />
            <span>Mózg Silnika 3D</span>
          </button>
        )}

        {/* Help Center Button */}
        {onOpenHelp && (
          <button
            onClick={onOpenHelp}
            style={{
              background: 'oklch(14% 0.025 250)',
              border: '1px solid oklch(28% 0.04 250)',
              borderRadius: 'var(--radius-sm)',
              padding: '0.45rem 0.875rem',
              fontSize: '0.8125rem',
              color: 'oklch(90% 0.02 250)',
              fontWeight: 700,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              transition: 'all 200ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'oklch(18% 0.035 250)'
              e.currentTarget.style.borderColor = 'oklch(40% 0.08 80)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'oklch(14% 0.025 250)'
              e.currentTarget.style.borderColor = 'oklch(28% 0.04 250)'
            }}
            title="Otwórz przewodnik dla laików i bazę wiedzy"
          >
            <span style={{
              width: '18px',
              height: '18px',
              borderRadius: '50%',
              background: 'oklch(75% 0.12 80 / 0.2)',
              color: 'oklch(75% 0.12 80)',
              fontSize: '0.6875rem',
              fontWeight: 900,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>?</span>
            <span>Pomoc dla Laików</span>
          </button>
        )}

        {/* Live status badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4375rem',
          padding: '0.375rem 0.75rem',
          borderRadius: 'var(--radius-full)',
          background: isBusy
            ? 'oklch(16% 0.04 70)'
            : 'oklch(16% 0.04 170)',
          border: `1px solid ${isBusy
            ? 'oklch(36% 0.09 72)'
            : 'oklch(35% 0.08 168)'}`,
          fontSize: '0.75rem',
          fontWeight: 600,
          color: isBusy
            ? 'oklch(80% 0.14 72)'
            : 'oklch(78% 0.14 168)',
          transition: 'all 300ms ease',
          whiteSpace: 'nowrap',
        }}>
          <span style={{
            width: '6px',
            height: '6px',
            borderRadius: '50%',
            background: isBusy ? 'oklch(80% 0.14 72)' : 'oklch(78% 0.14 168)',
            display: 'inline-block',
            flexShrink: 0,
            boxShadow: isBusy
              ? '0 0 8px oklch(80% 0.14 72 / 0.8)'
              : '0 0 8px oklch(78% 0.14 168 / 0.8)',
            animation: isBusy ? 'headerDotPulse 1.4s ease-in-out infinite' : 'none',
          }} />
          <span>{isBusy ? 'Obliczanie...' : 'Weryfikacja aktywna'}</span>
        </div>

        {/* New problem CTA */}
        <button
          onClick={onReset}
          style={{
            background: 'oklch(75% 0.12 80)',
            border: 'none',
            borderRadius: 'var(--radius-sm)',
            padding: '0.45rem 1rem',
            fontSize: '0.8125rem',
            color: 'oklch(6% 0.01 250)',
            fontWeight: 800,
            cursor: 'pointer',
            letterSpacing: '-0.01em',
            transition: 'background 200ms ease, transform 150ms ease',
            boxShadow: '0 0 16px oklch(75% 0.12 80 / 0.35)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'oklch(83% 0.14 80)'
            e.currentTarget.style.transform = 'translateY(-1px)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'oklch(75% 0.12 80)'
            e.currentTarget.style.transform = 'translateY(0)'
          }}
        >
          Nowy dylemat
        </button>
      </div>


      <style>{`
        @keyframes headerDotPulse {
          0%, 100% { opacity: 1; }
          50%       { opacity: 0.4; }
        }
      `}</style>
    </header>
  )
}
