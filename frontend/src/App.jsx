import { useEffect, useRef, useState } from 'react'
import ReactMarkdown from 'react-markdown'
import './App.css'
import AmbientGlow from './AmbientGlow'
import Mascot from './Mascot'
import MiniBarChart from './MiniBarChart'
import Splash from './Splash'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const SPLASH_SESSION_KEY = 'pai_splash_shown'
const LOADING_STATUSES = [
  'Querying MongoDB dataset…',
  'Analyzing results…',
  'Composing your answer…',
]

const SUGGESTIONS = [
  'How many orders were placed in 2013?',
  'What was our highest spending quarter?',
  'What are the 5 most frequently ordered line items?',
  'Which department spent the most overall?',
]

function ChatMessage({ message, onCopy, onRegenerate, onFeedback, canRegenerate }) {
  const isUser = message.role === 'user'
  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      <div className="avatar">
        {isUser ? 'U' : <Mascot size={26} />}
      </div>
      <div className="message-col">
        <div className={`bubble ${isUser ? '' : 'markdown'}`}>
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown>{message.content}</ReactMarkdown>
          )}
          {message.chart && <MiniBarChart {...message.chart} />}
        </div>
        {!isUser && !message.pending && (
          <div className="quick-actions">
            <button type="button" onClick={() => onCopy(message.content)} title="Copy response">
              Copy
            </button>
            {canRegenerate && (
              <button type="button" onClick={onRegenerate} title="Regenerate response">
                Regenerate
              </button>
            )}
            <button
              type="button"
              className={message.feedback === 'up' ? 'active' : ''}
              onClick={() => onFeedback('up')}
              title="Good response"
              aria-label="Good response"
            >
              👍
            </button>
            <button
              type="button"
              className={message.feedback === 'down' ? 'active' : ''}
              onClick={() => onFeedback('down')}
              title="Bad response"
              aria-label="Bad response"
            >
              👎
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content:
        "Hi, I'm your procurement assistant. Ask me about California state purchase orders — order counts, spend by quarter, frequently ordered items, and more.",
    },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingStatus, setLoadingStatus] = useState(LOADING_STATUSES[0])
  const [error, setError] = useState(null)
  const [showSplash, setShowSplash] = useState(
    () => !sessionStorage.getItem(SPLASH_SESSION_KEY)
  )
  const scrollRef = useRef(null)

  function dismissSplash() {
    sessionStorage.setItem(SPLASH_SESSION_KEY, '1')
    setShowSplash(false)
  }

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    if (!loading) return undefined
    let i = 0
    setLoadingStatus(LOADING_STATUSES[0])
    const interval = setInterval(() => {
      i = (i + 1) % LOADING_STATUSES.length
      setLoadingStatus(LOADING_STATUSES[i])
    }, 1400)
    return () => clearInterval(interval)
  }, [loading])

  async function sendMessage(text, historyOverride) {
    const trimmed = text.trim()
    if (!trimmed || loading) return

    const baseMessages = historyOverride ?? messages
    const history = baseMessages.map(({ role, content }) => ({ role, content }))
    const userMessage = { role: 'user', content: trimmed }
    const nextMessages = [...baseMessages, userMessage]
    setMessages(nextMessages)
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: trimmed, history }),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body.detail || `Request failed with status ${res.status}`)
      }
      const data = await res.json()
      setMessages([
        ...nextMessages,
        { role: 'assistant', content: data.response, chart: data.chart || null },
      ])
    } catch (err) {
      setError(err.message || 'Something went wrong talking to the assistant.')
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(e) {
    e.preventDefault()
    sendMessage(input)
  }

  function handleRegenerate(assistantIndex) {
    const userIndex = assistantIndex - 1
    const userMessage = messages[userIndex]
    if (!userMessage || userMessage.role !== 'user') return
    const historyBefore = messages.slice(0, userIndex)
    setMessages(historyBefore)
    sendMessage(userMessage.content, historyBefore)
  }

  function handleFeedback(index, kind) {
    setMessages((prev) =>
      prev.map((m, i) =>
        i === index ? { ...m, feedback: m.feedback === kind ? null : kind } : m
      )
    )
  }

  async function handleCopy(text) {
    try {
      await navigator.clipboard.writeText(text)
    } catch {}
  }

  return (
    <>
      <AmbientGlow />
      <div className="app">
        {showSplash && <Splash onFinish={dismissSplash} />}
        <header className="app-header">
          <div className="app-header-title">
            <Mascot size={36} />
            <h1>Procurement AI Assistant</h1>
          </div>
          <p>California State Procurement — conversational data explorer</p>
        </header>

        <div className="chat-window" ref={scrollRef}>
          {messages.map((m, i) => (
            <ChatMessage
              key={i}
              message={m}
              canRegenerate={i > 0}
              onCopy={handleCopy}
              onRegenerate={() => handleRegenerate(i)}
              onFeedback={(kind) => handleFeedback(i, kind)}
            />
          ))}
          {loading && (
            <div className="message-row assistant">
              <div className="avatar">
                <Mascot size={26} />
              </div>
              <div className="bubble typing">
                <span className="shimmer-dot" />
                <span className="shimmer-dot" />
                <span className="shimmer-dot" />
                {loadingStatus}
              </div>
            </div>
          )}
          {error && <div className="error-banner">{error}</div>}
        </div>

        <div className="suggestions">
          {SUGGESTIONS.map((s) => (
            <button key={s} type="button" onClick={() => sendMessage(s)} disabled={loading}>
              {s}
            </button>
          ))}
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about procurement orders, spend, or line items…"
            disabled={loading}
          />
          <button type="submit" disabled={loading || !input.trim()}>
            Send
          </button>
        </form>
      </div>
    </>
  )
}
