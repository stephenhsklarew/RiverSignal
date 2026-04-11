import { useEffect, useRef } from 'react'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import type { Site } from '../App'

interface MapViewProps {
  sites: Site[]
  selectedSite: string | null
  onSelectSite: (watershed: string | null) => void
}

const COLORS: Record<string, string> = {
  klamath: '#c4432b',
  mckenzie: '#1a6b4a',
  deschutes: '#2563eb',
  metolius: '#7c3aed',
}

export default function MapView({ sites, selectedSite, onSelectSite }: MapViewProps) {
  const mapContainer = useRef<HTMLDivElement>(null)
  const mapRef = useRef<maplibregl.Map | null>(null)
  const markersRef = useRef<maplibregl.Marker[]>([])

  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: 'https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',
      center: [-121.5, 43.8],
      zoom: 6.5,
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

      // Bbox rectangle
      map.on('load', () => {
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
      })

      markersRef.current.push(marker)
    })
  }, [sites, selectedSite, onSelectSite])

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
      {/* KPI chips */}
      <div className="map-kpis">
        <div className="kpi-chip">
          <span className="kpi-value">{totalObs.toLocaleString()}</span>
          <span className="kpi-label">observations</span>
        </div>
        <div className="kpi-chip">
          <span className="kpi-value">{sites.reduce((a, s) => a + s.interventions, 0).toLocaleString()}</span>
          <span className="kpi-label">interventions</span>
        </div>
      </div>

      {/* Watershed tabs */}
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
