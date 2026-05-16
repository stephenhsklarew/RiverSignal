import { useEffect, useState } from 'react'
import useSWR from 'swr'
import SaveButton from '../components/SaveButton'
import WatershedHeader from '../components/WatershedHeader'
import { useWatershed } from '../hooks/useWatershed'
import './HatchPage.css'

const MONTH_NAMES = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const HOUR = 60 * 60 * 1000

const STAGE_ICONS: Record<string, string> = { nymph: '🐛', emerger: '🪶', adult: '🪰' }

export default function HatchPage() {
  useEffect(() => {
    document.title = 'River Path'
    return () => { document.title = 'River Signal' }
  }, [])
  const ws = useWatershed('/path/hatch') || 'deschutes'

  // SWR-backed (stale-while-revalidate, cache survives navigation), so
  // the hatch panel renders instantly from the same cache RiverNowPage
  // primes on /path/now/<ws> — both pages share the
  // `/sites/<ws>/fishing/hatch-confidence` key. Previously this used
  // fetch+useState which cleared on every navigation and made the page
  // feel sluggish vs. /path/now. dedupingInterval=1h matches the value
  // RiverNowPage uses for the same endpoint.
  const { data: hatch } = useSWR<any>(`/sites/${ws}/fishing/hatch-confidence`, { dedupingInterval: HOUR })
  const { data: flies = [] } = useSWR<any[]>(`/sites/${ws}/fishing/fly-recommendations`, { dedupingInterval: HOUR })

  const currentMonth = hatch?.current_month || new Date().getMonth() + 1
  const nextMonth = (currentMonth % 12) + 1
  const thisMonthInsects = (hatch?.insects || []).filter((i: any) => i.month === currentMonth)
  const nextMonthInsects = (hatch?.insects || []).filter((i: any) => i.month === nextMonth)

  // Build a map of insect name → matching flies
  const flyByInsect: Record<string, any[]> = {}
  for (const fly of flies) {
    const key = (fly.insect || '').toLowerCase()
    if (!flyByInsect[key]) flyByInsect[key] = []
    flyByInsect[key].push(fly)
  }

  return (
    <div className="hatch-page">
      <WatershedHeader watershed={ws} basePath="/path/hatch" />

      {/* This Month */}
      <section className="hatch-section">
        <h2 className="hatch-section-title">{MONTH_NAMES[currentMonth]} — This Month</h2>
        {thisMonthInsects.length === 0 ? (
          <p className="hatch-empty">No hatch data for this month.</p>
        ) : (
          thisMonthInsects.slice(0, 5).map((insect: any, i: number) => (
            <InsectCardWithFlies key={i} insect={insect} ws={ws} matchingFlies={findFlies(insect, flyByInsect)} />
          ))
        )}
      </section>

      {/* Next Month */}
      <section className="hatch-section">
        <h2 className="hatch-section-title">{MONTH_NAMES[nextMonth]} — Next Month</h2>
        {nextMonthInsects.length === 0 ? (
          <p className="hatch-empty">No hatch data for next month.</p>
        ) : (
          nextMonthInsects.slice(0, 5).map((insect: any, i: number) => (
            <InsectCardWithFlies key={i} insect={insect} ws={ws} matchingFlies={findFlies(insect, flyByInsect)} />
          ))
        )}
      </section>

      {/* All Fly Patterns (deduplicated by name) */}
      {flies.length > 0 && (() => {
        const seen = new Set<string>()
        const uniqueFlies = flies.filter((fly: any) => {
          const key = (fly.fly_pattern || '').toLowerCase().trim()
          if (seen.has(key)) return false
          seen.add(key)
          return true
        })
        return (
          <section className="hatch-section">
            <h2 className="hatch-section-title">All Recommended Flies</h2>
            <div className="hatch-flies">
              {uniqueFlies.slice(0, 12).map((fly: any, i: number) => (
                <FlyCard key={i} fly={fly} ws={ws} />
              ))}
            </div>
          </section>
        )
      })()}
    </div>
  )
}

function findFlies(insect: any, flyByInsect: Record<string, any[]>): any[] {
  const name = (insect.common_name || insect.taxon_name || '').toLowerCase()
  // Try exact match, then partial match
  if (flyByInsect[name]) return flyByInsect[name]
  for (const [key, flies] of Object.entries(flyByInsect)) {
    if (name.includes(key) || key.includes(name)) return flies
  }
  return []
}

function InsectCardWithFlies({ insect, ws, matchingFlies }: { insect: any; ws: string; matchingFlies: any[] }) {
  const [expanded, setExpanded] = useState(false)
  // Guess lifecycle stage from activity level and observations
  const stage = insect.activity === 'peak' ? 'adult' : insect.observations > 5 ? 'emerger' : 'nymph'

  return (
    <div className="insect-card-wrap">
      <div className="insect-card" onClick={() => setExpanded(!expanded)}>
        {insect.photo_url && <img src={insect.photo_url} alt={insect.common_name} className="insect-img" title="Photo via iNaturalist" />}
        <div className="insect-info">
          <div className="insect-name">{insect.common_name || insect.taxon_name}</div>
          <div className="insect-sci">{insect.taxon_name}</div>
          <div className="insect-meta">
            <span className={`insect-confidence confidence-${insect.confidence}`}>{insect.confidence}</span>
            {insect.insect_order && <span className="insect-order">{insect.insect_order}</span>}
            <span className="insect-stage" title={`Likely ${stage}`}>{STAGE_ICONS[stage]} {stage}</span>
            {insect.activity && <span className="insect-activity">{insect.activity}</span>}
            {insect.observations != null && <span className="insect-obs">{insect.observations} obs</span>}
                      </div>
        </div>
        <span className="insect-expand">{expanded ? '▾' : '▸'}</span>
      </div>

      {/* Matching flies with images (primary), curated names as fallback */}
      {expanded && (
        <div className="insect-flies">
          {insect.fly_patterns?.length > 0 ? (
            <>
              <div className="insect-flies-label">Recommended flies:</div>
              {insect.fly_patterns.map((fp: any, i: number) => {
                const name = typeof fp === 'string' ? fp : fp.name
                const videoUrl = typeof fp === 'object' ? fp.tying_video_url : null
                const videoTitle = typeof fp === 'object' ? fp.tying_video_title : null
                return (
                  <div key={i} className="curated-fly-item">
                    <span className="curated-fly-name">{name}</span>
                    {videoUrl && (
                      <a href={videoUrl} target="_blank" rel="noopener noreferrer" className="fly-video-link" title={videoTitle || 'Fly tying video'}>
                        ▶ Tie it
                      </a>
                    )}
                    <SaveButton item={{ type: 'fly', id: `${ws}-${name}`, watershed: ws, label: name, sublabel: insect.common_name }} size={14} />
                  </div>
                )
              })}
            </>
          ) : matchingFlies.length > 0 ? (
            <>
              <div className="insect-flies-label">Matching flies:</div>
              {matchingFlies.slice(0, 4).map((fly, i) => (
                <FlyCard key={i} fly={fly} ws={ws} compact />
              ))}
            </>
          ) : (
            <div className="insect-flies-empty">No specific fly match — try a general attractor pattern.</div>
          )}
        </div>
      )}
    </div>
  )
}

function FlyCard({ fly, ws, compact }: { fly: any; ws: string; compact?: boolean }) {
  return (
    <div className={`fly-card${compact ? ' compact' : ''}`}>
      {fly.fly_image_url && <img src={fly.fly_image_url} alt={fly.fly_pattern} className="fly-img" />}
      <div className="fly-info">
        <div className="fly-name">{fly.fly_pattern}</div>
        <div className="fly-meta">
          {fly.fly_size && <span>#{fly.fly_size}</span>}
          {fly.fly_type && <span> · {fly.fly_type}</span>}
          {fly.life_stage && <span> · {fly.life_stage}</span>}
          {fly.time_of_day && <span> · {fly.time_of_day}</span>}
          {fly.water_type && <span> · {fly.water_type}</span>}
        </div>
        {!compact && fly.insect && <div className="fly-insect">Matches: {fly.insect}</div>}
        {fly.tying_video_url && (
          <a href={fly.tying_video_url} target="_blank" rel="noopener noreferrer" className="fly-video-link" title={fly.tying_video_title || 'Fly tying video'}>
            ▶ Tie it
          </a>
        )}
      </div>
      <SaveButton item={{
        type: 'fly',
        id: `${ws}-${fly.fly_pattern}-${fly.fly_size || ''}`,
        watershed: ws,
        label: fly.fly_pattern,
        sublabel: `${fly.fly_size ? '#' + fly.fly_size : ''} ${fly.fly_type || ''}`.trim(),
      }} size={compact ? 16 : 20} />
    </div>
  )
}
