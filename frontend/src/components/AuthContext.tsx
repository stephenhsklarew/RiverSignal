import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react'

const API_BASE = 'http://localhost:8001/api/v1'

export interface User {
  id: string
  email: string
  name: string
  avatar: string
  username: string
  is_new: boolean
  needs_username?: boolean
}

interface AuthState {
  user: User | null
  loading: boolean
  isLoggedIn: boolean
  needsUsername: boolean
  loginWithGoogle: () => void
  loginWithApple: () => void
  logout: () => void
  setUsername: (username: string) => Promise<{ ok: boolean; error?: string }>
  checkUsername: (username: string) => Promise<{ available: boolean; reason?: string }>
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

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [showLoginNudge, setShowLoginNudge] = useState(false)

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
    window.location.href = `${API_BASE}/auth/google/login`
  }, [])

  const loginWithApple = useCallback(() => {
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

  return (
    <AuthCtx.Provider value={{
      user, loading, isLoggedIn: !!user, needsUsername,
      loginWithGoogle, loginWithApple, logout,
      setUsername, checkUsername, syncSettings,
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
