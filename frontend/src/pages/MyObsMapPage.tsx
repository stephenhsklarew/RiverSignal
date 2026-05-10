import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import WatershedHeader, { getSelectedWatershed } from '../components/WatershedHeader'
import { useAuth } from '../components/AuthContext'
import { API_BASE } from '../config'
import './MyObsMapPage.css'

const API = API_BASE

const WS_CENTERS: Record<string, [number, number]> = {
  mckenzie: [-122.3, 44.1],
  deschutes: [-121.3, 44.3],
  metolius: [-121.6, 44.5],
  klamath: [-121.6, 42.6],
  johnday: [-119.0, 44.6],
  skagit: [-121.50, 48.45],
  green_river: [-110.15, 38.99],
}

interface UserObservation {
  id: string
  photo_url: string | null
  thumbnail_url: string | null
  latitude: number | null
  longitude: number | null
  observed_at: string | null
  species_name: string | null
  common_name: string | null
  category: string | null
  notes: string | null
  watershed: string | null
  visibility: string
  scientific_name: string | null
}

export default function MyObsMapPage() {
  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])

  const navigate = useNavigate()
  const { watershed: paramWs } = useParams<{ watershed?: string }>()
  const ws = paramWs || getSelectedWatershed() || 'mckenzie'
  const { isLoggedIn } = useAuth()

  const [obs, setObs] = useState<UserObservation[]>([])
  const [loading, setLoading] = useState(true)

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)

  useEffect(() => {
    if (!isLoggedIn) { setObs([]); setLoading(false); return }
    setLoading(true)
    fetch(`${API}/observations/user?mine=true&watershed=${ws}`, { credentials: 'include' })
      .then(r => r.json())
      .then(data => {
        setObs(Array.isArray(data) ? data.filter(o => o.latitude != null && o.longitude != null) : [])
        setLoading(false)
      })
      .catch(() => { setObs([]); setLoading(false) })
  }, [ws, isLoggedIn])

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return
    const center = WS_CENTERS[ws] || [-121.5, 44.0]
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center,
      zoom: 9,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    markersRef.current.forEach(m => m.remove())
    markersRef.current = []
    popupRef.current?.remove()

    if (obs.length === 0) return

    const bounds = new maplibregl.LngLatBounds()
    obs.forEach(o => bounds.extend([o.longitude!, o.latitude!]))
    map.fitBounds(bounds, { padding: 50, maxZoom: 13 })

    obs.forEach(o => {
      const el = document.createElement('div')
      el.className = 'myobs-map-pin'

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([o.longitude!, o.latitude!])
        .addTo(map)

      el.addEventListener('click', (e) => {
        e.stopPropagation()
        popupRef.current?.remove()

        const name = o.common_name || o.species_name || o.category || 'Observation'
        const sci = o.scientific_name || ''
        const date = o.observed_at ? new Date(o.observed_at).toLocaleDateString() : ''
        const photo = o.thumbnail_url || o.photo_url
        const photoHtml = photo
          ? `<img src="${photo}" class="myobs-popup-img" />`
          : '<div class="myobs-popup-no-img">No photo</div>'

        const popup = new maplibregl.Popup({ offset: 12, maxWidth: '240px' })
          .setLngLat([o.longitude!, o.latitude!])
          .setHTML(`
            <div class="myobs-popup">
              ${photoHtml}
              <div class="myobs-popup-name">${name}</div>
              ${sci ? `<div class="myobs-popup-sci">${sci}</div>` : ''}
              ${date ? `<div class="myobs-popup-date">${date}</div>` : ''}
              ${o.notes ? `<div class="myobs-popup-notes">${o.notes}</div>` : ''}
            </div>
          `)
          .addTo(map)
        popupRef.current = popup
      })

      markersRef.current.push(marker)
    })
  }, [obs])

  return (
    <div className="myobs-map-page">
      <div className="myobs-map-top">
        <button className="myobs-map-back" onClick={() => navigate('/path/saved')}>← Saved</button>
      </div>
      <WatershedHeader watershed={ws} basePath="/path/saved/map" />

      <div className="myobs-map-meta">
        <span className="myobs-map-count">
          {!isLoggedIn
            ? 'Sign in to see your observations'
            : loading
            ? 'Loading...'
            : `${obs.length} observation${obs.length === 1 ? '' : 's'}`}
        </span>
      </div>

      <div ref={mapContainer} className="myobs-map-container" />
    </div>
  )
}
