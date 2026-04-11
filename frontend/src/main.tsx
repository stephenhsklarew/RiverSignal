import { StrictMode, lazy, Suspense } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'

// Lazy-loaded product routes for code splitting
const LandingPage = lazy(() => import('./pages/LandingPage'))
const HomePage = lazy(() => import('./pages/HomePage'))
const MapPage = lazy(() => import('./pages/MapPage'))
const ReportsPage = lazy(() => import('./pages/ReportsPage'))
const DeepSignalPage = lazy(() => import('./pages/DeepSignalPage'))
const DeepTrailPage = lazy(() => import('./pages/DeepTrailPage'))

const Loading = () => (
  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', fontFamily: 'Outfit, sans-serif', color: '#64705b' }}>
    Loading...
  </div>
)

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
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

          {/* DeepSignal — B2B geologic intelligence (desktop-first) */}
          <Route path="/deepsignal" element={<DeepSignalPage />} />
          <Route path="/deepsignal/:watershed" element={<DeepSignalPage />} />

          {/* DeepTrail — B2C geology adventure (mobile-first) */}
          <Route path="/trail" element={<DeepTrailPage />} />
          <Route path="/trail/:location" element={<DeepTrailPage />} />

          {/* Legacy routes — redirect to new product routes */}
          <Route path="/map" element={<MapPage />} />
          <Route path="/map/:watershed" element={<MapPage />} />
          <Route path="/reports" element={<ReportsPage />} />
        </Routes>
      </Suspense>
    </BrowserRouter>
  </StrictMode>,
)
