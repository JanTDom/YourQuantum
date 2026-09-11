import React, { useEffect, useRef } from "react"
import { EngineBrain3D } from "./EngineBrain3D"
import { ErrorBoundary } from "./ErrorBoundary"

interface BrainModalProps {
  isOpen: boolean
  onClose: () => void
  onGoToDilemma?: () => void
}

// Uses a <div> overlay for maximum cross-browser compatibility (Safari <dialog> bugs).
// Browser Back button is handled via history.pushState / popstate so pressing Back
// closes the modal instead of leaving the SPA (white screen).
export const BrainModal: React.FC<BrainModalProps> = ({
  isOpen,
  onClose,
  onGoToDilemma,
}) => {
  const sentinelRef = useRef(false)

  // Push a history entry when the modal opens so browser Back = close modal.
  // On close, pop that entry if it's still in the stack.
  useEffect(() => {
    if (isOpen) {
      // Push a "brain open" state so Back brings the user back here
      history.pushState({ brainModal: true }, "")
      sentinelRef.current = true

      const handlePop = () => {
        sentinelRef.current = false
        onClose()
      }
      window.addEventListener("popstate", handlePop)
      return () => window.removeEventListener("popstate", handlePop)
    } else {
      // If we closed via button (not Back), pop the entry we pushed
      if (sentinelRef.current) {
        sentinelRef.current = false
        history.back()
      }
    }
  }, [isOpen, onClose])

  // Escape key
  useEffect(() => {
    if (!isOpen) return
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose()
    }
    window.addEventListener("keydown", handleKey)
    return () => window.removeEventListener("keydown", handleKey)
  }, [isOpen, onClose])

  // Lock body scroll while open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden"
    } else {
      document.body.style.overflow = ""
    }
    return () => { document.body.style.overflow = "" }
  }, [isOpen])

  if (!isOpen) return null

  const handleReturnToDilemma = () => {
    onClose()
    if (onGoToDilemma) {
      onGoToDilemma()
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" })
    }
  }

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Prezentacja Mózgu Silnika 3D"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(3, 5, 10, 0.92)",
        backdropFilter: "blur(22px)",
        WebkitBackdropFilter: "blur(22px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "clamp(0.5rem, 2vw, 1.5rem)",
      }}
    >
      {/* Inner panel */}
      <div
        style={{
          width: "100%",
          maxWidth: "1460px",
          height: "min(930px, 94vh)",
          background: "oklch(8% 0.015 250)",
          border: "1px solid oklch(24% 0.035 250)",
          borderRadius: "20px",
          boxShadow:
            "0 32px 120px rgba(0,0,0,0.95), 0 0 80px oklch(75% 0.12 80 / 0.12)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
          // Entrance animation
          animation: "brainModalIn 160ms cubic-bezier(0.16, 1, 0.3, 1) forwards",
        }}
      >
        <style>{`
          @keyframes brainModalIn {
            from { opacity: 0; transform: scale(0.97) translateY(8px); }
            to   { opacity: 1; transform: scale(1) translateY(0); }
          }
          @media (prefers-reduced-motion: reduce) {
            .brain-modal-panel { animation: none !important; }
          }
        `}</style>

        {/* ── Header bar ── */}
        <div
          style={{
            padding: "0.875rem 1.5rem",
            borderBottom: "1px solid oklch(18% 0.02 250)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "oklch(10% 0.02 250)",
            flexWrap: "wrap",
            gap: "0.75rem",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.875rem" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background:
                  "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.25rem",
                flexShrink: 0,
                boxShadow: "0 0 18px oklch(75% 0.12 80 / 0.4)",
              }}
            >
              🧠
            </div>
            <div>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  flexWrap: "wrap",
                }}
              >
                <h2
                  style={{
                    fontSize: "clamp(1rem, 2vw, 1.2rem)",
                    fontWeight: 900,
                    margin: 0,
                    color: "oklch(97% 0.008 250)",
                    letterSpacing: "-0.02em",
                  }}
                >
                  Mózg Silnika Decyzyjnego YourQuantum
                </h2>
                <span
                  style={{
                    fontSize: "0.6875rem",
                    fontWeight: 700,
                    padding: "0.15rem 0.5rem",
                    borderRadius: "100px",
                    background: "oklch(22% 0.05 170)",
                    color: "oklch(80% 0.16 168)",
                    border: "1px solid oklch(35% 0.08 168)",
                    letterSpacing: "0.05em",
                    textTransform: "uppercase",
                    whiteSpace: "nowrap",
                  }}
                >
                  Volumetric 3D • 60 FPS
                </span>
              </div>
              <p
                style={{
                  margin: "2px 0 0 0",
                  fontSize: "0.8125rem",
                  color: "oklch(68% 0.02 250)",
                }}
              >
                Interaktywna eksploracja półkuli logicznej (CP-SAT), kwantowej
                (QAOA) oraz jądra Globalnego Optimum.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
            <button
              onClick={handleReturnToDilemma}
              type="button"
              style={{
                background:
                  "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                border: "none",
                color: "oklch(10% 0.02 250)",
                padding: "0.45rem 1.1rem",
                borderRadius: "9px",
                fontWeight: 800,
                fontSize: "0.84375rem",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.4rem",
                boxShadow: "0 0 18px oklch(75% 0.12 80 / 0.35)",
                whiteSpace: "nowrap",
              }}
            >
              <span>← Opisz dylemat</span>
            </button>

            <button
              onClick={onClose}
              type="button"
              style={{
                background: "oklch(16% 0.02 250)",
                border: "1px solid oklch(28% 0.03 250)",
                color: "oklch(85% 0.01 250)",
                padding: "0.45rem 0.9rem",
                borderRadius: "9px",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                cursor: "pointer",
                fontSize: "0.84375rem",
                fontWeight: 700,
              }}
              title="Zamknij (ESC)"
            >
              <span>✕</span>
              <span>Zamknij</span>
            </button>
          </div>
        </div>

        {/* ── 3D Viewport ── */}
        <div style={{ flex: 1, minHeight: 0, position: "relative", overflow: "hidden" }}>
          <ErrorBoundary>
            <EngineBrain3D
              height="100%"
              interactive={true}
              onGoToDilemma={handleReturnToDilemma}
            />
          </ErrorBoundary>
        </div>
      </div>
    </div>
  )
}
