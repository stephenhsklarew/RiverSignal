import { StrictMode, lazy, Suspense, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { SWRConfig } from 'swr'
import { swrDefault } from './lib/swr'
import { SavedProvider } from './components/SavedContext'
import { DeepTrailProvider } from './components/DeepTrailContext'
import { AuthProvider, useAuth, RETURN_PATH_KEY } from './components/AuthContext'
import './index.css'

function DynamicFavicon() {
  const { pathname } = useLocation()
  useEffect(() => {
    const link = document.querySelector("link[rel='icon']") as HTMLLinkElement | null
    if (!link) return
    if (pathname.startsWith('/trail')) {
      link.href = '/favicon-deeptrail.svg'
      link.type = 'image/svg+xml'
    } else if (pathname.startsWith('/path')) {
      link.href = '/favicon-riverpath.svg'
      link.type = 'image/svg+xml'
    } else if (pathname === '/' || pathname.startsWith('/status')) {
      link.href = '/liquid-marble-favicon.png'
      link.type = 'image/png'
    } else {
      link.href = '/favicon.svg'
      link.type = 'image/svg+xml'
    }
  }, [pathname])
  return null
}

// Lazy-loaded product routes for code splitting
const LandingPage = lazy(() => import('./pages/LandingPage'))
const HomePage = lazy(() => import('./pages/HomePage'))
const MapPage = lazy(() => import('./pages/MapPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const DeepSignalPage = lazy(() => import('./pages/DeepSignalPage'))
// DeepTrail tab pages
const DeepTrailPickPage = lazy(() => import('./pages/DeepTrailPickPage'))
const TrailStoryPage = lazy(() => import('./pages/TrailStoryPage'))
const TrailExplorePage = lazy(() => import('./pages/TrailExplorePage'))
const TrailCollectPage = lazy(() => import('./pages/TrailCollectPage'))
const TrailLearnPage = lazy(() => import('./pages/TrailLearnPage'))
const TrailSavedPage = lazy(() => import('./pages/TrailSavedPage'))
const StatusPage = lazy(() => import('./pages/StatusPage'))
const UsernameSetupPage = lazy(() => import('./pages/UsernameSetupPage'))
const PersonaPromptModal = lazy(() => import('./components/PersonaPromptModal'))

// RiverPath mobile tab pages
const RiverNowPage = lazy(() => import('./pages/RiverNowPage'))
const ExplorePage = lazy(() => import('./pages/ExplorePage'))
const HatchPage = lazy(() => import('./pages/HatchPage'))
const FishRefugePage = lazy(() => import('./pages/FishRefugePage'))
const StewardPage = lazy(() => import('./pages/StewardPage'))
const SavedPage = lazy(() => import('./pages/SavedPage'))
const WherePage = lazy(() => import('./pages/WherePage'))
const AlertsPage = lazy(() => import('./pages/AlertsPage'))
const SpeciesMapPage = lazy(() => import('./pages/SpeciesMapPage'))
const ExploreMapPage = lazy(() => import('./pages/ExploreMapPage'))
const MyObsMapPage = lazy(() => import('./pages/MyObsMapPage'))
const StockingMapPage = lazy(() => import('./pages/StockingMapPage'))
const PhotoDetailPage = lazy(() => import('./pages/PhotoDetailPage'))
const AdminPhotosPage = lazy(() => import('./pages/AdminPhotosPage'))
const AdminPhotoHistoryPage = lazy(() => import('./pages/AdminPhotoHistoryPage'))
const AdminRiverStoriesPage = lazy(() => import('./pages/AdminRiverStoriesPage'))
const AdminRoute = lazy(() => import('./components/AdminRoute'))

// Bottom nav
const BottomNav = lazy(() => import('./components/BottomNav'))
const DeepTrailBottomNav = lazy(() => import('./components/DeepTrailBottomNav'))

function AuthSuccessRedirect() {
  const { loading, needsUsername } = useAuth()
  if (loading) return <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh' }}>Signing in...</div>
  if (needsUsername) return <Navigate to="/auth/setup-username" replace />
  // Return the user to where they signed in from (saved by AuthContext before the OAuth redirect).
  const returnTo = sessionStorage.getItem(RETURN_PATH_KEY)
  sessionStorage.removeItem(RETURN_PATH_KEY)
  if (returnTo && !returnTo.startsWith('/auth')) return <Navigate to={returnTo} replace />
  return <Navigate to="/" replace />
}

const Loading = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontFamily: 'Outfit, sans-serif', color: '#64705b' }}>
    Loading...
  </div>
)

function ConditionalBottomNav() {
  const { pathname } = useLocation()

  // DeepTrail bottom nav on /trail/<tab>/<location> routes. Require a
  // non-empty location segment — bare /trail and /trail/<tab> are the
  // location picker, which has its own nav.
  const isTrailTabRoute = /^\/trail\/(story|explore|collect|learn|saved)\/[^/]+/.test(pathname)
  if (isTrailTabRoute) return <DeepTrailBottomNav />

  // RiverPath bottom nav: show on every /path/<tab> route EXCEPT:
  //   - bare /path (HomePage splash)        — no tab in path at all
  //   - bare /path/now (RiverNowDefault     — the watershed-picker
  //     splash; renders the same card grid as /path)
  //
  // All other tabs default to the session-stored watershed when the
  // URL has no watershed segment (e.g. /path/alerts, /path/saved,
  // /path/hatch), so they need the toolbar even without a
  // watershed slug in the URL. The previous regex required
  // `\/[^/]+` after the tab name, which incorrectly hid the toolbar
  // on those routes.
  const isTabRoute = /^\/path\/(now|explore|hatch|steward|saved|fish|map|explore-map|stocking|where|alerts)(\/|$)/.test(pathname)
  const isBareNowPicker = pathname === '/path/now' || pathname === '/path/now/'
  if (isTabRoute && !isBareNowPicker) return <BottomNav />
  return null
}

function personaLanding(personas: string[]): string | null {
  if (!personas.length) return null
  // Resolve in plan-defined priority — most specific products first
  if (personas.includes('rockhound')) return '/trail'
  if (personas.includes('watershed_pro')) return '/riversignal'
  if (personas.some(p => ['angler_self_guided','guide_professional','family_outdoor','outdoor_general'].includes(p))) return '/path'
  return null
}

function PersonaPromptGate() {
  const { needsPersonas, skipPersonasThisSession } = useAuth()
  const { pathname } = useLocation()
  const navigate = useNavigate()
  // Don't intercept the username setup flow or the OAuth callback redirect
  if (!needsPersonas) return null
  if (pathname.startsWith('/auth/')) return null
  const isDark = pathname === '/' || pathname.startsWith('/status')
  // Only redirect from the landing page — never bounce users off product pages where they're editing interests
  const shouldRedirect = pathname === '/'
  return (
    <Suspense fallback={null}>
      <PersonaPromptModal
        onClose={skipPersonasThisSession}
        onComplete={(selected) => {
          if (!shouldRedirect) return
          const dest = personaLanding(selected)
          if (dest) navigate(dest, { replace: true })
        }}
        dark={isDark}
      />
    </Suspense>
  )
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <SWRConfig value={swrDefault}>
      <AuthProvider>
      <SavedProvider>
        <DeepTrailProvider>
        <DynamicFavicon />
        <Suspense fallback={<Loading />}>
          <Routes>
            {/* Landing — product selector */}
            <Route path="/" element={<LandingPage />} />

            {/* RiverSignal — B2B watershed intelligence (desktop-first) */}
            <Route path="/riversignal" element={<MapPage />} />
            <Route path="/riversignal/reports" element={<ReportsPage />} />
            <Route path="/riversignal/:watershed" element={<MapPage />} />

            {/* RiverPath — B2C river field companion (mobile-first) */}
            <Route path="/path" element={<HomePage />} />
            <Route path="/path/:watershed" element={<HomePage />} />

            {/* RiverPath — mobile tab screens (FEAT-014) */}
            <Route path="/path/now" element={<RiverNowPage />} />
            <Route path="/path/now/:watershed" element={<RiverNowPage />} />
            <Route path="/path/now/:watershed/photo" element={<PhotoDetailPage />} />
            <Route path="/path/explore" element={<ExplorePage />} />
            <Route path="/path/explore/:watershed" element={<ExplorePage />} />
            <Route path="/path/hatch" element={<HatchPage />} />
            <Route path="/path/hatch/:watershed" element={<HatchPage />} />
            <Route path="/path/steward" element={<StewardPage />} />
            <Route path="/path/steward/:watershed" element={<StewardPage />} />
            <Route path="/path/explore-map/:watershed" element={<ExploreMapPage />} />
            <Route path="/path/saved" element={<SavedPage />} />
            <Route path="/path/where" element={<WherePage />} />
            <Route path="/path/alerts" element={<AlertsPage />} />

            {/* Admin console (v0 = photo curation). Gated by AdminRoute. */}
            <Route path="/admin/photos" element={<AdminRoute><AdminPhotosPage /></AdminRoute>} />
            <Route path="/admin/photos/:species_key" element={<AdminRoute><AdminPhotosPage /></AdminRoute>} />
            <Route path="/admin/photos/:species_key/history" element={<AdminRoute><AdminPhotoHistoryPage /></AdminRoute>} />
            <Route path="/admin/river-stories" element={<AdminRoute><AdminRiverStoriesPage /></AdminRoute>} />
            <Route path="/admin/river-stories/:watershed/:reading_level" element={<AdminRoute><AdminRiverStoriesPage /></AdminRoute>} />
            <Route path="/path/saved/map/:watershed" element={<MyObsMapPage />} />
            <Route path="/path/stocking/:watershed" element={<StockingMapPage />} />
            <Route path="/path/map/:watershed" element={<SpeciesMapPage />} />
            <Route path="/path/fish/:watershed" element={<FishRefugePage />} />

            {/* DeepSignal — B2B geologic intelligence (desktop-first) */}
            <Route path="/deepsignal" element={<DeepSignalPage />} />
            <Route path="/deepsignal/:watershed" element={<DeepSignalPage />} />

            {/* DeepTrail — B2C geology adventure (mobile-first, 5 tabs) */}
            <Route path="/trail" element={<DeepTrailPickPage />} />
            <Route path="/trail/story/:locationId" element={<TrailStoryPage />} />
            <Route path="/trail/explore/:locationId" element={<TrailExplorePage />} />
            <Route path="/trail/collect/:locationId" element={<TrailCollectPage />} />
            <Route path="/trail/learn/:locationId" element={<TrailLearnPage />} />
            <Route path="/trail/saved" element={<TrailSavedPage />} />

            {/* Auth */}
            <Route path="/auth/success" element={<AuthSuccessRedirect />} />
            <Route path="/auth/setup-username" element={<UsernameSetupPage />} />

            {/* Legacy routes — redirect to new product routes */}
            <Route path="/map" element={<MapPage />} />
            <Route path="/map/:watershed" element={<MapPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/status" element={<StatusPage />} />
          </Routes>
          <ConditionalBottomNav />
          <PersonaPromptGate />
        </Suspense>
        </DeepTrailProvider>
      </SavedProvider>
      </AuthProvider>
      </SWRConfig>
    </BrowserRouter>
  </StrictMode>,
)
