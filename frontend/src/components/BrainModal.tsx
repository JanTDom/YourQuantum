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
        background: "rgba(0, 0, 0, 0.82)",
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1rem",
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      role="dialog"
      aria-modal="true"
      aria-label="Mózg Projektu 3D"
    >
      <div
        style={{
          width: "100%",
          maxWidth: "1320px",
          height: "min(900px, 94vh)",
          background: "oklch(10% 0.015 250)",
          border: "1px solid oklch(26% 0.03 250)",
          borderRadius: "20px",
          boxShadow: "0 32px 100px rgba(0, 0, 0, 0.9), 0 0 60px oklch(75% 0.12 80 / 0.15)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "1rem 1.75rem",
            borderBottom: "1px solid oklch(20% 0.02 250)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "oklch(12% 0.02 250)",
            flexWrap: "wrap",
            gap: "0.75rem",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "10px",
                background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 16px oklch(75% 0.12 80 / 0.4)",
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="oklch(10% 0.02 250)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 3a9 9 0 0 0-9 9m18 0a9 9 0 0 0-9-9m0 18a9 9 0 0 0 9-9m-18 0a9 9 0 0 0 9 9" />
              </svg>
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
                <h2 style={{ fontSize: "1.125rem", fontWeight: 900, margin: 0, color: "oklch(97% 0.008 250)", letterSpacing: "-0.02em" }}>
                  Mózg Silnika YourQuantum 3D
                </h2>
                <span
                  style={{
                    fontSize: "0.6875rem",
                    fontWeight: 700,
                    padding: "0.15rem 0.5rem",
                    borderRadius: "100px",
                    background: "oklch(22% 0.05 170)",
                    color: "oklch(78% 0.16 168)",
                    border: "1px solid oklch(35% 0.08 168)",
                    letterSpacing: "0.05em",
                    textTransform: "uppercase",
                  }}
                >
                  Live WebGL 60 FPS
                </span>
              </div>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.8125rem", color: "oklch(65% 0.02 250)" }}>
                Wielowymiarowy hipergraf kognitywny, krajobraz QUBO i pierścienie fazowe.
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
                padding: "0.45rem 1.1rem",
                borderRadius: "8px",
                fontWeight: 800,
                fontSize: "0.8125rem",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.5rem",
                boxShadow: "0 0 16px oklch(75% 0.12 80 / 0.4)",
              }}
            >
              <span>← Wróć do YourQuantum (Opisz dylemat)</span>
            </button>

            <button
              onClick={onClose}
              type="button"
              style={{
                background: "oklch(18% 0.02 250)",
                border: "1px solid oklch(28% 0.03 250)",
                color: "oklch(80% 0.01 250)",
                width: "36px",
                height: "36px",
                borderRadius: "50%",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "pointer",
                fontSize: "1.25rem",
                lineHeight: 1,
              }}
              title="Zamknij (ESC)"
            >
              ×
            </button>
          </div>
        </div>

        {/* Content Body: 3D Canvas + Technical Sidebar */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden", minHeight: 0 }}>
          {/* Main 3D Canvas with Error Boundary */}
          <div style={{ flex: 1, position: "relative", minWidth: 0, height: "100%", padding: "0.75rem" }}>
            <ErrorBoundary>
              <EngineBrain3D
                height="100%"
                interactive={true}
                onGoToDilemma={handleReturnToDilemma}
              />
            </ErrorBoundary>
          </div>

          {/* Sidebar Narrative */}
          <div
            style={{
              width: "360px",
              background: "oklch(11% 0.015 250)",
              borderLeft: "1px solid oklch(20% 0.02 250)",
              padding: "1.5rem",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "1.25rem",
            }}
          >
            <div>
              <div
                style={{
                  fontSize: "0.75rem",
                  fontWeight: 800,
                  textTransform: "uppercase",
                  letterSpacing: "0.08em",
                  color: "oklch(75% 0.12 80)",
                  marginBottom: "0.25rem",
                }}
              >
                Architektura Silnika
              </div>
              <h3 style={{ margin: "0 0 0.5rem 0", fontSize: "1.0625rem", fontWeight: 800, color: "oklch(96% 0.01 250)" }}>
                Jak silnik waży Twój dylemat?
              </h3>
              <p style={{ margin: 0, fontSize: "0.8125rem", color: "oklch(75% 0.015 250)", lineHeight: 1.6 }}>
                Ludzki mózg przy trudnym wyborze waży maksymalnie 2–3 czynniki naraz. Nasz silnik buduje <strong>wielowymiarowy hipergraf</strong>, w którym każde kryterium jest niezależnym wymiarem powiązanym ścisłymi sprzężeniami.
              </p>
            </div>

            {/* Visual Layers Card */}
            <div
              style={{
                background: "oklch(13% 0.02 250)",
                border: "1px solid oklch(22% 0.025 250)",
                borderRadius: "12px",
                padding: "1rem",
              }}
            >
              <div style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "oklch(60% 0.02 250)", marginBottom: "0.75rem" }}>
                3 Zjawiska w Wizualizacji
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.2rem" }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#4df0ff" }} />
                    <strong style={{ fontSize: "0.8125rem", color: "oklch(95% 0.01 250)" }}>Kryształy Kognitywne</strong>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "oklch(68% 0.02 250)", lineHeight: 1.45 }}>
                    Reprezentują cele i granice zdefiniowane w Twoim dylemacie.
                  </p>
                </div>

                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.2rem" }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: "#1e3a8a" }} />
                    <strong style={{ fontSize: "0.8125rem", color: "oklch(95% 0.01 250)" }}>Krajobraz QUBO (Studnia Energii)</strong>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "oklch(68% 0.02 250)", lineHeight: 1.45 }}>
                    Falująca siatka to mapa energii. Najgłębsza dolina w centrum to Stan Podstawowy — Globalne Optimum.
                  </p>
                </div>

                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.2rem" }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "50%", border: "1px solid #c084fc" }} />
                    <strong style={{ fontSize: "0.8125rem", color: "oklch(95% 0.01 250)" }}>Pierścienie Fazowe</strong>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "oklch(68% 0.02 250)", lineHeight: 1.45 }}>
                    Obrazują jednoczesne przeszukiwanie milionów permutacji w przestrzeni stanów.
                  </p>
                </div>
              </div>
            </div>

            {/* Action Return Box */}
            <div
              style={{
                marginTop: "auto",
                background: "oklch(14% 0.025 240 / 0.4)",
                border: "1px solid oklch(35% 0.08 240 / 0.5)",
                borderRadius: "12px",
                padding: "1rem",
                display: "flex",
                flexDirection: "column",
                gap: "0.75rem",
              }}
            >
              <div style={{ fontSize: "0.8125rem", fontWeight: 700, color: "oklch(95% 0.01 250)" }}>
                Gotowy rozwiązać swój dylemat?
              </div>
              <button
                onClick={handleReturnToDilemma}
                type="button"
                style={{
                  background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                  border: "none",
                  color: "oklch(10% 0.02 250)",
                  padding: "0.65rem 1rem",
                  borderRadius: "8px",
                  fontWeight: 800,
                  fontSize: "0.8125rem",
                  cursor: "pointer",
                  width: "100%",
                  textAlign: "center",
                }}
              >
                Przejdź do formularza →
              </button>
            </div>

            {/* Privacy & Know-How protection badge */}
            <div
              style={{
                fontSize: "0.6875rem",
                color: "oklch(60% 0.02 250)",
                lineHeight: 1.4,
              }}
            >
              🔒 <strong>Ochrona know-how:</strong> Wizualizacja prezentuje architekturę kognitywną w ujęciu topologicznym. Wewnętrzne wagi, parametry regularyzacji i kod algorytmów pozostają w pełni zabezpieczone w silniku.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
