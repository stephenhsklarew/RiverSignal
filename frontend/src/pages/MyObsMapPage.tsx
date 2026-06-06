import { useEffect, useMemo, useRef } from 'react'
import useSWR from 'swr'
import { useNavigate, useParams } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import WatershedHeader, { getSelectedWatershed } from '../components/WatershedHeader'
import { useAuth } from '../components/AuthContext'
import { useSaved } from '../components/SavedContext'
import './MyObsMapPage.css'


const WS_CENTERS: Record<string, [number, number]> = {
  mckenzie: [-122.3, 44.1],
  deschutes: [-121.3, 44.3],
  metolius: [-121.6, 44.5],
  klamath: [-121.6, 42.6],
  johnday: [-119.0, 44.6],
  skagit: [-121.50, 48.45],
  green_river: [-110.15, 38.99],
  shenandoah: [-78.20, 38.92],
  mad_river_oh: [-83.85, 40.05],
  ipswich_river_ma: [-70.95, 42.65],
  clinch_river_va: [-82.30, 36.88],
  new_river_va: [-80.72, 37.05],
  chattahoochee: [-84.30, 34.00],
  meramec: [-91.00, 38.25],
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
  const { listSaved } = useSaved()

  // SWR-backed so map pins render from cache instantly on navigation;
  // shares the cache key with SavedPage's `/observations/user` fetch.
  const { data: obsRaw, isLoading } = useSWR<UserObservation[]>(
    isLoggedIn ? `/observations/user?mine=true&watershed=${ws}` : null,
    { dedupingInterval: 60_000 },
  )

  // Normalize the owner's API observations and any observations received via a
  // shared link (localStorage, flagged `shared`) into one set of map points —
  // a recipient (often not signed in) only has the shared ones.
  const points = useMemo(() => {
    const api = (Array.isArray(obsRaw) ? obsRaw : [])
      .filter(o => o.latitude != null && o.longitude != null)
      .map(o => ({
        lng: o.longitude!, lat: o.latitude!,
        name: o.common_name || o.species_name || o.category || 'Observation',
        sci: o.scientific_name || '',
        date: o.observed_at ? new Date(o.observed_at).toLocaleDateString() : '',
        photo: o.thumbnail_url || o.photo_url, notes: o.notes, shared: false,
      }))
    const shared = listSaved()
      .filter(i => i.type === 'observation' && i.shared
        && (i.watershed || 'other') === ws && i.latitude != null && i.longitude != null)
      .map(i => ({
        lng: i.longitude!, lat: i.latitude!,
        name: i.label, sci: i.sublabel || '', date: '',
        photo: i.thumbnail || null, notes: null, shared: true,
      }))
    return [...api, ...shared]
  }, [obsRaw, listSaved, ws])
  const loading = isLoggedIn ? isLoading : false

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)

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

    if (points.length === 0) return

    const bounds = new maplibregl.LngLatBounds()
    points.forEach(p => bounds.extend([p.lng, p.lat]))
    map.fitBounds(bounds, { padding: 50, maxZoom: 13 })

    points.forEach(p => {
      const el = document.createElement('div')
      el.className = `myobs-map-pin${p.shared ? ' myobs-map-pin-shared' : ''}`

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat([p.lng, p.lat])
        .addTo(map)

      el.addEventListener('click', (e) => {
        e.stopPropagation()
        popupRef.current?.remove()

        const photoHtml = p.photo
          ? `<img src="${p.photo}" class="myobs-popup-img" />`
          : '<div class="myobs-popup-no-img">No photo</div>'

        const popup = new maplibregl.Popup({ offset: 12, maxWidth: '240px' })
          .setLngLat([p.lng, p.lat])
          .setHTML(`
            <div class="myobs-popup">
              ${photoHtml}
              <div class="myobs-popup-name">${p.name}</div>
              ${p.sci ? `<div class="myobs-popup-sci">${p.sci}</div>` : ''}
              ${p.date ? `<div class="myobs-popup-date">${p.date}</div>` : ''}
              ${p.notes ? `<div class="myobs-popup-notes">${p.notes}</div>` : ''}
              ${p.shared ? '<div class="myobs-popup-date">📬 shared with you</div>' : ''}
            </div>
          `)
          .addTo(map)
        popupRef.current = popup
      })

      markersRef.current.push(marker)
    })
  }, [points])

  return (
    <div className="myobs-map-page">
      <WatershedHeader watershed={ws} basePath="/path/saved/map" />

      <div className="myobs-map-top">
        <button className="myobs-map-back" onClick={() => navigate('/path/saved')}>← Saved</button>
      </div>

      <div className="myobs-map-meta">
        <span className="myobs-map-count">
          {loading
            ? 'Loading...'
            : (!isLoggedIn && points.length === 0)
            ? 'Sign in to see your observations'
            : `${points.length} observation${points.length === 1 ? '' : 's'}`}
        </span>
      </div>

      <div ref={mapContainer} className="myobs-map-container" />
    </div>
  )
}
