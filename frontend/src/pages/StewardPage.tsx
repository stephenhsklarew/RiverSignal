import { useEffect, useState } from 'react'
import SaveButton from '../components/SaveButton'
import WatershedHeader from '../components/WatershedHeader'
import { useWatershed } from '../hooks/useWatershed'
import './StewardPage.css'

const API = 'http://localhost:8001/api/v1'

const COUNCIL_LINKS: Record<string, { name: string; url: string }> = {
  mckenzie: { name: 'McKenzie Watershed Council', url: 'https://www.mckenziewc.org/' },
  deschutes: { name: 'Upper Deschutes Watershed Council', url: 'https://www.upperdeschuteswatershedcouncil.org/' },
  metolius: { name: 'Deschutes River Conservancy', url: 'https://www.deschutesriver.org/' },
  klamath: { name: 'Klamath Watershed Partnership', url: 'https://www.klamathpartnership.org/' },
  johnday: { name: 'Grant Soil & Water Conservation District', url: 'https://grantswcd.org/' },
}

const CATEGORY_ICONS: Record<string, string> = {
  'riparian restoration': '🌿',
  'instream habitat': '🪨',
  'fish passage': '🐟',
  'flow restoration': '💧',
  'invasive removal': '🚫',
  'water quality': '🧪',
}

export default function StewardPage() {
  const ws = useWatershed('/path/steward') || 'mckenzie'
  const [data, setData] = useState<any>(null)
  const [story, setStory] = useState<any>(null)

  useEffect(() => {
    setData(null); setStory(null)
    fetch(`${API}/sites/${ws}/stewardship`).then(r => r.json()).then(setData)
    fetch(`${API}/sites/${ws}/story`).then(r => r.json()).then(setStory)
  }, [ws])

  const timeline = story?.timeline || []
  const restorationEvents = timeline.filter((e: any) => e.event_type === 'restoration')
  const fireEvents = timeline.filter((e: any) => e.event_type === 'fire')
  const council = COUNCIL_LINKS[ws]

  const handleShare = (name: string, before: number, after: number) => {
    const text = `${name}: ${before} species before → ${after} species after restoration. See the impact at RiverPath.`
    if (navigator.share) {
      navigator.share({ title: name, text }).catch(() => {})
    } else {
      navigator.clipboard.writeText(text)
    }
  }

  return (
    <div className="steward-page">
      <WatershedHeader watershed={ws} basePath="/path/steward" />
      <h1 className="steward-title">Stewardship</h1>

      {/* ── Restoration Timeline ── */}
      {timeline.length > 0 && (
        <section className="steward-section">
          <h2 className="steward-section-title">Watershed Timeline</h2>
          <div className="steward-timeline">
            {timeline.slice(0, 15).map((event: any, i: number) => (
              <div key={i} className={`timeline-item ${event.event_type}`}>
                <div className="timeline-year">{event.year}</div>
                <div className="timeline-dot" />
                <div className="timeline-content">
                  <div className="timeline-name">{event.name}</div>
                  <div className="timeline-type">{event.event_type}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Restoration Outcomes ── */}
      {data?.outcomes?.length > 0 && (
        <section className="steward-section">
          <h2 className="steward-section-title">Restoration Outcomes</h2>
          {data.outcomes.map((o: any, i: number) => (
            <div key={i} className="outcome-card">
              <div className="outcome-header">
                <div className="outcome-title-row">
                  <span className="outcome-icon">{CATEGORY_ICONS[o.category?.toLowerCase()] || '♻'}</span>
                  <div>
                    <div className="outcome-name">{o.name}</div>
                    <div className="outcome-meta">{o.category} · {o.year}</div>
                  </div>
                </div>
                <div className="outcome-actions">
                  <SaveButton item={{ type: 'restoration', id: `${ws}-${o.name}-${o.year}`, watershed: ws, label: o.name, sublabel: `${o.category} · ${o.year}` }} />
                  <button className="outcome-cta" onClick={() => handleShare(o.name, o.species_before, o.species_after)} title="Share">↗ Share</button>
                </div>
              </div>
              <div className="outcome-comparison">
                <div className="outcome-before">
                  <span className="outcome-count">{o.species_before}</span>
                  <span className="outcome-label">species before</span>
                </div>
                <div className="outcome-arrow">→</div>
                <div className="outcome-after">
                  <span className="outcome-count">{o.species_after}</span>
                  <span className="outcome-label">species after</span>
                </div>
                {o.species_before > 0 && o.species_after > o.species_before && (
                  <div className="outcome-delta">
                    +{Math.round(((o.species_after - o.species_before) / o.species_before) * 100)}%
                  </div>
                )}
              </div>
            </div>
          ))}
        </section>
      )}

      {/* ── How to Help ── */}
      {data?.opportunities?.length > 0 && (
        <section className="steward-section">
          <h2 className="steward-section-title">How to Help</h2>
          <div className="opp-grid">
            {data.opportunities.map((opp: any, i: number) => (
              <div key={i} className="opp-card">
                <span className="opp-icon">{CATEGORY_ICONS[opp.category?.toLowerCase()] || '♻'}</span>
                <div className="opp-info">
                  <div className="opp-category">{opp.category}</div>
                  <div className="opp-type">{opp.type}</div>
                  <div className="opp-meta">{opp.project_count} projects · most recent: {opp.most_recent_year}</div>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Get Involved CTA ── */}
      {council && (
        <section className="steward-section">
          <div className="steward-cta-card">
            <h3 className="steward-cta-title">Get Involved</h3>
            <p className="steward-cta-text">
              Contact your local watershed council for volunteer opportunities, restoration workdays, and monitoring programs.
            </p>
            <a href={council.url} target="_blank" rel="noopener noreferrer" className="steward-cta-btn">
              Join {council.name} →
            </a>
          </div>
        </section>
      )}
    </div>
  )
}
