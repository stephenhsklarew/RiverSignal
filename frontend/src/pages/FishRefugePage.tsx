import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import SaveButton from '../components/SaveButton'
import WatershedHeader from '../components/WatershedHeader'
import { cToF, tempF } from '../utils/temp'
import { getSelectedWatershed } from '../components/WatershedHeader'
import './FishRefugePage.css'

const API = 'http://localhost:8001/api/v1'

const THERMAL_COLORS: Record<string, string> = {
  cold_water_refuge: '#2563eb', cool_water: '#0d9488', warm_water: '#d97706', thermal_stress: '#dc2626',
}
const THERMAL_BG: Record<string, string> = {
  cold_water_refuge: '#eff6ff', cool_water: '#f0fdfa', warm_water: '#fffbeb', thermal_stress: '#fef2f2',
}

// Rough preferred temp ranges for common species
const SPECIES_TEMPS: Record<string, [number, number]> = {
  'oncorhynchus mykiss': [7, 16],
  'salvelinus confluentus': [4, 12],
  'oncorhynchus tshawytscha': [6, 14],
  'oncorhynchus kisutch': [7, 15],
  'oncorhynchus nerka': [5, 14],
  'salmo trutta': [7, 18],
  'micropterus dolomieu': [15, 27],
}

function getTempStatus(currentTemp: number | null, taxon: string): { label: string; class: string; range: string } | null {
  if (currentTemp == null) return null
  const key = taxon.toLowerCase()
  for (const [species, [lo, hi]] of Object.entries(SPECIES_TEMPS)) {
    if (key.includes(species) || species.includes(key)) {
      const label = currentTemp < lo ? 'Below range' : currentTemp > hi ? 'Above range' : 'In range'
      const cls = currentTemp >= lo && currentTemp <= hi ? 'good' : currentTemp <= hi + 2 && currentTemp >= lo - 2 ? 'marginal' : 'stress'
      return { label, class: cls, range: `${cToF(lo)}–${cToF(hi)}°F` }
    }
  }
  const label = currentTemp < 18 ? 'Suitable' : 'Warm'
  const cls = currentTemp < 16 ? 'good' : currentTemp < 20 ? 'marginal' : 'stress'
  return { label, class: cls, range: `<${cToF(18)}°F preferred` }
}

export default function FishRefugePage() {
  const navigate = useNavigate()
  const { watershed: paramWs } = useParams<{ watershed: string }>()
  const [searchParams] = useSearchParams()
  const ws = paramWs || getSelectedWatershed() || 'deschutes'
  const scrollSection = searchParams.get('section')

  const [species, setSpecies] = useState<any[]>([])
  const [refuges, setRefuges] = useState<any[]>([])
  const [conditions, setConditions] = useState<any>(null)
  const [reachSpecies, setReachSpecies] = useState<any[]>([])

  const refugeRef = useRef<HTMLElement>(null)

  useEffect(() => {
    fetch(`${API}/sites/${ws}/species?taxonomic_group=Actinopterygii&limit=20`).then(r => r.json()).then(setSpecies)
    fetch(`${API}/sites/${ws}/cold-water-refuges`).then(r => r.json()).then(setRefuges)
    fetch(`${API}/sites/${ws}/fishing/conditions`).then(r => r.json()).then(d => setConditions(d?.[0]))
    fetch(`${API}/sites/${ws}/fishing/species`).then(r => r.json()).then(d => setReachSpecies(d?.slice(0, 10) || []))
  }, [ws])

  // Auto-scroll to refuges section if requested
  useEffect(() => {
    if (scrollSection === 'refuges' && refugeRef.current && refuges.length > 0) {
      refugeRef.current.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [scrollSection, refuges])

  const currentTemp = conditions?.water_temp_c

  return (
    <div className="fish-page">
      {/* Back button + header */}
      <div className="fish-back-row">
        <button className="fish-back-btn" onClick={() => navigate(`/path/now/${ws}`)}>← River Now</button>
      </div>
      <WatershedHeader watershed={ws} basePath="/path/fish" />

      <h1 className="fish-title">Fish + Cold-Water Refuges</h1>
      {currentTemp != null && (
        <div className="fish-current-temp">Current water: <strong>{tempF(currentTemp)}</strong></div>
      )}

      {/* ── Fish Carousel ── */}
      {species.length > 0 && (
        <section className="fish-section">
          <h2 className="fish-section-title">Fish Species</h2>
          <div className="fish-carousel">
            {species.map((sp, i) => {
              const tempInfo = getTempStatus(currentTemp, sp.taxon_name)
              return (
                <div key={i} className="fish-card">
                  {sp.photo_url && <img src={sp.photo_url} alt={sp.common_name} className="fish-card-img" />}
                  <div className="fish-card-body">
                    <div className="fish-card-top">
                      <div>
                        <div className="fish-card-name">{sp.common_name || sp.taxon_name}</div>
                        <div className="fish-card-sci">{sp.taxon_name}</div>
                      </div>
                      <SaveButton item={{ type: 'species', id: sp.taxon_name, watershed: ws, label: sp.common_name || sp.taxon_name, sublabel: sp.taxon_name, thumbnail: sp.photo_url }} size={18} />
                    </div>
                    {tempInfo && (
                      <div className="fish-temp-row">
                        <span className={`fish-temp-badge temp-${tempInfo.class}`}>
                          {tempF(currentTemp)} — {tempInfo.label}
                        </span>
                        <span className="fish-temp-range">Prefers {tempInfo.range}</span>
                      </div>
                    )}
                    {sp.conservation_status && (
                      <span className="fish-conservation">{sp.conservation_status}</span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </section>
      )}

      {/* ── Species by Reach ── */}
      {reachSpecies.length > 0 && (
        <section className="fish-section">
          <h2 className="fish-section-title">Species by Stream Reach</h2>
          <div className="reach-list">
            {reachSpecies.map((r: any, i: number) => (
              <div key={i} className="reach-row">
                <div className="reach-stream">{r.stream}</div>
                <div className="reach-species">{r.common_name || r.scientific_name}</div>
                <div className="reach-use">{r.use_type}</div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Thermal Refuge Stations ── */}
      {refuges.length > 0 && (
        <section className="fish-section" ref={refugeRef}>
          <h2 className="fish-section-title">Thermal Station Classifications</h2>
          <div className="refuge-grid">
            {refuges.map((r: any, i: number) => (
              <div key={i} className="refuge-card" style={{
                borderLeftColor: THERMAL_COLORS[r.thermal_class] || '#999',
                background: THERMAL_BG[r.thermal_class] || 'var(--surface)',
              }}>
                <div className="refuge-header">
                  <div className="refuge-station">{r.station}</div>
                  <div className="refuge-class" style={{ color: THERMAL_COLORS[r.thermal_class] || '#999' }}>
                    {r.thermal_class?.replace(/_/g, ' ')}
                  </div>
                </div>
                <div className="refuge-details">
                  <span className="refuge-temp">{r.avg_summer_temp_c != null ? tempF(r.avg_summer_temp_c) : '—'} avg summer</span>
                  {r.temp_trend_per_year != null && (
                    <span className={`refuge-trend ${r.temp_trend_per_year > 0 ? 'warming' : 'cooling'}`}>
                      {r.temp_trend_per_year > 0 ? '↑' : '↓'} {(Math.abs(r.temp_trend_per_year) * 9 / 5).toFixed(2)}°F/yr
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* ── Explanation ── */}
      <section className="fish-section">
        <div className="refuge-explain">
          <strong>Why cold-water refuges matter</strong>
          <p>Salmonids — trout, salmon, and steelhead — require water below 64°F to thrive. During summer heat, cold-water refuges fed by springs, deep pools, and tributaries provide critical thermal habitat. Fish concentrate at these stations during heat events. Stations showing warming trends (↑) may lose refuge status in coming years.</p>
          <p>Stations classified as <span style={{color: THERMAL_COLORS.cold_water_refuge, fontWeight: 600}}>cold-water refuge</span> or <span style={{color: THERMAL_COLORS.cool_water, fontWeight: 600}}>cool</span> are where to target for summer fishing. <span style={{color: THERMAL_COLORS.thermal_stress, fontWeight: 600}}>Thermal stress</span> zones should be avoided to reduce fish mortality.</p>
        </div>
      </section>
    </div>
  )
}
