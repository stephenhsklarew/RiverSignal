import { Component, type ReactNode } from 'react'

// A failed lazy-chunk import — happens when a client holds an old app shell
// after a redeploy and the referenced chunk hash no longer exists.
function isChunkLoadError(e: unknown): boolean {
  const msg = (e as Error)?.message || ''
  return /Loading chunk|dynamically imported module|Importing a module script failed|ChunkLoadError|Failed to fetch dynamically/i.test(msg)
}

const RELOAD_FLAG = 'rs_chunk_reloaded'

interface Props { children: ReactNode }
interface State { error: Error | null }

/**
 * App-wide error boundary. Without one, any render-time throw (or a failed
 * lazy-route import after a redeploy) unmounts the whole tree to a blank white
 * screen with no recovery. This catches it: stale-chunk errors trigger a single
 * automatic reload (to pull the new bundle); anything else shows a Reload card.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error) {
    // Stale lazy chunk after a deploy → reload once to fetch the new bundle.
    // The session flag stops a reload loop if the reload still fails.
    if (isChunkLoadError(error) && !sessionStorage.getItem(RELOAD_FLAG)) {
      sessionStorage.setItem(RELOAD_FLAG, '1')
      window.location.reload()
    }
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight: '100vh', display: 'flex', flexDirection: 'column',
          alignItems: 'center', justifyContent: 'center', gap: 14,
          fontFamily: 'Outfit, sans-serif', color: '#3d3527', padding: 24, textAlign: 'center',
        }}>
          <div style={{ fontSize: 34 }}>🌊</div>
          <div style={{ fontWeight: 600 }}>Something went wrong loading this page.</div>
          <button
            onClick={() => { sessionStorage.removeItem(RELOAD_FLAG); window.location.reload() }}
            style={{ padding: '10px 18px', borderRadius: 8, border: '1px solid var(--accent, #2b6cb0)', background: 'var(--accent, #2b6cb0)', color: '#fff', fontWeight: 600, cursor: 'pointer' }}>
            Reload
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
