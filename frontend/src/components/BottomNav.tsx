import { useRef } from 'react'
import { NavLink } from 'react-router-dom'
import { useSaved } from './SavedContext'
import { getSelectedWatershed } from './WatershedHeader'
import { useUserObsCount } from './useUserObsCount'
import PhotoObservation, { type PhotoObservationHandle } from './PhotoObservation'
import './BottomNav.css'

/**
 * RiverPath bottom toolbar — Option F.
 * 5 slots: River Now · Explore · 📷 Observe (featured FAB) · Hatch · Saved.
 * Steward / Alerts / Where / etc. live in the AppDrawer (top-left ☰).
 */

type Tab = {
  to: string
  label: string
  icon: React.ReactNode
  key: string
}

const TABS: Tab[] = [
  { to: '/path/now', key: 'now', label: 'River Now', icon: (
    <svg viewBox="0 0 24 24"><path d="M2 12c2-2.5 4-2.5 6 0s4 2.5 6 0 4-2.5 6 0M2 17c2-2.5 4-2.5 6 0s4 2.5 6 0 4-2.5 6 0"/></svg>
  ) },
  { to: '/path/explore', key: 'explore', label: 'Explore', icon: (
    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M15 9l-4 2-2 4 4-2z" strokeLinejoin="round"/></svg>
  ) },
  { to: '/path/hatch', key: 'hatch', label: 'Hatch', icon: (
    <svg viewBox="0 0 24 24"><ellipse cx="12" cy="13" rx="4" ry="6"/><path d="M12 7V4M9 5l-2-2M15 5l2-2M8 10l-3-1M16 10l3-1M8 16l-3 1M16 16l3 1"/></svg>
  ) },
  { to: '/path/saved', key: 'saved', label: 'Saved', icon: (
    <svg viewBox="0 0 24 24"><path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z" strokeLinejoin="round"/></svg>
  ) },
]

export default function BottomNav() {
  const { countSaved } = useSaved()
  const ws = getSelectedWatershed() || 'mckenzie'
  const obsCount = useUserObsCount(ws)
  const savedCount = countSaved(ws) + obsCount

  const photoRef = useRef<PhotoObservationHandle>(null)

  const renderTab = (tab: Tab) => (
    <NavLink
      key={tab.to}
      to={tab.to}
      role="tab"
      className={({ isActive }) => `bottom-nav-tab${isActive ? ' active' : ''}`}
      aria-selected={undefined}
    >
      <span className={`bottom-nav-icon bottom-nav-icon-${tab.key}`}>
        {tab.label === 'Saved' && savedCount > 0 ? (
          <span className="bottom-nav-icon-wrap">
            {tab.icon}
            <span className="bottom-nav-badge">{savedCount > 99 ? '99+' : savedCount}</span>
          </span>
        ) : tab.icon}
      </span>
      <span className="bottom-nav-label">{tab.label}</span>
    </NavLink>
  )

  return (
    <>
      <nav className="bottom-nav" role="tablist">
        {renderTab(TABS[0]) /* River Now */}
        {renderTab(TABS[1]) /* Explore */}

        <div className="bottom-nav-camera-slot">
          <button
            type="button"
            className="bottom-nav-camera-fab"
            onClick={() => photoRef.current?.open()}
            aria-label="Log a new observation"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M4 8h3l1.5-2h7L17 8h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z" strokeLinejoin="round"/>
              <circle cx="12" cy="13.5" r="4"/>
            </svg>
          </button>
          <span className="bottom-nav-camera-label">Log</span>
        </div>

        {renderTab(TABS[2]) /* Hatch */}
        {renderTab(TABS[3]) /* Saved */}
      </nav>

      {/* Single PhotoObservation instance for the RiverPath bottom toolbar.
          Its built-in FAB is hidden; we open it imperatively from the camera tab. */}
      <PhotoObservation app="riverpath" watershed={ws} hideFab ref={photoRef} />
    </>
  )
}
