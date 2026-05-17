import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'
import { API_BASE } from '../config'

export interface User {
  id: string
  email: string
  name: string
  avatar: string
  username: string
  is_new: boolean
  needs_username?: boolean
  personas?: string[]
  personas_set_at?: string | null
  personas_version?: number
  is_admin?: boolean
}

interface AuthState {
  user: User | null
  loading: boolean
  isLoggedIn: boolean
  needsUsername: boolean
  needsPersonas: boolean
  loginWithGoogle: () => void
  loginWithApple: () => void
  logout: () => void
  setUsername: (username: string) => Promise<{ ok: boolean; error?: string }>
  checkUsername: (username: string) => Promise<{ available: boolean; reason?: string }>
  setPersonas: (personas: string[]) => Promise<{ ok: boolean; error?: string }>
  skipPersonasThisSession: () => void
  hasPersona: (key: string) => boolean
  hasAnyPersona: (...keys: string[]) => boolean
  isUnsetOrSkipped: () => boolean
  syncSettings: (key: string, value: any) => void
  showLoginNudge: boolean
  setShowLoginNudge: (v: boolean) => void
}

const AuthCtx = createContext<AuthState | null>(null)

function getAnonymousId(): string {
  let id = localStorage.getItem('rs_anonymous_id')
  if (!id) {
    id = 'anon_' + Math.random().toString(36).slice(2) + Date.now().toString(36)
    localStorage.setItem('rs_anonymous_id', id)
  }
  return id
}

const PERSONA_SKIP_SESSION_KEY = 'rs_persona_skipped_session'
export const RETURN_PATH_KEY = 'rs_return_to'

/** Remember where the user was so /auth/success can send them back after OAuth. */
function saveReturnPath() {
  const here = window.location.pathname + window.location.search
  // Avoid bouncing back to /auth/* pages (would cause loops).
  if (!here.startsWith('/auth')) {
    sessionStorage.setItem(RETURN_PATH_KEY, here)
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [showLoginNudge, setShowLoginNudge] = useState(false)
  const [personaSkippedThisSession, setPersonaSkippedThisSession] = useState(() =>
    typeof sessionStorage !== 'undefined' && sessionStorage.getItem(PERSONA_SKIP_SESSION_KEY) === '1'
  )

  // Check session on mount
  useEffect(() => {
    fetch(`${API_BASE}/auth/me`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        if (data.user) setUser(data.user)
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const loginWithGoogle = useCallback(() => {
    saveReturnPath()
    window.location.href = `${API_BASE}/auth/google/login`
  }, [])

  const loginWithApple = useCallback(() => {
    saveReturnPath()
    window.location.href = `${API_BASE}/auth/apple/login`
  }, [])

  const logout = useCallback(async () => {
    await fetch(`${API_BASE}/auth/logout`, { method: 'POST', credentials: 'include' })
    setUser(null)
  }, [])

  const setUsername = useCallback(async (username: string): Promise<{ ok: boolean; error?: string }> => {
    try {
      const resp = await fetch(`${API_BASE}/auth/username`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ username }),
      })
      if (resp.ok) {
        // Refresh user state
        const meResp = await fetch(`${API_BASE}/auth/me`, { credentials: 'include' })
        const meData = await meResp.json()
        if (meData.user) setUser(meData.user)
        return { ok: true }
      }
      const err = await resp.json()
      return { ok: false, error: err.detail || 'Failed to set username' }
    } catch {
      return { ok: false, error: 'Network error' }
    }
  }, [])

  const checkUsername = useCallback(async (username: string): Promise<{ available: boolean; reason?: string }> => {
    try {
      const resp = await fetch(`${API_BASE}/auth/username/check?username=${encodeURIComponent(username)}`,
        { credentials: 'include' })
      return await resp.json()
    } catch {
      return { available: false, reason: 'Network error' }
    }
  }, [])

  // Sync settings to server when logged in
  const syncSettings = useCallback((key: string, value: any) => {
    // Always save to localStorage
    localStorage.setItem(key, JSON.stringify(value))
    // If logged in, also sync to server
    if (user) {
      fetch(`${API_BASE}/auth/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ [key]: value }),
      }).catch(() => {})
    }
  }, [user])

  // On login, pull server settings into localStorage
  useEffect(() => {
    if (!user) return
    // Migrate anonymous data
    const anonymousId = getAnonymousId()
    fetch(`${API_BASE}/auth/migrate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ anonymous_id: anonymousId, observation_ids: [], saved_items: [] }),
    }).catch(() => {})

    // Pull server settings
    fetch(`${API_BASE}/auth/settings`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        const settings = data.settings || {}
        for (const [key, value] of Object.entries(settings)) {
          if (value !== null && value !== undefined) {
            localStorage.setItem(key, JSON.stringify(value))
          }
        }
      })
      .catch(() => {})
  }, [user])

  const needsUsername = !!user && (!user.username || user.needs_username === true)

  const setPersonas = useCallback(async (personas: string[]): Promise<{ ok: boolean; error?: string }> => {
    try {
      const resp = await fetch(`${API_BASE}/auth/personas`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ personas }),
      })
      if (resp.ok) {
        const body = await resp.json()
        setUser(prev => prev ? {
          ...prev,
          personas: body.personas,
          personas_set_at: body.personas_set_at,
          personas_version: body.personas_version,
        } : prev)
        return { ok: true }
      }
      const err = await resp.json()
      return { ok: false, error: err.detail || 'Failed to save personas' }
    } catch {
      return { ok: false, error: 'Network error' }
    }
  }, [])

  const hasPersona = useCallback((key: string): boolean => {
    return !!user?.personas?.includes(key)
  }, [user])

  const hasAnyPersona = useCallback((...keys: string[]): boolean => {
    if (!user?.personas?.length) return false
    return keys.some(k => user.personas!.includes(k))
  }, [user])

  const isUnsetOrSkipped = useCallback((): boolean => {
    if (!user) return true
    return !user.personas || user.personas.length === 0
  }, [user])

  const skipPersonasThisSession = useCallback(() => {
    try { sessionStorage.setItem(PERSONA_SKIP_SESSION_KEY, '1') } catch {}
    setPersonaSkippedThisSession(true)
  }, [])

  const needsPersonas = !!user && !needsUsername && !user.personas_set_at && !personaSkippedThisSession

  return (
    <AuthCtx.Provider value={{
      user, loading, isLoggedIn: !!user, needsUsername, needsPersonas,
      loginWithGoogle, loginWithApple, logout,
      setUsername, checkUsername,
      setPersonas, skipPersonasThisSession,
      hasPersona, hasAnyPersona, isUnsetOrSkipped,
      syncSettings,
      showLoginNudge, setShowLoginNudge,
    }}>
      {children}
    </AuthCtx.Provider>
  )
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthCtx)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
