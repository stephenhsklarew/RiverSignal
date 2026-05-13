import { NavLink } from 'react-router-dom'
import useSWR from 'swr'
import { useSaved } from './SavedContext'
import { useAuth } from './AuthContext'
import { getSelectedWatershed } from './WatershedHeader'
import { useUserObsCount } from './useUserObsCount'
import { API_BASE } from '../config'
import './BottomNav.css'

type Tab = {
  to: string
  label: string
  icon: string
  key: string
  // Persona keys that should see this tab. Omit to always show.
  // Anonymous users and users who skipped persona selection see all tabs.
  requires?: string[]
}

const TABS: Tab[] = [
  { to: '/path/now', label: 'River Now', icon: '〰', key: 'now' },
  { to: '/path/explore', label: 'Explore', icon: '◎', key: 'explore' },
  { to: '/path/hatch', label: 'Hatch', icon: '◬', key: 'hatch' },
  { to: '/path/alerts', label: 'Alerts', icon: '🔔', key: 'alerts',
    requires: ['angler_self_guided', 'guide_professional'] },
  { to: '/path/steward', label: 'Steward', icon: '♻︎', key: 'steward' },
  { to: '/path/saved', label: 'Saved', icon: '♡', key: 'saved' },
]

export default function BottomNav() {
  const { countSaved } = useSaved()
  const { isLoggedIn, hasAnyPersona, isUnsetOrSkipped } = useAuth()
  const ws = getSelectedWatershed() || 'mckenzie'
  const obsCount = useUserObsCount(ws)
  const savedCount = countSaved(ws) + obsCount

  const { data: alertsData } = useSWR<{ alerts: unknown[] }>(
    isLoggedIn ? `${API_BASE}/alerts?seen=false` : null,
    (u: string) => fetch(u, { credentials: 'include' }).then(r => r.json()),
    { refreshInterval: 60_000 }
  )
  const unseenAlerts = alertsData?.alerts?.length || 0

  const visibleTabs = TABS.filter(tab => {
    if (!tab.requires) return true
    if (isUnsetOrSkipped()) return true
    return hasAnyPersona(...tab.requires)
  })

  return (
    <nav className="bottom-nav" role="tablist">
      {visibleTabs.map(tab => (
        <NavLink
          key={tab.to}
          to={tab.to}
          role="tab"
          className={({ isActive }) => `bottom-nav-tab${isActive ? ' active' : ''}`}
          aria-selected={undefined} // NavLink handles active state
        >
          <span className={`bottom-nav-icon bottom-nav-icon-${tab.key}`}>
            {tab.label === 'Saved' && savedCount > 0 ? (
              <span className="bottom-nav-icon-wrap">{tab.icon}<span className="bottom-nav-badge">{savedCount > 99 ? '99+' : savedCount}</span></span>
            ) : tab.label === 'Alerts' && unseenAlerts > 0 ? (
              <span className="bottom-nav-icon-wrap">{tab.icon}<span className="bottom-nav-badge">{unseenAlerts > 99 ? '99+' : unseenAlerts}</span></span>
            ) : tab.icon}
          </span>
          <span className="bottom-nav-label">{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
