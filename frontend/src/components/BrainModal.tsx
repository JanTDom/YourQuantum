import React, { useEffect } from "react"
import { EngineBrain3D } from "./EngineBrain3D"
import { ErrorBoundary } from "./ErrorBoundary"

interface BrainModalProps {
  isOpen: boolean
  onClose: () => void
  onGoToDilemma?: () => void
}

export const BrainModal: React.FC<BrainModalProps> = ({
  isOpen,
  onClose,
  onGoToDilemma,
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose()
      }
    }
    window.addEventListener("keydown", handleKeyDown)
    return () => window.removeEventListener("keydown", handleKeyDown)
  }, [isOpen, onClose])

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
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(3, 5, 10, 0.88)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "clamp(0.5rem, 2vw, 1.5rem)",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Prezentacja Mózgu Silnika 3D"
    >
      <div
        style={{
          width: "100%",
          maxWidth: "1420px",
          height: "min(920px, 94vh)",
          background: "oklch(8% 0.015 250)",
          border: "1px solid oklch(24% 0.035 250)",
          borderRadius: "24px",
          boxShadow: "0 32px 120px rgba(0, 0, 0, 0.95), 0 0 80px oklch(75% 0.12 80 / 0.12)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Top Header Bar */}
        <div
          style={{
            padding: "1rem 1.75rem",
            borderBottom: "1px solid oklch(18% 0.02 250)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "oklch(10% 0.02 250)",
            flexWrap: "wrap",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div
              style={{
                width: "44px",
                height: "44px",
                borderRadius: "12px",
                background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.35rem",
                boxShadow: "0 0 20px oklch(75% 0.12 80 / 0.4)",
              }}
            >
              🧠
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
                <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: 0, color: "oklch(97% 0.008 250)", letterSpacing: "-0.02em" }}>
                  Mózg Silnika Decyzyjnego YourQuantum
                </h2>
                <span
                  style={{
                    fontSize: "0.6875rem",
                    fontWeight: 700,
                    padding: "0.18rem 0.55rem",
                    borderRadius: "100px",
                    background: "oklch(22% 0.05 170)",
                    color: "oklch(80% 0.16 168)",
                    border: "1px solid oklch(35% 0.08 168)",
                    letterSpacing: "0.05em",
                    textTransform: "uppercase",
                  }}
                >
                  Volumetric 3D • 60 FPS
                </span>
              </div>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.8125rem", color: "oklch(68% 0.02 250)" }}>
                Interaktywna eksploracja półkuli logicznej (CP-SAT), kwantowej (QAOA) oraz jądra Globalnego Optimum.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
            <button
              onClick={handleReturnToDilemma}
              type="button"
              style={{
                background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                border: "none",
                color: "oklch(10% 0.02 250)",
                padding: "0.5rem 1.25rem",
                borderRadius: "10px",
                fontWeight: 800,
                fontSize: "0.84375rem",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                boxShadow: "0 0 20px oklch(75% 0.12 80 / 0.35)",
                transition: "all 150ms ease",
              }}
            >
              <span>← Wróć do YourQuantum (Opisz dylemat)</span>
            </button>

            <button
              onClick={onClose}
              type="button"
              style={{
                background: "oklch(16% 0.02 250)",
                border: "1px solid oklch(28% 0.03 250)",
                color: "oklch(85% 0.01 250)",
                padding: "0.5rem 1rem",
                borderRadius: "10px",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.375rem",
                cursor: "pointer",
                fontSize: "0.84375rem",
                fontWeight: 700,
                transition: "all 150ms ease",
              }}
              title="Zamknij (ESC)"
            >
              <span>✕</span>
              <span>Zamknij</span>
            </button>
          </div>
        </div>

        {/* 3D Visualizer Content */}
        <div style={{ flex: 1, position: "relative", minHeight: 0, overflow: "hidden" }}>
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
