import { useEffect, useRef, useCallback } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Site } from '../pages/MapPage'
import TimelineSlider from './TimelineSlider'

interface MapViewProps {
  sites: Site[]
  selectedSite: string | null
  onSelectSite: (watershed: string | null) => void
  observationOverlay?: any | null
  fossilOverlay?: any | null
  barrierOverlay?: any | null
}

const COLORS: Record<string, string> = {
  klamath: '#c4432b',
  mckenzie: '#1a6b4a',
  deschutes: '#2563eb',
  metolius: '#7c3aed',
  johnday: '#d97706',
  skagit: '#0891b2',
  green_river: '#059669',
}

const OBS_LAYER_ID = 'observation-points'
const OBS_SOURCE_ID = 'observation-source'
const FOS_LAYER_ID = 'fossil-points'
const FOS_SOURCE_ID = 'fossil-source'
const BAR_LAYER_ID = 'barrier-points'
const BAR_SOURCE_ID = 'barrier-source'

export default function MapView({ sites, selectedSite, onSelectSite, observationOverlay, fossilOverlay, barrierOverlay }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)
  const mapLoadedRef = useRef(false)

  // Stable callback to push observation overlay data into the map source
  const pushOverlay = useCallback((data: any) => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current) return
    const src = map.getSource(OBS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined
    if (src) {
      src.setData(data || { type: 'FeatureCollection', features: [] })
    }
    // When showing new observations, clear fossil overlay
    if (data?.features?.length > 0) {
      const fosSrc = map.getSource(FOS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined
      if (fosSrc) fosSrc.setData({ type: 'FeatureCollection', features: [] })
    }
  }, [])

  // Initialise map once
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return

    // Initial view fits the continental United States so every onboarded
    // watershed bbox is visible at first paint — including East Coast
    // ones like shenandoah. Previously centered on the Pacific Northwest
    // ([-116, 43] zoom 4.5), which left anything east of the Rockies
    // off-screen.
    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      bounds: [
        [-125.0, 24.5],  // SW: California / Florida latitude
        [-66.5, 49.5],   // NE: Maine / Canadian border
      ],
      fitBoundsOptions: { padding: 40 },
    })

    map.addControl(new maplibregl.NavigationControl(), 'top-right')

    map.on('load', () => {
      mapLoadedRef.current = true

      // Observation overlay source + layer
      map.addSource(OBS_SOURCE_ID, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: OBS_LAYER_ID,
        type: 'circle',
        source: OBS_SOURCE_ID,
        paint: {
          'circle-radius': 7,
          'circle-color': '#e65100',
          'circle-stroke-color': '#fff',
          'circle-stroke-width': 2,
          'circle-opacity': 0.9,
        },
      })

      // Click popup for observation points (living species only)
      map.on('click', OBS_LAYER_ID, (e) => {
        if (!e.features?.length) return
        const props = e.features[0].properties as any
        const coords = (e.features[0].geometry as any).coordinates.slice() as [number, number]
        const photoHtml = props.photo_url
          ? `<img src="${props.photo_url}" style="width:200px;border-radius:6px;margin-bottom:8px;display:block;" />`
          : ''
        const html = `
          <div style="font-family:Outfit,sans-serif;font-size:13px;max-width:220px;line-height:1.4;">
            ${photoHtml}
            <strong style="font-style:italic;">${props.taxon_name || 'Unknown'}</strong><br/>
            ${props.common_name ? `<span style="color:#666;">${props.common_name}</span><br/>` : ''}
            ${props.observed_at ? `<span style="color:#999;font-size:11px;">Observed: ${props.observed_at}</span>` : ''}
          </div>
        `
        if (popupRef.current) popupRef.current.remove()
        popupRef.current = new maplibregl.Popup({ maxWidth: '240px' }).setLngLat(coords).setHTML(html).addTo(map)
      })
      map.on('mouseenter', OBS_LAYER_ID, () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', OBS_LAYER_ID, () => { map.getCanvas().style.cursor = '' })

      // ── Fossil overlay: separate source, layer, popup (no timeline filter) ──
      map.addSource(FOS_SOURCE_ID, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: FOS_LAYER_ID,
        type: 'circle',
        source: FOS_SOURCE_ID,
        paint: {
          'circle-radius': 7,
          'circle-color': '#d4a96a',
          'circle-stroke-color': '#fff',
          'circle-stroke-width': 2,
          'circle-opacity': 0.9,
        },
      })
      map.on('click', FOS_LAYER_ID, (e) => {
        if (!e.features?.length) return
        const props = e.features[0].properties as any
        const coords = (e.features[0].geometry as any).coordinates.slice() as [number, number]
        const photoHtml = props.photo_url
          ? `<img src="${props.photo_url}" style="width:200px;border-radius:6px;margin-bottom:8px;display:block;" />`
          : ''
        const html = `
          <div style="font-family:Outfit,sans-serif;font-size:13px;max-width:220px;line-height:1.4;">
            ${photoHtml}
            <span style="font-size:10px;color:#d4a96a;text-transform:uppercase;letter-spacing:0.05em;">Fossil</span><br/>
            <strong style="font-style:italic;">${props.taxon_name || 'Unknown'}</strong><br/>
            ${props.common_name ? `<span style="color:#666;">${props.common_name}</span><br/>` : ''}
            ${props.period ? `<span style="color:#999;font-size:11px;">Period: ${props.period}</span><br/>` : ''}
            ${props.museum ? `<span style="color:#aaa;font-size:10px;">${props.museum}</span>` : ''}
          </div>
        `
        if (popupRef.current) popupRef.current.remove()
        popupRef.current = new maplibregl.Popup({ maxWidth: '240px' }).setLngLat(coords).setHTML(html).addTo(map)
      })
      map.on('mouseenter', FOS_LAYER_ID, () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', FOS_LAYER_ID, () => { map.getCanvas().style.cursor = '' })

      // Barrier overlay source + layer
      map.addSource(BAR_SOURCE_ID, {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
      })
      map.addLayer({
        id: BAR_LAYER_ID,
        type: 'circle',
        source: BAR_SOURCE_ID,
        paint: {
          'circle-radius': 6,
          'circle-color': '#d32f2f',
          'circle-stroke-color': '#fff',
          'circle-stroke-width': 1.5,
          'circle-opacity': 0.85,
        },
      })

      map.on('click', BAR_LAYER_ID, (e) => {
        if (!e.features?.length) return
        const props = e.features[0].properties as any
        const coords = (e.features[0].geometry as any).coordinates.slice() as [number, number]
        const html = `<div style="font-family:Outfit,sans-serif;font-size:12px;">
          <strong>${props.name || 'Barrier'}</strong><br/>
          Type: ${props.type || '—'}<br/>
          Status: ${props.status || '—'}
        </div>`
        if (popupRef.current) popupRef.current.remove()
        popupRef.current = new maplibregl.Popup({ maxWidth: '200px' }).setLngLat(coords).setHTML(html).addTo(map)
      })
      map.on('mouseenter', BAR_LAYER_ID, () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', BAR_LAYER_ID, () => { map.getCanvas().style.cursor = '' })
    })

    mapRef.current = map
    return () => { map.remove(); mapRef.current = null; mapLoadedRef.current = false }
  }, [])

  // Push observation overlay data and zoom to fit results
  useEffect(() => {
    pushOverlay(observationOverlay)
    const map = mapRef.current
    if (!map || !observationOverlay?.features?.length) return
    const bounds = new maplibregl.LngLatBounds()
    for (const f of observationOverlay.features) {
      const [lon, lat] = f.geometry.coordinates
      if (lon && lat) bounds.extend([lon, lat])
    }
    if (!bounds.isEmpty()) {
      map.fitBounds(bounds, { padding: 60, maxZoom: 13, duration: 600 })
    }
  }, [observationOverlay, pushOverlay])

  // Push fossil overlay data (separate source, no timeline filter)
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current) return
    const src = map.getSource(FOS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined
    if (src) {
      src.setData(fossilOverlay || { type: 'FeatureCollection', features: [] })
    }
    // When showing fossils, clear the observation overlay to avoid confusion
    if (fossilOverlay?.features?.length > 0) {
      const obsSrc = map.getSource(OBS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined
      if (obsSrc) obsSrc.setData({ type: 'FeatureCollection', features: [] })
    }
  }, [fossilOverlay])

  // Push barrier overlay
  useEffect(() => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current) return
    const src = map.getSource(BAR_SOURCE_ID) as maplibregl.GeoJSONSource | undefined
    if (src) src.setData(barrierOverlay || { type: 'FeatureCollection', features: [] })
  }, [barrierOverlay])

  // Watershed markers + bbox rectangles
  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    markersRef.current.forEach(m => m.remove())
    markersRef.current = []

    sites.forEach(site => {
      const { bbox } = site
      const center: [number, number] = [(bbox.east + bbox.west) / 2, (bbox.north + bbox.south) / 2]
      const color = COLORS[site.watershed] || '#666'
      const isSelected = site.watershed === selectedSite

      const el = document.createElement('div')
      el.style.width = isSelected ? '14px' : '10px'
      el.style.height = isSelected ? '14px' : '10px'
      el.style.borderRadius = '50%'
      el.style.background = color
      el.style.border = `2px solid ${isSelected ? color : 'white'}`
      el.style.cursor = 'pointer'
      el.style.boxShadow = '0 1px 4px rgba(0,0,0,0.25)'
      el.style.transition = 'all 0.15s'
      el.title = site.name

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(center)
        .addTo(map)

      el.addEventListener('click', () => {
        onSelectSite(site.watershed === selectedSite ? null : site.watershed)
      })

      // Bbox rectangle (only add once per load)
      const addBbox = () => {
        const sourceId = `bbox-${site.watershed}`
        if (map.getSource(sourceId)) return
        map.addSource(sourceId, {
          type: 'geojson',
          data: {
            type: 'Feature',
            properties: {},
            geometry: {
              type: 'Polygon',
              coordinates: [[
                [bbox.west, bbox.south], [bbox.east, bbox.south],
                [bbox.east, bbox.north], [bbox.west, bbox.north],
                [bbox.west, bbox.south],
              ]],
            },
          },
        })
        map.addLayer({
          id: `bbox-fill-${site.watershed}`, type: 'fill', source: sourceId,
          paint: { 'fill-color': color, 'fill-opacity': isSelected ? 0.1 : 0.03 },
        })
        map.addLayer({
          id: `bbox-line-${site.watershed}`, type: 'line', source: sourceId,
          paint: { 'line-color': color, 'line-width': isSelected ? 2 : 1, 'line-opacity': isSelected ? 0.6 : 0.2 },
        })
      }

      if (mapLoadedRef.current) {
        addBbox()
      } else {
        map.on('load', addBbox)
      }

      markersRef.current.push(marker)
    })
  }, [sites, selectedSite, onSelectSite])

  // Fly to selected watershed
  useEffect(() => {
    const map = mapRef.current
    if (!map || !selectedSite) return
    const site = sites.find(s => s.watershed === selectedSite)
    if (site) {
      map.fitBounds(
        [[site.bbox.west, site.bbox.south], [site.bbox.east, site.bbox.north]],
        { padding: 40, duration: 800 }
      )
    }
  }, [selectedSite, sites])

  const handleTimelineFilter = useCallback((startDate: string | null, endDate: string | null) => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current) return
    if (!startDate || !endDate) {
      // Remove filter — show all
      map.setFilter(OBS_LAYER_ID, null)
    } else {
      map.setFilter(OBS_LAYER_ID, [
        'all',
        ['>=', ['get', 'observed_at'], startDate],
        ['<=', ['get', 'observed_at'], endDate],
      ])
    }
  }, [])

  const totalObs = sites.reduce((a, s) => a + s.observations, 0)
  const obsFeatures = observationOverlay?.features || []

  return (
    <div className="map-container">
      <div className="map-kpis">
        <div className="kpi-chip">
          <span className="kpi-value">{totalObs.toLocaleString()}</span>
          <span className="kpi-label">observations</span>
        </div>
        <div className="kpi-chip">
          <span className="kpi-value">{sites.reduce((a, s) => a + s.interventions, 0).toLocaleString()}</span>
          <span className="kpi-label">interventions</span>
        </div>
        {observationOverlay && observationOverlay.features?.length > 0 && (
          <div className="kpi-chip" style={{ background: 'rgba(230,81,0,0.12)', borderColor: '#e65100' }}>
            <span className="kpi-value" style={{ color: '#e65100' }}>{observationOverlay.features.length}</span>
            <span className="kpi-label">found on map</span>
          </div>
        )}
        {fossilOverlay && fossilOverlay.features?.length > 0 && (
          <div className="kpi-chip" style={{ background: 'rgba(212,169,106,0.15)', borderColor: '#d4a96a' }}>
            <span className="kpi-value" style={{ color: '#d4a96a' }}>🦴 {fossilOverlay.features.length}</span>
            <span className="kpi-label">fossils on map</span>
          </div>
        )}
      </div>

      <div className="watershed-tabs">
        {[...sites].sort((a, b) => a.watershed.localeCompare(b.watershed)).map(s => (
          <button
            key={s.watershed}
            className={`ws-tab${selectedSite === s.watershed ? ' active' : ''}`}
            onClick={() => onSelectSite(selectedSite === s.watershed ? null : s.watershed)}
          >
            {s.name.replace(' River', '').replace('Upper ', '')}
          </button>
        ))}
      </div>

      <div ref={mapContainer} style={{ width: '100%', height: '100%' }} />

      {obsFeatures.length > 0 && (
        <TimelineSlider
          features={obsFeatures}
          onFilterChange={handleTimelineFilter}
        />
      )}
    </div>
  )
}
