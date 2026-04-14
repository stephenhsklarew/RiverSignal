import { useEffect, useState, useRef } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import Markdown from 'react-markdown'
import { tempF } from '../utils/temp'
import logo from '../assets/riverpath-logo.svg'
import './HomePage.css'

const API_BASE = '/api/v1'

// Real Oregon watershed photos from Unsplash (free for commercial use)
// Real Oregon watershed photos from Unsplash (free commercial use)
const PHOTOS: Record<string, string> = {
  mckenzie: 'https://images.unsplash.com/photo-1660806739398-0f0627930230?w=900&h=600&fit=crop', // Tamolitch Blue Pool, McKenzie River OR
  deschutes: 'https://images.unsplash.com/photo-1528672903139-6a4496639a68?w=900&h=600&fit=crop', // Smith Rock / Crooked River canyon (Deschutes tributary) by Dale Nibbe
  metolius: 'https://images.unsplash.com/photo-1657215223750-c4988d4a2635?w=900&h=600&fit=crop', // Cabin on Metolius River, Camp Sherman OR by Lance Reis
  klamath: 'https://images.unsplash.com/photo-1566126157268-bd7167924841?w=900&h=600&fit=crop', // Wood River meandering into Klamath Lake, Chiloquin OR by Dan Meyers
  johnday: 'https://images.unsplash.com/photo-1559867243-edf5915deaa7?w=900&h=600&fit=crop', // Painted Hills, John Day Fossil Beds National Monument OR by Dan Meyers
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
    narrative: 'The Metolius emerges fully formed from the base of Black Butte, a constant 49°F year-round. This spring-fed system is one of the coldest, most stable rivers in Oregon — a refuge for bull trout, kokanee salmon, and the Oregon spotted frog. It is the benchmark against which other watersheds are measured.',
  },
  klamath: {
    tagline: 'The largest dam removal in American history',
    narrative: 'The 2023-2024 removal of four dams on the Klamath River — the largest such action in US history — opened 400 miles of habitat for salmon returning for the first time in a century. Upper Klamath Lake\'s endangered suckers and the Klamath Tribes\' stewardship story make this one of the most consequential ecological experiments on Earth.',
  },
  johnday: {
    tagline: 'Wild & Scenic through ancient fossil beds',
    narrative: 'The John Day is one of the longest free-flowing rivers in the Pacific Northwest — 284 miles without a dam. It cuts through the Painted Hills and John Day Fossil Beds, where 40-million-year-old ecosystems are preserved in stone. Today it supports wild steelhead and spring Chinook runs through high-desert rangeland, making it one of Oregon\'s most remote and ecologically significant watersheds.',
  },
}

const WATERSHED_ORDER = ['mckenzie', 'deschutes', 'metolius', 'klamath', 'johnday']

export default function HomePage() {
  const navigate = useNavigate()
  const { watershed: activeWatershed } = useParams<{ watershed?: string }>()
  const [searchParams, setSearchParams] = useSearchParams()
  const [watersheds, setWatersheds] = useState<WatershedData[]>([])
  const [loading, setLoading] = useState(true)
  const pendingQuestion = searchParams.get('q')

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
      navigate(`/path/now/${watershed}?q=${encodeURIComponent(question.trim())}`)
    }
  }

  const handleQuestionConsumed = () => {
    setSearchParams({}, { replace: true })
  }

  const totalSpecies = watersheds.reduce((a, w) => a + (w.scorecard?.total_species || 0), 0)

  return (
    <div className="home">
      {/* River flow accent */}
      <div className="river-flow" />

      {/* Navigation */}
      <nav className="home-nav">
        <Link to="/" className="home-nav-brand"><img src={logo} alt="RiverPath" className="home-logo" /></Link>
      </nav>
      <div className="home-nav-links">
        {WATERSHED_ORDER.map(ws => (
          <Link key={ws} to={`/path/now/${ws}`} className="home-nav-link">
            {{ mckenzie: 'McKenzie', deschutes: 'Deschutes', metolius: 'Metolius', klamath: 'Klamath', johnday: 'John Day' }[ws]}
          </Link>
        ))}
      </div>

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
            onNavigate={() => navigate(`/path/now/${ws.watershed}`)}
            initialQuestion={ws.watershed === activeWatershed ? pendingQuestion : null}
            onQuestionConsumed={handleQuestionConsumed}
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
function WatershedBlock({ data, photo, reversed, onAsk, onNavigate, initialQuestion, onQuestionConsumed }: {
  data: WatershedData; photo: string; reversed: boolean;
  onAsk: (q: string) => void; onNavigate: () => void;
  initialQuestion?: string | null; onQuestionConsumed?: () => void
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [visible, setVisible] = useState(false)
  const [askInput, setAskInput] = useState('')
  const [chatQuestion, setChatQuestion] = useState<string | null>(null)
  const [chatAnswer, setChatAnswer] = useState<string | null>(null)
  const [chatLoading, setChatLoading] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const obs = new IntersectionObserver(([e]) => { if (e.isIntersecting) setVisible(true) }, { threshold: 0.15 })
    obs.observe(el)
    return () => obs.disconnect()
  }, [])

  // Handle incoming question from URL
  useEffect(() => {
    if (!initialQuestion || chatLoading || chatQuestion) return
    setChatQuestion(initialQuestion)
    setChatLoading(true)
    ref.current?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    fetch(`${API_BASE}/sites/${data.watershed}/chat`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: initialQuestion }),
    })
      .then(r => r.json())
      .then(res => setChatAnswer(res.answer || res.detail || 'Unable to answer.'))
      .catch(() => setChatAnswer('Set ANTHROPIC_API_KEY to enable AI answers.'))
      .finally(() => { setChatLoading(false); onQuestionConsumed?.() })
  }, [initialQuestion])

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

        {/* Inline chat */}
        <div className="ws-ask">
          <div className="ws-ask-label">Ask about {data.name.replace(' River', '').replace('Upper ', '')}</div>
          <div className="ws-ask-row">
            <input
              type="text"
              value={askInput}
              onChange={e => setAskInput(e.target.value)}
              onKeyDown={e => { if (e.key === 'Enter' && askInput.trim()) onAsk(askInput) }}
              placeholder="How's the fly fishing today?"
            />
            <button onClick={() => { if (askInput.trim()) onAsk(askInput) }}>Ask</button>
          </div>
        </div>

        {/* Inline chat response */}
        {(chatQuestion || chatLoading) && (
          <div className="ws-chat-response">
            <div className="ws-chat-question">{chatQuestion}</div>
            {chatLoading ? (
              <div className="ws-chat-loading">Thinking about the {data.name.replace('Upper ', '')}...</div>
            ) : chatAnswer ? (
              <div className="ws-chat-answer"><Markdown>{chatAnswer}</Markdown></div>
            ) : null}
          </div>
        )}
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
            </div>
          </div>
        ))}
      </div>
    </section>
  )
}
