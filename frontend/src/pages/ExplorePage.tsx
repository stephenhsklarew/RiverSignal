import { useEffect, useState } from 'react'
import SaveButton from '../components/SaveButton'
import WatershedHeader from '../components/WatershedHeader'
import { useWatershed } from '../hooks/useWatershed'
import './ExplorePage.css'

const API = 'http://localhost:8001/api/v1'

const FILTERS = [
  { key: 'campground', label: 'Camping', icon: '⛺' },
  { key: 'trailhead', label: 'Trails', icon: '🥾' },
  { key: 'boat_ramp', label: 'Boat Ramps', icon: '🚣' },
  { key: 'fishing_access', label: 'Fishing', icon: '🎣' },
  { key: 'day_use', label: 'Day Use', icon: '☀' },
  { key: 'swim_area', label: 'Swimming', icon: '🏊' },
]

const TYPE_ICONS: Record<string, string> = {
  campground: '⛺', trailhead: '🥾', boat_ramp: '🚣', day_use: '☀',
  fishing_access: '🎣', swim_area: '🏊', waterfall: '💧', swim_advisory: '⚠',
}

interface RecSite {
  id: number
  name: string
  rec_type: string
  latitude: number
  longitude: number
  amenities: Record<string, any>
  watershed: string
  distance_km?: number
}

export default function ExplorePage() {
  const ws = useWatershed('/path/explore') || 'deschutes'
  const [sites, setSites] = useState<RecSite[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set())
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list')
  const [userLoc, setUserLoc] = useState<{ lat: number; lon: number } | null>(null)

  // Try GPS
  useEffect(() => {
    navigator.geolocation?.getCurrentPosition(
      pos => setUserLoc({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => {},
      { timeout: 5000 }
    )
  }, [])

  // Fetch recreation sites
  useEffect(() => {
    setLoading(true)
    fetch(`${API}/sites/${ws}/recreation`)
      .then(r => r.json())
      .then((data: RecSite[]) => {
        // Calculate distance if we have user location
        if (userLoc) {
          data.forEach(s => {
            s.distance_km = haversine(userLoc.lat, userLoc.lon, s.latitude, s.longitude)
          })
          data.sort((a, b) => (a.distance_km || 999) - (b.distance_km || 999))
        }
        setSites(data)
        setLoading(false)
      })
      .catch(() => { setSites([]); setLoading(false) })
  }, [ws, userLoc])

  const toggleFilter = (key: string) => {
    setActiveFilters(prev => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key); else next.add(key)
      return next
    })
  }

  // Filter and search
  const filtered = sites.filter(s => {
    if (activeFilters.size > 0 && !activeFilters.has(s.rec_type)) return false
    if (search.trim()) {
      const q = search.toLowerCase()
      if (!s.name.toLowerCase().includes(q) && !s.rec_type.toLowerCase().includes(q)) return false
    }
    return true
  })

  return (
    <div className="explore-page">
      <WatershedHeader watershed={ws} basePath="/path/explore" />
      <h1 className="explore-title">Explore</h1>

      {/* Search */}
      <div className="explore-search">
        <input
          type="text"
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search campgrounds, trailheads, boat ramps..."
          className="explore-search-input"
        />
      </div>

      {/* Filters */}
      <div className="explore-filters">
        {FILTERS.map(f => (
          <button
            key={f.key}
            className={`explore-filter${activeFilters.has(f.key) ? ' active' : ''}`}
            onClick={() => toggleFilter(f.key)}
          >
            <span className="explore-filter-icon">{f.icon}</span> {f.label}
          </button>
        ))}
      </div>

      {/* Map/List toggle + count */}
      <div className="explore-bar">
        <span className="explore-count">{filtered.length} sites</span>
        <div className="explore-toggle">
          <button className={viewMode === 'list' ? 'active' : ''} onClick={() => setViewMode('list')}>List</button>
          <button className={viewMode === 'map' ? 'active' : ''} onClick={() => setViewMode('map')}>Map</button>
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <div className="explore-loading">Loading recreation sites...</div>
      ) : filtered.length === 0 ? (
        <div className="explore-empty">
          <p>No results{activeFilters.size > 0 ? ' — try removing a filter' : ''}.</p>
          {activeFilters.size > 0 && (
            <button className="explore-reset" onClick={() => setActiveFilters(new Set())}>Reset filters</button>
          )}
        </div>
      ) : viewMode === 'list' ? (
        <div className="explore-list">
          {filtered.map(s => (
            <AdventureCard key={`${s.rec_type}-${s.id}`} site={s} ws={ws} />
          ))}
        </div>
      ) : (
        <div className="explore-map-placeholder">
          <p>Map view coming soon. Showing {filtered.length} sites as list below.</p>
          <div className="explore-list">
            {filtered.map(s => (
              <AdventureCard key={`${s.rec_type}-${s.id}`} site={s} ws={ws} />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function AdventureCard({ site, ws }: { site: RecSite; ws: string }) {
  const icon = TYPE_ICONS[site.rec_type] || '📍'
  const amenities = site.amenities || {}

  return (
    <div className="adventure-card">
      <div className="adventure-icon">{icon}</div>
      <div className="adventure-body">
        <div className="adventure-name">{site.name}</div>
        <div className="adventure-meta">
          <span className="adventure-type">{site.rec_type.replace('_', ' ')}</span>
          {site.distance_km != null && (
            <span className="adventure-distance">{site.distance_km < 1 ? `${Math.round(site.distance_km * 1000)}m` : `${site.distance_km.toFixed(1)}km`}</span>
          )}
        </div>
        <div className="adventure-amenities">
          {amenities.fee && <span className="amenity-badge">💲 Fee</span>}
          {amenities.accessible && <span className="amenity-badge">♿ Accessible</span>}
          {amenities.pets_allowed && <span className="amenity-badge">🐕 Pets OK</span>}
          {amenities.reservable && <span className="amenity-badge">📅 Reservable</span>}
          {amenities.parking && <span className="amenity-badge">🅿 Parking</span>}
          {amenities.restrooms && <span className="amenity-badge">🚻 Restrooms</span>}
          {amenities.forest && <span className="amenity-badge forest">{amenities.forest}</span>}
          {amenities.season_start && amenities.season_end && (
            <span className="amenity-badge">📅 {amenities.season_start}–{amenities.season_end}</span>
          )}
          {amenities.status && amenities.status !== 'OPEN' && (
            <span className="amenity-badge closed">⚠ {amenities.status}</span>
          )}
        </div>
      </div>
      <SaveButton item={{
        type: 'recreation',
        id: `${site.rec_type}-${site.id}`,
        watershed: ws,
        label: site.name,
        sublabel: site.rec_type.replace('_', ' '),
      }} />
    </div>
  )
}

function haversine(lat1: number, lon1: number, lat2: number, lon2: number): number {
  const R = 6371
  const dLat = (lat2 - lat1) * Math.PI / 180
  const dLon = (lon2 - lon1) * Math.PI / 180
  const a = Math.sin(dLat / 2) ** 2 + Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLon / 2) ** 2
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}
