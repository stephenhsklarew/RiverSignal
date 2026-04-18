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
  skagit: [-121.50, 48.45],
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

/** Match an insect observation to a fly recommendation by taxon or common name. */
function matchFly(taxonName: string, commonName: string | null, recs: any[]): any | null {
  const taxon = taxonName.toLowerCase()
  const common = (commonName || '').toLowerCase()

  // Keywords from common insect group names to fly rec insect names
  const KEYWORD_MAP: Record<string, string[]> = {
    'midge': ['midge', 'cecidom', 'chironom'],
    'caddis': ['caddis', 'trichoptera'],
    'mayfly': ['mayfly', 'ephemeroptera', 'baetis', 'ephemerella'],
    'stonefly': ['stonefly', 'plecoptera', 'pteronarcys', 'salmonfly'],
    'moth': ['moth', 'lepidoptera'],
    'dragonfly': ['dragonfly', 'odonata', 'libellul'],
    'damselfly': ['damselfly', 'zygoptera'],
    'crane fly': ['crane', 'tipul'],
  }

  for (const rec of recs) {
    const recTaxon = (rec.insect_taxon || '').toLowerCase()
    const recInsect = (rec.insect || '').toLowerCase()

    // Direct taxon substring match (e.g., observation "Cecidomyiinae sp." contains fly's "Cecidomyiinae")
    if (recTaxon && (taxon.includes(recTaxon) || recTaxon.includes(taxon))) return rec

    // Common name keyword match
    for (const [keyword, variants] of Object.entries(KEYWORD_MAP)) {
      const obsMatches = common.includes(keyword) || variants.some(v => taxon.includes(v) || common.includes(v))
      const recMatches = recInsect.includes(keyword) || variants.some(v => recTaxon.includes(v) || recInsect.includes(v))
      if (obsMatches && recMatches) return rec
    }
  }
  return null
}

export default function SpeciesMapPage() {
  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])
  const navigate = useNavigate()
  const { watershed: paramWs } = useParams<{ watershed?: string }>()
  const ws = paramWs || getSelectedWatershed() || 'deschutes'

  const [category, setCategory] = useState('Actinopterygii')
  const [features, setFeatures] = useState<ObsFeature[]>([])
  const [loading, setLoading] = useState(true)
  const [flyRecs, setFlyRecs] = useState<any[]>([])

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)

  // Fetch observations + fly recs (for insects)
  useEffect(() => {
    setLoading(true)
    fetch(`${API}/sites/${ws}/observations/search?q=${category}&limit=500`)
      .then(r => r.json())
      .then(data => {
        setFeatures(data.features || [])
        setLoading(false)
      })
      .catch(() => { setFeatures([]); setLoading(false) })

    // Load fly recommendations for insect matching
    fetch(`${API}/sites/${ws}/fishing/fly-recommendations`)
      .then(r => r.json())
      .then(setFlyRecs)
      .catch(() => setFlyRecs([]))
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

        // Match a fly recommendation for insect observations
        let flyHtml = ''
        if (category === 'Insecta' && flyRecs.length > 0) {
          const match = matchFly(p.taxon_name, p.common_name, flyRecs)
          if (match) {
            const flyImg = match.fly_image_url
              ? `<img src="${match.fly_image_url}" class="species-popup-fly-img" />`
              : ''
            flyHtml = `
              <div class="species-popup-fly">
                ${flyImg}
                <div class="species-popup-fly-info">
                  <div class="species-popup-fly-label">Match the hatch</div>
                  <div class="species-popup-fly-name">${match.fly_pattern}</div>
                  ${match.fly_size ? `<div class="species-popup-fly-size">#${match.fly_size} ${match.fly_type || ''}</div>` : ''}
                </div>
              </div>
            `
          }
        }

        const popup = new maplibregl.Popup({ offset: 12, maxWidth: '240px' })
          .setLngLat(f.geometry.coordinates as [number, number])
          .setHTML(`
            <div class="species-popup">
              ${photoHtml}
              <div class="species-popup-name">${name}</div>
              <div class="species-popup-sci">${p.taxon_name}</div>
              <div class="species-popup-date">${date}</div>
              ${p.photo_url ? '<div class="species-popup-credit">📷 via iNaturalist</div>' : ''}
              ${flyHtml}
            </div>
          `)
          .addTo(map)

        popupRef.current = popup
      })

      markersRef.current.push(marker)
    })
  }, [features, category, flyRecs])

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
