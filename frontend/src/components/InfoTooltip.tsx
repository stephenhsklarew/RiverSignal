import { useState } from 'react'
import { createPortal } from 'react-dom'
import { useFreshness, sourceLabel, type FreshnessStatus } from '../hooks/useFreshness'
import './InfoTooltip.css'

interface InfoTooltipProps {
  text: string
  dark?: boolean
  /** Source identifiers (e.g., 'usgs', 'snotel') for the per-source freshness list in the popup. */
  sources?: string | string[]
}

const STATUS_CLASS: Record<FreshnessStatus, string> = {
  fresh: 'fresh',
  stale: 'stale',
  very_stale: 'very_stale',
  unknown: 'unknown',
}

export default function InfoTooltip({ text, dark, sources }: InfoTooltipProps) {
  const [open, setOpen] = useState(false)
  const freshness = useFreshness()

  const sourceList = sources ? (Array.isArray(sources) ? sources : [sources]) : []

  return (
    <>
      <span className="info-tooltip-wrap">
        <button
          className={`info-tooltip-btn ${dark ? 'dark' : ''}`}
          onClick={(e) => { e.stopPropagation(); setOpen(true) }}
          title="How this works"
          aria-label="How this works"
        >
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.4" />
            <circle cx="8" cy="4.6" r="0.95" fill="currentColor" />
            <rect x="7.05" y="6.6" width="1.9" height="5.4" rx="0.6" fill="currentColor" />
          </svg>
        </button>
      </span>

      {open && createPortal(
        <div className="info-tooltip-overlay" onClick={() => setOpen(false)}>
          <div className={`info-tooltip-card ${dark ? 'dark' : ''}`} onClick={e => e.stopPropagation()}>
            <div className="info-tooltip-header">
              <span>How this works</span>
              <button className="info-tooltip-close" onClick={() => setOpen(false)}>✕</button>
            </div>
            <p className="info-tooltip-text">{text}</p>
            {sourceList.length > 0 && freshness && (
              <div className="info-tooltip-sources">
                {sourceList.map(src => {
                  const entry = freshness.sources[src]
                  const label = sourceLabel(src)
                  if (!entry) {
                    return (
                      <div key={src} className="info-tooltip-source-row">
                        <span className={`info-tooltip-dot ${STATUS_CLASS.unknown}`} />
                        <span className="info-tooltip-source-name">{label}</span>
                        <span className="info-tooltip-source-age">—</span>
                      </div>
                    )
                  }
                  return (
                    <div key={src} className="info-tooltip-source-row">
                      <span className={`info-tooltip-dot ${STATUS_CLASS[entry.status]}`} />
                      <span className="info-tooltip-source-name">{label}</span>
                      <span className="info-tooltip-source-age">{entry.label}</span>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>,
        document.body
      )}
    </>
  )
}
