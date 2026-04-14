import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import WatershedHeader from '../components/WatershedHeader'
import { getSelectedWatershed } from '../components/WatershedHeader'
import './ExploreMapPage.css'

const API = 'http://localhost:8001/api/v1'

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'campground', label: '⛺ Camping' },
  { key: 'trailhead', label: '🥾 Trails' },
  { key: 'boat_ramp', label: '🚣 Boats' },
  { key: 'fishing_access', label: '🎣 Fishing' },
  { key: 'day_use', label: '☀ Day Use' },
]

const PIN_COLORS: Record<string, string> = {
  campground: '#1a6b4a',
  trailhead: '#92400e',
  boat_ramp: '#2563eb',
  fishing_access: '#d97706',
  day_use: '#7c3aed',
  swim_area: '#0891b2',
  waterfall: '#0d9488',
  swim_advisory: '#dc2626',
}

const WS_CENTERS: Record<string, [number, number]> = {
  mckenzie: [-122.3, 44.1],
  deschutes: [-121.3, 44.3],
  metolius: [-121.6, 44.5],
  klamath: [-121.6, 42.6],
  johnday: [-119.0, 44.6],
}

interface RecSite {
  id: number; name: string; rec_type: string
  latitude: number; longitude: number
  amenities: Record<string, any>
}

export default function ExploreMapPage() {
  const navigate = useNavigate()
  const { watershed: paramWs } = useParams<{ watershed?: string }>()
  const ws = paramWs || getSelectedWatershed() || 'deschutes'

  const [sites, setSites] = useState<RecSite[]>([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)

  // Fetch sites
  useEffect(() => {
    setLoading(true)
    fetch(`${API}/sites/${ws}/recreation`)
      .then(r => r.json())
      .then((data: RecSite[]) => { setSites(Array.isArray(data) ? data : []); setLoading(false) })
      .catch(() => { setSites([]); setLoading(false) })
  }, [ws])

  // Init map
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

  // Filtered sites
  const filtered = filter === 'all' ? sites : sites.filter(s => s.rec_type === filter)

  // Update markers
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    markersRef.current.forEach(m => m.remove())
    markersRef.current = []
    popupRef.current?.remove()

    if (filtered.length === 0) return

    const bounds = new maplibregl.LngLatBounds()
    filtered.forEach(s => bounds.extend([s.longitude, s.latitude]))
    map.fitBounds(bounds, { padding: 50, maxZoom: 13 })

    filtered.forEach(s => {
      const color = PIN_COLORS[s.rec_type] || '#666'
      const el = document.createElement('div')
      el.className = 'explore-map-pin'
      el.style.backgroundColor = color

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([s.longitude, s.latitude])
        .addTo(map)

      el.addEventListener('click', (e) => {
        e.stopPropagation()
        popupRef.current?.remove()

        const amenities = s.amenities || {}
        const badges = [
          amenities.fee ? '💲 Fee' : '',
          amenities.accessible ? '♿' : '',
          amenities.pets_allowed ? '🐕 Pets' : '',
          amenities.reservable ? '📅 Reserve' : '',
          amenities.restrooms ? '🚻' : '',
          amenities.parking ? '🅿' : '',
        ].filter(Boolean).join(' · ')

        const popup = new maplibregl.Popup({ offset: 12, maxWidth: '220px' })
          .setLngLat([s.longitude, s.latitude])
          .setHTML(`
            <div class="explore-popup">
              <div class="explore-popup-name">${s.name}</div>
              <div class="explore-popup-type" style="color:${color}">${s.rec_type.replace(/_/g, ' ')}</div>
              ${badges ? `<div class="explore-popup-badges">${badges}</div>` : ''}
              ${amenities.forest ? `<div class="explore-popup-forest">${amenities.forest}</div>` : ''}
            </div>
          `)
          .addTo(map)
        popupRef.current = popup
      })

      markersRef.current.push(marker)
    })
  }, [filtered])

  return (
    <div className="explore-map-page">
      <div className="explore-map-top">
        <button className="explore-map-back" onClick={() => navigate(`/path/explore/${ws}`)}>← Explore List</button>
      </div>
      <WatershedHeader watershed={ws} basePath="/path/explore-map" />

      {/* Type filter */}
      <div className="explore-map-filters">
        {FILTERS.map(f => (
          <button
            key={f.key}
            className={`explore-map-filter${filter === f.key ? ' active' : ''}`}
            onClick={() => setFilter(f.key)}
          >
            {f.label}
          </button>
        ))}
        <span className="explore-map-count">
          {loading ? 'Loading...' : `${filtered.length} sites`}
        </span>
      </div>

      {/* Map */}
      <div ref={mapContainer} className="explore-map-container" />
    </div>
  )
}
