import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import maplibregl from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { useDeepTrail, WATERSHEDS } from '../components/DeepTrailContext'
import DeepTrailHeader from '../components/DeepTrailHeader'
import { CardSettingsPanel, loadCardSettingsGeneric, type CardConfig } from '../components/CardSettings'
import { useSaved } from '../components/SavedContext'
import PhotoObservation from '../components/PhotoObservation'
import logo from '../assets/deeptrail-logo.svg'
import './DeepTrailPage.css'

const COLLECT_CARDS: CardConfig[] = [
  { id: 'rockhounding', label: 'Rockhounding Sites', icon: '🪨', visible: true },
  { id: 'legal_collecting', label: 'Legal Collecting Status', icon: '⚖️', visible: true },
  { id: 'mineral_shops', label: 'Mineral Shops Nearby', icon: '🏪', visible: true },
]

export default function TrailCollectPage() {
  useEffect(() => { document.title = 'Deep Trail'; return () => { document.title = 'RiverSignal' } }, [])
  const { locationId } = useParams<{ locationId: string }>()
  const navigate = useNavigate()
  const {
    loc, selectLocation, loading,
    rockhoundingSites, landStatus, mineralShops,
  } = useDeepTrail()
  const { save, unsave, isSaved } = useSaved()

  const [cardConfig, setCardConfig] = useState<CardConfig[]>(() =>
    loadCardSettingsGeneric('deeptrail-collect-cards', COLLECT_CARDS)
  )
  const [showSettings, setShowSettings] = useState(false)
  const [selectedSite, setSelectedSite] = useState<any>(null)

  // Resolve locationId if loc is null
  useEffect(() => {
    if (loc) return
    if (!locationId) { navigate('/trail'); return }

    const ws = WATERSHEDS.find(w => w.id === locationId)
    if (ws) { selectLocation(ws); return }

    const parts = locationId.split(',')
    if (parts.length === 2) {
      const lat = parseFloat(parts[0])
      const lon = parseFloat(parts[1])
      if (!isNaN(lat) && !isNaN(lon)) {
        selectLocation({
          id: locationId,
          name: `${lat.toFixed(4)}°N, ${Math.abs(lon).toFixed(4)}°W`,
          lat,
          lon,
        })
        return
      }
    }

    navigate('/trail')
  }, [loc, locationId, navigate, selectLocation])

  if (!loc) {
    return <div className="dt-app"><div className="dt-loading">Loading...</div></div>
  }

  const statusColor = landStatus?.collecting_status === 'permitted' ? '#4caf50'
    : landStatus?.collecting_status === 'prohibited' ? '#f44336' : '#ff9800'

  // Detail view for a selected rockhounding site
  if (selectedSite) {
    const s = selectedSite
    return (
      <div className="dt-app">
        <header className="dt-detail-header">
          <button className="dt-back" onClick={() => setSelectedSite(null)}>← Back</button>
          <img src={logo} alt="DeepTrail" className="dt-logo" />
        </header>

        {s.image_url && (
          <div className="dt-rockdetail-hero">
            <img src={s.image_url} alt={s.rock_type} />
          </div>
        )}

        <div className="dt-rockdetail-content">
          <h2 className="dt-rockdetail-name">{s.name}</h2>
          <div className="dt-rockdetail-rocks">{s.rock_type}</div>

          <div className="dt-rockdetail-badges">
            <span className={`dt-rocksite-owner ${s.land_owner === 'BLM' ? 'public' : s.land_owner === 'Private' ? 'private' : 'other'}`}>
              {s.land_owner}
            </span>
            {s.nearest_town && <span className="dt-rockdetail-town">📍 {s.nearest_town}</span>}
            {s.distance_km != null && <span className="dt-rockdetail-dist">{s.distance_km} km away</span>}
          </div>

          {s.description && (
            <div className="dt-rockdetail-section">
              <h3>Description</h3>
              <p>{s.description}</p>
            </div>
          )}

          {s.collecting_rules && (
            <div className="dt-rockdetail-section dt-rockdetail-rules-box">
              <h3>⚖️ Collecting Rules</h3>
              <p>{s.collecting_rules}</p>
            </div>
          )}

          <div className="dt-rockdetail-section">
            <h3>Location</h3>
            <p className="dt-rockdetail-coords">{s.latitude.toFixed(4)}°N, {Math.abs(s.longitude).toFixed(4)}°W</p>
          </div>

          <DetailMiniMap
            lat={s.latitude}
            lon={s.longitude}
            label={s.name}
          />
        </div>
      </div>
    )
  }

  return (
    <div className="dt-app">
      <DeepTrailHeader tab="collect" />

      {showSettings && (
        <CardSettingsPanel
          cards={cardConfig}
          onChange={setCardConfig}
          onClose={() => setShowSettings(false)}
          storageKey="deeptrail-collect-cards"
          defaults={COLLECT_CARDS}
          title="Customize Collect Cards"
          dark
        />
      )}

      {loading ? <div className="dt-loading">Loading geology data...</div> : (
        <main className="dt-content" style={{ paddingBottom: 72 }}>
          <style>{cardConfig.map((c, i) => {
            const rules = [`[data-dtcard="${c.id}"] { order: ${i}; }`]
            if (!c.visible) rules.push(`[data-dtcard="${c.id}"] { display: none !important; }`)
            return rules.join('\n')
          }).join('\n')}</style>

          <section className="dt-loc-hero">
            <div className="dt-hero-top-row">
              <h1>{loc.name}</h1>
              <button className="dt-settings-btn" onClick={() => setShowSettings(true)} title="Customize sections">⚙</button>
            </div>
            <p className="dt-loc-coords">{loc.lat.toFixed(4)}°N, {Math.abs(loc.lon).toFixed(4)}°W</p>
          </section>

          <div className="dt-card-container" style={{ display: 'flex', flexDirection: 'column' }}>

            {/* Rockhounding Sites */}
            <div data-dtcard="rockhounding">
              {rockhoundingSites.length > 0 && (
                <section className="dt-rockhounding">
                  <h3>🪨 Rockhounding Sites ({rockhoundingSites.length})</h3>
                  {rockhoundingSites.map((s: any, i: number) => {
                    const saved = isSaved('rocksite', s.name)
                    return (
                      <button key={i} className="dt-rocksite-row" onClick={() => setSelectedSite(s)}>
                        {s.image_url && <img src={s.image_url} alt={s.rock_type} className="dt-rocksite-row-img" loading="lazy" />}
                        <div className="dt-rocksite-row-body">
                          <div className="dt-rocksite-name">{s.name}</div>
                          <div className="dt-rocksite-rocks">{s.rock_type}</div>
                        </div>
                        <div className="dt-rocksite-row-right">
                          <span
                            style={{ fontSize: '1.2rem', cursor: 'pointer', marginRight: 4 }}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (saved) {
                                unsave('rocksite', s.name)
                              } else {
                                save({ type: 'rocksite', id: s.name, watershed: loc.id, label: s.name, sublabel: s.rock_type, thumbnail: s.image_url })
                              }
                            }}
                          >
                            {saved ? '★' : '☆'}
                          </span>
                          <span className={`dt-rocksite-owner ${s.land_owner === 'BLM' ? 'public' : s.land_owner === 'Private' ? 'private' : 'other'}`}>
                            {s.land_owner}
                          </span>
                          {s.distance_km != null && <span className="dt-rocksite-dist">{s.distance_km} km</span>}
                        </div>
                        <span className="dt-rocksite-arrow">→</span>
                      </button>
                    )
                  })}
                </section>
              )}
            </div>

            {/* Legal Collecting Status */}
            <div data-dtcard="legal_collecting">
              {landStatus && (
                <section className="dt-legal-card">
                  <div className="dt-legal-dot" style={{ background: statusColor }}></div>
                  <div>
                    <strong>Collecting: {landStatus.collecting_status || 'unknown'}</strong>
                    <span className="dt-legal-agency"> — {landStatus.agency || 'Unknown'}</span>
                    <p className="dt-legal-rules">{landStatus.collecting_rules}</p>
                    <p className="dt-legal-disclaimer">{landStatus.disclaimer}</p>
                  </div>
                </section>
              )}
            </div>

            {/* Mineral Shops */}
            <div data-dtcard="mineral_shops">
              {mineralShops.length > 0 && (
                <section className="dt-mineral-shops">
                  <h3>🏪 Mineral Shops Nearby</h3>
                  {mineralShops.map((s: any, i: number) => (
                    <div key={i} className="dt-shop-card">
                      <div className="dt-shop-name">{s.name}</div>
                      <div className="dt-shop-city">{s.city}</div>
                      <div className="dt-shop-desc">{s.description}</div>
                      <div className="dt-shop-links">
                        {s.phone && <a href={`tel:${s.phone}`} className="dt-shop-link">📞 {s.phone}</a>}
                        {s.website && <a href={s.website} target="_blank" rel="noopener noreferrer" className="dt-shop-link">🌐 Website</a>}
                      </div>
                    </div>
                  ))}
                </section>
              )}
            </div>

          </div>
        </main>
      )}

      <PhotoObservation app="deeptrail" watershed={loc?.id} />
    </div>
  )
}

// ── Detail MiniMap with a single green pin ──

function DetailMiniMap({ lat, lon, label }: { lat: number; lon: number; label: string }) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const map = new maplibregl.Map({
      container: ref.current,
      style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json',
      center: [lon, lat],
      zoom: 10,
      interactive: true,
    })

    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'top-right')

    map.on('load', () => {
      map.addSource('site', {
        type: 'geojson',
        data: {
          type: 'FeatureCollection',
          features: [{
            type: 'Feature',
            geometry: { type: 'Point', coordinates: [lon, lat] },
            properties: { label },
          }],
        },
      })
      map.addLayer({
        id: 'site-point', type: 'circle', source: 'site',
        paint: { 'circle-radius': 8, 'circle-color': '#4caf50', 'circle-stroke-color': '#fff', 'circle-stroke-width': 2 },
      })
    })

    return () => { map.remove() }
  }, [lat, lon, label])

  return <div ref={ref} className="dt-mini-map" />
}
