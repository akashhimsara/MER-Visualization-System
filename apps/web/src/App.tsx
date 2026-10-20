import { useEffect, useState, useRef } from 'react'
import './App.css'
import type {
  MERTier1Event,
  MERTier2Event,
  MERTier3Event,
  PersonalizationRecommendationEvent,
} from './types/mer'
import { PersonalizationDemo } from './components/personalization/PersonalizationDemo'

export function App() {
  const [activeTab, setActiveTab] = useState<'personalization' | 'pipeline'>('personalization')

  // Pipeline monitor state
  const [status, setStatus] = useState<'Connecting...' | 'Connected' | 'Disconnected' | 'Error'>('Connecting...')
  const [error, setError] = useState<string | null>(null)

  const [tier1Event, setTier1Event] = useState<MERTier1Event | null>(null)
  const [tier2Event, setTier2Event] = useState<MERTier2Event | null>(null)
  const [tier3Event, setTier3Event] = useState<MERTier3Event | null>(null)
  const [recommendationEvent, setRecommendationEvent] = useState<PersonalizationRecommendationEvent | null>(null)

  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Only connect WebSocket if on pipeline tab to save resources
    if (activeTab !== 'pipeline') return

    let reconnectTimeout: ReturnType<typeof setTimeout>
    let isMounted = true

    const connect = () => {
      if (!isMounted) return
      setStatus('Connecting...')
      setError(null)

      const rawBase = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
      const sanitizedBase = rawBase.replace(/\/+$/, '')
      const wsUrl = `${sanitizedBase}/ws/mock/mer`

      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        if (!isMounted) return
        setStatus('Connected')
      }

      ws.onmessage = (event) => {
        if (!isMounted) return
        try {
          const data = JSON.parse(event.data)
          if (!data || typeof data !== 'object') {
            console.warn('Received non-object JSON payload:', data)
            return
          }

          switch (data.event_type) {
            case 'mer.tier1':
              setTier1Event(data as MERTier1Event)
              break
            case 'mer.tier2':
              setTier2Event(data as MERTier2Event)
              break
            case 'mer.tier3':
              setTier3Event(data as MERTier3Event)
              break
            case 'personalization.recommendation':
              setRecommendationEvent(data as PersonalizationRecommendationEvent)
              break
            default:
              console.warn('Ignored unknown event_type:', data.event_type)
              break
          }
        } catch (err) {
          setError('Malformed JSON received from WebSocket')
          console.error('Failed to parse WebSocket message:', err)
        }
      }

      ws.onclose = () => {
        if (!isMounted) return
        setStatus('Disconnected')
        reconnectTimeout = setTimeout(connect, 2000)
      }

      ws.onerror = () => {
        if (!isMounted) return
        setStatus('Error')
      }
    }

    connect()

    return () => {
      isMounted = false
      clearTimeout(reconnectTimeout)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [activeTab])

  // Shared session ID derived from whichever tier emitted latest
  const sharedSessionId =
    tier1Event?.session_id ||
    tier2Event?.session_id ||
    tier3Event?.session_id ||
    recommendationEvent?.session_id ||
    'Waiting for session...'

  const getStatusColor = () => {
    switch (status) {
      case 'Connected':
        return '#10b981'
      case 'Connecting...':
        return '#f59e0b'
      case 'Error':
      case 'Disconnected':
        return '#ef4444'
      default:
        return '#9ca3af'
    }
  }

  return (
    <div style={{ backgroundColor: '#070b14', minHeight: '100vh' }}>
      {/* Top Application Navigation Bar */}
      <nav
        style={{
          backgroundColor: '#0d1322',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '0.75rem 1.5rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
          position: 'sticky',
          top: 0,
          zIndex: 50,
          backdropFilter: 'blur(12px)',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ fontSize: '1.25rem' }}>🎵</span>
          <div>
            <div style={{ fontWeight: 800, fontSize: '0.98rem', color: '#f8fafc', letterSpacing: '-0.01em' }}>
              Emotion-Adaptive Music Visualization System
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              Final Year Research Project • Member 4 Showcase
            </div>
          </div>
        </div>

        {/* View Switcher Tabs */}
        <div
          style={{
            display: 'flex',
            backgroundColor: '#070b14',
            padding: '0.25rem',
            borderRadius: '0.5rem',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            gap: '0.25rem',
          }}
        >
          <button
            type="button"
            onClick={() => setActiveTab('personalization')}
            style={{
              padding: '0.45rem 1rem',
              borderRadius: '0.375rem',
              fontSize: '0.85rem',
              fontWeight: 700,
              backgroundColor:
                activeTab === 'personalization'
                  ? 'rgba(56, 189, 248, 0.18)'
                  : 'transparent',
              color: activeTab === 'personalization' ? '#38bdf8' : '#94a3b8',
              border:
                activeTab === 'personalization'
                  ? '1px solid rgba(56, 189, 248, 0.4)'
                  : '1px solid transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              transition: 'all 0.15s ease',
            }}
          >
            <span>✨</span>
            <span>Personalization Demo</span>
            <span
              style={{
                fontSize: '0.65rem',
                backgroundColor: 'rgba(245, 158, 11, 0.2)',
                color: '#fbbf24',
                padding: '0.1rem 0.35rem',
                borderRadius: '0.25rem',
                marginLeft: '0.25rem',
              }}
            >
              VIVA
            </span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('pipeline')}
            style={{
              padding: '0.45rem 1rem',
              borderRadius: '0.375rem',
              fontSize: '0.85rem',
              fontWeight: 700,
              backgroundColor:
                activeTab === 'pipeline'
                  ? 'rgba(168, 85, 247, 0.18)'
                  : 'transparent',
              color: activeTab === 'pipeline' ? '#c084fc' : '#94a3b8',
              border:
                activeTab === 'pipeline'
                  ? '1px solid rgba(168, 85, 247, 0.4)'
                  : '1px solid transparent',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              transition: 'all 0.15s ease',
            }}
          >
            <span>📡</span>
            <span>Pipeline Monitor</span>
            <span
              style={{
                fontSize: '0.65rem',
                backgroundColor: 'rgba(100, 116, 139, 0.25)',
                color: '#94a3b8',
                padding: '0.1rem 0.35rem',
                borderRadius: '0.25rem',
                marginLeft: '0.25rem',
              }}
            >
              DEBUG
            </span>
          </button>
        </div>
      </nav>

      {/* Main View Router */}
      {activeTab === 'personalization' ? (
        <PersonalizationDemo />
      ) : (
        /* Existing Pipeline Monitor View */
        <div
          style={{
            maxWidth: '1300px',
            margin: '0 auto',
            padding: '2rem 1.5rem',
            fontFamily: 'Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
            color: '#e5e7eb',
            minHeight: 'calc(100vh - 65px)',
            boxSizing: 'border-box',
          }}
        >
          {/* Header */}
          <header style={{ marginBottom: '2rem' }}>
            <h1 style={{ fontSize: '1.875rem', fontWeight: 700, margin: '0 0 0.5rem 0', color: '#f8fafc' }}>
              Multi-Tier MER & Personalization Pipeline Monitor
            </h1>
            <p style={{ margin: 0, color: '#94a3b8', fontSize: '0.95rem' }}>
              Real-time debug dashboard monitoring multiplexed WebSocket stream at <code>/ws/mock/mer</code>
            </p>
          </header>

          {/* Connection & Session Bar */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              gap: '1rem',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '1rem 1.25rem',
              backgroundColor: '#1e293b',
              borderRadius: '0.75rem',
              border: '1px solid #334155',
              marginBottom: '2rem',
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <span
                style={{
                  display: 'inline-block',
                  width: '10px',
                  height: '10px',
                  borderRadius: '50%',
                  backgroundColor: getStatusColor(),
                  boxShadow: `0 0 8px ${getStatusColor()}`,
                }}
              />
              <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Status:</span>
              <span style={{ color: getStatusColor(), fontWeight: 600 }}>{status}</span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
              <span style={{ color: '#94a3b8' }}>Shared Session ID:</span>
              <code
                style={{
                  backgroundColor: '#0f172a',
                  padding: '0.25rem 0.5rem',
                  borderRadius: '0.375rem',
                  border: '1px solid #334155',
                  color: '#38bdf8',
                }}
              >
                {sharedSessionId}
              </code>
            </div>
          </div>

          {error && (
            <div
              style={{
                backgroundColor: '#451a1a',
                color: '#f87171',
                border: '1px solid #7f1d1d',
                padding: '0.75rem 1rem',
                borderRadius: '0.5rem',
                marginBottom: '1.5rem',
                fontSize: '0.9rem',
              }}
            >
              {error}
            </div>
          )}

          {/* Grid of 4 Debug Cards */}
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
              gap: '1.5rem',
            }}
          >
            {/* Tier 1 Section */}
            <section
              style={{
                backgroundColor: '#1e293b',
                borderRadius: '0.75rem',
                border: '1px solid #334155',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div style={{ borderBottom: '1px solid #334155', paddingBottom: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0, color: '#38bdf8' }}>Tier 1</h2>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', backgroundColor: '#0f172a', padding: '0.2rem 0.5rem', borderRadius: '0.25rem' }}>
                    ~100 ms
                  </span>
                </div>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>Acoustic & Low-Level</p>
              </div>

              {tier1Event ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.9rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Sequence:</span>
                    <span style={{ fontWeight: 600 }}>{tier1Event.sequence}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Audio Time:</span>
                    <span>{tier1Event.audio_time_ms} ms</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>RMS:</span>
                    <span style={{ fontFamily: 'monospace' }}>{tier1Event.rms}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Spectral Centroid:</span>
                    <span style={{ fontFamily: 'monospace' }}>{tier1Event.spectral_centroid_hz} Hz</span>
                  </div>

                  <div style={{ borderTop: '1px solid #334155', paddingTop: '0.6rem', marginTop: '0.2rem' }}>
                    <span style={{ fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600 }}>Onset</span>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                      <span style={{ color: '#94a3b8' }}>Detected:</span>
                      <span style={{ color: tier1Event.onset.detected ? '#10b981' : '#94a3b8', fontWeight: 600 }}>
                        {tier1Event.onset.detected ? 'True' : 'False'}
                      </span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                      <span style={{ color: '#94a3b8' }}>Strength:</span>
                      <span style={{ fontFamily: 'monospace' }}>
                        {tier1Event.onset.strength !== null ? tier1Event.onset.strength : 'null'}
                      </span>
                    </div>
                  </div>

                  <div style={{ borderTop: '1px solid #334155', paddingTop: '0.6rem', marginTop: '0.2rem' }}>
                    <span style={{ fontSize: '0.8rem', color: '#cbd5e1', fontWeight: 600 }}>Beat Data</span>
                    {tier1Event.beat ? (
                      <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                          <span style={{ color: '#94a3b8' }}>Detected:</span>
                          <span style={{ color: tier1Event.beat.detected ? '#10b981' : '#94a3b8', fontWeight: 600 }}>
                            {tier1Event.beat.detected ? 'True' : 'False'}
                          </span>
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.25rem' }}>
                          <span style={{ color: '#94a3b8' }}>Strength:</span>
                          <span style={{ fontFamily: 'monospace' }}>
                            {tier1Event.beat.strength !== null ? tier1Event.beat.strength : 'null'}
                          </span>
                        </div>
                      </>
                    ) : (
                      <div style={{ color: '#64748b', fontSize: '0.85rem', marginTop: '0.25rem' }}>None</div>
                    )}
                  </div>
                </div>
              ) : (
                <p style={{ color: '#64748b', fontSize: '0.9rem', margin: 'auto 0' }}>Waiting for Tier 1 events...</p>
              )}
            </section>

            {/* Tier 2 Section */}
            <section
              style={{
                backgroundColor: '#1e293b',
                borderRadius: '0.75rem',
                border: '1px solid #334155',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div style={{ borderBottom: '1px solid #334155', paddingBottom: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0, color: '#a855f7' }}>Tier 2</h2>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', backgroundColor: '#0f172a', padding: '0.2rem 0.5rem', borderRadius: '0.25rem' }}>
                    ~3000 ms
                  </span>
                </div>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>Rhythm & Tempo</p>
              </div>

              {tier2Event ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.9rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Sequence:</span>
                    <span style={{ fontWeight: 600 }}>{tier2Event.sequence}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Audio Time:</span>
                    <span>{tier2Event.audio_time_ms} ms</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Tempo BPM:</span>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#a855f7' }}>
                      {tier2Event.tempo_bpm} BPM
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Tempo Confidence:</span>
                    <span style={{ fontFamily: 'monospace' }}>
                      {tier2Event.tempo_confidence !== null ? tier2Event.tempo_confidence : 'null'}
                    </span>
                  </div>
                </div>
              ) : (
                <p style={{ color: '#64748b', fontSize: '0.9rem', margin: 'auto 0' }}>Waiting for Tier 2 events...</p>
              )}
            </section>

            {/* Tier 3 Section */}
            <section
              style={{
                backgroundColor: '#1e293b',
                borderRadius: '0.75rem',
                border: '1px solid #334155',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div style={{ borderBottom: '1px solid #334155', paddingBottom: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0, color: '#f43f5e' }}>Tier 3</h2>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', backgroundColor: '#0f172a', padding: '0.2rem 0.5rem', borderRadius: '0.25rem' }}>
                    ~1000 ms
                  </span>
                </div>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>Valence & Arousal Emotion</p>
              </div>

              {tier3Event ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.9rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Sequence:</span>
                    <span style={{ fontWeight: 600 }}>{tier3Event.sequence}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Audio Time:</span>
                    <span>{tier3Event.audio_time_ms} ms</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Valence:</span>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#38bdf8' }}>
                      {tier3Event.emotion.valence}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Arousal:</span>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#f43f5e' }}>
                      {tier3Event.emotion.arousal}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Confidence:</span>
                    <span style={{ fontFamily: 'monospace' }}>
                      {tier3Event.emotion.confidence !== null ? tier3Event.emotion.confidence : 'null'}
                    </span>
                  </div>
                </div>
              ) : (
                <p style={{ color: '#64748b', fontSize: '0.9rem', margin: 'auto 0' }}>Waiting for Tier 3 events...</p>
              )}
            </section>

            {/* Personalization Recommendation Section */}
            <section
              style={{
                backgroundColor: '#1e293b',
                borderRadius: '0.75rem',
                border: '1px solid #334155',
                padding: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                gap: '1rem',
              }}
            >
              <div style={{ borderBottom: '1px solid #334155', paddingBottom: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h2 style={{ fontSize: '1.25rem', fontWeight: 600, margin: 0, color: '#10b981' }}>
                    Personalization
                  </h2>
                  <span style={{ fontSize: '0.75rem', color: '#64748b', backgroundColor: '#0f172a', padding: '0.2rem 0.5rem', borderRadius: '0.25rem' }}>
                    ~1000 ms
                  </span>
                </div>
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8rem', color: '#94a3b8' }}>
                  Cold-Start Recommendation
                </p>
              </div>

              {recommendationEvent ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem', fontSize: '0.9rem' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Sequence:</span>
                    <span style={{ fontWeight: 600 }}>{recommendationEvent.sequence}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Audio Time:</span>
                    <span>{recommendationEvent.audio_time_ms} ms</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Recommendation ID:</span>
                    <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#38bdf8' }}>
                      {recommendationEvent.recommendation_id}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Recommended Preset:</span>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600, color: '#10b981' }}>
                      {recommendationEvent.recommended_preset_id}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Strategy:</span>
                    <span style={{ fontFamily: 'monospace', color: '#f59e0b', fontWeight: 600 }}>
                      {recommendationEvent.strategy}
                    </span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: '#94a3b8' }}>Score:</span>
                    <span style={{ fontFamily: 'monospace' }}>
                      {recommendationEvent.score !== null ? recommendationEvent.score : 'null'}
                    </span>
                  </div>
                </div>
              ) : (
                <p style={{ color: '#64748b', fontSize: '0.9rem', margin: 'auto 0' }}>
                  Waiting for recommendation events...
                </p>
              )}
            </section>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
