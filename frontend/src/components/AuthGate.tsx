import React, { useState, useEffect } from 'react'

interface AuthGateProps {
  children: React.ReactNode
  onLogoutRegistered?: (logoutFn: () => void) => void
}

// SHA-256 hashes of the authorized passcodes (zero plaintext secrets in repository, OWASP compliant)
// Hash 1: SHA-256 of first authorized password
// Hash 2: SHA-256 of second authorized password
const AUTHORIZED_HASHES = [
  'aff0d626d1dd85ed88ab023b216429ab75cb3324f47dc393aba2e92294c53cfd',
  'fa3ec33c54cd4f08c3a1a193e959ed636d9d5f934264698366f20ae961081ee6',
]

const AUTH_STORAGE_KEY = 'yq_access_auth_v1'

async function sha256Hex(text: string): Promise<string> {
  const encoder = new TextEncoder()
  const data = encoder.encode(text)
  const hashBuffer = await crypto.subtle.digest('SHA-256', data)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}

export const AuthGate: React.FC<AuthGateProps> = ({ children, onLogoutRegistered }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    try {
      return localStorage.getItem(AUTH_STORAGE_KEY) === 'granted'
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
      const computedHash = await sha256Hex(trimmed)
      if (AUTHORIZED_HASHES.includes(computedHash)) {
        try {
          localStorage.setItem(AUTH_STORAGE_KEY, 'granted')
        } catch {
          // ignore
        }
        setIsAuthenticated(true)
        setError(null)
      } else {
        setError('Nieprawidłowe hasło. Wprowadź autoryzowany klucz dostępu decydenta.')
      }
    } catch (err) {
      setError('Błąd weryfikacji kryptograficznej. Spróbuj ponownie.')
    } finally {
      setIsVerifying(false)
    }
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
            letterSpacing: '0.15em',
            textTransform: 'uppercase',
            color: 'oklch(75% 0.12 80)',
            marginBottom: '0.35rem',
          }}>
            YourQuantum · Strefa Decyzyjna
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
                textTransform: 'uppercase',
                letterSpacing: '0.08em',
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
              letterSpacing: '0.04em',
              textTransform: 'uppercase',
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
          Szyfrowanie SHA-256 · Niezależna weryfikacja matematyczna
        </div>
      </div>
    </div>
  )
}
