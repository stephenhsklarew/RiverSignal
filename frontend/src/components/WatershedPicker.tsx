import { useEffect, useMemo, useRef, useState } from 'react'
import type { Site } from '../pages/MapPage'
import './WatershedPicker.css'

interface WatershedPickerProps {
  sites: Site[]
  selectedSite: string | null
  onSelectSite: (watershed: string | null) => void
}

/** Watershed → US state. Drives the state → watershed drill-down. */
const WATERSHED_STATES: Record<string, string> = {
  mckenzie: 'Oregon',
  deschutes: 'Oregon',
  metolius: 'Oregon',
  klamath: 'Oregon',
  johnday: 'Oregon',
  skagit: 'Washington',
  green_river: 'Utah',
  shenandoah: 'Virginia',
  mad_river_oh: 'Ohio',
  ipswich_river_ma: 'Massachusetts',
}

const stateOf = (watershed: string) => WATERSHED_STATES[watershed] || 'Other'
const shortName = (name: string) => name.replace(' River', '').replace('Upper ', '')

export default function WatershedPicker({ sites, selectedSite, onSelectSite }: WatershedPickerProps) {
  const [open, setOpen] = useState(false)
  const [hoverState, setHoverState] = useState<string | null>(null)
  const rootRef = useRef<HTMLDivElement>(null)

  // Group sites by state, each list sorted by name; states sorted alphabetically.
  const byState = useMemo(() => {
    const groups = new Map<string, Site[]>()
    for (const s of sites) {
      const st = stateOf(s.watershed)
      if (!groups.has(st)) groups.set(st, [])
      groups.get(st)!.push(s)
    }
    for (const list of groups.values()) list.sort((a, b) => a.name.localeCompare(b.name))
    return [...groups.entries()].sort((a, b) => a[0].localeCompare(b[0]))
  }, [sites])

  const selected = selectedSite ? sites.find(s => s.watershed === selectedSite) : null
  const selectedState = selected ? stateOf(selected.watershed) : null

  // Close on outside click.
  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  const toggle = () => {
    setHoverState(selectedState)
    setOpen(o => !o)
  }

  const pickWatershed = (ws: string) => {
    onSelectSite(ws)
    setOpen(false)
  }

  const showAll = () => {
    onSelectSite(null)
    setOpen(false)
  }

  const activeState = hoverState ?? selectedState
  const activeStateSites = activeState ? byState.find(([st]) => st === activeState)?.[1] ?? [] : []

  return (
    <div className="wp" ref={rootRef}>
      <button className="wp-pill" onClick={toggle} aria-expanded={open} aria-haspopup="true">
        <span className={`wp-pin${selected ? ' is-selected' : ''}`}>{selected ? '◆' : '◇'}</span>
        {selected ? (
          <span><span className="wp-pill-state">{selectedState} · </span><b>{shortName(selected.name)}</b></span>
        ) : (
          <span className="wp-pill-all">All rivers</span>
        )}
        <span className="wp-caret">▾</span>
      </button>

      {open && (
        <div className="wp-panel">
          <div className="wp-cols">
            <div className="wp-col wp-states">
              <h4>State</h4>
              {byState.map(([st, list]) => (
                <button
                  key={st}
                  className={`wp-state${st === activeState ? ' active' : ''}`}
                  onMouseEnter={() => setHoverState(st)}
                  onClick={() => setHoverState(st)}
                >
                  <span>{st}</span>
                  <span className="wp-count">{list.length}</span>
                </button>
              ))}
            </div>
            <div className="wp-col wp-ws">
              <h4>Watershed</h4>
              {activeState === null ? (
                <div className="wp-hint">Pick a state to see its rivers.</div>
              ) : (
                activeStateSites.map(s => (
                  <button
                    key={s.watershed}
                    className={`wp-river${s.watershed === selectedSite ? ' active' : ''}`}
                    onClick={() => pickWatershed(s.watershed)}
                  >
                    {shortName(s.name)}
                  </button>
                ))
              )}
            </div>
          </div>
          <button className="wp-all" onClick={showAll}>◇ Show all rivers</button>
        </div>
      )}
    </div>
  )
}
