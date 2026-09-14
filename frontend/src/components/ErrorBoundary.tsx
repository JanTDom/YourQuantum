import { Component, ErrorInfo, ReactNode } from "react"

interface Props {
  children: ReactNode
  fallback?: ReactNode
  title?: string
  description?: string
  onReset?: () => void
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
  }

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo)
  }

  private handleReset = () => {
    this.setState({ hasError: false, error: null })
    if (this.props.onReset) {
      this.props.onReset()
    }
  }

  public render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div
          style={{
            padding: "2rem",
            background: "oklch(12% 0.02 250)",
            border: "1px solid oklch(30% 0.05 250)",
            borderRadius: "16px",
            color: "oklch(90% 0.01 250)",
            textAlign: "center",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "1rem",
            margin: "1rem 0",
          }}
        >
          <div
            style={{
              width: "48px",
              height: "48px",
              borderRadius: "50%",
              background: "oklch(20% 0.08 30)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "1.5rem",
            }}
          >
            ⚡
          </div>
          <div>
            <h3 style={{ margin: "0 0 0.5rem 0", fontSize: "1.125rem", fontWeight: 700 }}>
              {this.props.title || "Wystąpił nieoczekiwany problem z wyświetlaniem widoku"}
            </h3>
            <p style={{ margin: 0, fontSize: "0.875rem", color: "oklch(70% 0.02 250)", maxWidth: "480px" }}>
              {this.props.description || (this.state.error?.message ? `Szczegóły: ${this.state.error.message}` : "Główny silnik obliczeniowy działa normalnie. Możesz zresetować widok i spróbować ponownie.")}
            </p>
          </div>
          <div style={{ display: "flex", gap: "0.75rem", marginTop: "0.5rem" }}>
            <button
              onClick={this.handleReset}
              style={{
                background: "oklch(22% 0.03 250)",
                border: "1px solid oklch(35% 0.05 250)",
                color: "oklch(95% 0.01 250)",
                padding: "0.5rem 1.25rem",
                borderRadius: "8px",
                fontWeight: 600,
                fontSize: "0.875rem",
                cursor: "pointer",
              }}
            >
              Odśwież widok
            </button>
            <button
              onClick={() => {
                window.scrollTo({ top: 0, behavior: "smooth" })
              }}
              style={{
                background: "linear-gradient(135deg, oklch(75% 0.12 80), oklch(62% 0.18 240))",
                border: "none",
                color: "oklch(10% 0.02 250)",
                padding: "0.5rem 1.25rem",
                borderRadius: "8px",
                fontWeight: 700,
                fontSize: "0.875rem",
                cursor: "pointer",
              }}
            >
              Wróć do opisu dylematu →
            </button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
