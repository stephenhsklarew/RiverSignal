import { NavLink, useLocation } from 'react-router-dom'
import { useSaved } from './SavedContext'
import { useDeepTrail } from './DeepTrailContext'
import './DeepTrailBottomNav.css'

export default function DeepTrailBottomNav() {
  const { loc } = useDeepTrail()
  const { listSaved } = useSaved()
  const dtSavedCount = listSaved().filter(i => ['fossil', 'mineral', 'rocksite'].includes(i.type)).length

  // Extract locationId from context or current URL
  const { pathname } = useLocation()
  const urlMatch = pathname.match(/\/trail\/\w+\/(.+)/)
  const locationId = loc?.id || (urlMatch ? urlMatch[1] : '')
  const suffix = locationId ? `/${locationId}` : ''

  const TABS = [
    { to: `/trail/story${suffix}`, label: 'Story', icon: '📖' },
    { to: `/trail/explore${suffix}`, label: 'Explore', icon: '🗺' },
    { to: `/trail/collect${suffix}`, label: 'Collect', icon: '🪨' },
    { to: `/trail/learn${suffix}`, label: 'Learn', icon: '🧩' },
    { to: `/trail/saved`, label: 'Saved', icon: '⭐' },
  ]

  return (
    <nav className="dt-bottom-nav" role="tablist">
      {TABS.map(tab => (
        <NavLink
          key={tab.to}
          to={tab.to}
          role="tab"
          className={({ isActive }) => `dt-bottom-nav-tab${isActive ? ' active' : ''}`}
        >
          <span className="dt-bottom-nav-icon">
            {tab.label === 'Saved' && dtSavedCount > 0
              ? <span className="dt-bottom-nav-icon-wrap">{tab.icon}<span className="dt-bottom-nav-badge">{dtSavedCount > 99 ? '99+' : dtSavedCount}</span></span>
              : tab.icon}
          </span>
          <span className="dt-bottom-nav-label">{tab.label}</span>
        </NavLink>
      ))}
    </nav>
  )
}
