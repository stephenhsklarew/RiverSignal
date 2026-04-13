import { useEffect, useState } from 'react'
import SaveButton from '../components/SaveButton'
import WatershedHeader from '../components/WatershedHeader'
import { useWatershed } from '../hooks/useWatershed'
import { tempF } from '../utils/temp'
import './HatchPage.css'

const API = 'http://localhost:8001/api/v1'
const MONTH_NAMES = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

const LIFECYCLE_STAGES = ['nymph', 'emerger', 'adult']
const STAGE_ICONS: Record<string, string> = { nymph: '🐛', emerger: '🪶', adult: '🪰' }

export default function HatchPage() {
  const ws = useWatershed('/path/hatch') || 'deschutes'
  const [hatch, setHatch] = useState<any>(null)
  const [flies, setFlies] = useState<any[]>([])

  useEffect(() => {
    setHatch(null); setFlies([])
    fetch(`${API}/sites/${ws}/fishing/hatch-confidence`).then(r => r.json()).then(setHatch)
    fetch(`${API}/sites/${ws}/fishing/fly-recommendations`).then(r => r.json()).then(setFlies)
  }, [ws])

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
      <h1 className="hatch-title">Hatch Intelligence</h1>
      {hatch?.water_temp_c != null && (
        <div className="hatch-temp">Current water: {tempF(hatch.water_temp_c)}</div>
      )}

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

      {/* Unmatched Fly Patterns */}
      {flies.length > 0 && (
        <section className="hatch-section">
          <h2 className="hatch-section-title">All Recommended Flies</h2>
          <div className="hatch-flies">
            {flies.slice(0, 12).map((fly: any, i: number) => (
              <FlyCard key={i} fly={fly} ws={ws} />
            ))}
          </div>
        </section>
      )}
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
        {insect.photo_url && <img src={insect.photo_url} alt={insect.common_name} className="insect-img" />}
        <div className="insect-info">
          <div className="insect-name">{insect.common_name || insect.taxon_name}</div>
          <div className="insect-sci">{insect.taxon_name}</div>
          <div className="insect-meta">
            <span className={`insect-confidence confidence-${insect.confidence}`}>{insect.confidence}</span>
            <span className="insect-stage" title={`Likely ${stage}`}>{STAGE_ICONS[stage]} {stage}</span>
            {insect.activity && <span className="insect-activity">{insect.activity}</span>}
            <span className="insect-obs">{insect.observations} obs · {insect.years_observed}yr</span>
          </div>
        </div>
        <span className="insect-expand">{expanded ? '▾' : '▸'}</span>
      </div>

      {/* Matching flies inline */}
      {expanded && matchingFlies.length > 0 && (
        <div className="insect-flies">
          <div className="insect-flies-label">Matching flies:</div>
          {matchingFlies.slice(0, 4).map((fly, i) => (
            <FlyCard key={i} fly={fly} ws={ws} compact />
          ))}
        </div>
      )}
      {expanded && matchingFlies.length === 0 && (
        <div className="insect-flies">
          <div className="insect-flies-empty">No specific fly match — try a general attractor pattern.</div>
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
