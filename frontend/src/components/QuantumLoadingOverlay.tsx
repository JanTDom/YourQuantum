import React, { useState, useEffect } from 'react'

interface QuantumLoadingOverlayProps {
  statusMessage?: string | null
}

const PHASES = [
  'Inicjalizacja pętli Active Inference i ekstrakcja przesłanek...',
  'Budowa przestrzeni stanów i hamiltonianu sprzężeń...',
  'Symulacja ewolucji unitarnej w symulatorze Qiskit Aer...',
  'Kwantowa kombinatoryka stanów i próbkowanie Borna P(s) = |⟨s|ψ⟩|²...',
  'Niezależna weryfikacja ograniczeń brzegowych (0 naruszeń)...',
]

export const QuantumLoadingOverlay: React.FC<QuantumLoadingOverlayProps> = ({ statusMessage }) => {
  const [phaseIndex, setPhaseIndex] = useState(0)

  useEffect(() => {
    const interval = setInterval(() => {
      setPhaseIndex((prev) => (prev + 1) % PHASES.length)
    }, 2200)
    return () => clearInterval(interval)
  }, [])

  return (
    <div
      role="status"
      aria-live="polite"
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 9999,
        background: 'oklch(6% 0.015 250 / 0.85)',
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
        animation: 'fadeIn 300ms ease-out forwards',
      }}
    >
      <style>{`
        @keyframes fadeIn {
          from { opacity: 0; transform: scale(0.98); }
          to { opacity: 1; transform: scale(1); }
        }
        @keyframes quantumOrbit1 {
          0% { transform: rotateX(65deg) rotateY(0deg) rotateZ(0deg); }
          100% { transform: rotateX(65deg) rotateY(0deg) rotateZ(360deg); }
        }
        @keyframes quantumOrbit2 {
          0% { transform: rotateX(65deg) rotateY(60deg) rotateZ(0deg); }
          100% { transform: rotateX(65deg) rotateY(60deg) rotateZ(360deg); }
        }
        @keyframes quantumOrbit3 {
          0% { transform: rotateX(65deg) rotateY(-60deg) rotateZ(0deg); }
          100% { transform: rotateX(65deg) rotateY(-60deg) rotateZ(360deg); }
        }
        @keyframes corePulse {
          0%, 100% { transform: scale(1); box-shadow: 0 0 35px oklch(75% 0.15 80 / 0.8), 0 0 70px oklch(75% 0.15 80 / 0.35); }
          50% { transform: scale(1.18); box-shadow: 0 0 50px oklch(85% 0.18 80 / 1), 0 0 100px oklch(75% 0.15 80 / 0.6); }
        }
        @keyframes wavePulse {
          0% { transform: scale(0.6); opacity: 0.8; }
          100% { transform: scale(2.2); opacity: 0; }
        }
      `}</style>

      <div style={{
        background: 'oklch(10% 0.025 250 / 0.95)',
        border: '1.5px solid oklch(75% 0.14 80 / 0.6)',
        borderRadius: '24px',
        padding: '3rem 2.5rem',
        maxWidth: '520px',
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        textAlign: 'center',
        boxShadow: '0 24px 80px oklch(0% 0 0 / 0.8), 0 0 80px oklch(75% 0.14 80 / 0.25)',
        position: 'relative',
        overflow: 'hidden',
      }}>
        {/* Subtle top gold accent line */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: '15%',
          right: '15%',
          height: '2px',
          background: 'linear-gradient(to right, transparent, oklch(75% 0.14 80), transparent)',
        }} />

        {/* ── 3D QUANTUM ATOM / QUBIT SPINNER ── */}
        <div style={{
          position: 'relative',
          width: '180px',
          height: '180px',
          marginBottom: '2rem',
          perspective: '800px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {/* Wave pulses */}
          <div style={{
            position: 'absolute',
            width: '120px',
            height: '120px',
            borderRadius: '50%',
            border: '2px solid oklch(75% 0.14 80 / 0.4)',
            animation: 'wavePulse 2.4s cubic-bezier(0.2, 0.8, 0.4, 1) infinite',
            pointerEvents: 'none',
          }} />

          {/* Central Pulsing Qubit Nucleus */}
          <div style={{
            width: '32px',
            height: '32px',
            borderRadius: '50%',
            background: 'radial-gradient(circle, #ffffff 10%, oklch(85% 0.16 80) 40%, oklch(70% 0.16 75) 100%)',
            animation: 'corePulse 2s ease-in-out infinite',
            zIndex: 10,
          }} />

          {/* Orbital Ring 1 (Horizontal tilt) */}
          <div style={{
            position: 'absolute',
            width: '150px',
            height: '150px',
            borderRadius: '50%',
            border: '2px solid oklch(75% 0.14 80 / 0.75)',
            boxShadow: '0 0 15px oklch(75% 0.14 80 / 0.4)',
            animation: 'quantumOrbit1 2.8s linear infinite',
            transformStyle: 'preserve-3d',
          }}>
            {/* Electron bead */}
            <div style={{
              position: 'absolute',
              top: '-5px',
              left: '50%',
              transform: 'translateX(-50%)',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: '#ffffff',
              boxShadow: '0 0 12px #ffffff, 0 0 20px oklch(85% 0.14 80)',
            }} />
          </div>

          {/* Orbital Ring 2 (60deg tilt) */}
          <div style={{
            position: 'absolute',
            width: '150px',
            height: '150px',
            borderRadius: '50%',
            border: '2px dashed oklch(65% 0.18 240 / 0.8)',
            boxShadow: '0 0 15px oklch(65% 0.18 240 / 0.35)',
            animation: 'quantumOrbit2 3.4s linear infinite reverse',
            transformStyle: 'preserve-3d',
          }}>
            {/* Electron bead */}
            <div style={{
              position: 'absolute',
              top: '-5px',
              left: '50%',
              transform: 'translateX(-50%)',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: 'oklch(85% 0.15 220)',
              boxShadow: '0 0 12px oklch(85% 0.15 220), 0 0 20px oklch(65% 0.18 240)',
            }} />
          </div>

          {/* Orbital Ring 3 (-60deg tilt) */}
          <div style={{
            position: 'absolute',
            width: '150px',
            height: '150px',
            borderRadius: '50%',
            border: '2px solid oklch(80% 0.14 160 / 0.7)',
            boxShadow: '0 0 15px oklch(80% 0.14 160 / 0.35)',
            animation: 'quantumOrbit3 4s linear infinite',
            transformStyle: 'preserve-3d',
          }}>
            {/* Electron bead */}
            <div style={{
              position: 'absolute',
              top: '-5px',
              left: '50%',
              transform: 'translateX(-50%)',
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              background: 'oklch(90% 0.14 160)',
              boxShadow: '0 0 12px oklch(90% 0.14 160)',
            }} />
          </div>
        </div>

        {/* ── STATUS TEXT ── */}
        <div style={{
          fontSize: '0.6875rem',
          fontWeight: 800,
          letterSpacing: '0.15em',
          textTransform: 'uppercase',
          color: 'oklch(75% 0.14 80)',
          marginBottom: '0.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.5rem',
        }}>
          <span style={{
            display: 'inline-block',
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            background: 'oklch(75% 0.14 80)',
            boxShadow: '0 0 10px oklch(75% 0.14 80)',
          }} />
          <span>Silnik Kwantowy w Toku Obliczeń</span>
        </div>

        <h2 style={{
          margin: '0 0 0.85rem 0',
          fontSize: '1.375rem',
          fontWeight: 900,
          letterSpacing: '-0.02em',
          color: 'oklch(98% 0.005 250)',
        }}>
          {statusMessage || 'Przetwarzanie problemu decyzyjnego...'}
        </h2>

        {/* Dynamic cycling phase */}
        <p style={{
          margin: 0,
          fontSize: '0.9rem',
          color: 'oklch(80% 0.05 80)',
          lineHeight: 1.6,
          fontWeight: 500,
          minHeight: '2.8rem',
          transition: 'opacity 200ms ease',
        }}>
          {PHASES[phaseIndex]}
        </p>

        {/* Quantum Shimmer Progress Bar */}
        <div style={{
          width: '100%',
          height: '6px',
          borderRadius: '3px',
          background: 'oklch(18% 0.02 250)',
          marginTop: '1.75rem',
          overflow: 'hidden',
          position: 'relative',
        }}>
          <div style={{
            position: 'absolute',
            top: 0,
            bottom: 0,
            width: '45%',
            background: 'linear-gradient(to right, transparent, oklch(75% 0.14 80), #ffffff, oklch(75% 0.14 80), transparent)',
            borderRadius: '3px',
            animation: 'progressSlide 1.8s ease-in-out infinite',
          }} />
        </div>
        <style>{`
          @keyframes progressSlide {
            0% { left: -50%; }
            100% { left: 100%; }
          }
        `}</style>
      </div>
    </div>
  )
}
