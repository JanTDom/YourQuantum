import React, { useEffect } from "react"
import { EngineBrain3D } from "./EngineBrain3D"

interface BrainModalProps {
  isOpen: boolean
  onClose: () => void
}

export const BrainModal: React.FC<BrainModalProps> = ({ isOpen, onClose }) => {
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

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "oklch(0% 0 0 / 0.85)",
        backdropFilter: "blur(16px)",
        WebkitBackdropFilter: "blur(16px)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "1.5rem",
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
          maxWidth: "1280px",
          height: "min(920px, 94vh)",
          background: "oklch(10% 0.015 250)",
          border: "1px solid oklch(25% 0.03 250)",
          borderRadius: "24px",
          boxShadow: "0 32px 100px oklch(0% 0 0 / 0.9), 0 0 60px oklch(75% 0.12 80 / 0.12)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "1.25rem 2rem",
            borderBottom: "1px solid oklch(18% 0.02 250)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "oklch(12% 0.02 250)",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "1rem" }}>
            <div
              style={{
                width: "42px",
                height: "42px",
                borderRadius: "12px",
                background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 20px oklch(75% 0.12 80 / 0.4)",
              }}
            >
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="oklch(10% 0.02 250)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 3a9 9 0 0 0-9 9m18 0a9 9 0 0 0-9-9m0 18a9 9 0 0 0 9-9m-18 0a9 9 0 0 0 9 9" />
              </svg>
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "0.75rem" }}>
                <h2 style={{ fontSize: "1.25rem", fontWeight: 900, margin: 0, color: "oklch(97% 0.008 250)", letterSpacing: "-0.02em" }}>
                  Mózg Silnika YourQuantum 3D
                </h2>
                <span
                  style={{
                    fontSize: "0.6875rem",
                    fontWeight: 700,
                    padding: "0.2rem 0.6rem",
                    borderRadius: "100px",
                    background: "oklch(22% 0.05 170)",
                    color: "oklch(78% 0.16 168)",
                    border: "1px solid oklch(35% 0.08 168)",
                    letterSpacing: "0.05em",
                    textTransform: "uppercase",
                  }}
                >
                  Czas Rzeczywisty • WebGL 60 FPS
                </span>
              </div>
              <p style={{ margin: "2px 0 0 0", fontSize: "0.8125rem", color: "oklch(65% 0.02 250)" }}>
                Interaktywna eksploracja wielowymiarowej matrycy decyzyjnej, topologii QUBO i koherencji fazowej.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              background: "oklch(18% 0.02 250)",
              border: "1px solid oklch(26% 0.03 250)",
              color: "oklch(80% 0.01 250)",
              width: "38px",
              height: "38px",
              borderRadius: "50%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              fontSize: "1.35rem",
              lineHeight: 1,
              transition: "all 150ms ease",
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = "oklch(26% 0.03 250)")}
            onMouseLeave={(e) => (e.currentTarget.style.background = "oklch(18% 0.02 250)")}
            title="Zamknij (ESC)"
          >
            ×
          </button>
        </div>

        {/* Content Body: 3D Canvas + Technical Sidebar */}
        <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
          {/* Main 3D Canvas */}
          <div style={{ flex: 1, position: "relative", minWidth: 0 }}>
            <EngineBrain3D height="100%" interactive={true} />
          </div>

          {/* Sidebar Narrative */}
          <div
            style={{
              width: "380px",
              background: "oklch(11% 0.015 250)",
              borderLeft: "1px solid oklch(18% 0.02 250)",
              padding: "1.75rem",
              overflowY: "auto",
              display: "flex",
              flexDirection: "column",
              gap: "1.5rem",
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
                  marginBottom: "0.375rem",
                }}
              >
                Architektura Silnika
              </div>
              <h3 style={{ margin: "0 0 0.75rem 0", fontSize: "1.125rem", fontWeight: 800, color: "oklch(96% 0.01 250)" }}>
                Jak silnik waży Twój dylemat?
              </h3>
              <p style={{ margin: 0, fontSize: "0.84375rem", color: "oklch(75% 0.015 250)", lineHeight: 1.65 }}>
                Ludzki mózg przy skomplikowanym wyborze próbuje ważyć maksymalnie 2–3 czynniki naraz, ulegając paraliżowi decyzyjnemu lub uciekając w emocje.
              </p>
              <p style={{ margin: "0.75rem 0 0 0", fontSize: "0.84375rem", color: "oklch(75% 0.015 250)", lineHeight: 1.65 }}>
                Wizualizowana obok matryca tworzy <strong>wielowymiarowy hipergraf</strong>, gdzie każdy punkt to niezależne kryterium, a łączące je promienie to wzajemne napięcia i synergie.
              </p>
            </div>

            {/* Visual Layers Card */}
            <div
              style={{
                background: "oklch(13% 0.02 250)",
                border: "1px solid oklch(22% 0.025 250)",
                borderRadius: "12px",
                padding: "1.25rem",
              }}
            >
              <div style={{ fontSize: "0.75rem", fontWeight: 700, textTransform: "uppercase", color: "oklch(60% 0.02 250)", marginBottom: "0.75rem" }}>
                3 Kluczowe Zjawiska w Wizualizacji
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "0.875rem" }}>
                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "#4df0ff" }} />
                    <strong style={{ fontSize: "0.8125rem", color: "oklch(95% 0.01 250)" }}>Kryształy Kognitywne</strong>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "oklch(68% 0.02 250)", lineHeight: 1.5 }}>
                    Reprezentują cele i granice zdefiniowane w Twoim dylemacie. Pulsują wraz ze zmianą wag.
                  </p>
                </div>

                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "2px", background: "#1e3a8a" }} />
                    <strong style={{ fontSize: "0.8125rem", color: "oklch(95% 0.01 250)" }}>Krajobraz QUBO (Dno Potencjału)</strong>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "oklch(68% 0.02 250)", lineHeight: 1.5 }}>
                    Siatka poniżej to mapa energii. Zadaniem solwera jest odnalezienie najgłębszej studni — punktu idealnej harmonii.
                  </p>
                </div>

                <div>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", marginBottom: "0.25rem" }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "50%", border: "1px solid #c084fc" }} />
                    <strong style={{ fontSize: "0.8125rem", color: "oklch(95% 0.01 250)" }}>Pierścienie Koherencji Fazowej</strong>
                  </div>
                  <p style={{ margin: 0, fontSize: "0.75rem", color: "oklch(68% 0.02 250)", lineHeight: 1.5 }}>
                    Ilustrują jednoczesne badanie milionów permutacji w przestrzeni stanów kwantowych.
                  </p>
                </div>
              </div>
            </div>

            {/* Privacy & Know-How protection badge */}
            <div
              style={{
                background: "oklch(14% 0.025 170 / 0.3)",
                border: "1px solid oklch(35% 0.08 168 / 0.5)",
                borderRadius: "10px",
                padding: "0.875rem 1rem",
                fontSize: "0.75rem",
                color: "oklch(80% 0.1 168)",
                lineHeight: 1.5,
              }}
            >
              🔒 <strong>Ochrona know-how:</strong> Wizualizacja prezentuje architekturę kognitywną w ujęciu topologicznym. Wewnętrzne wagi, parametry regularyzacji i kod algorytmów pozostają w pełni zabezpieczone w zamkniętym silniku produkcyjnym.
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
