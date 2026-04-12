import { useEffect, useRef, useCallback } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Site } from '../pages/MapPage'

interface MapViewProps {
  sites: Site[]
  selectedSite: string | null
  onSelectSite: (watershed: string | null) => void
  observationOverlay?: any | null
}

const COLORS: Record<string, string> = {
  klamath: '#c4432b',
  mckenzie: '#1a6b4a',
  deschutes: '#2563eb',
  metolius: '#7c3aed',
  johnday: '#d97706',
}

const OBS_LAYER_ID = 'observation-points'
const OBS_SOURCE_ID = 'observation-source'

export default function MapView({ sites, selectedSite, onSelectSite, observationOverlay }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])
  const popupRef = useRef<maplibregl.Popup | null>(null)
  const mapLoadedRef = useRef(false)

  // Stable callback to push overlay data into the map source
  const pushOverlay = useCallback((data: any) => {
    const map = mapRef.current
    if (!map || !mapLoadedRef.current) return
    const src = map.getSource(OBS_SOURCE_ID) as maplibregl.GeoJSONSource | undefined
    if (src) {
      src.setData(data || { type: 'FeatureCollection', features: [] })
    }
  }, [])

  // Initialise map once
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [-121.5, 43.8],
      zoom: 6.5,
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

      // Click popup for observation points
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
        popupRef.current = new maplibregl.Popup({ maxWidth: '240px' })
          .setLngLat(coords)
          .setHTML(html)
          .addTo(map)
      })

      map.on('mouseenter', OBS_LAYER_ID, () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', OBS_LAYER_ID, () => { map.getCanvas().style.cursor = '' })
    })

    mapRef.current = map
    return () => { map.remove(); mapRef.current = null; mapLoadedRef.current = false }
  }, [])

  // Push overlay data whenever it changes
  useEffect(() => {
    pushOverlay(observationOverlay)
  }, [observationOverlay, pushOverlay])

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
      map.flyTo({
        center: [(site.bbox.east + site.bbox.west) / 2, (site.bbox.north + site.bbox.south) / 2],
        zoom: 9,
        duration: 800,
      })
    }
  }, [selectedSite, sites])

  const totalObs = sites.reduce((a, s) => a + s.observations, 0)

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
      </div>

      <div className="watershed-tabs">
        {sites.map(s => (
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
    </div>
  )
}
