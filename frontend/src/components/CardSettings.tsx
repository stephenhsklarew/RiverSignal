import { useState } from 'react'
import './CardSettings.css'

export interface CardConfig {
  id: string
  label: string
  icon: string
  visible: boolean
}

// ── RiverPath defaults ──
const RIVERPATH_STORAGE_KEY = 'riverpath-card-settings'

const RIVERPATH_DEFAULT_CARDS: CardConfig[] = [
  { id: 'river_replay', label: 'River Replay — What Changed', icon: '🔄', visible: true },
  { id: 'catch_probability', label: 'Catch Probability', icon: '🎯', visible: true },
  { id: 'species_spotter', label: 'Likely Sightings Today', icon: '👀', visible: true },
  { id: 'campfire_story', label: 'River Story', icon: '🔥', visible: true },
  { id: 'current_activity', label: 'Current Activity Cards', icon: '📊', visible: true },
  { id: 'fish_present', label: 'Fish Present', icon: '🐟', visible: true },
  { id: 'barriers', label: 'Fish Passage Barriers', icon: '⚠', visible: true },
  { id: 'fly_shops', label: 'Fly Shops & Guides', icon: '🏪', visible: true },
  { id: 'time_machine', label: 'Time Machine — Species', icon: '🕰️', visible: true },
  { id: 'compare_rivers', label: 'Compare Rivers', icon: '⚖️', visible: true },
  { id: 'weather', label: 'Weather Forecast', icon: '🌤', visible: true },
  { id: 'snowpack', label: 'Snowpack & Mountain', icon: '❄', visible: true },
  { id: 'stocking', label: 'Fish Stocking', icon: '🐟', visible: true },
  { id: 'whats_here', label: "What's Here Now", icon: '🌿', visible: true },
  { id: 'nearby_access', label: 'Nearby Access', icon: '📍', visible: true },
]

// ── DeepTrail defaults ──
const DEEPTRAIL_STORAGE_KEY = 'deeptrail-card-settings'

export const DEEPTRAIL_DEFAULT_CARDS: CardConfig[] = [
  { id: 'deep_time_story', label: 'Deep Time Story', icon: '📖', visible: true },
  { id: 'kid_quiz', label: 'Kid Quiz Mode', icon: '🧩', visible: true },
  { id: 'ask_place', label: 'Ask About This Place', icon: '💬', visible: true },
  { id: 'geologic_context', label: 'Geologic Context', icon: '🪨', visible: true },
  { id: 'cross_domain', label: 'Why This River?', icon: '🌋', visible: true },
  { id: 'formation_explorer', label: 'Formation Explorer', icon: '🗺️', visible: true },
  { id: 'legal_collecting', label: 'Legal Collecting Status', icon: '⚖️', visible: true },
  { id: 'deep_time_timeline', label: 'Deep Time Timeline', icon: '🕰️', visible: true },
  { id: 'compare_eras', label: 'Compare Eras', icon: '⚖️', visible: true },
  { id: 'fossils_nearby', label: 'Fossils Found Nearby', icon: '🦴', visible: true },
  { id: 'minerals_nearby', label: 'Mineral Sites Nearby', icon: '💎', visible: true },
  { id: 'mineral_shops', label: 'Mineral Shops Nearby', icon: '🏪', visible: true },
  { id: 'living_river', label: 'Living River Link', icon: '🐟', visible: true },
]

// ── Generic loader ──
export function loadCardSettingsGeneric(storageKey: string, defaults: CardConfig[]): CardConfig[] {
  try {
    const raw = localStorage.getItem(storageKey)
    if (!raw) return defaults
    const saved: CardConfig[] = JSON.parse(raw)
    const savedMap = new Map(saved.map(c => [c.id, c]))
    const merged: CardConfig[] = []
    for (const s of saved) {
      const def = defaults.find(d => d.id === s.id)
      if (def) merged.push({ ...def, visible: s.visible })
    }
    for (const d of defaults) {
      if (!savedMap.has(d.id)) merged.push(d)
    }
    return merged
  } catch {
    return defaults
  }
}

function saveCardSettingsGeneric(storageKey: string, cards: CardConfig[]) {
  localStorage.setItem(storageKey, JSON.stringify(cards.map(c => ({ id: c.id, visible: c.visible }))))
}

// ── RiverPath convenience (backwards compat) ──
export function loadCardSettings(): CardConfig[] {
  return loadCardSettingsGeneric(RIVERPATH_STORAGE_KEY, RIVERPATH_DEFAULT_CARDS)
}

// ── DeepTrail convenience ──
export function loadDeepTrailCardSettings(): CardConfig[] {
  return loadCardSettingsGeneric(DEEPTRAIL_STORAGE_KEY, DEEPTRAIL_DEFAULT_CARDS)
}

// ── Reusable settings panel ──
export function CardSettingsPanel({ cards, onChange, onClose, storageKey, defaults, title, dark }: {
  cards: CardConfig[]
  onChange: (cards: CardConfig[]) => void
  onClose: () => void
  storageKey?: string
  defaults?: CardConfig[]
  title?: string
  dark?: boolean
}) {
  const key = storageKey || RIVERPATH_STORAGE_KEY
  const defs = defaults || RIVERPATH_DEFAULT_CARDS
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
    saveCardSettingsGeneric(key, local)
    onChange(local)
    onClose()
  }

  const reset = () => {
    const fresh = [...defs]
    setLocal(fresh)
    saveCardSettingsGeneric(key, fresh)
    onChange(fresh)
    onClose()
  }

  return (
    <div className="card-settings-overlay" onClick={onClose}>
      <div className={`card-settings-modal${dark ? ' dark' : ''}`} onClick={e => e.stopPropagation()}>
        <div className="card-settings-header">
          <span>{title || 'Customize'}</span>
          <button className="card-settings-close" onClick={onClose}>✕</button>
        </div>
        <p className="card-settings-hint">Toggle sections on/off and reorder with arrows.</p>

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
