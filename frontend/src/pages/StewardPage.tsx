import { useEffect, useState } from 'react'
import WatershedHeader from '../components/WatershedHeader'
import { useWatershed } from '../hooks/useWatershed'
import { API_BASE } from '../config'
import './StewardPage.css'

const API = API_BASE

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
  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])
  const ws = useWatershed('/path/steward') || 'mckenzie'
  const [data, setData] = useState<any>(null)
  const [story, setStory] = useState<any>(null)
  const [impact, setImpact] = useState<any>(null)

  useEffect(() => {
    setData(null); setStory(null); setImpact(null)
    fetch(`${API}/sites/${ws}/stewardship`).then(r => r.json()).then(setData)
    fetch(`${API}/sites/${ws}/story`).then(r => r.json()).then(setStory)
    fetch(`${API}/sites/${ws}/restoration-impact`).then(r => r.json()).then(setImpact).catch(() => {})
  }, [ws])

  const timeline = story?.timeline || []
  const council = COUNCIL_LINKS[ws]


  return (
    <div className="steward-page">
      <WatershedHeader watershed={ws} basePath="/path/steward" />

      {/* ── Restoration Impact Hero ── */}
      {impact && (
        <section className="steward-impact">
          <div className="steward-impact-grid">
            <div className="steward-impact-stat">
              <span className="steward-impact-value">{impact.total_species?.toLocaleString()}</span>
              <span className="steward-impact-label">species documented</span>
            </div>
            <div className="steward-impact-stat">
              <span className="steward-impact-value">{impact.total_projects?.toLocaleString()}</span>
              <span className="steward-impact-label">restoration projects</span>
            </div>
            <div className="steward-impact-stat">
              <span className="steward-impact-value">{impact.total_observations?.toLocaleString()}</span>
              <span className="steward-impact-label">observations</span>
            </div>
          </div>
          {impact.fire_recovery?.length > 0 && (
            <div className="steward-impact-recovery">
              {impact.fire_recovery.map((f: any, i: number) => (
                <div key={i} className="steward-recovery-item">
                  <span className="steward-recovery-icon">🔥</span>
                  <div>
                    <div className="steward-recovery-name">{f.fire} ({f.year})</div>
                    <div className="steward-recovery-stat">
                      +{f.species_gained} species recovered over {f.years_tracked} years
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          {impact.top_interventions?.length > 0 && (
            <div className="steward-impact-interventions">
              <div className="steward-impact-subtitle">Most Effective Approaches</div>
              {impact.top_interventions.slice(0, 3).map((t: any, i: number) => (
                <div key={i} className="steward-intervention-row">
                  <span className="steward-intervention-cat">{CATEGORY_ICONS[t.category?.toLowerCase()] || '♻'} {t.category}</span>
                  <span className="steward-intervention-gain">+{t.avg_species_gain} species avg</span>
                  <span className="steward-intervention-count">{t.projects} projects</span>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

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
