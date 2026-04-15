import { useState, useMemo, useCallback, useEffect } from 'react'
import './TimelineSlider.css'

interface TimelineSliderProps {
  features: any[]
  onFilterChange: (startDate: string | null, endDate: string | null) => void
}

export default function TimelineSlider({ features, onFilterChange }: TimelineSliderProps) {
  // Extract date range from features
  const { minDate, maxDate, dateRange } = useMemo(() => {
    const dates: string[] = []
    for (const f of features) {
      const d = f.properties?.observed_at
      if (d && d !== 'None') dates.push(d)
    }
    dates.sort()
    if (dates.length === 0) return { minDate: '', maxDate: '', dateRange: 0 }
    const min = dates[0]
    const max = dates[dates.length - 1]
    const msRange = new Date(max).getTime() - new Date(min).getTime()
    const dayRange = Math.ceil(msRange / (1000 * 60 * 60 * 24))
    return { minDate: min, maxDate: max, dateRange: dayRange }
  }, [features])

  const [range, setRange] = useState<[number, number]>([0, 100])
  const [isActive, setIsActive] = useState(false)

  // Reset when features change
  useEffect(() => {
    setRange([0, 100])
    setIsActive(false)
    onFilterChange(null, null)
  }, [features])

  const pctToDate = useCallback((pct: number): string => {
    if (!minDate) return ''
    const minMs = new Date(minDate).getTime()
    const maxMs = new Date(maxDate).getTime()
    const ms = minMs + (pct / 100) * (maxMs - minMs)
    return new Date(ms).toISOString().split('T')[0]
  }, [minDate, maxDate])

  const startLabel = pctToDate(range[0])
  const endLabel = pctToDate(range[1])

  // Count visible features
  const visibleCount = useMemo(() => {
    if (!isActive) return features.length
    return features.filter(f => {
      const d = f.properties?.observed_at
      if (!d || d === 'None') return false
      return d >= startLabel && d <= endLabel
    }).length
  }, [features, isActive, startLabel, endLabel])

  const handleLeftChange = (val: number) => {
    const newRange: [number, number] = [Math.min(val, range[1] - 1), range[1]]
    setRange(newRange)
    if (!isActive) setIsActive(true)
    onFilterChange(pctToDate(newRange[0]), pctToDate(newRange[1]))
  }

  const handleRightChange = (val: number) => {
    const newRange: [number, number] = [range[0], Math.max(val, range[0] + 1)]
    setRange(newRange)
    if (!isActive) setIsActive(true)
    onFilterChange(pctToDate(newRange[0]), pctToDate(newRange[1]))
  }

  const handleReset = () => {
    setRange([0, 100])
    setIsActive(false)
    onFilterChange(null, null)
  }

  if (!minDate || dateRange < 2) return null

  // Year ticks
  const startYear = new Date(minDate).getFullYear()
  const endYear = new Date(maxDate).getFullYear()
  const yearTicks: { year: number; pct: number }[] = []
  for (let y = startYear; y <= endYear; y++) {
    const ms = new Date(`${y}-01-01`).getTime()
    const minMs = new Date(minDate).getTime()
    const maxMs = new Date(maxDate).getTime()
    const pct = ((ms - minMs) / (maxMs - minMs)) * 100
    if (pct >= 0 && pct <= 100) yearTicks.push({ year: y, pct })
  }

  return (
    <div className={`timeline-slider${isActive ? ' active' : ''}`}>
      <div className="timeline-header">
        <span className="timeline-title">Timeline</span>
        <span className="timeline-range">
          {isActive ? `${startLabel} — ${endLabel}` : `${minDate} — ${maxDate}`}
        </span>
        <span className="timeline-count">{visibleCount} / {features.length}</span>
        {isActive && (
          <button className="timeline-reset" onClick={handleReset} title="Show all dates">Reset</button>
        )}
      </div>
      <div className="timeline-track">
        <div className="timeline-ticks">
          {yearTicks.map(t => (
            <div key={t.year} className="timeline-tick" style={{ left: `${t.pct}%` }}>
              <span className="timeline-tick-label">{t.year}</span>
            </div>
          ))}
        </div>
        <div
          className="timeline-highlight"
          style={{ left: `${range[0]}%`, width: `${range[1] - range[0]}%` }}
        />
        <input
          type="range"
          min={0}
          max={100}
          step={0.5}
          value={range[0]}
          onChange={e => handleLeftChange(Number(e.target.value))}
          className="timeline-input timeline-left"
        />
        <input
          type="range"
          min={0}
          max={100}
          step={0.5}
          value={range[1]}
          onChange={e => handleRightChange(Number(e.target.value))}
          className="timeline-input timeline-right"
        />
      </div>
    </div>
  )
}
