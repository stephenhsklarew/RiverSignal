import { createContext, useContext, useState, useEffect, useRef, useCallback, type ReactNode } from 'react'

const API_BASE = 'http://localhost:8001/api/v1'

export interface Location { id: string; name: string; lat: number; lon: number; photo?: string; caption?: string }
export interface Fossil {
  taxon_name: string; common_name: string | null; phylum: string; class_name: string; period: string;
  age_max_ma: number | null; distance_km: number | null; source_id: string | null;
  image_url: string | null; image_license: string | null; museum: string | null;
  latitude: number; longitude: number; morphosource_url?: string | null;
}
export interface Mineral {
  site_name: string; commodity: string; dev_status: string;
  distance_km: number | null; latitude: number; longitude: number;
  image_url?: string | null; image_license?: string | null;
}
export interface TimelineItem {
  type: string; name: string; period: string; age_max_ma: number | null;
  rock_type?: string; taxon_name?: string; phylum?: string;
}

export const WATERSHEDS = [
  { id: 'klamath', name: 'Upper Klamath Basin', lat: 42.65, lon: -121.55,
    photo: 'https://images.unsplash.com/photo-1566126157268-bd7167924841?w=900&h=400&fit=crop',
    caption: 'Crater Lake & volcanic highlands' },
  { id: 'mckenzie', name: 'McKenzie River', lat: 44.075, lon: -122.3,
    photo: 'https://images.unsplash.com/photo-1660806739398-0f0627930230?w=900&h=400&fit=crop',
    caption: 'Tamolitch Blue Pool — lava tube hydrology' },
  { id: 'deschutes', name: 'Deschutes River', lat: 44.325, lon: -121.225,
    photo: 'https://images.unsplash.com/photo-1528672903139-6a4496639a68?w=900&h=400&fit=crop',
    caption: 'Smith Rock — 30 Ma welded tuff canyon' },
  { id: 'metolius', name: 'Metolius River', lat: 44.5, lon: -121.575,
    photo: 'https://images.unsplash.com/photo-1657215223750-c4988d4a2635?w=900&h=400&fit=crop',
    caption: 'Spring-fed from Cascade volcanic aquifer' },
  { id: 'johnday', name: 'John Day River', lat: 44.6, lon: -119.15,
    photo: 'https://images.unsplash.com/photo-1559867243-edf5915deaa7?w=900&h=400&fit=crop',
    caption: 'Painted Hills — 33 Ma volcanic ash layers' },
  { id: 'skagit', name: 'Skagit River', lat: 48.45, lon: -121.50,
    photo: 'https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=900&h=600&fit=crop',
    caption: 'North Cascades glacial geology' },
]

interface DeepTrailState {
  loc: Location | null
  selectLocation: (l: Location) => void
  loading: boolean
  // Data
  fossils: Fossil[]
  minerals: Mineral[]
  timeline: TimelineItem[]
  landStatus: any
  geoContext: any
  riverData: any
  crossDomain: any
  quiz: any
  quizAnswers: Record<number, string>
  setQuizAnswers: React.Dispatch<React.SetStateAction<Record<number, string>>>
  rarityScores: Record<string, any>
  mineralShops: any[]
  rockhoundingSites: any[]
  // Story
  storyNarrative: string
  storyLoading: boolean
  readingLevel: string
  setReadingLevel: (l: string) => void
  speaking: boolean
  audioLoading: boolean
  speakStory: () => void
  // Chat
  chatInput: string
  setChatInput: (v: string) => void
  chatMessages: { role: string; text: string }[]
  chatLoading: boolean
  sendChat: () => void
  // Compare eras
  compareEra1: string
  setCompareEra1: (v: string) => void
  compareEra2: string
  setCompareEra2: (v: string) => void
  compareData: any
  fetchCompareData: () => void
  // Filters
  periodFilter: string
  setPeriodFilter: (v: string) => void
  phylumFilter: string
  setPhylumFilter: (v: string) => void
  mineralFilter: string
  setMineralFilter: (v: string) => void
}

const DeepTrailCtx = createContext<DeepTrailState | null>(null)

export function DeepTrailProvider({ children }: { children: ReactNode }) {
  const [loc, setLoc] = useState<Location | null>(() => {
    try {
      const raw = sessionStorage.getItem('deeptrail-location')
      return raw ? JSON.parse(raw) : null
    } catch { return null }
  })
  const [loading, setLoading] = useState(false)

  // Data state
  const [fossils, setFossils] = useState<Fossil[]>([])
  const [minerals, setMinerals] = useState<Mineral[]>([])
  const [timeline, setTimeline] = useState<TimelineItem[]>([])
  const [landStatus, setLandStatus] = useState<any>(null)
  const [geoContext, setGeoContext] = useState<any>(null)
  const [riverData, setRiverData] = useState<any>(null)
  const [crossDomain, setCrossDomain] = useState<any>(null)
  const [quiz, setQuiz] = useState<any>(null)
  const [quizAnswers, setQuizAnswers] = useState<Record<number, string>>({})
  const [rarityScores, setRarityScores] = useState<Record<string, any>>({})
  const [mineralShops, setMineralShops] = useState<any[]>([])
  const [rockhoundingSites, setRockhoundingSites] = useState<any[]>([])

  // Story
  const [storyNarrative, setStoryNarrative] = useState('')
  const [storyLoading, setStoryLoading] = useState(false)
  const [readingLevel, setReadingLevel] = useState('adult')
  const [speaking, setSpeaking] = useState(false)
  const [audioLoading, setAudioLoading] = useState(false)
  const audioRef = useRef<HTMLAudioElement | null>(null)

  // Chat
  const [chatInput, setChatInput] = useState('')
  const [chatMessages, setChatMessages] = useState<{ role: string; text: string }[]>([])
  const [chatLoading, setChatLoading] = useState(false)

  // Compare eras
  const [compareEra1, setCompareEra1] = useState('Eocene')
  const [compareEra2, setCompareEra2] = useState('Miocene')
  const [compareData, setCompareData] = useState<any>(null)

  // Filters
  const [periodFilter, setPeriodFilter] = useState('')
  const [phylumFilter, setPhylumFilter] = useState('')
  const [mineralFilter, setMineralFilter] = useState('')

  const selectLocation = useCallback((l: Location) => {
    setLoc(l)
    sessionStorage.setItem('deeptrail-location', JSON.stringify(l))
    setChatMessages([])
    setQuizAnswers({})
    setPeriodFilter('')
    setPhylumFilter('')
    setMineralFilter('')
    setCompareData(null)
  }, [])

  // Fetch data when location changes
  useEffect(() => {
    if (!loc) return
    setLoading(true)
    Promise.all([
      fetch(`${API_BASE}/fossils/near/${loc.lat}/${loc.lon}?radius_km=50`).then(r => r.json()),
      fetch(`${API_BASE}/deep-time/timeline/${loc.lat}/${loc.lon}`).then(r => r.json()),
      fetch(`${API_BASE}/land/at/${loc.lat}/${loc.lon}`).then(r => r.json()),
      fetch(`${API_BASE}/minerals/near/${loc.lat}/${loc.lon}?radius_km=50`).then(r => r.json()),
      fetch(`${API_BASE}/geology/at/${loc.lat}/${loc.lon}`).then(r => r.json()),
    ]).then(([f, t, l, m, g]) => {
      setFossils(f.fossils || [])
      setTimeline(t.timeline || [])
      setLandStatus(l)
      setMinerals(m.minerals || [])
      setGeoContext(g)
      setLoading(false)
    }).catch(() => setLoading(false))

    fetch(`${API_BASE}/deep-time/geology-ecology/${loc.lat}/${loc.lon}`).then(r => r.json()).then(setCrossDomain).catch(() => {})
    fetch(`${API_BASE}/deep-time/quiz?lat=${loc.lat}&lon=${loc.lon}`).then(r => r.json()).then(setQuiz).catch(() => {})
    fetch(`${API_BASE}/deep-time/rarity`).then(r => r.json()).then(d => setRarityScores(d.scores || {})).catch(() => {})
    fetch(`${API_BASE}/deep-time/mineral-shops`).then(r => r.json()).then(setMineralShops).catch(() => {})
    fetch(`${API_BASE}/rockhounding/near/${loc.lat}/${loc.lon}?radius_km=150`).then(r => r.json()).then(d => setRockhoundingSites(d.sites || [])).catch(() => {})

    setRiverData(null)
    fetch(`${API_BASE}/sites/nearest?lat=${loc.lat}&lon=${loc.lon}`)
      .then(r => r.ok ? r.json() : null)
      .then(nearest => {
        if (!nearest) return
        return fetch(`${API_BASE}/sites/${nearest.watershed}`).then(r => r.json()).then(site => {
          setRiverData({ ...nearest, ...site })
        })
      })
      .catch(() => {})
  }, [loc])

  // Fetch story when location or reading level changes
  useEffect(() => {
    if (!loc) return
    if (audioRef.current) { audioRef.current.pause(); audioRef.current.currentTime = 0 }
    if ('speechSynthesis' in window) speechSynthesis.cancel()
    setSpeaking(false)
    setStoryLoading(true)
    setStoryNarrative('')
    fetch(`${API_BASE}/deep-time/story`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat: loc.lat, lon: loc.lon, reading_level: readingLevel }),
    })
      .then(r => r.json())
      .then(data => { setStoryNarrative(data.narrative || 'No geologic data available.'); setStoryLoading(false) })
      .catch(() => { setStoryNarrative('Unable to load story.'); setStoryLoading(false) })
  }, [loc, readingLevel])

  const speakStory = useCallback(async () => {
    if (speaking && audioRef.current) {
      audioRef.current.pause(); audioRef.current.currentTime = 0; setSpeaking(false); return
    }
    if (!storyNarrative || storyLoading) return
    setAudioLoading(true)
    try {
      const resp = await fetch(`${API_BASE}/tts`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: storyNarrative, voice: 'nova' }),
      })
      if (!resp.ok) throw new Error('TTS failed')
      const blob = await resp.blob()
      const url = URL.createObjectURL(blob)
      if (audioRef.current) { audioRef.current.pause(); URL.revokeObjectURL(audioRef.current.src) }
      const audio = new Audio(url)
      audioRef.current = audio
      audio.onended = () => setSpeaking(false)
      audio.onerror = () => setSpeaking(false)
      setSpeaking(true); setAudioLoading(false); audio.play()
    } catch {
      setAudioLoading(false)
      if ('speechSynthesis' in window) {
        const u = new SpeechSynthesisUtterance(storyNarrative)
        u.rate = 0.95; u.lang = 'en-US'; u.onend = () => setSpeaking(false)
        setSpeaking(true); speechSynthesis.speak(u)
      }
    }
  }, [speaking, storyNarrative, storyLoading])

  const sendChat = useCallback(() => {
    if (!chatInput.trim() || chatLoading || !loc) return
    const q = chatInput.trim()
    setChatMessages(prev => [...prev, { role: 'user', text: q }])
    setChatInput('')
    setChatLoading(true)
    fetch(`${API_BASE}/deep-time/story`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ lat: loc.lat, lon: loc.lon, reading_level: readingLevel, question: q }),
    })
      .then(r => r.json())
      .then(data => {
        setChatMessages(prev => [...prev, { role: 'assistant', text: data.context_summary || data.narrative || 'No data.' }])
        setChatLoading(false)
      })
      .catch(() => { setChatMessages(prev => [...prev, { role: 'assistant', text: 'Unable to answer.' }]); setChatLoading(false) })
  }, [chatInput, chatLoading, loc, readingLevel])

  const fetchCompareData = useCallback(() => {
    if (!loc) return
    fetch(`${API_BASE}/deep-time/compare-eras?lat=${loc.lat}&lon=${loc.lon}&era1=${compareEra1}&era2=${compareEra2}`)
      .then(r => r.json()).then(setCompareData)
  }, [loc, compareEra1, compareEra2])

  return (
    <DeepTrailCtx.Provider value={{
      loc, selectLocation, loading,
      fossils, minerals, timeline, landStatus, geoContext, riverData,
      crossDomain, quiz, quizAnswers, setQuizAnswers, rarityScores,
      mineralShops, rockhoundingSites,
      storyNarrative, storyLoading, readingLevel, setReadingLevel,
      speaking, audioLoading, speakStory,
      chatInput, setChatInput, chatMessages, chatLoading, sendChat,
      compareEra1, setCompareEra1, compareEra2, setCompareEra2, compareData, fetchCompareData,
      periodFilter, setPeriodFilter, phylumFilter, setPhylumFilter, mineralFilter, setMineralFilter,
    }}>
      {children}
    </DeepTrailCtx.Provider>
  )
}

export function useDeepTrail(): DeepTrailState {
  const ctx = useContext(DeepTrailCtx)
  if (!ctx) throw new Error('useDeepTrail must be used within DeepTrailProvider')
  return ctx
}
