import { useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import rsLogo from '../assets/riversignal-logo.svg'
import rpLogo from '../assets/riverpath-logo.svg'
import dtLogo from '../assets/deeptrail-logo.svg'
import lmLogo from '../assets/liquid-marble-logo.png'
import { useAuth } from '../components/AuthContext'
import './LandingPage.css'

const products = [
  {
    name: 'RiverSignal',
    tagline: 'Watershed Research Assistant',
    description: 'Professional grade analytics for citizen scientists and amateur naturalists.',
    audience: 'Desktop-first',
    path: '/riversignal',
    icon: '🔬',
    color: '#1a6b4a',
  },
  {
    name: 'RiverPath',
    tagline: 'River Field Companion',
    description: 'Story-driven mobile guide for fly fishing anglers and educators exploring living rivers.',
    audience: 'Mobile-first',
    path: '/path/now',
    icon: '🏞️',
    color: '#2d7a9c',
  },
  {
    name: 'DeepTrail',
    tagline: 'Ancient World Explorer',
    description: 'Adventure-focused mobile guide for rockhounds exploring places to make new discoveries.',
    audience: 'Mobile-first',
    path: '/trail',
    icon: '🦴',
    color: '#996633',
  },
]

export default function LandingPage() {
  const { user } = useAuth()
  const isAdmin = !!user?.is_admin
  const navigate = useNavigate()
  useEffect(() => {
    document.title = 'Liquid Marble'
    return () => { document.title = 'River Signal' }
  }, [])
  return (
    <div className="landing">
      <header className="landing-header">
        <img src={lmLogo} alt="Liquid Marble" className="landing-title-logo" />
        <p className="landing-subtitle">
          One data platform where watershed ecology meets deep time geology.
        </p>
      </header>

      <p className="landing-powers-label">Apps built on Liquid Marble:</p>
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
            <p className="product-tagline">{p.tagline}</p>
            <p className="product-desc">{p.description}</p>
            <span className="product-audience">{p.audience}</span>
            {/* RiverPath admin entry — only renders for users with is_admin.
                Rendered as a <button> not <Link> to avoid nested anchors. */}
            {p.name === 'RiverPath' && isAdmin && (
              <button
                type="button"
                className="product-admin-pill"
                onClick={e => {
                  e.preventDefault()
                  e.stopPropagation()
                  navigate('/admin/photos')
                }}
                aria-label="RiverPath admin"
              >Admin</button>
            )}
          </Link>
        ))}
      </div>

      <footer className="landing-footer">
        <Link to="/status" className="landing-status-link">View Data Status →</Link>
        <p className="landing-note">
          Powered by dozens of curated public data sources and thoughtful use of artificial intelligence.
        </p>
      </footer>
    </div>
  )
}
