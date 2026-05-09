import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useDeepTrail, WATERSHEDS } from '../components/DeepTrailContext'
import DeepTrailHeader from '../components/DeepTrailHeader'
import { CardSettingsPanel, loadCardSettingsGeneric, type CardConfig } from '../components/CardSettings'
import './DeepTrailPage.css'

const LEARN_CARDS: CardConfig[] = [
  { id: 'kid_quiz', label: 'Kid Quiz Mode', icon: '🧩', visible: true },
  { id: 'ask_place', label: 'Ask About This Place', icon: '💬', visible: true },
  { id: 'living_river', label: 'Living River Link', icon: '🐟', visible: true },
]

export default function TrailLearnPage() {
  useEffect(() => { document.title = 'Deep Trail'; return () => { document.title = 'RiverSignal' } }, [])
  const { locationId } = useParams<{ locationId: string }>()
  const navigate = useNavigate()
  const {
    loc, selectLocation, loading,
    quiz, quizAnswers, setQuizAnswers,
    chatInput, setChatInput, chatMessages, chatLoading, sendChat,
    riverData,
  } = useDeepTrail()

  const [cardConfig, setCardConfig] = useState<CardConfig[]>(() =>
    loadCardSettingsGeneric('deeptrail-learn-cards', LEARN_CARDS)
  )
  const [showSettings, setShowSettings] = useState(false)

  // Resolve locationId if loc is null
  useEffect(() => {
    if (loc) return
    if (!locationId) { navigate('/trail'); return }

    const ws = WATERSHEDS.find(w => w.id === locationId)
    if (ws) { selectLocation(ws); return }

    const parts = locationId.split(',')
    if (parts.length === 2) {
      const lat = parseFloat(parts[0])
      const lon = parseFloat(parts[1])
      if (!isNaN(lat) && !isNaN(lon)) {
        selectLocation({
          id: locationId,
          name: `${lat.toFixed(4)}°N, ${Math.abs(lon).toFixed(4)}°W`,
          lat,
          lon,
        })
        return
      }
    }

    navigate('/trail')
  }, [loc, locationId, navigate, selectLocation])

  if (!loc) {
    return <div className="dt-app"><div className="dt-loading">Loading...</div></div>
  }

  return (
    <div className="dt-app">
      <DeepTrailHeader tab="learn" onSettingsClick={() => setShowSettings(true)} />

      {showSettings && (
        <CardSettingsPanel
          cards={cardConfig}
          onChange={setCardConfig}
          onClose={() => setShowSettings(false)}
          storageKey="deeptrail-learn-cards"
          defaults={LEARN_CARDS}
          title="Customize Learn Cards"
          dark
        />
      )}

      {loading ? <div className="dt-loading">Loading geology data...</div> : (
        <main className="dt-content" style={{ paddingBottom: 72 }}>
          <style>{cardConfig.map((c, i) => {
            const rules = [`[data-dtcard="${c.id}"] { order: ${i}; }`]
            if (!c.visible) rules.push(`[data-dtcard="${c.id}"] { display: none !important; }`)
            return rules.join('\n')
          }).join('\n')}</style>

          <div className="dt-card-container" style={{ display: 'flex', flexDirection: 'column' }}>

            {/* Kid Quiz */}
            <div data-dtcard="kid_quiz">
              {quiz && quiz.questions?.length > 0 && (
                <section className="dt-quiz-section">
                  <h3>🧩 Quiz Me!</h3>
                  {quiz.questions.map((q: any, i: number) => (
                    <div key={i} className="dt-quiz-q">
                      <div className="dt-quiz-question">{q.question}</div>
                      <div className="dt-quiz-choices">
                        {q.choices.map((c: string, j: number) => {
                          const answered = quizAnswers[i] !== undefined
                          const isCorrect = c === q.correct
                          const isChosen = quizAnswers[i] === c
                          return (
                            <button key={j}
                              className={`dt-quiz-choice${answered ? (isCorrect ? ' correct' : isChosen ? ' wrong' : '') : ''}`}
                              onClick={() => !answered && setQuizAnswers(prev => ({...prev, [i]: c}))}
                              disabled={answered}>
                              {c}
                            </button>
                          )
                        })}
                      </div>
                      {quizAnswers[i] !== undefined && (
                        <div className={`dt-quiz-hint ${quizAnswers[i] === q.correct ? 'right' : 'wrong-hint'}`}>
                          {quizAnswers[i] === q.correct ? '✅ Correct!' : `❌ The answer is: ${q.correct}`}
                          {q.hint && <span> — {q.hint}</span>}
                        </div>
                      )}
                    </div>
                  ))}
                </section>
              )}
            </div>

            {/* Ask About This Place */}
            <div data-dtcard="ask_place">
              <section className="dt-chat-section">
                <h3>Ask About This Place</h3>
                <div className="dt-chat-messages">
                  {chatMessages.map((msg, i) => (
                    <div key={i} className={`dt-chat-msg ${msg.role}`}>
                      <div className="dt-chat-bubble">{msg.text}</div>
                    </div>
                  ))}
                  {chatLoading && <div className="dt-chat-msg assistant"><div className="dt-chat-bubble">Thinking...</div></div>}
                </div>
                <div className="dt-chat-input-row">
                  <input type="text" value={chatInput} onChange={e => setChatInput(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') sendChat() }}
                    placeholder="What was this place like millions of years ago?"
                    className="dt-chat-input" />
                  <button onClick={sendChat} disabled={!chatInput.trim() || chatLoading} className="dt-chat-btn">Ask</button>
                </div>
              </section>
            </div>

            {/* Living River Link */}
            <div data-dtcard="living_river">
              {riverData && (
                <section className="dt-nav-cards">
                  <a href={`/path/now/${riverData.watershed}`} target="_blank" rel="noopener noreferrer" className="dt-nav-card dt-nav-card-river">
                    <span className="dt-nav-card-icon">🐟</span>
                    <span className="dt-nav-card-label">
                      Living River
                      <span className="dt-nav-card-sub">{riverData.name}</span>
                    </span>
                    <span className="dt-nav-card-count">
                      {riverData.scorecard?.total_species?.toLocaleString() || '—'}
                      <span className="dt-nav-card-unit">species</span>
                    </span>
                    <span className="dt-nav-card-arrow">↗</span>
                  </a>
                </section>
              )}
            </div>

          </div>
        </main>
      )}
    </div>
  )
}
