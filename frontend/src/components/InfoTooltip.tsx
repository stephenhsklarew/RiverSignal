import { useState } from 'react'
import './InfoTooltip.css'

interface InfoTooltipProps {
  text: string
  dark?: boolean
}

export default function InfoTooltip({ text, dark }: InfoTooltipProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
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

      {open && (
        <div className="info-tooltip-overlay" onClick={() => setOpen(false)}>
          <div className={`info-tooltip-card ${dark ? 'dark' : ''}`} onClick={e => e.stopPropagation()}>
            <div className="info-tooltip-header">
              <span>How this works</span>
              <button className="info-tooltip-close" onClick={() => setOpen(false)}>✕</button>
            </div>
            <p className="info-tooltip-text">{text}</p>
          </div>
        </div>
      )}
    </>
  )
}
