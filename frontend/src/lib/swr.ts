/**
 * Shared SWR fetcher: prefixes with API_BASE and parses JSON.
 *
 * Usage:
 *   const { data, isLoading } = useSWR(`/sites/${ws}/weather`, swrFetcher)
 *
 * Pass a per-call config to override the defaults from `swrDefault` below:
 *   useSWR(key, swrFetcher, { dedupingInterval: 5_000 })  // live data
 */
import { API_BASE } from '../config'

export const swrFetcher = (path: string) =>
  fetch(`${API_BASE}${path}`, { credentials: 'include' }).then(r => {
    if (!r.ok) throw new Error(`${r.status} ${r.statusText}`)
    return r.json()
  })

/**
 * Sane defaults for "page-level" data: cache for 60 s, revalidate on focus
 * so users see fresh data when they return to the tab. Override per-call
 * for live data (lower dedupingInterval) or static data (higher).
 */
export const swrDefault = {
  fetcher: swrFetcher,
  dedupingInterval: 60_000,
  revalidateOnFocus: true,
  revalidateIfStale: true,
  keepPreviousData: true,
}
