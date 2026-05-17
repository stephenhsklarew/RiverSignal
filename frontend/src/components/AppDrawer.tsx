import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'
import useSWR from 'swr'
import { useAuth } from './AuthContext'
import LoginModal from './LoginModal'
import { API_BASE } from '../config'
import './AppDrawer.css'

const TIP_DISMISSED_KEY = 'riverpath-drawer-tip-dismissed'

interface AppDrawerProps {
  open: boolean
  onClose: () => void
  /** When provided, the drawer shows a "Customize this page" row in Features. */
  onCustomizeCards?: () => void
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then(r => {
    if (r.status === 401) return null
    return r.json()
  })

export default function AppDrawer({ open, onClose, onCustomizeCards }: AppDrawerProps) {
  const { user, isLoggedIn, logout } = useAuth()
  const [showLogin, setShowLogin] = useState(false)

  const { data: alertsData } = useSWR<{ alerts: unknown[] }>(
    isLoggedIn && open ? `${API_BASE}/alerts?seen=false` : null,
    fetcher,
    { refreshInterval: 60_000 },
  )
  const unseenAlerts = alertsData?.alerts?.length || 0

  // Esc closes the drawer.
  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  const tipDismissed = (typeof window !== 'undefined') && localStorage.getItem(TIP_DISMISSED_KEY) === '1'

  function dismissTip() {
    localStorage.setItem(TIP_DISMISSED_KEY, '1')
    // Force a re-render via a no-op state set on the parent — easiest is to close+reopen, but here we just navigate to same path.
    // Simpler: set inline style on the tip via DOM. We'll just rely on the next open showing it as dismissed.
    const tip = document.getElementById('app-drawer-tip')
    if (tip) tip.style.display = 'none'
  }

  function handleLogout() {
    onClose()
    logout()
  }

  function handleSignIn() {
    onClose()
    setShowLogin(true)
  }

  const initials = isLoggedIn ? (user?.username || user?.name || 'U')[0].toUpperCase() : ''

  return (
    <>
      <div
        className={`app-drawer-backdrop${open ? ' open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={`app-drawer${open ? ' open' : ''}`}
        aria-label="Main menu"
        aria-hidden={!open}
      >
        <div className="app-drawer-header">
          <button
            type="button"
            className="app-drawer-close"
            onClick={onClose}
            aria-label="Close menu"
          >✕</button>
          {isLoggedIn ? (
            user?.avatar ? (
              <img src={user.avatar} alt="" className="app-drawer-avatar" />
            ) : (
              <div className="app-drawer-avatar app-drawer-avatar-text">{initials}</div>
            )
          ) : (
            <div className="app-drawer-avatar app-drawer-avatar-empty" aria-hidden="true">
              <svg viewBox="0 0 24 24"><circle cx="12" cy="8.5" r="3.5"/><path d="M5 20c0-3.5 3.5-6 7-6s7 2.5 7 6" strokeLinecap="round"/></svg>
            </div>
          )}
          <div className="app-drawer-user">
            {isLoggedIn ? (
              <>
                <span className="app-drawer-user-name">{user?.username ? `@${user.username}` : user?.name}</span>
                <span className="app-drawer-user-email">{user?.email}</span>
              </>
            ) : (
              <>
                <span className="app-drawer-user-name">Sign in to RiverPath</span>
                <button className="app-drawer-signin" onClick={handleSignIn}>
                  Sign in or sign up
                </button>
              </>
            )}
          </div>
        </div>

        <div className="app-drawer-scroll">
          {!tipDismissed && (
            <div className="app-drawer-tip" id="app-drawer-tip">
              <span className="app-drawer-tip-text">
                Find watershed‑health trends in <b>Steward</b> and the best reaches near you in <b>Where to fish</b>. Tap any item below to explore.
              </span>
              <button className="app-drawer-tip-close" onClick={dismissTip} aria-label="Dismiss tip">✕</button>
            </div>
          )}

          <div className="app-drawer-section-head">Features</div>

          {onCustomizeCards && (
            <button className="app-drawer-row" onClick={() => { onClose(); onCustomizeCards() }}>
              <svg viewBox="0 0 24 24"><rect x="3" y="4" width="7" height="7" rx="1.5"/><rect x="14" y="4" width="7" height="7" rx="1.5"/><rect x="3" y="13" width="7" height="7" rx="1.5"/><rect x="14" y="13" width="7" height="7" rx="1.5"/></svg>
              <span className="app-drawer-row-label">Customize this page</span>
            </button>
          )}

          <NavLink to="/path/steward" className={({ isActive }) => `app-drawer-row${isActive ? ' active' : ''}`} onClick={onClose}>
            <svg viewBox="0 0 24 24"><path d="M12 3l9 4-9 4-9-4 9-4z"/><path d="M3 11l9 4 9-4M3 15l9 4 9-4" strokeLinejoin="round"/></svg>
            <span className="app-drawer-row-label">Steward</span>
          </NavLink>
          <NavLink to="/path/where" className={({ isActive }) => `app-drawer-row${isActive ? ' active' : ''}`} onClick={onClose}>
            <svg viewBox="0 0 24 24"><path d="M12 2C8 2 5 5 5 9c0 5 7 13 7 13s7-8 7-13c0-4-3-7-7-7z"/><circle cx="12" cy="9" r="2.5"/></svg>
            <span className="app-drawer-row-label">Where to fish</span>
          </NavLink>

          <div className="app-drawer-divider" />
          <div className="app-drawer-section-head">Notifications</div>

          <NavLink to="/path/alerts" className={({ isActive }) => `app-drawer-row${isActive ? ' active' : ''}`} onClick={onClose}>
            <svg viewBox="0 0 24 24"><path d="M12 3.5a5.5 5.5 0 0 0-5.5 5.5v3.2L4.9 15a.9.9 0 0 0 .8 1.4h12.6a.9.9 0 0 0 .8-1.4l-1.6-2.8V9A5.5 5.5 0 0 0 12 3.5Z" strokeLinejoin="round"/><path d="M9.7 18.5a2.5 2.5 0 0 0 4.6 0" strokeLinecap="round"/></svg>
            <span className="app-drawer-row-label">Configure alerts</span>
            {unseenAlerts > 0 && <span className="app-drawer-row-badge">{unseenAlerts > 99 ? '99+' : unseenAlerts}</span>}
          </NavLink>

          {isLoggedIn && (
            <>
              <div className="app-drawer-divider" />
              <div className="app-drawer-section-head">Account</div>
              <button className="app-drawer-row" onClick={handleLogout}>
                <svg viewBox="0 0 24 24"><path d="M15 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4" strokeLinejoin="round"/><path d="M10 16l4-4-4-4M14 12H3" strokeLinecap="round" strokeLinejoin="round"/></svg>
                <span className="app-drawer-row-label">Sign out</span>
              </button>
            </>
          )}
        </div>
      </aside>
      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          mode={localStorage.getItem('rs_has_account') === 'true' ? 'signin' : 'signup'}
        />
      )}
    </>
  )
}
