/**
 * TailwaterSafetyCard — static dam-release safety banner for dam-controlled
 * tailwaters (Phase A). Renders ABOVE the Go Score on watersheds that have a
 * dam-safety config. It is intentionally data-INDEPENDENT: it always shows the
 * caution and routes anglers to the authoritative USACE schedule + siren, so it
 * can never give false "all-clear" confidence.
 *
 * Phase B (deferred — RiverSignal-c8155522 /
 * docs/helix/02-design/plan-2026-06-04-chattahoochee-dam-release-safety.md) will
 * upgrade this into a live release-status state machine fed by the
 * usace_sam_hydropower adapter, with a stale-data fail-safe back to this static
 * caution.
 */

interface DamSafetyConfig {
  dam: string
  blurb: string
  scheduleUrl: string
  scheduleLabel: string
  forecastUrl?: string
  forecastLabel?: string
}

// Keyed by watershed slug. Add an entry when onboarding another dam-controlled
// tailwater so the component is reusable (no per-watershed code).
const DAM_SAFETY: Record<string, DamSafetyConfig> = {
  chattahoochee: {
    dam: 'Buford Dam',
    blurb:
      'Buford Dam controls this water. Hydropower releases raise the river 2–4 ft ' +
      'within minutes, often with only a siren/horn for warning. Check the official ' +
      'release schedule and listen for the siren before you wade or float.',
    scheduleUrl: 'https://water.sam.usace.army.mil/buford.htm',
    scheduleLabel: 'USACE Buford release schedule',
    forecastUrl: 'https://www.weather.gov/serfc/inflows_cmmg1',
    forecastLabel: 'SERFC inflow forecast',
  },
}

export function hasDamSafety(watershed: string | null | undefined): boolean {
  return !!watershed && watershed in DAM_SAFETY
}

export default function TailwaterSafetyCard({ watershed }: { watershed: string }) {
  const cfg = DAM_SAFETY[watershed]
  if (!cfg) return null
  return (
    <section
      role="alert"
      aria-label={`${cfg.dam} release safety warning`}
      style={{
        background: '#fff7e6',
        border: '1px solid #e0a000',
        borderLeft: '5px solid #e0a000',
        borderRadius: 10,
        padding: '12px 14px',
        margin: '12px 0',
        color: '#5a4300',
      }}
    >
      <div style={{ fontWeight: 700, marginBottom: 4 }}>⚠️ {cfg.dam} controls this water</div>
      <div style={{ fontSize: 14, lineHeight: 1.4 }}>{cfg.blurb}</div>
      <div style={{ marginTop: 8, display: 'flex', flexWrap: 'wrap', gap: 12 }}>
        <a href={cfg.scheduleUrl} target="_blank" rel="noopener noreferrer"
           style={{ fontWeight: 600, color: '#9a5b00' }}>
          {cfg.scheduleLabel} →
        </a>
        {cfg.forecastUrl && (
          <a href={cfg.forecastUrl} target="_blank" rel="noopener noreferrer"
             style={{ fontWeight: 600, color: '#9a5b00' }}>
            {cfg.forecastLabel} →
          </a>
        )}
      </div>
    </section>
  )
}
