import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import WatershedHeader from '../components/WatershedHeader'
import { getSelectedWatershed } from '../components/WatershedHeader'
import { useSaved } from '../components/SavedContext'
import { API_BASE } from '../config'
import './SpeciesMapPage.css'

const API = API_BASE

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
  green_river: [-110.15, 38.99],
  shenandoah: [-78.20, 38.92],
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
  const [searchParams] = useSearchParams()
  const ws = paramWs || getSelectedWatershed() || 'deschutes'

  // ?filter scopes the map to the species shown in a specific /path/now section:
  //   fish_present → fish species from gold.species_by_reach (via /fishing/species)
  //   eating_now   → insects from /species-spotter
  // When filter is set we force the category and disable the manual toggle.
  const filter = searchParams.get('filter')          // 'fish_present' | 'eating_now' | null
  const filterLocked = filter === 'fish_present' || filter === 'eating_now'

  const forcedCategory = filter === 'eating_now' ? 'Insecta'
                       : filter === 'fish_present' ? 'Actinopterygii'
                       : (searchParams.get('category') === 'Insecta' ? 'Insecta' : 'Actinopterygii')
  const [category, setCategory] = useState(forcedCategory)
  // SavedContext accessor — used by the fly-save button injected into insect popups.
  const { save, unsave, isSaved } = useSaved()
  const [features, setFeatures] = useState<ObsFeature[]>([])
  // Loading reflects either the observation fetch or the curated-list fetch (filter mode).
  const [obsLoading, setObsLoading] = useState(true)
  const [curatedLoading, setCuratedLoading] = useState(filterLocked)
  const loading = obsLoading || curatedLoading
  // Lowercased name set built from the curated list when filter is active.
  // `null` means "no filter, show every observation".
  const [curatedNames, setCuratedNames] = useState<Set<string> | null>(null)
  const [flyRecs, setFlyRecs] = useState<any[]>([])

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)

  // Fetch curated species list (only when ?filter is set).
  useEffect(() => {
    if (!filterLocked) { setCuratedNames(null); setCuratedLoading(false); return }
    setCuratedLoading(true)
    const url = filter === 'fish_present'
      ? `${API}/sites/${ws}/fishing/species`
      : `${API}/sites/${ws}/species-spotter`
    fetch(url)
      .then(r => r.json())
      .then(data => {
        // /fishing/species returns an array of rows.
        // /species-spotter returns { species: [...] }.
        const rows: any[] = filter === 'eating_now' ? (data.species || []) : (Array.isArray(data) ? data : [])
        const names = new Set<string>()
        for (const r of rows) {
          for (const key of ['common_name', 'scientific_name', 'taxon_name', 'species']) {
            const v = r[key]
            if (typeof v === 'string' && v.trim()) names.add(v.trim().toLowerCase())
          }
        }
        setCuratedNames(names)
        setCuratedLoading(false)
      })
      .catch(() => { setCuratedNames(new Set()); setCuratedLoading(false) })
  }, [ws, filter, filterLocked])

  // Fetch observations + fly recs.
  useEffect(() => {
    setObsLoading(true)
    // Higher limit when filter is on so post-filter we still have plenty of pins.
    const limit = filterLocked ? 2000 : 500
    fetch(`${API}/sites/${ws}/observations/search?q=${category}&limit=${limit}`)
      .then(r => r.json())
      .then(data => {
        setFeatures(data.features || [])
        setObsLoading(false)
      })
      .catch(() => { setFeatures([]); setObsLoading(false) })

    // Fly recommendations for insect popups.
    fetch(`${API}/sites/${ws}/fishing/fly-recommendations`)
      .then(r => r.json())
      .then(setFlyRecs)
      .catch(() => setFlyRecs([]))
  }, [ws, category, filterLocked])

  // Apply curated-name filter to the observation features when filter is on.
  const visibleFeatures = !filterLocked || !curatedNames
    ? features
    : features.filter(f => {
        const t = (f.properties.taxon_name || '').toLowerCase()
        const c = (f.properties.common_name || '').toLowerCase()
        if (curatedNames.has(t) || curatedNames.has(c)) return true
        // Loose substring match — handles "Oncorhynchus mykiss (Walbaum, 1792)" vs "Oncorhynchus mykiss"
        for (const name of curatedNames) {
          if (name.length < 4) continue
          if (t.includes(name) || (c && c.includes(name))) return true
        }
        return false
      })

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

    if (visibleFeatures.length === 0) return

    // Fit bounds to features
    const bounds = new maplibregl.LngLatBounds()
    visibleFeatures.forEach(f => bounds.extend(f.geometry.coordinates as [number, number]))
    map.fitBounds(bounds, { padding: 50, maxZoom: 13 })

    // Add markers
    visibleFeatures.forEach(f => {
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
        let matchedFly: any = null
        let flySavedId = ''
        if (category === 'Insecta' && flyRecs.length > 0) {
          matchedFly = matchFly(p.taxon_name, p.common_name, flyRecs)
          if (matchedFly) {
            // Same id shape used by HatchPage so saves are consistent across surfaces.
            flySavedId = `${ws}-${matchedFly.fly_pattern}-${matchedFly.fly_size || ''}`
            const flyImg = matchedFly.fly_image_url
              ? `<img src="${matchedFly.fly_image_url}" class="species-popup-fly-img" />`
              : ''
            const initiallySaved = isSaved('fly', flySavedId)
            const heart = initiallySaved ? '♥' : '♡'
            const heartColor = initiallySaved
              ? 'var(--alert, #c4432b)'
              : 'var(--text-muted, #9e9b96)'
            flyHtml = `
              <div class="species-popup-fly">
                ${flyImg}
                <div class="species-popup-fly-info">
                  <div class="species-popup-fly-label">Match the hatch</div>
                  <div class="species-popup-fly-name">${matchedFly.fly_pattern}</div>
                  ${matchedFly.fly_size ? `<div class="species-popup-fly-size">#${matchedFly.fly_size} ${matchedFly.fly_type || ''}</div>` : ''}
                </div>
                <button class="species-popup-fly-save"
                        type="button"
                        aria-label="${initiallySaved ? 'Remove fly from saved' : 'Save fly'}"
                        data-saved="${initiallySaved ? 'true' : 'false'}"
                        style="color: ${heartColor};">${heart}</button>
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

        // Wire up the save-fly heart inside the popup, if present.
        if (matchedFly && flySavedId) {
          const popupEl = popup.getElement()
          const btn = popupEl?.querySelector<HTMLButtonElement>('.species-popup-fly-save')
          if (btn) {
            btn.addEventListener('click', (ev) => {
              ev.stopPropagation()
              const currentlySaved = btn.dataset.saved === 'true'
              if (currentlySaved) {
                unsave('fly', flySavedId)
                btn.dataset.saved = 'false'
                btn.textContent = '♡'
                btn.style.color = 'var(--text-muted, #9e9b96)'
                btn.setAttribute('aria-label', 'Save fly')
              } else {
                save({
                  type: 'fly',
                  id: flySavedId,
                  watershed: ws,
                  label: matchedFly.fly_pattern,
                  sublabel: `${matchedFly.fly_size ? '#' + matchedFly.fly_size : ''} ${matchedFly.fly_type || ''}`.trim(),
                  thumbnail: matchedFly.fly_image_url,
                })
                btn.dataset.saved = 'true'
                btn.textContent = '♥'
                btn.style.color = 'var(--alert, #c4432b)'
                btn.setAttribute('aria-label', 'Remove fly from saved')
              }
            })
          }
        }

        popupRef.current = popup
      })

      markersRef.current.push(marker)
    })
  }, [visibleFeatures, category, flyRecs])

  return (
    <div className="species-map-page">
      <WatershedHeader watershed={ws} basePath="/path/map" />
      <div className="species-map-top">
        <button className="species-map-back" onClick={() => navigate(`/path/now/${ws}`)}>← River Now</button>
      </div>

      {/* Category toggle (disabled in filter mode — the filter pins the category) */}
      <div className="species-map-toggle">
        {CATEGORIES.map(c => (
          <button
            key={c.key}
            className={`species-map-cat${category === c.key ? ' active' : ''}${filterLocked ? ' locked' : ''}`}
            onClick={() => { if (!filterLocked) setCategory(c.key) }}
            disabled={filterLocked && category !== c.key}
            title={filterLocked && category !== c.key ? 'Disabled while filtered to a section from River Now' : undefined}
          >
            {c.label}
          </button>
        ))}
        <span className="species-map-count">
          {loading
            ? 'Loading…'
            : filterLocked
              ? `${visibleFeatures.length} pins · ${filter === 'fish_present' ? 'Fish Present' : "What Fish Are Eating Now"}`
              : `${visibleFeatures.length} observations`}
        </span>
      </div>

      {/* Map */}
      <div className="species-map-stage">
        <div ref={mapContainer} className="species-map-container" />
        {loading && (
          <div className="species-map-loading-overlay" role="status" aria-live="polite">
            <div className="species-map-spinner" aria-hidden="true" />
            <div className="species-map-loading-text">Loading pins…</div>
          </div>
        )}
      </div>
    </div>
  )
}
