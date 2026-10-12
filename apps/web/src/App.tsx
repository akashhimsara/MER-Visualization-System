import { useEffect, useState, useRef } from 'react'
import './App.css'
import type { MERTier3Event } from './types/mer'

function App() {
  const [event, setEvent] = useState<MERTier3Event | null>(null)
  const [status, setStatus] = useState<string>('Disconnected')
  const [error, setError] = useState<string | null>(null)
  const wsRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    let reconnectTimeout: ReturnType<typeof setTimeout>;
    
    const connect = () => {
      setStatus('Connecting...')
      const baseUrl = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000'
      const wsUrl = `${baseUrl}/ws/mock/mer-tier3`
      
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      ws.onopen = () => {
        setStatus('Connected')
        setError(null)
      }

      ws.onmessage = (msg) => {
        try {
          const data = JSON.parse(msg.data) as MERTier3Event
          setEvent(data)
        } catch (e) {
          setError('Malformed JSON received')
        }
      }

      ws.onclose = () => {
        setStatus('Disconnected')
        reconnectTimeout = setTimeout(connect, 2000)
      }

      ws.onerror = () => {
        setStatus('Error')
      }
    }

    connect()

    return () => {
      clearTimeout(reconnectTimeout)
      if (wsRef.current) {
        wsRef.current.close()
      }
    }
  }, [])

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>MER Tier 3 Mock Stream</h1>
      
      <div style={{ marginBottom: '1rem' }}>
        <strong>Status: </strong> 
        <span style={{ 
          color: status === 'Connected' ? '#4caf50' : 
                 status === 'Error' ? '#f44336' : 
                 status === 'Connecting...' ? '#ff9800' : '#9e9e9e' 
        }}>
          {status}
        </span>
      </div>

      {error && <div style={{ color: '#f44336', marginBottom: '1rem' }}>{error}</div>}

      {event ? (
        <div style={{
          background: '#242424',
          color: '#e0e0e0',
          padding: '1.5rem',
          borderRadius: '8px',
          fontFamily: 'monospace',
          border: '1px solid #444',
          textAlign: 'left'
        }}>
          <p><strong>Session ID:</strong> {event.session_id}</p>
          <p><strong>Sequence:</strong> {event.sequence}</p>
          <p><strong>Audio Time (ms):</strong> {event.audio_time_ms}</p>
          <hr style={{ borderColor: '#444', margin: '1rem 0' }} />
          <p><strong>Valence:</strong> {event.emotion.valence}</p>
          <p><strong>Arousal:</strong> {event.emotion.arousal}</p>
          <p><strong>Confidence:</strong> {event.emotion.confidence !== null ? event.emotion.confidence : 'null'}</p>
        </div>
      ) : (
        <p>Waiting for data...</p>
      )}
    </div>
  )
}

export default App
