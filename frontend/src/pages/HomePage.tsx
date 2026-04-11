import { useEffect, useState, useRef } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import logo from '../assets/riversignal-logo.svg'
import './HomePage.css'

const API_BASE = 'http://localhost:8001/api/v1'

// Real Oregon watershed photos from Unsplash (free for commercial use)
// Real Oregon watershed photos from Unsplash (free commercial use)
const PHOTOS: Record<string, string> = {
  mckenzie: 'https://images.unsplash.com/photo-1660806739398-0f0627930230?w=900&h=600&fit=crop', // Tamolitch Blue Pool, McKenzie River OR
  deschutes: 'https://images.unsplash.com/photo-1470173479932-81a508f4b1b7?w=900&h=600&fit=crop', // Deschutes River OR by Jack Long
  metolius: 'https://images.unsplash.com/photo-1688057937854-c94e7ad00b57?w=900&h=600&fit=crop', // Oregon forest river by Peter Robbins
  klamath: 'https://images.unsplash.com/photo-1548869447-faef5000334c?w=900&h=600&fit=crop', // Klamath Falls OR sunset by Eric Muhr
}

interface WatershedData {
  name: string
  watershed: string
  tagline: string
  narrative: string
  health?: any
  scorecard?: any
  indicators?: any[]
  story?: any
}

const WATERSHED_META: Record<string, { tagline: string; narrative: string }> = {
  mckenzie: {
    tagline: 'Fire, recovery, and the return of salmon',
    narrative: 'In September 2020, the Holiday Farm Fire burned 174,390 acres through the McKenzie corridor. Five years later, the watershed tells a remarkable recovery story: species richness has grown from 1,282 to 3,644 — nearly tripling. Chinook salmon are spawning in reaches that were barren. The river endures.',
  },
  deschutes: {
    tagline: '111 miles of canyon ecology and steelhead runs',
    narrative: 'From the springs above Bend to the canyon at Maupin, the Deschutes flows through one of Oregon\'s most dramatic ecological gradients. Cold-water refuges at the headwaters give way to thermal stress zones in the lower canyon. In 2024, anglers harvested 1,757 steelhead — the strongest run in years.',
  },
  metolius: {
    tagline: 'Spring-fed sanctuary — Oregon\'s purest river',
    narrative: 'The Metolius emerges fully formed from the base of Black Butte, a constant 9.5°C year-round. This spring-fed system is one of the coldest, most stable rivers in Oregon — a refuge for bull trout, kokanee salmon, and the Oregon spotted frog. It is the benchmark against which other watersheds are measured.',
  },
  klamath: {
    tagline: 'The largest dam removal in American history',
    narrative: 'The 2023-2024 removal of four dams on the Klamath River — the largest such action in US history — opened 400 miles of habitat for salmon returning for the first time in a century. Upper Klamath Lake\'s endangered suckers and the Klamath Tribes\' stewardship story make this one of the most consequential ecological experiments on Earth.',
  },
}

const WATERSHED_ORDER = ['mckenzie', 'deschutes', 'metolius', 'klamath']

export default function HomePage() {
  const navigate = useNavigate()
  const [watersheds, setWatersheds] = useState<WatershedData[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all(
      WATERSHED_ORDER.map(ws =>
        fetch(`${API_BASE}/sites/${ws}`).then(r => r.json()).then(data => ({
          ...data,
          watershed: ws,
          ...WATERSHED_META[ws],
        }))
      )
    )
      .then(data => { setWatersheds(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  const handleAsk = (watershed: string, question: string) => {
    if (question.trim()) {
      navigate(`/map/${watershed}?q=${encodeURIComponent(question.trim())}`)
    }
  }

  const totalSpecies = watersheds.reduce((a, w) => a + (w.scorecard?.total_species || 0), 0)

  return (
    <div className="home">
      {/* River flow accent */}
      <div className="river-flow" />

      {/* Navigation */}
      <nav className="home-nav">
        <Link to="/" className="home-nav-brand"><img src={logo} alt="RiverSignal" className="home-logo" /></Link>
        <div className="home-nav-links">
          {WATERSHED_ORDER.map(ws => (
            <Link key={ws} to={`/map/${ws}`} className="home-nav-link">
              {{ mckenzie: 'McKenzie', deschutes: 'Deschutes', metolius: 'Metolius', klamath: 'Klamath' }[ws]}
            </Link>
          ))}
          <Link to="/map" className="home-nav-link home-nav-map">Map →</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="home-hero">
        <div className="home-hero-eyebrow">Oregon's Living Rivers</div>
        <h1 className="home-hero-title">
          Every river has<br />a story <em>worth telling</em>
        </h1>
        <p className="home-hero-subtitle">
          Real-time ecological intelligence from {loading ? '...' : totalSpecies.toLocaleString()} species,
          2.2 million observations, and 15 public data sources across four iconic Oregon watersheds.
        </p>
      </section>

      {/* Watershed stories */}
      <section className="home-watersheds">
        {watersheds.map((ws, idx) => (
          <WatershedBlock
            key={ws.watershed}
            data={ws}
            photo={PHOTOS[ws.watershed]}
            reversed={idx % 2 === 1}
            onAsk={(q) => handleAsk(ws.watershed, q)}
            onNavigate={() => navigate(`/map/${ws.watershed}`)}
          />
        ))}
      </section>

      {/* Species discovery */}
      <SpeciesSection />

      {/* Footer */}
      <footer className="home-footer">
        <div className="home-footer-brand">RiverSignal + RiverPath</div>
        <p>2.2 million records · 15 public data sources · 24 materialized views · 4 Oregon watersheds</p>
        <p>Built on iNaturalist, USGS, SNOTEL, PRISM, OWRI, ODFW, NHDPlus, MTBS, and more.</p>
      </footer>
    </div>
  )
}

/* ── Watershed Block ── */
function WatershedBlock({ data, photo, reversed, onAsk, onNavigate }: {
  data: WatershedData; photo: string; reversed: boolean;
  onAsk: (q: string) => void; onNavigate: () => void
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)
  const [askInput, setAskInput] = useState('')

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
          {health.water_temp_c != null && <span className="pill water">{health.water_temp_c}°C water</span>}
          {health.dissolved_oxygen_mg_l != null && <span className="pill water">{health.dissolved_oxygen_mg_l} mg/L DO</span>}
          {sc.total_interventions > 0 && <span className="pill earth">{sc.total_interventions} restoration projects</span>}
        </div>

        {/* Inline chat */}
        <div className="ws-ask">
          <div className="ws-ask-label">Ask about {data.name.replace(' River', '').replace('Upper ', '')}</div>
          <div className="ws-ask-row">
            <input
              type="text"
              value={askInput}
              onChange={e => setAskInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && askInput.trim()) onAsk(askInput) }}
              placeholder={`Is the ${data.name.replace('Upper ', '')} healthy?`}
            />
            <button onClick={() => { if (askInput.trim()) onAsk(askInput) }}>Ask</button>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Species Carousel ── */
function SpeciesSection() {
  const [species, setSpecies] = useState<any[]>([])

  useEffect(() => {
    // Fetch fish species with photos from McKenzie (most diverse)
    fetch(`${API_BASE}/sites/mckenzie/species?taxonomic_group=Actinopterygii&limit=12`)
      .then(r => r.json())
      .then(data => setSpecies(data.filter((s: any) => s.photo_url)))
      .catch(console.error)
  }, [])

  if (species.length === 0) return null

  return (
    <section className="home-species">
      <h2 className="home-species-title">18,544 species documented</h2>
      <p className="home-species-sub">Every species photographed, mapped, and connected to the living story of its watershed</p>
      <div className="species-scroll">
        {species.map((s, i) => (
          <div key={i} className="species-scroll-item">
            <img src={s.photo_url} alt={s.common_name || s.taxon_name} loading="lazy" />
            <div className="species-scroll-info">
              <div className="species-scroll-common">{s.common_name || s.taxon_name}</div>
              <div className="species-scroll-sci">{s.taxon_name}</div>
              {s.conservation_status && <span className="species-scroll-tag">{s.conservation_status}</span>}
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
