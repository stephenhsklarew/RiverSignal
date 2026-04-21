import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDeepTrail, WATERSHEDS } from './DeepTrailContext'
import UserMenu from './UserMenu'
import logo from '../assets/deeptrail-logo.svg'

interface DeepTrailHeaderProps {
  /** Current tab path segment (e.g. "story", "explore", "collect", "learn") */
  tab: string
}

export default function DeepTrailHeader({ tab }: DeepTrailHeaderProps) {
  const navigate = useNavigate()
  const { loc, selectLocation } = useDeepTrail()
  const [showPicker, setShowPicker] = useState(false)

  const handleSelect = (ws: typeof WATERSHEDS[0]) => {
    setShowPicker(false)
    selectLocation(ws)
    navigate(`/trail/${tab}/${ws.id}`)
  }

  return (
    <>
      <header className="dt-detail-header">
        <img src={logo} alt="DeepTrail" className="dt-logo" />
        {loc && (
          <>
            <span className="dt-header-name">{loc.name}</span>
            <button className="dt-header-change" onClick={() => setShowPicker(true)}>Change</button>
          </>
        )}
        <UserMenu dark />
      </header>

      {showPicker && (
        <div className="dt-ws-modal-overlay" onClick={() => setShowPicker(false)}>
          <div className="dt-ws-modal" onClick={e => e.stopPropagation()}>
            <div className="dt-ws-modal-top">
              <span>Choose a location</span>
              <button className="dt-ws-modal-close" onClick={() => setShowPicker(false)}>✕</button>
            </div>
            <div className="dt-ws-modal-list">
              {WATERSHEDS.map(ws => (
                <button
                  key={ws.id}
                  className={`dt-ws-modal-item${ws.id === loc?.id ? ' active' : ''}`}
                  onClick={() => handleSelect(ws)}
                >
                  <span className="dt-ws-modal-item-name">{ws.name}</span>
                  {ws.caption && <span className="dt-ws-modal-item-caption">{ws.caption}</span>}
                </button>
              ))}
            </div>
            <button className="dt-ws-modal-all" onClick={() => {
              setShowPicker(false)
              navigate('/trail')
            }}>
              Browse all locations
            </button>
          </div>
        </div>
      )}
    </>
  )
}
