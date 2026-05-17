/**
 * Full-bleed photo viewer for any /path/now image.
 *
 * Reads the photo metadata from react-router state (TappablePhoto stuffs it
 * there). If a user lands on this URL directly (no state), redirect them
 * back to the watershed page — there's no good way to reconstruct which
 * photo to show without it.
 */
import { useEffect } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import WatershedHeader from '../components/WatershedHeader'
import type { PhotoMeta } from '../components/TappablePhoto'
import './PhotoDetailPage.css'

interface LocationState {
  photo?: PhotoMeta
  /** Optional override for the back-link target. Defaults to `/path/now/:watershed`. */
  backTo?: { path: string; label: string }
}

export default function PhotoDetailPage() {
  const { watershed = '' } = useParams<{ watershed: string }>()
  const location = useLocation()
  const navigate = useNavigate()
  const state = location.state as LocationState | null
  const photo = state?.photo
  const backTo = state?.backTo

  // No state → user reloaded the page or pasted the URL.
  // Bounce them back to the watershed view.
  useEffect(() => {
    if (!photo) {
      navigate(`/path/now/${watershed}`, { replace: true })
    }
  }, [photo, watershed, navigate])

  if (!photo) return null

  const wsLabel = watershed.replace(/_/g, ' ')
  const backPath = backTo?.path ?? `/path/now/${watershed}`
  const backLabel = backTo?.label ?? `Back to ${wsLabel}`

  return (
    <>
      <WatershedHeader watershed={watershed} basePath="/path/now" />
      <div className="photo-detail">
        <Link to={backPath} className="photo-detail-back">
          ← {backLabel}
        </Link>

        <figure className="photo-detail-figure">
          <img
            src={photo.url}
            alt={photo.title || 'Photo'}
            className="photo-detail-img"
          />
        </figure>

        <div className="photo-detail-meta">
          {photo.title && <h1 className="photo-detail-title">{photo.title}</h1>}
          {photo.subtitle && (
            <div className="photo-detail-subtitle">{photo.subtitle}</div>
          )}
          {photo.caption && (
            <p className="photo-detail-caption">{photo.caption}</p>
          )}
          <dl className="photo-detail-dl">
            {photo.observer && (
              <>
                <dt>Photographer</dt>
                <dd>📷 {photo.observer}</dd>
              </>
            )}
            {photo.source && (
              <>
                <dt>Source</dt>
                <dd>{photo.source}</dd>
              </>
            )}
            {photo.observedAt && (
              <>
                <dt>Observed</dt>
                <dd>{formatDate(photo.observedAt)}</dd>
              </>
            )}
          </dl>
        </div>
      </div>
    </>
  )
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleDateString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
    })
  } catch {
    return iso
  }
}
