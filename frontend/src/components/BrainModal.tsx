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
  // onClose przychodzi z rodzica jako nowa funkcja przy każdym przerysowaniu.
  // Trzymamy ją w ref, żeby efekt historii nie restartował się co render —
  // inaczej każde przerysowanie dokładało kolejny wpis do historii przeglądarki.
  const onCloseRef = useRef(onClose)
  onCloseRef.current = onClose

  // Push a history entry when the modal opens so browser Back = close modal.
  // On close, pop that entry if it's still in the stack.
  useEffect(() => {
    if (isOpen) {
      // Push a "brain open" state so Back brings the user back here
      history.pushState({ brainModal: true }, "")
      sentinelRef.current = true

      const handlePop = () => {
        sentinelRef.current = false
        onCloseRef.current()
      }
      window.addEventListener("popstate", handlePop)
      return () => window.removeEventListener("popstate", handlePop)
    } else {
      // If we closed via button (not Back), pop the entry we pushed
      if (sentinelRef.current) {
        sentinelRef.current = false
        // Cofamy się WYŁĄCZNIE wtedy, gdy na wierzchu historii nadal stoi wpis,
        // który sami dołożyliśmy. Bez tego warunku history.back() potrafi wyprowadzić
        // użytkownika poza aplikację — na pustą stronę.
        if (typeof history.state === "object" && history.state?.brainModal === true) {
          history.back()
        }
      }
    }
  }, [isOpen])

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
      className="brain-modal-overlay"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose()
      }}
      style={{
        position: "fixed",
        inset: 0,
        zIndex: 9999,
        background: "rgba(3, 5, 10, 0.94)",
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
        className="brain-modal-panel"
        style={{
          width: "100%",
          maxWidth: "1460px",
          height: "min(930px, 94vh)",
          maxHeight: "96dvh",
          background: "oklch(8% 0.015 250)",
          border: "1px solid oklch(24% 0.035 250)",
          borderRadius: "20px",
          boxShadow:
            "0 32px 120px rgba(0,0,0,0.95), 0 0 80px oklch(75% 0.12 80 / 0.12)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
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
          .brain-modal-mobile-title { display: none; }
          .brain-modal-desktop-title { display: inline; }
          @media (max-width: 768px) {
            .brain-modal-mobile-title { display: inline !important; }
            .brain-modal-desktop-title { display: none !important; }
            .brain-modal-overlay {
              padding: 0 !important;
              align-items: stretch !important;
              justify-content: stretch !important;
            }
            .brain-modal-panel {
              width: 100vw !important;
              max-width: 100vw !important;
              height: 100dvh !important;
              max-height: 100dvh !important;
              border-radius: 0 !important;
              border: none !important;
            }
            .brain-modal-header {
              padding: max(env(safe-area-inset-top, 0px), 0.75rem) 0.875rem 0.625rem 0.875rem !important;
              gap: 0.5rem !important;
            }
            .brain-modal-desc {
              display: none !important;
            }
            .brain-modal-title {
              font-size: 1rem !important;
            }
            .brain-modal-btn-dilemma {
              padding: 0.35rem 0.65rem !important;
              font-size: 0.75rem !important;
            }
            .brain-modal-btn-close {
              padding: 0.35rem 0.65rem !important;
              font-size: 0.75rem !important;
            }
          }
        `}</style>

        {/* ── Header bar ── */}
        <div
          className="brain-modal-header"
          style={{
            padding: "0.875rem 1.5rem",
            borderBottom: "1px solid oklch(18% 0.02 250)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            background: "oklch(10% 0.02 250)",
            flexWrap: "nowrap",
            gap: "0.75rem",
            flexShrink: 0,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "0.625rem", minWidth: 0 }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "9px",
                background:
                  "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontSize: "1.125rem",
                flexShrink: 0,
                boxShadow: "0 0 16px oklch(75% 0.12 80 / 0.4)",
              }}
            >
              🧠
            </div>
            <div style={{ minWidth: 0 }}>
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "0.5rem",
                  flexWrap: "nowrap",
                }}
              >
                <h2
                  className="brain-modal-title"
                  style={{
                    fontSize: "clamp(0.9375rem, 2vw, 1.15rem)",
                    fontWeight: 900,
                    margin: 0,
                    color: "oklch(97% 0.008 250)",
                    letterSpacing: "-0.02em",
                    whiteSpace: "nowrap",
                  }}
                >
                  <span className="brain-modal-mobile-title">Mózg 3D</span>
                  <span className="brain-modal-desktop-title">Mózg Silnika 3D</span>
                </h2>
                <span
                  style={{
                    fontSize: "0.625rem",
                    fontWeight: 800,
                    padding: "0.15rem 0.45rem",
                    borderRadius: "100px",
                    background: "oklch(22% 0.05 170)",
                    color: "oklch(80% 0.16 168)",
                    border: "1px solid oklch(35% 0.08 168)",
                    letterSpacing: "0.05em",
                    textTransform: "uppercase",
                    whiteSpace: "nowrap",
                    flexShrink: 0,
                  }}
                >
                  60 FPS
                </span>
              </div>
              <p
                className="brain-modal-desc"
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

          <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexShrink: 0 }}>
            <button
              onClick={handleReturnToDilemma}
              type="button"
              className="brain-modal-btn-dilemma"
              style={{
                background:
                  "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                border: "none",
                color: "oklch(10% 0.02 250)",
                padding: "0.45rem 1rem",
                borderRadius: "8px",
                fontWeight: 800,
                fontSize: "0.8125rem",
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                boxShadow: "0 0 16px oklch(75% 0.12 80 / 0.35)",
                whiteSpace: "nowrap",
              }}
            >
              <span>← Dylemat</span>
            </button>

            <button
              onClick={onClose}
              type="button"
              className="brain-modal-btn-close"
              style={{
                background: "oklch(16% 0.02 250)",
                border: "1px solid oklch(28% 0.03 250)",
                color: "oklch(85% 0.01 250)",
                padding: "0.45rem 0.8rem",
                borderRadius: "8px",
                display: "inline-flex",
                alignItems: "center",
                gap: "0.35rem",
                cursor: "pointer",
                fontSize: "0.8125rem",
                fontWeight: 700,
                whiteSpace: "nowrap",
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
