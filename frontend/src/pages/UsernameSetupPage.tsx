import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../components/AuthContext'

export default function UsernameSetupPage() {
  const { user, isLoggedIn, needsUsername, setUsername, checkUsername } = useAuth()
  const navigate = useNavigate()
  const [input, setInput] = useState('')
  const [checking, setChecking] = useState(false)
  const [available, setAvailable] = useState<boolean | null>(null)
  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Redirect if not logged in or already has username
  useEffect(() => {
    if (!isLoggedIn) navigate('/', { replace: true })
    else if (!needsUsername) navigate('/', { replace: true })
  }, [isLoggedIn, needsUsername, navigate])

  // Debounced availability check
  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current)
    setAvailable(null)
    setReason('')

    const clean = input.trim().toLowerCase()
    if (clean.length < 3) return

    if (!/^[a-z0-9_]+$/.test(clean)) {
      setAvailable(false)
      setReason('Letters, numbers, and underscores only')
      return
    }

    setChecking(true)
    debounceRef.current = setTimeout(async () => {
      const result = await checkUsername(clean)
      setAvailable(result.available)
      setReason(result.reason || (result.available ? '' : 'Already taken'))
      setChecking(false)
    }, 400)
  }, [input, checkUsername])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!available || submitting) return
    setSubmitting(true)
    setError('')
    const result = await setUsername(input.trim().toLowerCase())
    if (result.ok) {
      navigate('/', { replace: true })
    } else {
      setError(result.error || 'Failed to set username')
      setSubmitting(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh', display: 'flex', flexDirection: 'column',
      alignItems: 'center', justifyContent: 'center',
      fontFamily: "'Outfit', sans-serif", padding: 24,
      background: '#faf9f6',
    }}>
      <div style={{ maxWidth: 380, width: '100%', textAlign: 'center' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 600, marginBottom: 8 }}>
          Choose your username
        </h1>
        <p style={{ color: '#888', fontSize: '0.88rem', marginBottom: 24 }}>
          This will appear on your observations and is visible to others.
        </p>

        {user?.avatar && (
          <img src={user.avatar} alt="" style={{
            width: 64, height: 64, borderRadius: '50%', marginBottom: 16,
            border: '3px solid #e8e5de',
          }} />
        )}
        {user?.name && (
          <div style={{ fontSize: '0.9rem', color: '#555', marginBottom: 20 }}>
            Welcome, {user.name}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div style={{ position: 'relative', marginBottom: 8 }}>
            <span style={{
              position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)',
              color: '#aaa', fontSize: '0.9rem',
            }}>@</span>
            <input
              type="text"
              value={input}
              onChange={e => setInput(e.target.value.replace(/\s/g, ''))}
              placeholder="your_username"
              maxLength={30}
              autoFocus
              style={{
                width: '100%', padding: '12px 14px 12px 30px',
                border: `2px solid ${available === true ? '#4caf50' : available === false ? '#f44336' : '#e0ddd8'}`,
                borderRadius: 10, fontSize: '1rem', fontFamily: 'inherit',
                boxSizing: 'border-box', transition: 'border-color 0.2s',
              }}
            />
            {checking && (
              <span style={{ position: 'absolute', right: 14, top: '50%', transform: 'translateY(-50%)', color: '#aaa', fontSize: '0.8rem' }}>
                checking...
              </span>
            )}
          </div>

          {/* Feedback */}
          <div style={{ minHeight: 20, marginBottom: 12, fontSize: '0.78rem' }}>
            {available === true && (
              <span style={{ color: '#4caf50' }}>@{input.trim().toLowerCase()} is available</span>
            )}
            {available === false && (
              <span style={{ color: '#f44336' }}>{reason}</span>
            )}
            {error && (
              <span style={{ color: '#f44336' }}>{error}</span>
            )}
          </div>

          <button
            type="submit"
            disabled={!available || submitting}
            style={{
              width: '100%', padding: 12, border: 'none', borderRadius: 10,
              background: available ? '#1a6b4a' : '#ccc',
              color: '#fff', fontSize: '0.95rem', fontWeight: 600,
              fontFamily: 'inherit', cursor: available ? 'pointer' : 'not-allowed',
              transition: 'background 0.15s',
            }}
          >
            {submitting ? 'Setting up...' : 'Continue'}
          </button>
        </form>

        <p style={{ fontSize: '0.7rem', color: '#bbb', marginTop: 16, lineHeight: 1.4 }}>
          Usernames are permanent and publicly visible. Choose wisely.
        </p>
      </div>
    </div>
  )
}
