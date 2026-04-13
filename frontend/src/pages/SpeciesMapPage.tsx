import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import WatershedHeader from '../components/WatershedHeader'
import { getSelectedWatershed } from '../components/WatershedHeader'
import './SpeciesMapPage.css'

const API = 'http://localhost:8001/api/v1'

const CATEGORIES = [
  { key: 'Actinopterygii', label: 'Fish' },
  { key: 'Insecta', label: 'Insects' },
]

// Watershed center coordinates for initial map view
const WS_CENTERS: Record<string, [number, number]> = {
  mckenzie: [-122.3, 44.1],
  deschutes: [-121.3, 44.3],
  metolius: [-121.6, 44.5],
  klamath: [-121.6, 42.6],
  johnday: [-119.0, 44.6],
}

interface ObsFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: {
    taxon_name: string
    common_name: string | null
    observed_at: string | null
    photo_url: string | null
    quality_grade: string
    source: string
  }
}

export default function SpeciesMapPage() {
  const navigate = useNavigate()
  const { watershed: paramWs } = useParams<{ watershed?: string }>()
  const ws = paramWs || getSelectedWatershed() || 'deschutes'

  const [category, setCategory] = useState('Actinopterygii')
  const [features, setFeatures] = useState<ObsFeature[]>([])
  const [loading, setLoading] = useState(true)

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)

  // Fetch observations
  useEffect(() => {
    setLoading(true)
    fetch(`${API}/sites/${ws}/observations/search?q=${category}&limit=500`)
      .then(r => r.json())
      .then(data => {
        setFeatures(data.features || [])
        setLoading(false)
      })
      .catch(() => { setFeatures([]); setLoading(false) })
  }, [ws, category])

  // Initialize map
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

  // Update markers when features change
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    // Clear old markers
    markersRef.current.forEach(m => m.remove())
    markersRef.current = []
    popupRef.current?.remove()

    if (features.length === 0) return

    // Fit bounds to features
    const bounds = new maplibregl.LngLatBounds()
    features.forEach(f => bounds.extend(f.geometry.coordinates as [number, number]))
    map.fitBounds(bounds, { padding: 50, maxZoom: 13 })

    // Add markers
    features.forEach(f => {
      const el = document.createElement('div')
      el.className = `species-map-pin ${category === 'Actinopterygii' ? 'fish' : 'insect'}`

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(f.geometry.coordinates as [number, number])
        .addTo(map)

      el.addEventListener('click', (e) => {
        e.stopPropagation()
        popupRef.current?.remove()

        const p = f.properties
        const photoHtml = p.photo_url
          ? `<img src="${p.photo_url}" class="species-popup-img" />`
          : '<div class="species-popup-no-img">No photo</div>'
        const name = p.common_name || p.taxon_name
        const date = p.observed_at || 'Unknown date'

        const popup = new maplibregl.Popup({ offset: 12, maxWidth: '220px' })
          .setLngLat(f.geometry.coordinates as [number, number])
          .setHTML(`
            <div class="species-popup">
              ${photoHtml}
              <div class="species-popup-name">${name}</div>
              <div class="species-popup-sci">${p.taxon_name}</div>
              <div class="species-popup-date">${date}</div>
            </div>
          `)
          .addTo(map)

        popupRef.current = popup
      })

      markersRef.current.push(marker)
    })
  }, [features, category])

  return (
    <div className="species-map-page">
      {/* Back + header */}
      <div className="species-map-top">
        <button className="species-map-back" onClick={() => navigate(`/path/now/${ws}`)}>← River Now</button>
      </div>
      <WatershedHeader watershed={ws} basePath="/path/map" />

      {/* Category toggle */}
      <div className="species-map-toggle">
        {CATEGORIES.map(c => (
          <button
            key={c.key}
            className={`species-map-cat${category === c.key ? ' active' : ''}`}
            onClick={() => setCategory(c.key)}
          >
            {c.label}
          </button>
        ))}
        <span className="species-map-count">
          {loading ? 'Loading...' : `${features.length} observations`}
        </span>
      </div>

      {/* Map */}
      <div ref={mapContainer} className="species-map-container" />
    </div>
  )
}
