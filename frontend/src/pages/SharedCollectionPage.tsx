/**
 * /path/shared/:token — opens a shared Saved collection.
 *
 * Fetches the snapshot, drops the items into the recipient's own Saved (flagged
 * `shared`, expiring in 24h via SavedContext), then sends them to /path/saved for
 * that watershed. A banner there offers "sign in to keep" — on sign-in,
 * SavedPage calls keepShared() to make them permanent. Expired/invalid tokens
 * show a friendly message.
 */
import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { API_BASE } from '../config'
import { useSaved } from '../components/SavedContext'
import { setSelectedWatershed } from '../components/WatershedHeader'

export default function SharedCollectionPage() {
  const { token } = useParams<{ token: string }>()
  const navigate = useNavigate()
  const { addShared } = useSaved()
  const [status, setStatus] = useState<'loading' | 'error'>('loading')
  const [errMsg, setErrMsg] = useState('')

  useEffect(() => {
    let cancelled = false
    ;(async () => {
      try {
        const r = await fetch(`${API_BASE}/saved/shared/${token}`)
        if (!r.ok) {
          const body = await r.json().catch(() => ({}))
          throw new Error(body.detail || 'This shared link is invalid or has expired.')
        }
        const data = await r.json()
        if (cancelled) return
        const items = (data.items || []).map((it: any) => ({
          type: it.type,
          id: it.id,
          watershed: it.data?.watershed || data.watershed || 'other',
          label: it.data?.label || it.id,
          sublabel: it.data?.sublabel,
          thumbnail: it.data?.thumbnail,
          latitude: it.data?.latitude,
          longitude: it.data?.longitude,
        }))
        addShared(items, data.expires_at)
        if (data.watershed) setSelectedWatershed(data.watershed)
        navigate(`/path/saved?shared=1`, { replace: true })
      } catch (e: any) {
        if (!cancelled) { setErrMsg(e.message || 'Link unavailable.'); setStatus('error') }
      }
    })()
    return () => { cancelled = true }
  }, [token])

  if (status === 'error') {
    return (
      <div className="alerts-empty" style={{ padding: 32, textAlign: 'center' }}>
        <h2>Shared link unavailable</h2>
        <p>{errMsg}</p>
        <p style={{ marginTop: 12 }}>Shared collections last 24 hours. Ask your friend to send a fresh link.</p>
        <button className="alerts-cta" onClick={() => navigate('/path')}>Go to RiverPath</button>
      </div>
    )
  }
  return <div className="alerts-empty" style={{ padding: 32, textAlign: 'center' }}>Opening shared collection…</div>
}
