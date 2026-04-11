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
  klamath: '#e74c3c',
  mckenzie: '#2ecc71',
  deschutes: '#3498db',
  metolius: '#9b59b6',
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

    // Clear existing markers
    markersRef.current.forEach(m => m.remove())
    markersRef.current = []

    sites.forEach(site => {
      const { bbox } = site
      const center: [number, number] = [(bbox.east + bbox.west) / 2, (bbox.north + bbox.south) / 2]
      const color = COLORS[site.watershed] || '#666'
      const isSelected = site.watershed === selectedSite

      // Create marker element
      const el = document.createElement('div')
      el.style.width = isSelected ? '40px' : '32px'
      el.style.height = isSelected ? '40px' : '32px'
      el.style.borderRadius = '50%'
      el.style.background = color
      el.style.border = `3px solid ${isSelected ? '#f39c12' : 'white'}`
      el.style.cursor = 'pointer'
      el.style.boxShadow = '0 2px 6px rgba(0,0,0,0.3)'
      el.style.transition = 'all 0.15s'
      el.title = `${site.name} (${site.observations.toLocaleString()} observations)`

      const marker = new maplibregl.Marker({ element: el })
        .setLngLat(center)
        .addTo(map)

      el.addEventListener('click', () => {
        onSelectSite(site.watershed === selectedSite ? null : site.watershed)
      })

      // Add bbox rectangle
      const sourceId = `bbox-${site.watershed}`
      if (!map.getSource(sourceId)) {
        map.on('load', () => {
          if (map.getSource(sourceId)) return
          map.addSource(sourceId, {
            type: 'geojson',
            data: {
              type: 'Feature',
              properties: {},
              geometry: {
                type: 'Polygon',
                coordinates: [[
                  [bbox.west, bbox.south],
                  [bbox.east, bbox.south],
                  [bbox.east, bbox.north],
                  [bbox.west, bbox.north],
                  [bbox.west, bbox.south],
                ]],
              },
            },
          })
          map.addLayer({
            id: `bbox-fill-${site.watershed}`,
            type: 'fill',
            source: sourceId,
            paint: {
              'fill-color': color,
              'fill-opacity': isSelected ? 0.15 : 0.05,
            },
          })
          map.addLayer({
            id: `bbox-line-${site.watershed}`,
            type: 'line',
            source: sourceId,
            paint: {
              'line-color': color,
              'line-width': isSelected ? 3 : 1,
              'line-opacity': isSelected ? 0.8 : 0.3,
            },
          })
        })
      }

      markersRef.current.push(marker)
    })
  }, [sites, selectedSite, onSelectSite])

  // Fly to selected site
  useEffect(() => {
    const map = mapRef.current
    if (!map || !selectedSite) return
    const site = sites.find(s => s.watershed === selectedSite)
    if (site) {
      map.flyTo({
        center: [(site.bbox.east + site.bbox.west) / 2, (site.bbox.north + site.bbox.south) / 2],
        zoom: 9,
        duration: 1000,
      })
    }
  }, [selectedSite, sites])

  return <div ref={mapContainer} className="map-container" />
}
