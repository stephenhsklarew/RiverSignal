/**
 * Wrap a page in an is_admin guard. Non-admin signed-in users see a
 * "Not authorised" message and get redirected to /path after 3s. Anonymous
 * users land on /path immediately (auth flow handles them).
 */
import { useEffect, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from './AuthContext'

export default function AdminRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth()
  const navigate = useNavigate()
  const isAdmin = !!user?.is_admin

  useEffect(() => {
    if (loading) return
    if (!user) {
      navigate('/path', { replace: true })
      return
    }
    if (!isAdmin) {
      const t = setTimeout(() => navigate('/path', { replace: true }), 3000)
      return () => clearTimeout(t)
    }
  }, [loading, user, isAdmin, navigate])

  if (loading) {
    return <div style={{ padding: 40, textAlign: 'center', fontFamily: 'Outfit, sans-serif' }}>Loading…</div>
  }
  if (!user) {
    return null // navigating
  }
  if (!isAdmin) {
    return (
      <div style={{
        padding: 40, textAlign: 'center',
        fontFamily: 'Outfit, sans-serif', maxWidth: 480, margin: '60px auto',
      }}>
        <h2 style={{ color: '#a13a3a', marginBottom: 12 }}>Not authorised</h2>
        <p style={{ color: '#666' }}>This area is for site administrators only. Redirecting you home…</p>
      </div>
    )
  }
  return <>{children}</>
}
