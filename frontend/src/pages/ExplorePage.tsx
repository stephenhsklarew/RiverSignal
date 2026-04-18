import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
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
  { key: 'fly_shop', label: 'Fly Shops', icon: '🏪' },
  { key: 'guide_service', label: 'Guides', icon: '🚣' },
  { key: 'day_use', label: 'Day Use', icon: '☀' },
  { key: 'swim_area', label: 'Swimming', icon: '🏊' },
]

const TYPE_ICONS: Record<string, string> = {
  campground: '⛺', trailhead: '🥾', boat_ramp: '🚣', day_use: '☀',
  fishing_access: '🎣', swim_area: '🏊', waterfall: '💧', swim_advisory: '⚠',
  fly_shop: '🏪', guide_service: '🚣', both: '🏪',
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
  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])
  const navigate = useNavigate()
  const ws = useWatershed('/path/explore') || 'deschutes'
  const [sites, setSites] = useState<RecSite[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [activeFilters, setActiveFilters] = useState<Set<string>>(new Set())
  const [userLoc, setUserLoc] = useState<{ lat: number; lon: number } | null>(null)

  // Try GPS
  useEffect(() => {
    navigator.geolocation?.getCurrentPosition(
      pos => setUserLoc({ lat: pos.coords.latitude, lon: pos.coords.longitude }),
      () => {},
      { timeout: 5000 }
    )
  }, [])

  // Fetch recreation sites + fly shops
  useEffect(() => {
    setLoading(true)
    Promise.all([
      fetch(`${API}/sites/${ws}/recreation`).then(r => r.json()).catch(() => []),
      fetch(`${API}/sites/${ws}/fly-shops`).then(r => r.json()).catch(() => []),
    ]).then(([recData, shopData]) => {
      // Convert fly shops to RecSite format
      const shops: RecSite[] = (shopData || []).map((s: any, i: number) => ({
        id: 90000 + i,
        name: s.name,
        rec_type: s.type === 'both' ? 'fly_shop' : s.type,
        latitude: s.latitude,
        longitude: s.longitude,
        amenities: {
          phone: s.phone,
          website: s.website,
          address: s.address,
          description: s.description,
        },
        watershed: ws,
      }))

      const all = [...(recData || []), ...shops]

      // Calculate distance if we have user location
      if (userLoc) {
        all.forEach(s => {
          s.distance_km = haversine(userLoc.lat, userLoc.lon, s.latitude, s.longitude)
        })
        all.sort((a, b) => (a.distance_km || 999) - (b.distance_km || 999))
      }
      setSites(all)
      setLoading(false)
    })
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
    if (activeFilters.size > 0) {
      const matches = activeFilters.has(s.rec_type)
        || (s.rec_type === 'fly_shop' && (activeFilters.has('fly_shop') || activeFilters.has('guide_service')))
        || (s.rec_type === 'guide_service' && activeFilters.has('guide_service'))
      if (!matches) return false
    }
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

      {/* Count + Map button */}
      <div className="explore-bar">
        <span className="explore-count">{filtered.length} sites</span>
        <button className="explore-map-btn" onClick={() => navigate(`/path/explore-map/${ws}`)}>View Map</button>
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
      ) : (
        <div className="explore-list">
          {filtered.map(s => (
            <AdventureCard key={`${s.rec_type}-${s.id}`} site={s} ws={ws} />
          ))}
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
        {amenities.description && (
          <div className="adventure-desc">{amenities.description}</div>
        )}
        {(amenities.phone || amenities.website) && (
          <div className="adventure-contact">
            {amenities.phone && <a href={`tel:${amenities.phone}`} className="adventure-link">📞 {amenities.phone}</a>}
            {amenities.website && <a href={amenities.website} target="_blank" rel="noopener noreferrer" className="adventure-link">🌐 Website</a>}
          </div>
        )}
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
