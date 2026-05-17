import { useEffect } from 'react'
import useSWR from 'swr'
import WatershedHeader from '../components/WatershedHeader'
import { useWatershed } from '../hooks/useWatershed'
import './StewardPage.css'


const COUNCIL_LINKS: Record<string, { name: string; url: string }> = {
  mckenzie: { name: 'McKenzie Watershed Council', url: 'https://www.mckenziewc.org/' },
  deschutes: { name: 'Upper Deschutes Watershed Council', url: 'https://www.upperdeschuteswatershedcouncil.org/' },
  metolius: { name: 'Deschutes River Conservancy', url: 'https://www.deschutesriver.org/' },
  klamath: { name: 'Klamath Watershed Partnership', url: 'https://www.klamathpartnership.org/' },
  johnday: { name: 'Grant Soil & Water Conservation District', url: 'https://grantswcd.org/' },
  shenandoah: { name: 'Friends of the Shenandoah River', url: 'https://www.fosr.org/' },
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
  // SWR-backed — story key shared with RiverNowPage. Stewardship + impact
  // are 6-hour-stable per watershed.
  const { data } = useSWR<any>(`/sites/${ws}/stewardship`, { dedupingInterval: 6 * 60 * 60 * 1000 })
  const { data: story } = useSWR<any>(`/sites/${ws}/story`, { dedupingInterval: 24 * 60 * 60 * 1000 })
  const { data: impact } = useSWR<any>(`/sites/${ws}/restoration-impact`, { dedupingInterval: 6 * 60 * 60 * 1000 })

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

      {/* ── Get Involved CTA — surfaced above the project list so users see
             the call-to-action before scrolling through the project log. ── */}
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

      {/* ── Projects (sorted reverse-chronologically by most recent year) ── */}
      {data?.opportunities?.length > 0 && (
        <section className="steward-section">
          <h2 className="steward-section-title">Projects</h2>
          <div className="opp-grid">
            {[...data.opportunities]
              .sort((a: any, b: any) => (b.most_recent_year || 0) - (a.most_recent_year || 0))
              .map((opp: any, i: number) => (
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
    </div>
  )
}
