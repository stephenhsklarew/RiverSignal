import { useState } from 'react'
import './CardSettings.css'

export interface CardConfig {
  id: string
  label: string
  icon: string
  visible: boolean
}

const STORAGE_KEY = 'riverpath-card-settings'

// Default card order and visibility
const DEFAULT_CARDS: CardConfig[] = [
  { id: 'river_replay', label: 'River Replay — What Changed', icon: '🔄', visible: true },
  { id: 'catch_probability', label: 'Catch Probability', icon: '🎯', visible: true },
  { id: 'species_spotter', label: 'Likely Sightings Today', icon: '👀', visible: true },
  { id: 'campfire_story', label: 'Campfire Story', icon: '🔥', visible: true },
  { id: 'current_activity', label: 'Current Activity Cards', icon: '📊', visible: true },
  { id: 'fish_present', label: 'Fish Present', icon: '🐟', visible: true },
  { id: 'barriers', label: 'Fish Passage Barriers', icon: '⚠', visible: true },
  { id: 'time_machine', label: 'Time Machine — Species', icon: '🕰️', visible: true },
  { id: 'compare_rivers', label: 'Compare Rivers', icon: '⚖️', visible: true },
  { id: 'weather', label: 'Weather Forecast', icon: '🌤', visible: true },
  { id: 'snowpack', label: 'Snowpack & Mountain', icon: '❄', visible: true },
  { id: 'stocking', label: 'Fish Stocking', icon: '🐟', visible: true },
  { id: 'whats_here', label: "What's Here Now", icon: '🌿', visible: true },
  { id: 'nearby_access', label: 'Nearby Access', icon: '📍', visible: true },
]

export function loadCardSettings(): CardConfig[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_CARDS
    const saved: CardConfig[] = JSON.parse(raw)
    // Merge with defaults to handle new cards added after save
    const savedMap = new Map(saved.map(c => [c.id, c]))
    const merged: CardConfig[] = []
    // Keep saved order for known cards
    for (const s of saved) {
      const def = DEFAULT_CARDS.find(d => d.id === s.id)
      if (def) merged.push({ ...def, visible: s.visible })
    }
    // Append any new cards not in saved
    for (const d of DEFAULT_CARDS) {
      if (!savedMap.has(d.id)) merged.push(d)
    }
    return merged
  } catch {
    return DEFAULT_CARDS
  }
}

function saveCardSettings(cards: CardConfig[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(cards.map(c => ({ id: c.id, visible: c.visible }))))
}

export function CardSettingsPanel({ cards, onChange, onClose }: {
  cards: CardConfig[]; onChange: (cards: CardConfig[]) => void; onClose: () => void
}) {
  const [local, setLocal] = useState<CardConfig[]>(cards)

  const toggle = (id: string) => {
    setLocal(prev => prev.map(c => c.id === id ? { ...c, visible: !c.visible } : c))
  }

  const move = (index: number, dir: -1 | 1) => {
    const target = index + dir
    if (target < 0 || target >= local.length) return
    const next = [...local]
    ;[next[index], next[target]] = [next[target], next[index]]
    setLocal(next)
  }

  const apply = () => {
    saveCardSettings(local)
    onChange(local)
    onClose()
  }

  const reset = () => {
    const fresh = [...DEFAULT_CARDS]
    setLocal(fresh)
    saveCardSettings(fresh)
    onChange(fresh)
    onClose()
  }

  return (
    <div className="card-settings-overlay" onClick={onClose}>
      <div className="card-settings-modal" onClick={e => e.stopPropagation()}>
        <div className="card-settings-header">
          <span>Customize River Now</span>
          <button className="card-settings-close" onClick={onClose}>✕</button>
        </div>
        <p className="card-settings-hint">Toggle cards on/off and reorder with arrows.</p>

        <div className="card-settings-list">
          {local.map((card, i) => (
            <div key={card.id} className={`card-settings-item${card.visible ? '' : ' hidden'}`}>
              <div className="card-settings-arrows">
                <button disabled={i === 0} onClick={() => move(i, -1)}>↑</button>
                <button disabled={i === local.length - 1} onClick={() => move(i, 1)}>↓</button>
              </div>
              <span className="card-settings-icon">{card.icon}</span>
              <span className="card-settings-label">{card.label}</span>
              <button className={`card-settings-toggle${card.visible ? ' on' : ''}`} onClick={() => toggle(card.id)}>
                {card.visible ? 'ON' : 'OFF'}
              </button>
            </div>
          ))}
        </div>

        <div className="card-settings-actions">
          <button className="card-settings-reset" onClick={reset}>Reset to Default</button>
          <button className="card-settings-apply" onClick={apply}>Apply</button>
        </div>
      </div>
    </div>
  )
}
