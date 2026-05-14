import { useEffect, useRef, useState } from 'react'
import useSWR from 'swr'
import { API_BASE } from '../config'
import './TripQualityForecastModal.css'

interface SubScores {
  catch: number
  water_temp: number
  flow: number
  weather: number
  hatch: number
  access: number
}

interface ForecastWeather {
  temp_f: number | null
  precip_in: number | null
  wind_mph: number | null
  wind_bearing: number | null
  water_temp_f: number | null
  forecast_source: string | null
}

interface ForecastDay {
  target_date: string
  offset_days: number
  tqs: number
  confidence: 'high' | 'medium' | 'low'
  confidence_pct: number
  band: 'excellent' | 'good' | 'fair' | 'poor'
  primary_factor: string | null
  sub_scores: SubScores | null
  weather: ForecastWeather | null
  forecast_source: string
  is_climatological: boolean
  is_actual: boolean
  is_hard_closed: boolean
}

interface ForecastResponse {
  watershed: string
  generated_at: string
  days: ForecastDay[]
}

const fetcher = (url: string) =>
  fetch(url, { credentials: 'include' }).then(r => r.json())

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const SUB_LABELS: Array<[keyof SubScores, string]> = [
  ['catch',      'Catch'],
  ['water_temp', 'Water Temp'],
  ['flow',       'Flow'],
  ['weather',    'Weather'],
  ['hatch',      'Hatch'],
  ['access',     'Access'],
]

function formatDate(iso: string): { weekday: string; calendar: string } {
  const d = new Date(iso + 'T12:00:00')
  return {
    weekday: DAY_NAMES[d.getDay()],
    calendar: d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
  }
}

function bearingToCompass(b: number | null | undefined): string | null {
  if (b == null) return null
  const dirs = ['N','NNE','NE','ENE','E','ESE','SE','SSE','S','SSW','SW','WSW','W','WNW','NW','NNW']
  return dirs[Math.round(((b % 360) / 22.5)) % 16]
}

export default function TripQualityForecastModal({
  watershed,
  open,
  onClose,
}: {
  watershed: string
  open: boolean
  onClose: () => void
}) {
  const { data, error, isLoading } = useSWR<ForecastResponse>(
    open ? `${API_BASE}/sites/${watershed}/trip-quality/forecast?days=14` : null,
    fetcher,
    { dedupingInterval: 30 * 60_000 }  // 30 min — forecast values shift slowly
  )

  const carouselRef = useRef<HTMLDivElement>(null)
  const [activeIndex, setActiveIndex] = useState(0)
  const [expandedWhy, setExpandedWhy] = useState<number | null>(null)

  // Track which card is centered via IntersectionObserver → for pagination dots.
  useEffect(() => {
    if (!open || !data) return
    const root = carouselRef.current
    if (!root) return
    const cards = Array.from(root.querySelectorAll<HTMLDivElement>('.tqs-fc-card'))
    if (!cards.length) return

    const io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.intersectionRatio >= 0.6) {
            const idx = cards.indexOf(entry.target as HTMLDivElement)
            if (idx >= 0) setActiveIndex(idx)
          }
        }
      },
      { root, threshold: [0.6] }
    )
    cards.forEach(c => io.observe(c))
    return () => io.disconnect()
  }, [open, data])

  // Close on ESC
  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onClose])

  function jumpToDay(index: number) {
    const root = carouselRef.current
    if (!root) return
    const card = root.querySelectorAll<HTMLDivElement>('.tqs-fc-card')[index]
    if (card) card.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' })
  }

  if (!open) return null

  return (
    <div className="tqs-fc-overlay" onClick={onClose} role="dialog" aria-label="14-day Trip Quality forecast">
      <div className="tqs-fc-sheet" onClick={e => e.stopPropagation()}>
        <header className="tqs-fc-header">
          <div className="tqs-fc-title">14-day Forecast</div>
          <button className="tqs-fc-close" onClick={onClose} aria-label="Close forecast">✕</button>
        </header>

        {error && (
          <div className="tqs-fc-state">Couldn't load the forecast. Try again later.</div>
        )}
        {isLoading && !data && (
          <div className="tqs-fc-state">
            <div className="tqs-fc-spinner" aria-hidden="true" />
            Loading 14-day forecast…
          </div>
        )}

        {data && data.days.length > 0 && (
          <>
            <div className="tqs-fc-carousel" ref={carouselRef}>
              {data.days.map((day, i) => {
                const { weekday, calendar } = formatDate(day.target_date)
                const isToday = day.is_actual
                const wind = day.weather?.wind_mph ?? null
                const compass = bearingToCompass(day.weather?.wind_bearing)
                const showWindCallout = wind != null && wind >= 10
                const why = expandedWhy === i

                return (
                  <div
                    key={day.target_date}
                    className={`tqs-fc-card conf-${day.confidence} band-${day.band}`}
                  >
                    <div className="tqs-fc-card-head">
                      <div className="tqs-fc-card-date">
                        <span className="tqs-fc-card-weekday">{weekday}</span>
                        <span className="tqs-fc-card-calendar">{calendar}</span>
                      </div>
                      {isToday ? (
                        <span className="tqs-fc-card-today">Today</span>
                      ) : day.is_climatological ? (
                        <span className="tqs-fc-card-approx">Approximate</span>
                      ) : (
                        <span className={`tqs-fc-card-confidence conf-${day.confidence}`}>
                          {day.confidence === 'high' ? 'High confidence' : day.confidence === 'medium' ? 'Medium confidence' : 'Low confidence'}
                        </span>
                      )}
                    </div>

                    <div className={`tqs-fc-card-score band-${day.band}${day.is_hard_closed ? ' closed' : ''}`}>
                      {day.is_hard_closed ? (
                        <span className="tqs-fc-card-closed">Reach closed</span>
                      ) : (
                        <>
                          <span className="tqs-fc-card-score-value">{day.tqs}</span>
                          <span className="tqs-fc-card-score-band">{day.band}</span>
                        </>
                      )}
                    </div>

                    {day.primary_factor && (
                      <div className="tqs-fc-card-factor">
                        Primary factor: <strong>{day.primary_factor}</strong>
                      </div>
                    )}

                    {day.weather && (
                      <div className="tqs-fc-card-weather-row">
                        {day.weather.temp_f != null && (
                          <span className="tqs-fc-chip">🌡️ {Math.round(day.weather.temp_f)}°F</span>
                        )}
                        {day.weather.precip_in != null && day.weather.precip_in > 0 && (
                          <span className="tqs-fc-chip">💧 {day.weather.precip_in.toFixed(2)}″</span>
                        )}
                        {showWindCallout && (
                          <span className={`tqs-fc-chip ${wind >= 15 ? 'warn' : ''}`}>
                            🍃 {Math.round(wind!)} mph{compass ? ` ${compass}` : ''}
                          </span>
                        )}
                        {day.weather.water_temp_f != null && (
                          <span className="tqs-fc-chip">🐟 {Math.round(day.weather.water_temp_f)}°F water</span>
                        )}
                      </div>
                    )}

                    {day.sub_scores && (
                      <button
                        className="tqs-fc-card-why-btn"
                        onClick={() => setExpandedWhy(why ? null : i)}
                      >
                        {why ? 'Hide breakdown' : 'Why this score?'}
                      </button>
                    )}

                    {why && day.sub_scores && (
                      <div className="tqs-fc-card-why">
                        {SUB_LABELS.map(([key, label]) => (
                          <div key={key} className="tqs-fc-subscore">
                            <span className="tqs-fc-subscore-label">{label}</span>
                            <div className="tqs-fc-subscore-bar">
                              <div
                                className={`tqs-fc-subscore-fill band-${day.band}`}
                                style={{ width: `${Math.max(0, Math.min(100, day.sub_scores![key]))}%` }}
                              />
                            </div>
                            <span className="tqs-fc-subscore-value">{day.sub_scores![key]}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            <div className="tqs-fc-dots" role="tablist" aria-label="Forecast day">
              {data.days.map((d, i) => (
                <button
                  key={d.target_date}
                  type="button"
                  className={`tqs-fc-dot${activeIndex === i ? ' active' : ''}`}
                  aria-label={`Jump to ${d.target_date}`}
                  onClick={() => jumpToDay(i)}
                />
              ))}
            </div>
          </>
        )}

        {data && data.days.length === 0 && (
          <div className="tqs-fc-state">No forecast available yet for {watershed}.</div>
        )}
      </div>
    </div>
  )
}
