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
      >
        ⓘ
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
