import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import WatershedHeader from '../components/WatershedHeader'
import { getSelectedWatershed } from '../components/WatershedHeader'
import { useSaved } from '../components/SavedContext'
import { API_BASE } from '../config'
import './ExploreMapPage.css'

const API = API_BASE

const FILTERS = [
  { key: 'all', label: 'All' },
  { key: 'campground', label: '⛺ Camping' },
  { key: 'trailhead', label: '🥾 Trails' },
  { key: 'boat_ramp', label: '🚣 Boats' },
  { key: 'fishing_access', label: '🎣 Fishing' },
  { key: 'fly_shop', label: '🏪 Fly Shops' },
  { key: 'guide_service', label: '🚣 Guides' },
  { key: 'day_use', label: '☀ Day Use' },
]

const PIN_COLORS: Record<string, string> = {
  campground: '#1a6b4a',
  trailhead: '#92400e',
  boat_ramp: '#2563eb',
  fishing_access: '#d97706',
  fly_shop: '#9333ea',
  guide_service: '#9333ea',
  both: '#9333ea',
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
  skagit: [-121.50, 48.45],
}

interface RecSite {
  id: number; name: string; rec_type: string
  latitude: number; longitude: number
  amenities: Record<string, any>
}

export default function ExploreMapPage() {
  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])
  const navigate = useNavigate()
  const { watershed: paramWs } = useParams<{ watershed?: string }>()
  const ws = paramWs || getSelectedWatershed() || 'deschutes'

  const { save, unsave, isSaved } = useSaved()
  const savedRef = useRef({ save, unsave, isSaved })
  savedRef.current = { save, unsave, isSaved }

  const [sites, setSites] = useState<RecSite[]>([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)

  // Fetch sites + fly shops
  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetch(`${API}/sites/${ws}/recreation`).then(r => r.json()).catch(() => []),
      fetch(`${API}/sites/${ws}/fly-shops`).then(r => r.json()).catch(() => []),
    ]).then(([recData, shopData]) => {
      const shops: RecSite[] = (shopData || []).map((s: any, i: number) => ({
        id: 90000 + i,
        name: s.name,
        rec_type: s.type === 'both' ? 'fly_shop' : s.type,
        latitude: s.latitude,
        longitude: s.longitude,
        amenities: { phone: s.phone, website: s.website, description: s.description },
      }))
      setSites([...(Array.isArray(recData) ? recData : []), ...shops])
      setLoading(false)
    })
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
  const filtered = filter === 'all' ? sites : sites.filter(s =>
    s.rec_type === filter
    || (filter === 'fly_shop' && s.rec_type === 'both')
    || (filter === 'guide_service' && (s.rec_type === 'guide_service' || s.rec_type === 'both'))
  )

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

        const itemId = `${s.rec_type}-${s.id}`
        const alreadySaved = savedRef.current.isSaved('recreation', itemId)

        const popup = new maplibregl.Popup({ offset: 12, maxWidth: '220px' })
          .setLngLat([s.longitude, s.latitude])
          .setHTML(`
            <div class="explore-popup">
              <div class="explore-popup-header">
                <div class="explore-popup-name">${s.name}</div>
                <button class="explore-popup-save" data-site-id="${s.id}" data-rec-type="${s.rec_type}" data-name="${s.name.replace(/"/g, '&quot;')}" title="${alreadySaved ? 'Remove from saved' : 'Save this place'}">${alreadySaved ? '♥' : '♡'}</button>
              </div>
              <div class="explore-popup-type" style="color:${color}">${s.rec_type.replace(/_/g, ' ')}</div>
              ${badges ? `<div class="explore-popup-badges">${badges}</div>` : ''}
              ${amenities.forest ? `<div class="explore-popup-forest">${amenities.forest}</div>` : ''}
              ${amenities.description ? `<div style="font-size:10px;color:#666;margin-top:3px">${amenities.description}</div>` : ''}
              ${amenities.phone ? `<div style="font-size:11px;margin-top:3px"><a href="tel:${amenities.phone}" style="color:#1a6b4a">📞 ${amenities.phone}</a></div>` : ''}
              ${amenities.website ? `<div style="font-size:11px"><a href="${amenities.website}" target="_blank" style="color:#1a6b4a">🌐 Website</a></div>` : ''}
            </div>
          `)
          .addTo(map)
        popupRef.current = popup

        // Attach save button click handler
        const saveBtn = popup.getElement()?.querySelector('.explore-popup-save')
        if (saveBtn) {
          saveBtn.addEventListener('click', (evt) => {
            evt.stopPropagation()
            const id = `${s.rec_type}-${s.id}`
            if (savedRef.current.isSaved('recreation', id)) {
              savedRef.current.unsave('recreation', id)
              saveBtn.textContent = '♡'
              saveBtn.setAttribute('title', 'Save this place')
            } else {
              savedRef.current.save({
                type: 'recreation',
                id,
                watershed: ws,
                label: s.name,
                sublabel: s.rec_type.replace(/_/g, ' '),
              })
              saveBtn.textContent = '♥'
              saveBtn.setAttribute('title', 'Remove from saved')
            }
          })
        }
      })

      markersRef.current.push(marker)
    })
  }, [filtered])

  return (
    <div className="explore-map-page">
      <WatershedHeader watershed={ws} basePath="/path/explore-map" />

      <div className="explore-map-top">
        <button className="explore-map-back" onClick={() => navigate(`/path/explore/${ws}`)}>← Explore List</button>
      </div>

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
