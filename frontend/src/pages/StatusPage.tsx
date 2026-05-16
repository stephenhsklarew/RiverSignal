import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { API_BASE } from '../config'
import lmLogo from '../assets/liquid-marble-logo.png'
import './StatusPage.css'

const API = API_BASE

// Static metadata about each pipeline adapter
const SOURCE_META: Record<string, { description: string; upstream: string; refresh: string; license?: string; commercial?: boolean }> = {
  inaturalist: { description: 'Citizen science species observations with photos', upstream: 'Continuous', refresh: 'Daily', license: 'CC BY-NC', commercial: false },
  usgs: { description: 'Stream gauge readings — flow, temperature, dissolved oxygen', upstream: 'Real-time (15 min)', refresh: 'Daily', license: 'Public Domain', commercial: true },
  snotel: { description: 'Snowpack, snow water equivalent, precipitation, air temp', upstream: 'Daily', refresh: 'Daily', license: 'Public Domain', commercial: true },
  prism: { description: 'Gridded climate normals — monthly temp and precipitation', upstream: 'Monthly', refresh: 'Monthly', license: 'Academic Free', commercial: false },
  biodata: { description: 'Professional macroinvertebrate and fish surveys (USGS)', upstream: 'Quarterly', refresh: 'Monthly', license: 'Public Domain', commercial: true },
  wqp_bugs: { description: 'Aquatic macroinvertebrate data from Water Quality Portal', upstream: 'Quarterly', refresh: 'Monthly', license: 'Public Domain', commercial: true },
  owdp: { description: 'Water chemistry — nutrients, pH, conductivity, turbidity', upstream: 'Monthly', refresh: 'Weekly', license: 'Public Domain', commercial: true },
  streamnet: { description: 'Salmon and steelhead abundance monitoring', upstream: 'Annually', refresh: 'Monthly', license: 'Public Domain', commercial: true },
  mtbs: { description: 'Fire burn severity perimeters (MTBS/NIFC)', upstream: 'Annually', refresh: 'Quarterly', license: 'Public Domain', commercial: true },
  nhdplus: { description: 'Stream flowlines, river miles, drainage network', upstream: 'Static', refresh: 'Annually', license: 'Public Domain', commercial: true },
  restoration: { description: 'Restoration projects — OWRI, NOAA, PCSRF', upstream: 'Quarterly', refresh: 'Monthly', license: 'Public Domain', commercial: true },
  fish_barrier: { description: 'Fish passage barriers with passage status', upstream: 'Annually', refresh: 'Quarterly', license: 'Public Domain', commercial: true },
  fishing: { description: 'ODFW sport catch, harvest trends, stocking schedule', upstream: 'Monthly', refresh: 'Weekly', license: 'Public Records', commercial: true },
  deq_303d: { description: 'EPA 303(d) impaired waters — temperature, nutrients', upstream: 'Biennial', refresh: 'Quarterly', license: 'Public Domain', commercial: true },
  nwi: { description: 'National Wetlands Inventory — wetland polygons and types', upstream: 'Static', refresh: 'Annually', license: 'Public Domain', commercial: true },
  wbd: { description: 'USGS watershed boundaries (HUC)', upstream: 'Static', refresh: 'Annually', license: 'Public Domain', commercial: true },
  macrostrat: { description: 'Geologic units — rock type, age, formation, lithology', upstream: 'Rarely', refresh: 'Annually', license: 'CC BY 4.0', commercial: true },
  pbdb: { description: 'Paleobiology Database — fossil occurrences with taxonomy', upstream: 'Weekly', refresh: 'Monthly', license: 'CC BY 4.0', commercial: true },
  idigbio: { description: 'Museum fossil specimen records', upstream: 'Monthly', refresh: 'Monthly', license: 'Varies', commercial: false },
  gbif: { description: 'GBIF fossil specimens with images from global museums', upstream: 'Weekly', refresh: 'Monthly', license: 'Varies (CC0/BY/BY-NC)', commercial: false },
  blm_sma: { description: 'BLM land ownership and collecting legality', upstream: 'Annually', refresh: 'Quarterly', license: 'Public Domain', commercial: true },
  dogami: { description: 'Oregon geology polygons (DOGAMI/OGDC)', upstream: 'Rarely', refresh: 'Annually', license: 'Public Records', commercial: true },
  mrds: { description: 'USGS mineral deposit locations — commodity, status', upstream: 'Rarely', refresh: 'Annually', license: 'Public Domain', commercial: true },
  recreation: { description: 'USFS campgrounds/trailheads + OSMB boat ramps', upstream: 'Seasonally', refresh: 'Monthly', license: 'Public Domain', commercial: true },
  washington: { description: 'Washington state data — WDFW SalmonScape, stocking, WA DNR geology, SRFB restoration, WA parks, water access', upstream: 'Varies', refresh: 'Monthly', license: 'Public Domain', commercial: true },
  utah: { description: 'Utah state data — UDWR fish stocking, special-regulation streams (Green River basin)', upstream: 'Varies', refresh: 'Weekly', license: 'Public Records (Utah GRAMA)', commercial: true },
  virginia: { description: 'Virginia state data — VA DWR weekly trout stocking, fishing regulations, VGS (DGMR) geology, VA DCR state parks', upstream: 'Weekly', refresh: 'Weekly', license: 'Public Records (VA Code §2.2-3700)', commercial: true },
  west_virginia: { description: 'West Virginia state data — WV DNR stocked-trout-streams registry, regulations, WVGES geology, WV state parks', upstream: 'Varies', refresh: 'Weekly', license: 'Public Records (WV Code §29B-1)', commercial: true },
  nws: { description: 'National Weather Service observations (daily roll-ups per watershed gridpoint)', upstream: 'Daily', refresh: 'Daily', license: 'Public Domain', commercial: true },
  nws_forecast: { description: 'NWS 7-day weather forecast captured daily per watershed', upstream: 'Hourly', refresh: 'Daily', license: 'Public Domain', commercial: true },
}

const BRONZE_DESCRIPTIONS: Record<string, string> = {
  observations: 'Species observations from iNaturalist, BioData, WQP, and other sources',
  time_series: 'Sensor readings: stream gauges, snowpack, climate, water chemistry',
  interventions: 'Restoration projects with outcomes from OWRI, NOAA, PCSRF',
  fire_perimeters: 'Wildfire burn perimeters from MTBS/NIFC',
  stream_flowlines: 'NHDPlus HR stream network with river mile references',
  impaired_waters: 'EPA 303(d) listed impaired stream segments',
  wetlands: 'National Wetlands Inventory polygons',
  watershed_boundaries: 'USGS HUC watershed boundary polygons',
  geologic_units: 'Rock formations from Macrostrat + DOGAMI with age and lithology',
  fossil_occurrences: 'Fossil specimens from PBDB, iDigBio, and GBIF — 99.5% with images (specimen photos, Wikimedia, PhyloPic)',
  mineral_deposits: 'USGS MRDS mineral deposit locations',
  land_ownership: 'BLM Surface Management Agency land parcels',
  recreation_sites: 'Campgrounds, trailheads, boat ramps from USFS + OSMB',
  curated_hatch_chart: 'Expert fly fishing hatch timing data (manually curated)',
  deep_time_stories: 'Cached AI-generated deep time narratives',
  rockhounding_sites: 'Oregon rockhounding locations — thundereggs, agates, obsidian, sunstone, opal, petrified wood',
  river_stories: 'Pre-cached AI-generated ecological narratives at 3 reading levels per watershed',
  wa_salmonscape: 'WDFW SalmonScape fish species distribution — all 5 Pacific salmon, steelhead, bull trout',
  wa_fish_stocking: 'WDFW fish stocking/planting releases by county, species, and date',
  wa_surface_geology: 'WA DNR 100K surface geology map units with formation labels',
  wa_srfb_projects: 'Salmon Recovery Funding Board restoration projects with funding and status',
  wa_state_parks: 'Washington State Parks boundaries, boat launches, and recreation facilities',
}

const SILVER_DESCRIPTIONS: Record<string, string> = {
  species_observations: 'Unified species observations across all sources with taxonomy',
  water_conditions: 'Standardized water/climate time series with normalized parameters',
  interventions_enriched: 'Restoration records with standardized categories and sites',
  geologic_context: 'Standardized geologic unit metadata with geometry',
  fossil_records: 'Cleaned fossil records with age midpoints, specimen images, and MorphoSource 3D links',
  land_access: 'Land ownership with collecting status and rules',
  mineral_sites: 'Mineral deposits with normalized commodity names and representative images',
}

const GOLD_DESCRIPTIONS: Record<string, string> = {
  anomaly_flags: 'Temperature and dissolved oxygen exceedance alerts',
  aquatic_hatch_chart: 'Aquatic insect observations filtered to EPT + Diptera',
  cold_water_refuges: 'Thermal classification of stream stations',
  deep_time_story: 'Geologic narrative synthesis per formation',
  fishing_conditions: 'Monthly water conditions for angler decision support',
  formation_species_history: 'Fossil species found in each geologic formation',
  fossils_nearby: 'Fossil occurrences with distance, specimen photos (Smithsonian, Yale Peabody), and 3D models',
  geologic_age_at_location: 'Geologic unit metadata at survey coordinates',
  geology_watershed_link: 'Geologic units within watershed boundaries',
  harvest_trends: 'Year-over-year sport catch with delta tracking',
  hatch_chart: 'Monthly insect observations with activity levels',
  hatch_fly_recommendations: 'Insect-to-fly-pattern matching',
  indicator_species_status: 'Presence/absence checklist of indicator species',
  invasive_detections: 'Invasive species tracker with trends',
  legal_collecting_sites: 'Public lands with permitted fossil/mineral collecting',
  mineral_sites_nearby: 'Mineral deposits with distance, commodity images from Wikimedia Commons',
  post_fire_recovery: 'Species trajectory pre/post fire events',
  restoration_outcomes: 'Before/after species counts at intervention sites',
  river_health_score: 'Composite monthly health score (0-100)',
  river_miles: 'Stream segments with river mile references',
  river_story_timeline: 'Multi-event watershed timeline',
  seasonal_observation_patterns: 'Monthly observation patterns by taxonomic group',
  site_ecological_summary: 'Annual species richness per watershed',
  snowpack_current: 'Latest SNOTEL readings with 7-day trend and % of normal',
  species_by_reach: 'Fish distribution by stream reach (ODFW)',
  species_by_river_mile: 'Species observations grouped by 5-mile river sections',
  species_gallery: 'Photo gallery of observed species with conservation status',
  species_trends: 'Year-over-year species count deltas',
  stewardship_opportunities: 'Active restoration projects by category',
  stocking_schedule: 'Fish stocking events by waterbody',
  swim_safety: 'Water safety assessment by station and month',
  water_quality_monthly: 'Monthly water parameter aggregates',
  watershed_scorecard: 'Cross-watershed comparison metrics',
  whats_alive_now: 'Species observed in current month',
}

const ENRICHMENT_SOURCES: Record<string, { description: string; upstream: string; refresh: string }> = {
  idigbio_media: { description: 'Museum specimen photos resolved from iDigBio media records (Smithsonian, Yale Peabody, UO Condon)', upstream: 'Monthly', refresh: 'Monthly' },
  morphosource: { description: 'MorphoSource 3D fossil scans and CT imagery linked by taxon genus', upstream: 'Monthly', refresh: 'Monthly' },
  smithsonian_nmnh: { description: 'Smithsonian National Museum of Natural History specimen images (CC0)', upstream: 'Monthly', refresh: 'Monthly' },
  wikimedia_commons: { description: 'Representative fossil photographs from Wikimedia Commons matched by genus (CC-BY-SA)', upstream: 'Continuously', refresh: 'Monthly' },
  phylopic: { description: 'Taxonomic silhouette illustrations from PhyloPic matched by genus/family/class (CC0)', upstream: 'Monthly', refresh: 'Monthly' },
}

const LIVE_SOURCES = [
  { name: 'NWS Weather Forecast', description: '7-day weather forecast by watershed from api.weather.gov', upstream: 'Hourly', cache: '30 min' },
  { name: 'USGS Instantaneous Values', description: 'Real-time stream flow and water temperature', upstream: '15 minutes', cache: '15 min' },
  { name: 'BLM Land Ownership', description: 'Real-time point query for land agency and collecting legality', upstream: 'On-demand', cache: 'None' },
  { name: 'Anthropic Claude AI', description: 'LLM reasoning for river stories, campfire stories, deep time narration, species analysis', upstream: 'On-demand', cache: 'Disk' },
  { name: 'OpenAI TTS', description: 'Text-to-speech narration for campfire stories and deep time narratives (nova voice)', upstream: 'On-demand', cache: 'Disk' },
]

interface SourceInfo {
  source_type: string; description: string; upstream_frequency: string
  refresh_schedule: string; last_sync: string | null; status: string
  license?: string; commercial?: boolean
}

export default function StatusPage() {
  const [sources, setSources] = useState<SourceInfo[]>([])
  const [bronzeTables, setBronzeTables] = useState<Record<string, number>>({})
  const [silverTables, setSilverTables] = useState<Record<string, number>>({})
  const [goldTables, setGoldTables] = useState<Record<string, number>>({})
  const [curated, setCurated] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [totalRecords, setTotalRecords] = useState(0)

  useEffect(() => {
    document.title = 'Liquid Marble'
    return () => { document.title = 'River Signal' }
  }, [])

  // Keep --status-header-h in sync with the sticky header's actual height
  // so scroll-margin-top matches whatever it renders to (legend wrap, etc.).
  useEffect(() => {
    const root = document.documentElement
    const measure = () => {
      const header = document.querySelector('.status-header') as HTMLElement | null
      if (header) root.style.setProperty('--status-header-h', `${header.offsetHeight}px`)
    }
    measure()
    window.addEventListener('resize', measure)
    const observer = new ResizeObserver(measure)
    const header = document.querySelector('.status-header')
    if (header) observer.observe(header)
    return () => {
      window.removeEventListener('resize', measure)
      observer.disconnect()
    }
  }, [loading])

  useEffect(() => {
    fetch(`${API}/data-status`)
      .then(r => r.json())
      .then(data => {
        const syncMap: Record<string, { last_sync: string; failed: number }> = {}
        for (const p of (data.pipelines || [])) {
          syncMap[p.source] = { last_sync: p.last_sync, failed: p.failed }
        }

        setSources(Object.entries(SOURCE_META).map(([key, meta]) => ({
          source_type: key,
          description: meta.description,
          upstream_frequency: meta.upstream,
          refresh_schedule: meta.refresh,
          last_sync: syncMap[key]?.last_sync || null,
          status: syncMap[key] ? (syncMap[key].failed > 0 ? 'warning' : 'healthy') : 'unknown',
          license: meta.license,
          commercial: meta.commercial,
        })))

        setBronzeTables(data.bronze?.tables || {})
        setSilverTables(data.silver?.tables || {})
        setGoldTables(data.gold?.tables || {})
        setCurated(data.curated || [])

        const bt = data.bronze?.tables || {}
        setTotalRecords(Object.values(bt).reduce((a: number, b: any) => a + (b || 0), 0))
        setLoading(false)
      })
      .catch(() => setLoading(false))
  }, [])

  const now = new Date()
  function freshness(lastSync: string | null): { label: string; cls: string } {
    if (!lastSync) return { label: 'Never synced', cls: 'stale' }
    const days = (now.getTime() - new Date(lastSync).getTime()) / (1000 * 60 * 60 * 24)
    if (days < 1) return { label: `${Math.round(days * 24)}h ago`, cls: 'fresh' }
    if (days < 7) return { label: `${Math.round(days)}d ago`, cls: 'recent' }
    if (days < 30) return { label: `${Math.round(days)}d ago`, cls: 'aging' }
    return { label: `${Math.round(days)}d ago`, cls: 'stale' }
  }

  const enrichmentCount = Object.keys(ENRICHMENT_SOURCES).length
  const sourceCount = sources.length + enrichmentCount + LIVE_SOURCES.length + curated.length
  const viewCount = Object.keys(silverTables).length + Object.keys(goldTables).length

  return (
    <div className="status-page">
      <div className="status-header">
        <Link to="/" className="status-home-link" aria-label="Back to home">
          <img src={lmLogo} alt="Liquid Marble" className="status-logo" />
        </Link>
        <h1 className="status-title">Data Platform Status</h1>
        <Link to="/" className="status-back-link">← Back to home</Link>
        <nav className="status-toc" aria-label="Jump to section">
          <a href="#ingested">Ingested Sources</a>
          <a href="#enrichment">Enrichment Pipelines</a>
          <a href="#live">Live API Sources</a>
          <a href="#bronze">Bronze Layer</a>
          <a href="#silver">Silver Layer</a>
          <a href="#gold">Gold Layer</a>
          <a href="#curated">Curated Data</a>
        </nav>
        <div className="status-stats">
          <div className="status-stat">
            <span className="status-stat-value">{sourceCount}</span>
            <span className="status-stat-label">Data Sources</span>
          </div>
          <div className="status-stat">
            <span className="status-stat-value">{totalRecords.toLocaleString()}</span>
            <span className="status-stat-label">Total Records</span>
          </div>
          <div className="status-stat">
            <span className="status-stat-value">{viewCount}</span>
            <span className="status-stat-label">Materialized Views</span>
          </div>
          <div className="status-stat">
            <span className="status-stat-value">7</span>
            <span className="status-stat-label">Watersheds</span>
          </div>
        </div>
        <div className="status-legend">
          <span className="status-legend-item"><span className="status-badge healthy">healthy</span> Last sync completed successfully</span>
          <span className="status-legend-item"><span className="status-badge warning">warning</span> Last sync had some failures</span>
          <span className="status-legend-item"><span className="status-badge unknown">unknown</span> No sync record found</span>
          <span className="status-legend-item"><span className="status-badge live">live</span> Real-time API, not stored in database</span>
        </div>
      </div>

      {loading ? (
        <div className="status-loading">Loading pipeline status...</div>
      ) : (
        <>
          {/* ── Ingested Data Sources ── */}
          <section id="ingested" className="status-section">
            <h2>Ingested Data Sources ({sources.length})</h2>
            <div className="status-table-wrap">
              <table className="status-table">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Description</th>
                    <th>License</th>
                    <th>Upstream</th>
                    <th>Refresh</th>
                    <th>Last Synced</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {sources.map(s => {
                    const f = freshness(s.last_sync)
                    return (
                      <tr key={s.source_type}>
                        <td className="status-source">{s.source_type}</td>
                        <td className="status-desc">{s.description}</td>
                        <td className={`status-license ${s.commercial ? 'ok' : 'restricted'}`}>{s.license}</td>
                        <td className="status-freq">{s.upstream_frequency}</td>
                        <td className="status-freq">{s.refresh_schedule}</td>
                        <td className={`status-sync ${f.cls}`}>
                          {s.last_sync ? new Date(s.last_sync).toLocaleDateString() : '—'}
                          <span className="status-ago">{f.label}</span>
                        </td>
                        <td><span className={`status-badge ${s.status}`}>{s.status}</span></td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </section>

          {/* ── Enrichment Pipelines ── */}
          <section id="enrichment" className="status-section">
            <h2>Enrichment Pipelines ({enrichmentCount})</h2>
            <p className="status-layer-desc">Post-ingestion pipelines that resolve images, 3D models, and media from museum collections.</p>
            <div className="status-table-wrap">
              <table className="status-table">
                <thead>
                  <tr><th>Source</th><th>Description</th><th>Upstream</th><th>Refresh</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {Object.entries(ENRICHMENT_SOURCES).map(([key, meta]) => (
                    <tr key={key}>
                      <td className="status-source">{key}</td>
                      <td className="status-desc">{meta.description}</td>
                      <td className="status-freq">{meta.upstream}</td>
                      <td className="status-freq">{meta.refresh}</td>
                      <td><span className="status-badge healthy">healthy</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* ── Live API Sources ── */}
          <section id="live" className="status-section">
            <h2>Live API Sources ({LIVE_SOURCES.length})</h2>
            <div className="status-table-wrap">
              <table className="status-table">
                <thead>
                  <tr><th>Source</th><th>Description</th><th>Upstream</th><th>Cache TTL</th><th>Status</th></tr>
                </thead>
                <tbody>
                  {LIVE_SOURCES.map(s => (
                    <tr key={s.name}>
                      <td className="status-source">{s.name}</td>
                      <td className="status-desc">{s.description}</td>
                      <td className="status-freq">{s.upstream}</td>
                      <td className="status-freq">{s.cache}</td>
                      <td><span className="status-badge live">live</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* ── Bronze Tables ── */}
          <section id="bronze" className="status-section">
            <h2>Bronze Layer — Raw Ingested Tables ({Object.keys(bronzeTables).length})</h2>
            <p className="status-layer-desc">Raw data as received from upstream sources. Indexed by site, timestamp, and data source.</p>
            <div className="status-table-wrap">
              <table className="status-table">
                <thead>
                  <tr><th>Table</th><th>Description</th><th className="status-num-col">Records</th></tr>
                </thead>
                <tbody>
                  {Object.entries(bronzeTables).sort((a, b) => b[1] - a[1]).map(([name, count]) => (
                    <tr key={name}>
                      <td className="status-source">{name}</td>
                      <td className="status-desc">{BRONZE_DESCRIPTIONS[name] || ''}</td>
                      <td className="status-num">{count.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr>
                    <td colSpan={2} className="status-total-label">Total</td>
                    <td className="status-num status-total">{Object.values(bronzeTables).reduce((a, b) => a + b, 0).toLocaleString()}</td>
                  </tr>
                </tfoot>
              </table>
            </div>
          </section>

          {/* ── Silver Views ── */}
          <section id="silver" className="status-section">
            <h2>Silver Layer — Cleaned & Standardized Views ({Object.keys(silverTables).length})</h2>
            <p className="status-layer-desc">Unified, deduplicated, and normalized data across all sources.</p>
            <div className="status-table-wrap">
              <table className="status-table">
                <thead>
                  <tr><th>View</th><th>Description</th><th className="status-num-col">Records</th></tr>
                </thead>
                <tbody>
                  {Object.entries(silverTables).sort((a, b) => b[1] - a[1]).map(([name, count]) => (
                    <tr key={name}>
                      <td className="status-source">silver.{name}</td>
                      <td className="status-desc">{SILVER_DESCRIPTIONS[name] || ''}</td>
                      <td className="status-num">{count.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* ── Gold Views ── */}
          <section id="gold" className="status-section">
            <h2>Gold Layer — Business Aggregates ({Object.keys(goldTables).length})</h2>
            <p className="status-layer-desc">Feature-ready aggregations powering the RiverPath, DeepTrail, and RiverSignal apps.</p>
            <div className="status-table-wrap">
              <table className="status-table">
                <thead>
                  <tr><th>View</th><th>Description</th><th className="status-num-col">Records</th></tr>
                </thead>
                <tbody>
                  {Object.entries(goldTables).sort((a, b) => b[1] - a[1]).map(([name, count]) => (
                    <tr key={name}>
                      <td className="status-source">gold.{name}</td>
                      <td className="status-desc">{GOLD_DESCRIPTIONS[name] || ''}</td>
                      <td className="status-num">{count.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>

          {/* ── Manually Curated Data ── */}
          {curated.length > 0 && (
            <section id="curated" className="status-section">
              <h2>Manually Curated Data ({curated.length})</h2>
              <p className="status-layer-desc">Hand-built datasets created from expert knowledge, fly fishing literature, and local business directories.</p>
              <div className="status-table-wrap">
                <table className="status-table">
                  <thead>
                    <tr><th>Name</th><th>Description</th><th>Source</th><th>Table</th><th className="status-num-col">Records</th></tr>
                  </thead>
                  <tbody>
                    {curated.map((c, i) => (
                      <tr key={i}>
                        <td className="status-source">{c.name}</td>
                        <td className="status-desc">{c.description}</td>
                        <td className="status-curated-source">{c.source}</td>
                        <td className="status-source">{c.table}</td>
                        <td className="status-num">{c.records?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}
        </>
      )}
    </div>
  )
}
