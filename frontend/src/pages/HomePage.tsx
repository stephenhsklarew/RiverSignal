import { useEffect, useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { tempF } from '../utils/temp'
import logo from '../assets/riverpath-logo.svg'
import { API_BASE } from '../config'
import { SPLASH_PHOTOS, SPLASH_META } from '../lib/watershedSplash'
import './HomePage.css'

interface WatershedData {
  name: string
  watershed: string
  tagline: string
  narrative: string
  splash_image_url?: string | null
  health?: any
  scorecard?: any
  indicators?: any[]
  story?: any
}

const WATERSHED_ORDER = ['chattahoochee', 'clinch_river_va', 'deschutes', 'green_river', 'ipswich_river_ma', 'johnday', 'klamath', 'mad_river_oh', 'mckenzie', 'meramec', 'metolius', 'new_river_va', 'shenandoah', 'skagit']

export default function HomePage() {
  const navigate = useNavigate()
  const [watersheds, setWatersheds] = useState<WatershedData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all(
      WATERSHED_ORDER.map(ws =>
        fetch(`${API_BASE}/sites/${ws}`).then(r => r.json()).then(data => {
          const meta = SPLASH_META[ws] || { tagline: '', narrative: '' }
          // Admin overrides (gold.watershed_splash) win; otherwise fall back
          // to the built-in defaults.
          return {
            ...data,
            watershed: ws,
            tagline: data.splash_tagline ?? meta.tagline,
            narrative: data.splash_narrative ?? meta.narrative,
            splash_image_url: data.splash_image_url ?? null,
          }
        })
      )
    )
      .then(data => { setWatersheds(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const totalSpecies = watersheds.reduce((a, w) => a + (w.scorecard?.total_species || 0), 0)

  return (
    <div className="home">
      {/* River flow accent */}
      <div className="river-flow" />

      {/* Navigation */}
      <nav className="home-nav">
        <Link to="/" className="home-nav-brand"><img src={logo} alt="RiverPath" className="home-logo" /></Link>
      </nav>

      {/* Hero */}
      <section className="home-hero">
        <div className="home-hero-eyebrow">Oregon's Living Rivers</div>
        <h1 className="home-hero-title">
          Every river has<br />a story <em>worth telling</em>
        </h1>
        <p className="home-hero-subtitle">
          Real-time ecological intelligence from {loading ? '...' : totalSpecies.toLocaleString()} species observed
          — across plants, animals &amp; fungi — plus millions of public observations spanning {loading ? '' : watersheds.length} watersheds nationwide.
        </p>
      </section>

      {/* Watershed stories */}
      <section className="home-watersheds">
        {watersheds.map((ws, idx) => (
          <WatershedBlock
            key={ws.watershed}
            data={ws}
            photo={ws.splash_image_url || SPLASH_PHOTOS[ws.watershed]}
            reversed={idx % 2 === 1}
            onNavigate={() => navigate(`/path/now/${ws.watershed}`)}
          />
        ))}
      </section>

      {/* Species discovery */}
      <SpeciesSection />

      {/* Footer */}
      <footer className="home-footer">
        <div className="home-footer-brand">RiverPath — <Link to="/trail" style={{color:'#d4a96a'}}>Explore DeepTrail</Link></div>
        <p>2.2 million records · 15 public data sources · 24 materialized views · 4 Oregon watersheds</p>
        <p>Built on iNaturalist, USGS, SNOTEL, PRISM, OWRI, ODFW, NHDPlus, MTBS, and more.</p>
      </footer>
    </div>
  )
}

/* ── Watershed Block ── */
function WatershedBlock({ data, photo, reversed, onNavigate }: {
  data: WatershedData; photo: string; reversed: boolean;
  onNavigate: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true) }, { threshold: 0.15 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  const health = data.health || {}
  const sc = data.scorecard || {}
  const healthClass = (health.score || 0) >= 70 ? 'good' : (health.score || 0) >= 50 ? 'moderate' : 'poor'

  return (
    <div ref={ref} className={`ws-block ${reversed ? 'reversed' : ''} ${visible ? 'visible' : ''}`}>
      <div className="ws-image" onClick={onNavigate}>
        <img src={photo} alt={data.name} loading="lazy" />
        {health.score != null && (
          <div className="ws-health-orb">
            <div className={`ws-score ${healthClass}`}>{health.score}</div>
            <div className="ws-score-label">health</div>
          </div>
        )}
      </div>
      <div className="ws-content">
        <h2 className="ws-title" onClick={onNavigate}>{data.name}</h2>
        <div className="ws-tagline">{data.tagline}</div>
        <p className="ws-narrative">{data.narrative}</p>

        <div className="ws-pills">
          <span className="pill river">{sc.total_species?.toLocaleString() || '—'} species</span>
          {health.water_temp_c != null && <span className="pill water">{tempF(health.water_temp_c)} water</span>}
          {health.dissolved_oxygen_mg_l != null && <span className="pill water">{health.dissolved_oxygen_mg_l} mg/L DO</span>}
          {sc.total_interventions > 0 && <span className="pill earth">{sc.total_interventions} restoration projects</span>}
        </div>

        {/* Go to this watershed in /path/now */}
        <button className="ws-go-btn" onClick={onNavigate}>
          Explore {data.name.replace(' River', '').replace('Upper ', '')} →
        </button>
      </div>
    </div>
  )
}

/* ── Species Carousel ── */
function SpeciesSection() {
  const [species, setSpecies] = useState<any[]>([])
  const [activeGroup, setActiveGroup] = useState<string>('all')

  const GROUPS = [
    { key: 'all', label: 'All Species' },
    { key: 'Actinopterygii', label: 'Fish' },
    { key: 'Aves', label: 'Birds' },
    { key: 'Insecta', label: 'Insects' },
    { key: 'Plantae', label: 'Plants' },
    { key: 'Mammalia', label: 'Mammals' },
    { key: 'Amphibia', label: 'Amphibians' },
  ]

  useEffect(() => {
    // Fetch species with photos from multiple watersheds for diversity
    const watersheds = ['mckenzie', 'deschutes', 'klamath', 'johnday', 'metolius']
    const groupParam = activeGroup !== 'all' ? `&taxonomic_group=${activeGroup}` : ''
    Promise.all(
      watersheds.map(ws =>
        fetch(`${API_BASE}/sites/${ws}/species?limit=10${groupParam}`)
          .then(r => r.json())
          .catch(() => [])
      )
    ).then(results => {
      const all = results.flat().filter((s: any) => s.photo_url)
      // Deduplicate by taxon_name, shuffle
      const seen = new Set<string>()
      const unique = all.filter((s: any) => {
        if (seen.has(s.taxon_name)) return false
        seen.add(s.taxon_name)
        return true
      })
      // Shuffle
      for (let i = unique.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [unique[i], unique[j]] = [unique[j], unique[i]]
      }
      setSpecies(unique.slice(0, 24))
    })
  }, [activeGroup])

  if (species.length === 0) return null

  return (
    <section className="home-species">
      <h2 className="home-species-title">18,500+ species documented</h2>
      <p className="home-species-sub">Photographed, mapped, and connected to the living story of each watershed</p>
      <div className="species-group-tabs">
        {GROUPS.map(g => (
          <button key={g.key}
            className={`species-group-tab${activeGroup === g.key ? ' active' : ''}`}
            onClick={() => setActiveGroup(g.key)}>
            {g.label}
          </button>
        ))}
      </div>
      <div className="species-scroll">
        {species.map((s, i) => (
          <div key={i} className="species-scroll-item">
            <img src={s.photo_url} alt={s.common_name || s.taxon_name} loading="lazy" />
            <div className="species-scroll-info">
              <div className="species-scroll-common">{s.common_name || s.taxon_name}</div>
              <div className="species-scroll-sci">{s.taxon_name}</div>
              {s.conservation_status && <span className="species-scroll-tag">{s.conservation_status}</span>}
              {s.observer && <div className="species-scroll-credit">📷 {s.observer}</div>}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
