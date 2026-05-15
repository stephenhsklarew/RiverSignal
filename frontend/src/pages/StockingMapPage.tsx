import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import WatershedHeader, { getSelectedWatershed } from '../components/WatershedHeader'
import { API_BASE } from '../config'
import './StockingMapPage.css'

const API = API_BASE

const WS_CENTERS: Record<string, [number, number]> = {
  mckenzie: [-122.3, 44.1],
  deschutes: [-121.3, 44.3],
  metolius: [-121.6, 44.5],
  klamath: [-121.6, 42.6],
  johnday: [-119.0, 44.6],
  skagit: [-121.50, 48.45],
  green_river: [-110.15, 38.99],
  shenandoah: [-78.20, 38.92],
}

interface StockingLocation {
  waterbody: string
  latitude: number | null
  longitude: number | null
  notes: string | null
  most_recent_date: string | null
  total_fish: number
  record_count: number
}

export default function StockingMapPage() {
  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])
  const navigate = useNavigate()
  const { watershed: paramWs } = useParams<{ watershed?: string }>()
  const ws = paramWs || getSelectedWatershed() || 'deschutes'

  const [locations, setLocations] = useState<StockingLocation[]>([])
  const [loading, setLoading] = useState(true)

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)

  useEffect(() => {
    setLoading(true)
    fetch(`${API}/sites/${ws}/fishing/stocking/locations`)
      .then(r => r.json())
      .then(data => {
        setLocations(Array.isArray(data) ? data : [])
        setLoading(false)
      })
      .catch(() => { setLocations([]); setLoading(false) })
  }, [ws])

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return
    const center = WS_CENTERS[ws] || [-121.5, 44.0]
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center,
      zoom: 8,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    mapRef.current = map
    return () => { map.remove(); mapRef.current = null }
  }, [])

  const mappable = locations.filter(l => l.latitude != null && l.longitude != null)
  const unmapped = locations.length - mappable.length

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    markersRef.current.forEach(m => m.remove())
    markersRef.current = []
    popupRef.current?.remove()

    if (mappable.length === 0) return

    const bounds = new maplibregl.LngLatBounds()
    mappable.forEach(l => bounds.extend([l.longitude!, l.latitude!]))
    map.fitBounds(bounds, { padding: 60, maxZoom: 11 })

    mappable.forEach(l => {
      const el = document.createElement('div')
      el.className = 'stocking-map-pin'

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([l.longitude!, l.latitude!])
        .addTo(map)

      el.addEventListener('click', (e) => {
        e.stopPropagation()
        popupRef.current?.remove()

        const dateLabel = l.most_recent_date ? `Last release: ${new Date(l.most_recent_date).toLocaleDateString()}` : ''
        const fishLabel = l.total_fish ? `${l.total_fish.toLocaleString()} fish across ${l.record_count} releases` : `${l.record_count} releases`
        const notesLabel = l.notes ? `<div class="stocking-popup-notes">${l.notes}</div>` : ''

        const popup = new maplibregl.Popup({ offset: 12, maxWidth: '260px' })
          .setLngLat([l.longitude!, l.latitude!])
          .setHTML(`
            <div class="stocking-popup">
              <div class="stocking-popup-name">${l.waterbody}</div>
              ${notesLabel}
              <div class="stocking-popup-stat">${fishLabel}</div>
              ${dateLabel ? `<div class="stocking-popup-date">${dateLabel}</div>` : ''}
            </div>
          `)
          .addTo(map)
        popupRef.current = popup
      })

      markersRef.current.push(marker)
    })
  }, [mappable])

  return (
    <div className="stocking-map-page">
      <WatershedHeader watershed={ws} basePath="/path/stocking" />
      <div className="stocking-map-top">
        <button className="stocking-map-back" onClick={() => navigate(`/path/now/${ws}`)}>← River Now</button>
      </div>

      <div className="stocking-map-meta">
        <span className="stocking-map-count">
          {loading
            ? 'Loading stocking locations…'
            : `${mappable.length} mapped${unmapped > 0 ? ` · ${unmapped} unmapped (coordinates pending)` : ''}`}
        </span>
      </div>

      <div className="stocking-map-stage">
        <div ref={mapContainer} className="stocking-map-container" />
        {loading && (
          <div className="stocking-map-loading-overlay" role="status" aria-live="polite">
            <div className="stocking-map-spinner" aria-hidden="true" />
            <div className="stocking-map-loading-text">Loading pins…</div>
          </div>
        )}
      </div>
    </div>
  )
}
