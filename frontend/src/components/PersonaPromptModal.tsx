import { useEffect, useState } from 'react'
import { useAuth } from './AuthContext'
import { API_BASE } from '../config'
import './PersonaPromptModal.css'

interface Persona {
  key: string
  display_label: string
  description: string
  icon: string
  sort_order: number
}

interface PersonaPromptModalProps {
  onClose: () => void
  onComplete?: (selected: string[]) => void
  dark?: boolean
}

export default function PersonaPromptModal({ onClose, onComplete, dark }: PersonaPromptModalProps) {
  const { user, setPersonas, skipPersonasThisSession } = useAuth()
  const [catalog, setCatalog] = useState<Persona[] | null>(null)
  const [selected, setSelected] = useState<Set<string>>(() => new Set(user?.personas || []))
  const isEdit = !!user?.personas_set_at
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    fetch(`${API_BASE}/personas/catalog`, { credentials: 'include' })
      .then(r => {
        if (!r.ok) throw new Error('Failed to load personas')
        return r.json()
      })
      .then(data => {
        if (cancelled) return
        setCatalog(data.personas || [])
        setLoading(false)
      })
      .catch(() => {
        if (cancelled) return
        setError('Could not load personas. Please try again.')
        setLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const toggle = (key: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

  const submit = async (keys: string[]) => {
    if (submitting) return
    setSubmitting(true)
    setError('')
    const result = await setPersonas(keys)
    if (result.ok) {
      skipPersonasThisSession()
      onComplete?.(keys)
      onClose()
    } else {
      setError(result.error || 'Failed to save')
      setSubmitting(false)
    }
  }

  return (
    <div className={`persona-overlay ${dark ? 'dark' : ''}`}>
      <div className="persona-modal" onClick={e => e.stopPropagation()}>
        <div className="persona-header">
          <h2>{isEdit ? 'Edit your interests' : "Tell us what you're into"}</h2>
          <p>Pick anything that fits. We'll tailor what you see — and you can change this anytime.</p>
        </div>

        {loading && (
          <div className="persona-loading">Loading…</div>
        )}

        {!loading && catalog && (
          <div className="persona-list">
            {catalog.map(p => {
              const isOn = selected.has(p.key)
              return (
                <button
                  key={p.key}
                  type="button"
                  className={`persona-card ${isOn ? 'on' : ''}`}
                  onClick={() => toggle(p.key)}
                  aria-pressed={isOn}
                >
                  <span className="persona-icon" aria-hidden>{p.icon}</span>
                  <span className="persona-text">
                    <span className="persona-label">{p.display_label}</span>
                    <span className="persona-desc">{p.description}</span>
                  </span>
                  <span className={`persona-check ${isOn ? 'on' : ''}`} aria-hidden>
                    {isOn ? '✓' : ''}
                  </span>
                </button>
              )
            })}
          </div>
        )}

        {error && <div className="persona-error">{error}</div>}

        <div className="persona-actions">
          {isEdit ? (
            <>
              <button
                type="button"
                className="persona-btn skip"
                onClick={onClose}
                disabled={submitting}
              >
                Cancel
              </button>
              <button
                type="button"
                className="persona-btn save"
                onClick={() => submit(Array.from(selected))}
                disabled={submitting || loading}
              >
                {submitting ? 'Saving…' : 'Save'}
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className="persona-btn skip"
                onClick={() => submit([])}
                disabled={submitting || loading}
              >
                Skip — show me everything
              </button>
              <button
                type="button"
                className="persona-btn save"
                onClick={() => submit(Array.from(selected))}
                disabled={submitting || loading || selected.size === 0}
              >
                {submitting ? 'Saving…' : 'Save and continue'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
