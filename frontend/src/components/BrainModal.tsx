import React, { useEffect, useLayoutEffect, useRef, useState } from "react"
import { EngineBrain3D } from "./EngineBrain3D"
import { ErrorBoundary } from "./ErrorBoundary"

interface BrainModalProps {
  isOpen: boolean
  onClose: () => void
  onGoToDilemma?: () => void
}

// Uses native <dialog> so browser Back button closes the modal instead of leaving the SPA.
export const BrainModal: React.FC<BrainModalProps> = ({
  isOpen,
  onClose,
  onGoToDilemma,
}) => {
  const dialogRef = useRef<HTMLDialogElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const [contentHeight, setContentHeight] = useState<number>(600)

  // Open / close the native <dialog> element imperatively
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    if (isOpen) {
      if (!dialog.open) {
        dialog.showModal()
      }
    } else {
      if (dialog.open) {
        dialog.close()
      }
    }
  }, [isOpen])

  // When the native dialog fires its own "close" event (ESC or browser back),
  // propagate that to the React state so it stays in sync.
  useEffect(() => {
    const dialog = dialogRef.current
    if (!dialog) return
    const handleNativeClose = () => onClose()
    dialog.addEventListener("close", handleNativeClose)
    return () => dialog.removeEventListener("close", handleNativeClose)
  }, [onClose])

  // Measure the real available pixel height for the Three.js canvas
  // so the renderer never initialises with 0×0 dimensions.
  useLayoutEffect(() => {
    if (!isOpen || !contentRef.current) return
    const measure = () => {
      const h = contentRef.current?.clientHeight ?? 0
      if (h > 0) setContentHeight(h)
    }
    // First measurement on next paint
    requestAnimationFrame(measure)
    // Also observe resize so fullscreen changes work
    const ro = new ResizeObserver(measure)
    if (contentRef.current) ro.observe(contentRef.current)
    return () => ro.disconnect()
  }, [isOpen])

  const handleReturnToDilemma = () => {
    onClose()
    if (onGoToDilemma) {
      onGoToDilemma()
    } else {
      window.scrollTo({ top: 0, behavior: "smooth" })
    }
  }

  return (
    <dialog
      ref={dialogRef}
      aria-label="Prezentacja Mózgu Silnika 3D"
      // Intercept clicks on the backdrop (the ::backdrop pseudo-element is
      // behind the dialog; clicks on the outer <dialog> itself mean backdrop)
      onClick={(e) => {
        if (e.target === dialogRef.current) onClose()
      }}
      style={{
        // Reset browser default dialog styles
        border: "none",
        padding: 0,
        background: "transparent",
        maxWidth: "100vw",
        maxHeight: "100vh",
        width: "100vw",
        height: "100vh",
        // Centre the content
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Backdrop — applied via <style> below; also handle click-outside via dialog onClick above */}
      <style>{`
        dialog::backdrop {
          background: rgba(3, 5, 10, 0.88);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
        }
        dialog[open] {
          animation: dlg-in 160ms ease;
        }
        @keyframes dlg-in {
          from { opacity: 0; transform: scale(0.97); }
          to   { opacity: 1; transform: scale(1); }
        }
      `}</style>

      {/* Inner panel */}
      <div
        style={{
          width: "calc(100vw - clamp(1rem, 4vw, 3rem))",
          maxWidth: "1460px",
          height: "min(930px, 96vh)",
          background: "oklch(8% 0.015 250)",
          border: "1px solid oklch(24% 0.035 250)",
          borderRadius: "24px",
          boxShadow: "0 32px 120px rgba(0,0,0,0.95), 0 0 80px oklch(75% 0.12 80 / 0.12)",
          display: "flex",
          flexDirection: "column",
          overflow: "hidden",
        }}
      >
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
                background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
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
              <div style={{ display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap" }}>
                <h2
                  style={{
                    fontSize: "clamp(1rem, 2.2vw, 1.2rem)",
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
              <p style={{ margin: "2px 0 0 0", fontSize: "0.8125rem", color: "oklch(68% 0.02 250)" }}>
                Interaktywna eksploracja półkuli logicznej (CP-SAT), kwantowej (QAOA) oraz jądra Globalnego Optimum.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "0.625rem" }}>
            <button
              onClick={handleReturnToDilemma}
              type="button"
              style={{
                background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
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

        {/* ── 3D Viewport — flex:1 fills remaining height, explicit px height passed to Three.js ── */}
        <div
          ref={contentRef}
          style={{ flex: 1, minHeight: 0, position: "relative", overflow: "hidden" }}
        >
          <ErrorBoundary>
            {/* Pass the measured pixel height so Three.js renderer never starts at 0×0 */}
            <EngineBrain3D
              height={contentHeight > 0 ? contentHeight : "100%"}
              interactive={true}
              onGoToDilemma={handleReturnToDilemma}
            />
          </ErrorBoundary>
        </div>
      </div>
    </dialog>
  )
}
