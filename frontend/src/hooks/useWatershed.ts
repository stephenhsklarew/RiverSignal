import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { getSelectedWatershed, setSelectedWatershed } from '../components/WatershedHeader'

/**
 * Returns the active watershed from URL params or sessionStorage.
 * If no watershed in URL but one is saved, redirects to the saved one.
 * Saves the selection whenever it changes.
 */
export function useWatershed(basePath: string): string | null {
  const { watershed } = useParams<{ watershed?: string }>()
  const navigate = useNavigate()

  // Redirect to saved watershed if none in URL
  useEffect(() => {
    if (!watershed) {
      const saved = getSelectedWatershed()
      if (saved) navigate(`${basePath}/${saved}`, { replace: true })
    }
  }, [watershed, basePath, navigate])

  // Save selection
  useEffect(() => {
    if (watershed) setSelectedWatershed(watershed)
  }, [watershed])

  return watershed || null
}
