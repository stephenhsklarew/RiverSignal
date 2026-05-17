import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import rpLogo from '../assets/riverpath-logo.svg'
import AppDrawer from './AppDrawer'
import './WatershedHeader.css'

const WATERSHED_ORDER = ['deschutes', 'green_river', 'johnday', 'klamath', 'mckenzie', 'metolius', 'shenandoah', 'skagit']
const WATERSHED_LABELS: Record<string, string> = {
  mckenzie: 'McKenzie River', deschutes: 'Deschutes River', metolius: 'Metolius River',
  klamath: 'Upper Klamath Basin', johnday: 'John Day River', skagit: 'Skagit River',
  green_river: 'Green River',
  shenandoah: 'Shenandoah River',
}

export const WS_STORAGE_KEY = 'riverpath-selected-watershed'

export function getSelectedWatershed(): string | null {
  return sessionStorage.getItem(WS_STORAGE_KEY)
}

export function setSelectedWatershed(ws: string) {
  sessionStorage.setItem(WS_STORAGE_KEY, ws)
}

export function clearSelectedWatershed() {
  sessionStorage.removeItem(WS_STORAGE_KEY)
}

interface WatershedHeaderProps {
  watershed: string
  /** Base path for navigation when changing watershed (e.g. "/path/now") */
  basePath: string
  /** Optional handler for the page-specific "Customize this page" row in the drawer. */
  onSettingsClick?: () => void
  /** Deprecated — UserMenu is no longer rendered; kept for backward-compatible call sites. */
  hideUserMenu?: boolean
}

export default function WatershedHeader({ watershed, basePath, onSettingsClick }: WatershedHeaderProps) {
  const navigate = useNavigate()
  const [showPicker, setShowPicker] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)

  const handleSelect = (ws: string) => {
    setShowPicker(false)
    setSelectedWatershed(ws)
    navigate(`${basePath}/${ws}`)
  }

  return (
    <>
      <div className="ws-header">
        <button
          type="button"
          className={`ws-header-hamburger${drawerOpen ? ' is-x' : ''}`}
          onClick={() => setDrawerOpen(o => !o)}
          aria-label="Open menu"
          aria-expanded={drawerOpen}
        >
          <span className="ws-header-hamburger-bar" />
          <span className="ws-header-hamburger-bar" />
          <span className="ws-header-hamburger-bar" />
        </button>
        <img src={rpLogo} alt="RiverPath" className="ws-header-logo" />
        <button className="ws-header-name" onClick={() => setShowPicker(true)}>
          {WATERSHED_LABELS[watershed] || watershed} <span className="ws-header-caret">▾</span>
        </button>
      </div>

      <AppDrawer
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        onCustomizeCards={onSettingsClick}
      />

      {showPicker && (
        <div className="ws-modal-overlay" onClick={() => setShowPicker(false)}>
          <div className="ws-modal" onClick={e => e.stopPropagation()}>
            <div className="ws-modal-top">
              <span>Choose a river</span>
              <button className="ws-modal-close" onClick={() => setShowPicker(false)}>✕</button>
            </div>
            <div className="ws-modal-list">
              {WATERSHED_ORDER.map(ws => (
                <button
                  key={ws}
                  className={`ws-modal-item${ws === watershed ? ' active' : ''}`}
                  onClick={() => handleSelect(ws)}
                >
                  {WATERSHED_LABELS[ws]}
                </button>
              ))}
            </div>
            <button className="ws-modal-all" onClick={() => {
              setShowPicker(false)
              clearSelectedWatershed()
              navigate('/path/now')
            }}>
              View all rivers
            </button>
          </div>
        </div>
      )}
    </>
  )
}
