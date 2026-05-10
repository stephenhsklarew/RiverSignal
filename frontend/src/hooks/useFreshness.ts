import { useEffect, useState } from 'react'
import { API_BASE } from '../config'

export type FreshnessStatus = 'fresh' | 'stale' | 'very_stale' | 'unknown'

export interface SourceFreshness {
  last_sync: string | null
  hours_ago: number | null
  status: FreshnessStatus
  label: string
  expected_cadence_hours: number
}

interface FreshnessResponse {
  sources: Record<string, SourceFreshness>
  as_of: string
}

const SOURCE_LABELS: Record<string, string> = {
  inaturalist: 'iNaturalist',
  usgs: 'USGS gauges',
  snotel: 'NRCS SNOTEL',
  fishing: 'ODFW fishing',
  wqp: 'EPA Water Quality Portal',
  wqp_bugs: 'WQP macroinvertebrates',
  biodata: 'USGS BioData',
  pbdb: 'Paleobiology DB',
  idigbio: 'iDigBio',
  gbif: 'GBIF',
  recreation: 'USFS / OSMB recreation',
  prism: 'PRISM climate',
  restoration: 'OWRI / NOAA / PCSRF',
  streamnet: 'StreamNet',
  macrostrat: 'Macrostrat',
  blm_sma: 'BLM lands',
  dogami: 'DOGAMI',
  mrds: 'USGS MRDS',
  mtbs: 'MTBS fire',
  fish_barrier: 'Fish passage barriers',
  deq_303d: 'EPA 303(d)',
  washington: 'Washington state',
  utah: 'Utah state',
  wbd: 'USGS WBD',
  nhdplus: 'NHDPlus',
  nwi: 'National Wetlands Inventory',
}

let cached: FreshnessResponse | null = null
let inFlight: Promise<FreshnessResponse | null> | null = null

async function fetchFreshness(): Promise<FreshnessResponse | null> {
  if (cached) return cached
  if (inFlight) return inFlight
  inFlight = fetch(`${API_BASE}/data-status/freshness`)
    .then(r => (r.ok ? r.json() : null))
    .then((data: FreshnessResponse | null) => {
      cached = data
      inFlight = null
      return data
    })
    .catch(() => {
      inFlight = null
      return null
    })
  return inFlight
}

/** Hook: returns the freshness map (loaded once per session). */
export function useFreshness(): FreshnessResponse | null {
  const [data, setData] = useState<FreshnessResponse | null>(cached)
  useEffect(() => {
    if (cached) {
      if (data !== cached) setData(cached)
      return
    }
    let mounted = true
    fetchFreshness().then(d => {
      if (mounted) setData(d)
    })
    return () => { mounted = false }
  }, [])
  return data
}

/** Pretty-print a source identifier for the tooltip popup. */
export function sourceLabel(src: string): string {
  return SOURCE_LABELS[src] || src
}

/**
 * Combine multiple source statuses — worst wins. Order: very_stale > stale >
 * unknown > fresh. If no source matches, returns 'unknown'.
 */
export function rollupStatus(
  data: FreshnessResponse | null,
  sources: string[],
): FreshnessStatus {
  if (!data || sources.length === 0) return 'unknown'
  const order: FreshnessStatus[] = ['fresh', 'unknown', 'stale', 'very_stale']
  let worst: FreshnessStatus = 'fresh'
  let any = false
  for (const s of sources) {
    const entry = data.sources[s]
    if (!entry) continue
    any = true
    if (order.indexOf(entry.status) > order.indexOf(worst)) worst = entry.status
  }
  return any ? worst : 'unknown'
}

/**
 * Roll up a single representative age label across multiple sources — the
 * oldest age wins (consistent with the worst-status rollup). Returns null
 * when no source has data yet.
 */
export function rollupAgeLabel(
  data: FreshnessResponse | null,
  sources: string[],
): string | null {
  if (!data || sources.length === 0) return null
  let worstHours = -1
  let worstLabel: string | null = null
  for (const s of sources) {
    const entry = data.sources[s]
    if (!entry || entry.hours_ago == null) continue
    if (entry.hours_ago > worstHours) {
      worstHours = entry.hours_ago
      worstLabel = entry.label
    }
  }
  return worstLabel
}
