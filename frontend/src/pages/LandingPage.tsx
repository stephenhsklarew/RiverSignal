import { Link } from 'react-router-dom'
import rsLogo from '../assets/riversignal-logo.svg'
import rpLogo from '../assets/riverpath-logo.svg'
import dtLogo from '../assets/deeptrail-logo.svg'
import './LandingPage.css'

const products = [
  {
    name: 'RiverSignal',
    tagline: 'Watershed Intelligence Copilot',
    description: 'Professional data-dense dashboard for watershed managers, restoration ecologists, and conservation agencies.',
    audience: 'B2B — Desktop-first',
    path: '/riversignal',
    icon: '🔬',
    color: '#1a6b4a',
  },
  {
    name: 'RiverPath',
    tagline: 'River Field Companion',
    description: 'Story-driven mobile guide for families, anglers, and educators exploring Oregon\'s living rivers.',
    audience: 'B2C — Mobile-first',
    path: '/path',
    icon: '🏞️',
    color: '#2d7a9c',
  },
  {
    name: 'DeepSignal',
    tagline: 'Geologic Intelligence Platform',
    description: 'Professional geology dashboard with geologic maps, fossil data, and ecology-geology correlations.',
    audience: 'B2B — Desktop-first',
    path: '/deepsignal',
    icon: '🪨',
    color: '#8b5a2b',
  },
  {
    name: 'DeepTrail',
    tagline: 'Ancient World Explorer',
    description: 'Adventure-focused mobile guide for families and rockhounds discovering fossils and deep time stories.',
    audience: 'B2C — Mobile-first',
    path: '/trail',
    icon: '🦴',
    color: '#996633',
  },
]

export default function LandingPage() {
  return (
    <div className="landing">
      <header className="landing-header">
        <h1 className="landing-title">Field Intelligence Platform</h1>
        <p className="landing-subtitle">
          Four products, one data platform. Watershed ecology meets deep time geology.
        </p>
      </header>

      <div className="landing-grid">
        {products.map(p => (
          <Link to={p.path} key={p.name} className="product-card" style={{ '--accent': p.color } as React.CSSProperties}>
            <div className="product-icon">
              {p.name === 'RiverSignal'
                ? <img src={rsLogo} alt="RiverSignal" className="product-logo" />
                : p.name === 'RiverPath'
                ? <img src={rpLogo} alt="RiverPath" className="product-logo" />
                : p.name === 'DeepTrail'
                ? <img src={dtLogo} alt="DeepTrail" className="product-logo" />
                : p.icon}
            </div>
            <h2 className="product-name">{p.name}</h2>
            <p className="product-tagline">{p.tagline}</p>
            <p className="product-desc">{p.description}</p>
            <span className="product-audience">{p.audience}</span>
          </Link>
        ))}
      </div>

      <footer className="landing-footer">
        <div className="landing-stats">
          <div className="stat"><strong>2.2M+</strong> records</div>
          <div className="stat"><strong>18</strong> data pipelines</div>
          <div className="stat"><strong>5</strong> Oregon watersheds</div>
          <div className="stat"><strong>18,500+</strong> species</div>
          <div className="stat"><strong>667</strong> fossil occurrences</div>
          <div className="stat"><strong>352</strong> geologic units</div>
        </div>
        <p className="landing-note">
          Powered by iNaturalist, USGS, PBDB, Macrostrat, BLM, and 12 more public data sources.
          AI reasoning by Claude.
        </p>
      </footer>
    </div>
  )
}
