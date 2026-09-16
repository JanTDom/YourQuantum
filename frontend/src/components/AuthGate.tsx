import React, { useState, useEffect } from 'react'
import { api } from '../api'

interface AuthGateProps {
  children: React.ReactNode
  onLogoutRegistered?: (logoutFn: () => void) => void
}

// ARCHITEKTURA AUTORYZACJI I BRAMY APLIKACJI (SERVER-SIDE):
// UWAGA DOTYCZĄCA BEZPIECZEŃSTWA:
// Weryfikacja dostępu odbywa się w całości po stronie serwera (POST /api/v1/auth/verify-app-access).
// Hasło jest porównywane na serwerze z wartością zmiennej środowiskowej YQ_APP_ACCESS_SECRET
// za pomocą funkcji stałoczasowej (hmac.compare_digest).
// W kodzie klienta ani w przeglądarce nie są przechowywane żadne hasła ani ich skróty.
// Po udanej autoryzacji serwer wydaje wygasający kryptograficzny token HMAC (TTL 24h),
// który jest zapisywany w localStorage i walidowany serwerowo przy każdym uruchomieniu aplikacji.
// Ochrona przed atakiem brute-force: blokada czasowa po 5 nieudanych próbach z danego IP (HTTP 429).
const AUTH_STORAGE_KEY = 'yq_access_auth_v1'

export const AuthGate: React.FC<AuthGateProps> = ({ children, onLogoutRegistered }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [isCheckingInitialAuth, setIsCheckingInitialAuth] = useState<boolean>(() => {
    try {
      return Boolean(localStorage.getItem(AUTH_STORAGE_KEY))
    } catch {
      return false
    }
  })

  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)

  const handleLogout = () => {
    try {
      localStorage.removeItem(AUTH_STORAGE_KEY)
    } catch {
      // ignore
    }
    setIsAuthenticated(false)
    setPassword('')
    setError(null)
  }

  useEffect(() => {
    if (onLogoutRegistered) {
      onLogoutRegistered(handleLogout)
    }
  }, [onLogoutRegistered])

  // Walidacja zapisanego tokenu sesyjnego przy starcie komponentu
  useEffect(() => {
    let active = true
    const savedToken = (() => {
      try {
        return localStorage.getItem(AUTH_STORAGE_KEY)
      } catch {
        return null
      }
    })()

    if (!savedToken) {
      setIsCheckingInitialAuth(false)
      return
    }

    api.verifyAppAccess(undefined, savedToken)
      .then((res) => {
        if (active) {
          if (res.valid) {
            setIsAuthenticated(true)
          } else {
            try { localStorage.removeItem(AUTH_STORAGE_KEY) } catch {}
            setIsAuthenticated(false)
          }
        }
      })
      .catch(() => {
        if (active) {
          try { localStorage.removeItem(AUTH_STORAGE_KEY) } catch {}
          setIsAuthenticated(false)
        }
      })
      .finally(() => {
        if (active) {
          setIsCheckingInitialAuth(false)
        }
      })

    return () => {
      active = false
    }
  }, [])

  const handleUnlock = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    const trimmed = password.trim()
    if (!trimmed) {
      setError('Wprowadź hasło dostępu.')
      return
    }

    setIsVerifying(true)
    setError(null)

    try {
      const res = await api.verifyAppAccess(trimmed)
      if (res.valid && res.token) {
        try {
          localStorage.setItem(AUTH_STORAGE_KEY, res.token)
        } catch {
          // ignore
        }
        setIsAuthenticated(true)
        setError(null)
      } else {
        setError('Nieprawidłowe hasło dostępu do aplikacji.')
      }
    } catch (err: any) {
      let msg = 'Nieprawidłowe hasło dostępu do aplikacji.'
      const rawMsg = err?.message || ''
      try {
        const jsonMatch = rawMsg.match(/\{.*\}/)
        if (jsonMatch) {
          const parsed = JSON.parse(jsonMatch[0])
          if (parsed.detail) msg = parsed.detail
        } else if (rawMsg.includes('429')) {
          msg = 'Zbyt wiele nieudanych prób logowania. Dostęp zablokowany na 15 minut.'
        } else if (rawMsg.includes('503')) {
          msg = 'Brama aplikacji nie jest skonfigurowana na serwerze.'
        }
      } catch {
        // ignore parse error
      }
      setError(msg)
    } finally {
      setIsVerifying(false)
    }
  }

  if (isCheckingInitialAuth) {
    return (
      <div style={{
        minHeight: '100vh',
        width: '100%',
        background: 'oklch(6% 0.01 250)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'oklch(75% 0.12 80)',
        fontFamily: 'var(--font-sans, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif)',
        fontSize: '0.95rem',
      }}>
        Weryfikacja autoryzacji sesji...
      </div>
    )
  }

  if (isAuthenticated) {
    return <>{children}</>
  }

  return (
    <div style={{
      minHeight: '100vh',
      width: '100%',
      background: 'radial-gradient(ellipse at center top, oklch(14% 0.035 250) 0%, oklch(6% 0.01 250) 100%)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '1.5rem',
      fontFamily: 'var(--font-sans, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif)',
      color: 'oklch(95% 0.01 250)',
      position: 'relative',
      overflow: 'hidden',
    }}>
      {/* Ambient background particles/grid glow */}
      <div style={{
        position: 'absolute',
        top: '20%',
        left: '50%',
        transform: 'translate(-50%, -50%)',
        width: '600px',
        height: '600px',
        background: 'radial-gradient(circle, oklch(75% 0.14 80 / 0.12) 0%, transparent 70%)',
        pointerEvents: 'none',
      }} />

      <div style={{
        maxWidth: '460px',
        width: '100%',
        background: 'oklch(9% 0.02 250 / 0.95)',
        border: '1.5px solid oklch(75% 0.12 80 / 0.45)',
        borderRadius: '16px',
        padding: 'clamp(2rem, 5vw, 2.75rem)',
        boxShadow: '0 20px 60px oklch(0% 0 0 / 0.7), 0 0 50px oklch(75% 0.12 80 / 0.15)',
        backdropFilter: 'blur(20px)',
        position: 'relative',
        zIndex: 1,
      }}>
        {/* Top gold bar */}
        <div style={{
          position: 'absolute',
          top: 0,
          left: '10%',
          right: '10%',
          height: '2px',
          background: 'linear-gradient(to right, transparent, oklch(75% 0.14 80), transparent)',
        }} />

        {/* Brand Header */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '48px',
            height: '48px',
            borderRadius: '12px',
            background: 'oklch(75% 0.14 80 / 0.15)',
            border: '1px solid oklch(75% 0.14 80 / 0.5)',
            color: 'oklch(85% 0.14 80)',
            fontSize: '1.5rem',
            marginBottom: '1rem',
            boxShadow: '0 0 25px oklch(75% 0.14 80 / 0.25)',
          }}>
            🔒
          </div>
          <div style={{
            fontSize: '0.6875rem',
            fontWeight: 800,
            letterSpacing: '0.04em',
            color: 'oklch(75% 0.12 80)',
            marginBottom: '0.35rem',
          }}>
            YourQuantum · strefa decyzyjna
          </div>
          <h1 style={{
            margin: '0 0 0.5rem 0',
            fontSize: '1.625rem',
            fontWeight: 900,
            letterSpacing: '-0.02em',
            color: 'oklch(98% 0.005 250)',
          }}>
            Wymagana autoryzacja
          </h1>
          <p style={{
            margin: 0,
            fontSize: '0.875rem',
            color: 'oklch(72% 0.02 250)',
            lineHeight: 1.5,
          }}>
            Dostęp do silnika kognitywnego i kombinatoryki kwantowej jest chroniony. Wprowadź hasło decydenta.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleUnlock}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label
              htmlFor="gate-password-input"
              style={{
                display: 'block',
                fontSize: '0.75rem',
                fontWeight: 700,
                letterSpacing: '0.02em',
                color: 'oklch(80% 0.08 80)',
                marginBottom: '0.5rem',
              }}
            >
              Hasło dostępowe
            </label>
            <div style={{ position: 'relative' }}>
              <input
                id="gate-password-input"
                type={showPassword ? 'text' : 'password'}
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value)
                  if (error) setError(null)
                }}
                placeholder="Wpisz hasło..."
                autoFocus
                disabled={isVerifying}
                style={{
                  width: '100%',
                  boxSizing: 'border-box',
                  padding: '0.9rem 3rem 0.9rem 1.1rem',
                  fontSize: '1.125rem',
                  fontWeight: 600,
                  borderRadius: '10px',
                  background: '#ffffff',
                  color: '#090d16',
                  border: error ? '2px solid oklch(65% 0.22 25)' : '2px solid oklch(75% 0.14 80)',
                  boxShadow: error
                    ? '0 0 20px oklch(65% 0.22 25 / 0.25)'
                    : '0 0 25px oklch(75% 0.14 80 / 0.2)',
                  outline: 'none',
                  fontFamily: 'inherit',
                  transition: 'all 200ms ease',
                }}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '1.1rem',
                  color: '#475569',
                  padding: '0.25rem',
                  display: 'flex',
                  alignItems: 'center',
                }}
                title={showPassword ? 'Ukryj hasło' : 'Pokaż hasło'}
              >
                {showPassword ? '👁️' : '🔒'}
              </button>
            </div>
            {error && (
              <div style={{
                marginTop: '0.625rem',
                fontSize: '0.8125rem',
                color: 'oklch(75% 0.2 25)',
                fontWeight: 600,
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
              }}>
                <span>⚠️</span>
                <span>{error}</span>
              </div>
            )}
          </div>

          <button
            type="submit"
            disabled={isVerifying || !password}
            style={{
              width: '100%',
              padding: '0.95rem 1.5rem',
              borderRadius: '10px',
              border: 'none',
              background: 'linear-gradient(135deg, oklch(75% 0.14 80) 0%, oklch(68% 0.16 70) 100%)',
              color: '#0a0f1d',
              fontSize: '0.9375rem',
              fontWeight: 800,
              letterSpacing: '0.02em',
              cursor: isVerifying || !password ? 'not-allowed' : 'pointer',
              boxShadow: '0 4px 20px oklch(75% 0.14 80 / 0.4)',
              transition: 'all 180ms ease',
              opacity: isVerifying || !password ? 0.6 : 1,
            }}
          >
            {isVerifying ? 'Weryfikacja klucza...' : 'Odblokuj dostęp do silnika →'}
          </button>
        </form>

        <div style={{
          marginTop: '1.75rem',
          paddingTop: '1.25rem',
          borderTop: '1px solid oklch(20% 0.02 250)',
          textAlign: 'center',
          fontSize: '0.75rem',
          color: 'oklch(55% 0.02 250)',
        }}>
          Szyfrowanie SHA-256 · niezależna weryfikacja matematyczna
        </div>
      </div>
    </div>
  )
}
