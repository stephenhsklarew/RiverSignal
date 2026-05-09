import { Link } from 'react-router-dom'
import rsLogo from '../assets/riversignal-logo.svg'
import rpLogo from '../assets/riverpath-logo.svg'
import dtLogo from '../assets/deeptrail-logo.svg'
import './LandingPage.css'

const products = [
  {
    name: 'RiverSignal',
    tagline: 'Watershed Intelligence Copilot',
    description: 'Professional grade analytics for watershed managers, restoration ecologists, and conservation agencies.',
    audience: 'B2B — Desktop-first',
    path: '/riversignal',
    icon: '🔬',
    color: '#1a6b4a',
  },
  {
    name: 'RiverPath',
    tagline: 'River Field Companion',
    description: 'Story-driven mobile guide for families, anglers, and educators exploring living rivers.',
    audience: 'B2C — Mobile-first',
    path: '/path/now',
    icon: '🏞️',
    color: '#2d7a9c',
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
        <h1 className="landing-title">Liquid Marble</h1>
        <p className="landing-subtitle">
          Watershed ecology meets deep time geology. One data platform power three apps.
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
        <Link to="/status" className="landing-status-link">View data status →</Link>
        <p className="landing-note">
          Powered by dozens of curated public data sources and thoughtful artificial intelligence.
        </p>
      </footer>
    </div>
  )
}
