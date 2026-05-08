import { useState, useRef, useCallback, useEffect } from 'react'
import { useAuth } from './AuthContext'
import { LoginNudge } from './LoginModal'
import { API_BASE } from '../config'
import './PhotoObservation.css'

interface PhotoObservationProps {
  app: 'riverpath' | 'deeptrail'
  watershed?: string
  onSaved?: () => void
}

const RP_CATEGORIES = ['Fish', 'Bird', 'Insect', 'Plant', 'Mammal', 'Amphibian', 'Other']
const DT_CATEGORIES = ['Fossil', 'Rock', 'Mineral', 'Crystal', 'Landscape', 'Other']

interface ExifData {
  lat: number | null
  lon: number | null
  dateTime: string | null
}

/** Parse EXIF GPS and DateTime from a JPEG ArrayBuffer. */
function parseExif(buffer: ArrayBuffer): ExifData {
  const result: ExifData = { lat: null, lon: null, dateTime: null }
  const view = new DataView(buffer)

  // Check JPEG SOI marker
  if (view.getUint16(0) !== 0xFFD8) return result

  let offset = 2
  while (offset < view.byteLength - 2) {
    const marker = view.getUint16(offset)
    if (marker === 0xFFE1) {
      // APP1 — EXIF
      const exifStart = offset + 4

      // Check "Exif\0\0"
      const exifHeader = String.fromCharCode(
        view.getUint8(exifStart), view.getUint8(exifStart + 1),
        view.getUint8(exifStart + 2), view.getUint8(exifStart + 3)
      )
      if (exifHeader !== 'Exif') return result

      const tiffStart = exifStart + 6
      const bigEndian = view.getUint16(tiffStart) === 0x4D4D

      const getUint16 = (o: number) => view.getUint16(o, !bigEndian)
      const getUint32 = (o: number) => view.getUint32(o, !bigEndian)
      const getRational = (o: number) => {
        const num = getUint32(o)
        const den = getUint32(o + 4)
        return den === 0 ? 0 : num / den
      }

      // Read IFD0
      const ifd0Offset = tiffStart + getUint32(tiffStart + 4)
      const ifd0Count = getUint16(ifd0Offset)

      let exifIfdOffset = 0
      let gpsIfdOffset = 0

      for (let i = 0; i < ifd0Count; i++) {
        const entryOffset = ifd0Offset + 2 + i * 12
        const tag = getUint16(entryOffset)
        if (tag === 0x8769) exifIfdOffset = tiffStart + getUint32(entryOffset + 8)
        if (tag === 0x8825) gpsIfdOffset = tiffStart + getUint32(entryOffset + 8)
      }

      // Read DateTimeOriginal from ExifIFD
      if (exifIfdOffset) {
        const exifCount = getUint16(exifIfdOffset)
        for (let i = 0; i < exifCount; i++) {
          const entryOffset = exifIfdOffset + 2 + i * 12
          const tag = getUint16(entryOffset)
          if (tag === 0x9003) { // DateTimeOriginal
            const valOffset = tiffStart + getUint32(entryOffset + 8)
            let dt = ''
            for (let j = 0; j < 19; j++) dt += String.fromCharCode(view.getUint8(valOffset + j))
            // "2024:03:15 14:30:00" → ISO
            result.dateTime = dt.replace(/^(\d{4}):(\d{2}):(\d{2})/, '$1-$2-$3').replace(' ', 'T')
          }
        }
      }

      // Read GPS from GPS IFD
      if (gpsIfdOffset) {
        const gpsCount = getUint16(gpsIfdOffset)
        let latRef = 'N', lonRef = 'E'
        let latVals: number[] = [], lonVals: number[] = []

        for (let i = 0; i < gpsCount; i++) {
          const entryOffset = gpsIfdOffset + 2 + i * 12
          const tag = getUint16(entryOffset)

          if (tag === 1) { // GPSLatitudeRef
            latRef = String.fromCharCode(view.getUint8(entryOffset + 8))
          } else if (tag === 2) { // GPSLatitude
            const valOff = tiffStart + getUint32(entryOffset + 8)
            latVals = [getRational(valOff), getRational(valOff + 8), getRational(valOff + 16)]
          } else if (tag === 3) { // GPSLongitudeRef
            lonRef = String.fromCharCode(view.getUint8(entryOffset + 8))
          } else if (tag === 4) { // GPSLongitude
            const valOff = tiffStart + getUint32(entryOffset + 8)
            lonVals = [getRational(valOff), getRational(valOff + 8), getRational(valOff + 16)]
          }
        }

        if (latVals.length === 3) {
          result.lat = (latVals[0] + latVals[1] / 60 + latVals[2] / 3600) * (latRef === 'S' ? -1 : 1)
        }
        if (lonVals.length === 3) {
          result.lon = (lonVals[0] + lonVals[1] / 60 + lonVals[2] / 3600) * (lonRef === 'W' ? -1 : 1)
        }
      }

      return result
    }

    // Skip to next marker
    if ((marker & 0xFF00) !== 0xFF00) break
    const segLength = view.getUint16(offset + 2)
    offset += 2 + segLength
  }

  return result
}

export default function PhotoObservation({ app, watershed, onSaved }: PhotoObservationProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [photoPreview, setPhotoPreview] = useState<string | null>(null)
  const [photoBase64, setPhotoBase64] = useState<string | null>(null)
  const [latitude, setLatitude] = useState<string>('')
  const [longitude, setLongitude] = useState<string>('')
  const [dateTime, setDateTime] = useState<string>('')
  const [speciesName, setSpeciesName] = useState('')
  const [category, setCategory] = useState('')
  const [notes, setNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [success, setSuccess] = useState(false)
  const [typeaheadResults, setTypeaheadResults] = useState<{ name: string; type: string }[]>([])
  const [showTypeahead, setShowTypeahead] = useState(false)

  const fileRef = useRef<HTMLInputElement>(null)
  const cameraRef = useRef<HTMLInputElement>(null)
  const [showSourcePicker, setShowSourcePicker] = useState(false)
  const typeaheadTimeout = useRef<ReturnType<typeof setTimeout> | null>(null)

  const categories = app === 'deeptrail' ? DT_CATEGORIES : RP_CATEGORIES

  const reset = useCallback(() => {
    setPhotoPreview(null)
    setPhotoBase64(null)
    setLatitude('')
    setLongitude('')
    setDateTime('')
    setSpeciesName('')
    setCategory('')
    setNotes('')
    setSuccess(false)
    setTypeaheadResults([])
  }, [])

  const handleFile = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Preview
    const reader = new FileReader()
    reader.onload = (ev) => {
      const dataUrl = ev.target?.result as string
      setPhotoPreview(dataUrl)
      setPhotoBase64(dataUrl)
    }
    reader.readAsDataURL(file)

    // Parse EXIF
    const arrayBuffer = await file.arrayBuffer()
    const exif = parseExif(arrayBuffer)

    if (exif.lat && exif.lon) {
      setLatitude(exif.lat.toFixed(6))
      setLongitude(exif.lon.toFixed(6))
    }
    if (exif.dateTime) {
      setDateTime(exif.dateTime.slice(0, 16)) // YYYY-MM-DDTHH:MM format for datetime-local
    }

    // If no EXIF location, try GPS
    if (!exif.lat && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        pos => {
          if (!latitude) setLatitude(pos.coords.latitude.toFixed(6))
          if (!longitude) setLongitude(pos.coords.longitude.toFixed(6))
        },
        () => {}
      )
    }

    // Default date to now if not extracted
    if (!exif.dateTime) {
      setDateTime(new Date().toISOString().slice(0, 16))
    }

    setIsOpen(true)
  }, [latitude, longitude])

  // Typeahead search
  const handleSpeciesInput = useCallback((val: string) => {
    setSpeciesName(val)
    if (typeaheadTimeout.current) clearTimeout(typeaheadTimeout.current)
    if (val.length < 2) { setTypeaheadResults([]); setShowTypeahead(false); return }

    typeaheadTimeout.current = setTimeout(() => {
      fetch(`${API_BASE}/observations/typeahead?q=${encodeURIComponent(val)}&app=${app}`)
        .then(r => r.json())
        .then(data => { setTypeaheadResults(data); setShowTypeahead(data.length > 0) })
        .catch(() => {})
    }, 300)
  }, [app])

  const handleSubmit = useCallback(async () => {
    if (!speciesName && !category) return
    setSubmitting(true)

    try {
      const resp = await fetch(`${API_BASE}/observations/user`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          source_app: app,
          photo_base64: photoBase64,
          latitude: latitude ? parseFloat(latitude) : null,
          longitude: longitude ? parseFloat(longitude) : null,
          observed_at: dateTime ? new Date(dateTime).toISOString() : null,
          species_name: speciesName || null,
          common_name: speciesName || null,
          category: category.toLowerCase() || null,
          notes: notes || null,
          watershed: watershed || null,
        }),
      })

      if (resp.ok) {
        setSuccess(true)
        onSaved?.()
        setTimeout(() => { setIsOpen(false); reset() }, 1500)
      }
    } catch {
      // silent
    } finally {
      setSubmitting(false)
    }
  }, [app, photoBase64, latitude, longitude, dateTime, speciesName, category, notes, watershed, onSaved, reset])

  const isDark = app === 'deeptrail'
  const { isLoggedIn } = useAuth()
  const [showNudge, setShowNudge] = useState(false)

  // Show login nudge after successful anonymous save
  useEffect(() => {
    if (success && !isLoggedIn) {
      const timer = setTimeout(() => setShowNudge(true), 1800)
      return () => clearTimeout(timer)
    }
  }, [success, isLoggedIn])

  return (
    <>
      {/* Login nudge after anonymous save */}
      {showNudge && !isLoggedIn && (
        <LoginNudge dark={isDark} onDismiss={() => setShowNudge(false)} />
      )}

      {/* Floating action button */}
      <button
        className={`photo-fab ${isDark ? 'dark' : ''}`}
        onClick={() => setShowSourcePicker(true)}
        title="Add observation"
      >
        📷
      </button>

      {/* Source picker menu */}
      {showSourcePicker && (
        <div className="photo-source-overlay" onClick={() => setShowSourcePicker(false)}>
          <div className={`photo-source-menu ${isDark ? 'dark' : ''}`} onClick={e => e.stopPropagation()}>
            <button className="photo-source-option" onClick={() => { setShowSourcePicker(false); cameraRef.current?.click() }}>
              <span className="photo-source-icon">📸</span>
              <span>Take Photo</span>
            </button>
            <button className="photo-source-option" onClick={() => { setShowSourcePicker(false); fileRef.current?.click() }}>
              <span className="photo-source-icon">🖼</span>
              <span>Choose from Library</span>
            </button>
            <button className="photo-source-cancel" onClick={() => setShowSourcePicker(false)}>Cancel</button>
          </div>
        </div>
      )}

      {/* Hidden file input — photo library (no capture attribute) */}
      <input
        ref={fileRef}
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        onChange={handleFile}
      />

      {/* Hidden file input — camera (capture="environment") */}
      <input
        ref={cameraRef}
        type="file"
        accept="image/*"
        capture="environment"
        style={{ display: 'none' }}
        onChange={handleFile}
      />

      {/* Observation form overlay */}
      {isOpen && (
        <div className={`photo-overlay ${isDark ? 'dark' : ''}`} onClick={() => { setIsOpen(false); reset() }}>
          <div className="photo-modal" onClick={e => e.stopPropagation()}>
            {success ? (
              <div className="photo-success">
                <div className="photo-success-icon">✅</div>
                <div className="photo-success-text">Observation saved!</div>
              </div>
            ) : (
              <>
                <div className="photo-modal-header">
                  <span>New Observation</span>
                  <button className="photo-modal-close" onClick={() => { setIsOpen(false); reset() }}>✕</button>
                </div>

                {/* Photo preview */}
                {photoPreview && (
                  <div className="photo-preview-wrap">
                    <img src={photoPreview} alt="Preview" className="photo-preview" />
                  </div>
                )}

                {/* Auto-extracted metadata */}
                <div className="photo-field-row">
                  <div className="photo-field">
                    <label>Date / Time</label>
                    <input type="datetime-local" value={dateTime} onChange={e => setDateTime(e.target.value)} />
                  </div>
                </div>

                <div className="photo-field-row">
                  <div className="photo-field">
                    <label>Latitude</label>
                    <input type="text" value={latitude} onChange={e => setLatitude(e.target.value)} placeholder="Auto-detected" />
                  </div>
                  <div className="photo-field">
                    <label>Longitude</label>
                    <input type="text" value={longitude} onChange={e => setLongitude(e.target.value)} placeholder="Auto-detected" />
                  </div>
                </div>

                {/* Species / name search */}
                <div className="photo-field" style={{ position: 'relative' }}>
                  <label>{app === 'deeptrail' ? 'What did you find?' : 'Species name'}</label>
                  <input
                    type="text"
                    value={speciesName}
                    onChange={e => handleSpeciesInput(e.target.value)}
                    onFocus={() => typeaheadResults.length > 0 && setShowTypeahead(true)}
                    onBlur={() => setTimeout(() => setShowTypeahead(false), 200)}
                    placeholder={app === 'deeptrail' ? 'Obsidian, Thunderegg, Agate...' : 'Rainbow Trout, Mayfly...'}
                  />
                  {showTypeahead && (
                    <div className="photo-typeahead">
                      {typeaheadResults.map((r, i) => (
                        <button key={i} className="photo-typeahead-item"
                          onMouseDown={() => { setSpeciesName(r.name); setShowTypeahead(false) }}>
                          <span className="photo-ta-name">{r.name}</span>
                          <span className="photo-ta-type">{r.type}</span>
                        </button>
                      ))}
                    </div>
                  )}
                </div>

                {/* Category chips */}
                <div className="photo-field">
                  <label>Category</label>
                  <div className="photo-chips">
                    {categories.map(c => (
                      <button key={c}
                        className={`photo-chip ${category === c ? 'active' : ''}`}
                        onClick={() => setCategory(category === c ? '' : c)}>
                        {c}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Notes */}
                <div className="photo-field">
                  <label>Notes (optional)</label>
                  <textarea
                    value={notes}
                    onChange={e => setNotes(e.target.value)}
                    placeholder="Any details..."
                    rows={2}
                  />
                </div>

                {/* Submit */}
                <button
                  className="photo-submit"
                  onClick={handleSubmit}
                  disabled={submitting || (!speciesName && !category)}
                >
                  {submitting ? 'Saving...' : 'Save Observation'}
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </>
  )
}
