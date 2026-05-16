/**
 * Wraps an <img> with click/keyboard navigation to /path/now/:watershed/photo.
 *
 * Passes the photo metadata via react-router state so the detail page can
 * render full-bleed image + observer/source/caption without a re-fetch.
 *
 * Stops event propagation so this doesn't also trigger any clickable parent
 * (e.g. a card that navigates elsewhere when its body is tapped).
 */
import { useNavigate } from 'react-router-dom'

export interface PhotoMeta {
  url: string
  title?: string        // e.g. common name or river name
  subtitle?: string     // e.g. scientific name
  observer?: string     // e.g. iNat user handle
  source?: string       // e.g. "iNaturalist", "Unsplash"
  observedAt?: string   // ISO date string, if known
  caption?: string      // optional descriptive text
}

interface Props {
  src: string
  alt?: string
  className?: string
  loading?: 'lazy' | 'eager'
  title?: string
  watershed: string
  meta: PhotoMeta
}

export default function TappablePhoto({
  src, alt, className, loading, title, watershed, meta,
}: Props) {
  const navigate = useNavigate()

  const open = (e?: React.SyntheticEvent) => {
    e?.stopPropagation()
    navigate(`/path/now/${watershed}/photo`, { state: { photo: meta } })
  }

  return (
    <img
      src={src}
      alt={alt}
      className={`tappable-photo${className ? ' ' + className : ''}`}
      loading={loading}
      title={title}
      role="button"
      tabIndex={0}
      onClick={open}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          open(e)
        }
      }}
    />
  )
}
