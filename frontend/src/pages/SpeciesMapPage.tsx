import { useEffect, useRef, useState } from 'react'
import useSWR from 'swr'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import WatershedHeader from '../components/WatershedHeader'
import { getSelectedWatershed } from '../components/WatershedHeader'
import { useSaved } from '../components/SavedContext'
import './SpeciesMapPage.css'


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
  mad_river_oh: [-83.85, 40.05],
  ipswich_river_ma: [-70.95, 42.65],
  clinch_river_va: [-82.30, 36.88],
  new_river_va: [-80.72, 37.05],
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
  // Per-species filter chips shown above the map in fish_present mode. Each
  // chip toggles one species in the Fish Present list on/off. activeChips
  // holds the keys (lowercased common_name) currently enabled.
  const [activeChips, setActiveChips] = useState<Set<string>>(new Set())

  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)

  // SWR-backed reads. Curated species list keys conditional on filterLocked
  // (null key → SWR skips the fetch). Observations + fly recs share cache
  // with HatchPage / RiverNowPage.
  const curatedKey = filterLocked
    ? (filter === 'fish_present' ? `/sites/${ws}/fishing/species` : `/sites/${ws}/species-spotter`)
    : null
  const { data: curatedData, isLoading: curatedSwrLoading } = useSWR<any>(curatedKey, { dedupingInterval: 60 * 60 * 1000 })
  useEffect(() => {
    if (!filterLocked) { setCuratedNames(null); setCuratedLoading(false); return }
    setCuratedLoading(curatedSwrLoading)
    if (curatedData == null) return
    const rows: any[] = filter === 'eating_now' ? (curatedData.species || []) : (Array.isArray(curatedData) ? curatedData : [])
    const names = new Set<string>()
    for (const r of rows) {
      for (const key of ['common_name', 'scientific_name', 'taxon_name', 'species']) {
        const v = r[key]
        if (typeof v === 'string' && v.trim()) names.add(v.trim().toLowerCase())
      }
    }
    setCuratedNames(names)
    setCuratedLoading(false)
  }, [filterLocked, filter, curatedData, curatedSwrLoading])

  const obsLimit = filterLocked ? 2000 : 500
  const { data: obsData, isLoading: obsSwrLoading } = useSWR<any>(
    `/sites/${ws}/observations/search?q=${category}&limit=${obsLimit}`,
    { dedupingInterval: 30 * 60 * 1000 },
  )
  const { data: flyRecsData } = useSWR<any>(
    `/sites/${ws}/fishing/fly-recommendations`,
    { dedupingInterval: 60 * 60 * 1000 },
  )
  useEffect(() => {
    setObsLoading(obsSwrLoading)
    setFeatures(obsData?.features || [])
  }, [obsData, obsSwrLoading])
  useEffect(() => {
    setFlyRecs(Array.isArray(flyRecsData) ? flyRecsData : [])
  }, [flyRecsData])

  // Build the per-species chip list from the curated Fish Present rows.
  // One chip per unique common_name (dedupe matches RiverNowPage.uniqueFishByReach).
  // Capped to the same FISH_PRESENT_LIMIT the carousel uses so the map filter
  // exactly matches the cards the user sees on /path/now — without the cap,
  // /fishing/species returns ~48 species for a typical PNW watershed and the
  // map shows pins for 38 fish that don't appear in the section above.
  // Only rendered for fish_present; eating_now has a different shape.
  const FISH_PRESENT_LIMIT = 10
  type FishChip = { key: string; label: string; photo: string | null; names: Set<string> }
  const fishChips: FishChip[] = []
  if (filter === 'fish_present' && Array.isArray(curatedData)) {
    const seen = new Set<string>()
    for (const r of curatedData) {
      if (fishChips.length >= FISH_PRESENT_LIMIT) break
      const label = (r.common_name || r.scientific_name || r.species || '').trim()
      if (!label) continue
      const key = label.toLowerCase()
      if (seen.has(key)) continue
      seen.add(key)
      const names = new Set<string>()
      for (const k of ['common_name', 'scientific_name', 'species', 'taxon_name']) {
        const v = r[k]
        if (typeof v === 'string' && v.trim()) names.add(v.trim().toLowerCase())
      }
      fishChips.push({ key, label, photo: r.photo_url || null, names })
    }
  }

  // When the chip list changes (curated data finished loading, or watershed
  // switched), enable every chip by default — matches the prior "show all
  // Fish Present" behavior.
  const chipsSig = fishChips.map(c => c.key).join('|')
  useEffect(() => {
    setActiveChips(new Set(fishChips.map(c => c.key)))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [chipsSig])

  // When chips are present, the effective filter narrows to the union of
  // names from the currently-active chips. Falls back to the full curated
  // set when there are no chips (e.g. eating_now mode).
  const effectiveCuratedNames = fishChips.length > 0
    ? (() => {
        const out = new Set<string>()
        for (const c of fishChips) {
          if (!activeChips.has(c.key)) continue
          for (const n of c.names) out.add(n)
        }
        return out
      })()
    : curatedNames

  // Apply curated-name filter to the observation features when filter is on.
  const visibleFeatures = !filterLocked || !effectiveCuratedNames
    ? features
    : features.filter(f => {
        const t = (f.properties.taxon_name || '').toLowerCase()
        const c = (f.properties.common_name || '').toLowerCase()
        if (effectiveCuratedNames.has(t) || effectiveCuratedNames.has(c)) return true
        // Loose substring match — handles "Oncorhynchus mykiss (Walbaum, 1792)" vs "Oncorhynchus mykiss"
        for (const name of effectiveCuratedNames) {
          if (name.length < 4) continue
          if (t.includes(name) || (c && c.includes(name))) return true
        }
        return false
      })

  const toggleChip = (key: string) => {
    setActiveChips(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }

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

      {/* Fish Present species chips — one per species, tap to toggle */}
      {fishChips.length > 1 && (
        <div className="species-map-chip-row" role="group" aria-label="Filter by fish species">
          {fishChips.map(chip => {
            const on = activeChips.has(chip.key)
            return (
              <button
                key={chip.key}
                type="button"
                className={`species-map-chip${on ? ' active' : ''}`}
                aria-pressed={on}
                onClick={() => toggleChip(chip.key)}
              >
                {chip.photo && <img src={chip.photo} alt="" className="species-map-chip-img" />}
                <span className="species-map-chip-label">{chip.label}</span>
              </button>
            )
          })}
        </div>
      )}

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
