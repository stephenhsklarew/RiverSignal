import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDeepTrail, WATERSHEDS } from '../components/DeepTrailContext'
import logo from '../assets/deeptrail-logo.svg'
import './DeepTrailPage.css'

export default function DeepTrailPickPage() {
  const { loc, selectLocation } = useDeepTrail()
  const navigate = useNavigate()
  const [gpsLoading, setGpsLoading] = useState(false)

  useEffect(() => {
    document.title = 'Deep Trail'
    return () => { document.title = 'RiverSignal' }
  }, [])

  // If user already has a location in context, redirect
  useEffect(() => {
    if (loc) navigate(`/trail/story/${loc.id}`, { replace: true })
  }, [loc, navigate])

  const useMyLocation = () => {
    if (!navigator.geolocation) return
    setGpsLoading(true)
    navigator.geolocation.getCurrentPosition(
      pos => {
        setGpsLoading(false)
        const lat = pos.coords.latitude
        const lon = pos.coords.longitude
        const id = `${lat.toFixed(4)},${lon.toFixed(4)}`
        selectLocation({ id, name: `${lat.toFixed(4)}°N, ${Math.abs(lon).toFixed(4)}°W`, lat, lon })
        navigate(`/trail/story/${id}`)
      },
      () => setGpsLoading(false)
    )
  }

  const pickWatershed = (ws: typeof WATERSHEDS[number]) => {
    selectLocation(ws)
    navigate(`/trail/story/${ws.id}`)
  }

  return (
    <div className="dt-app">
      <header className="dt-header">
        <div className="dt-header-top">
          <span className="dt-logo-link"><img src={logo} alt="DeepTrail" className="dt-logo" /></span>
        </div>
        <h1 className="dt-title">Discover the Ancient Worlds Beneath Your Feet</h1>
      </header>

      <main className="dt-pick-content">
        <button className="dt-gps-btn" onClick={useMyLocation} disabled={gpsLoading}>
          📍 {gpsLoading ? 'Getting location...' : 'Use My Location'}
        </button>

        <div className="dt-pick-divider">pick a watershed</div>
        <div className="dt-watershed-list">
          {WATERSHEDS.map(ws => (
            <button key={ws.id} className="dt-watershed-btn" onClick={() => pickWatershed(ws)}>
              <img src={ws.photo} alt={ws.name} className="dt-ws-thumb" loading="lazy" />
              <div className="dt-ws-info">
                <span className="dt-ws-name">{ws.name}</span>
                <span className="dt-ws-caption">{ws.caption}</span>
              </div>
              <span className="dt-ws-arrow">→</span>
            </button>
          ))}
        </div>
      </main>
    </div>
  )
}
