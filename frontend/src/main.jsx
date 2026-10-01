import React, { useState, useRef, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

const API = 'https://ai-college-helpdesk-4ha1.onrender.com'

const SUGGESTIONS = [
  ['Courses', 'What courses are offered by the college?'],
  ['Departments', 'What departments are available?'],
  ['Admissions', 'Tell me about the admission process.'],
  ['Examinations', 'Tell me about examinations.'],
  ['Facilities', 'What facilities are available?'],
  ['Contact', 'Give me the college contact information.'],
]

/* ---------- icons ---------- */
const Icon = ({ d, size = 20, fill = 'none' }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill={fill} stroke="currentColor"
    strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {d.map((p, i) => <path key={i} d={p} />)}
  </svg>
)
const CapIcon = () => <Icon d={['M22 10 12 5 2 10l10 5 10-5z', 'M6 12v5c3 2.5 9 2.5 12 0v-5']} />
const SendIcon = () => <Icon d={['M5 12h14', 'm13 6 6 6-6 6']} />
const PlusIcon = () => <Icon size={16} d={['M12 5v14', 'M5 12h14']} />
const WarnIcon = () => <Icon d={['M12 9v4', 'M12 17h.01', 'M10.3 3.9 2.4 18a2 2 0 0 0 1.7 3h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z']} />
const Check = () => <Icon size={13} d={['m5 12 5 5L20 7']} />
const Avatar = () => <span className="avatar"><CapIcon /></span>

/* ---------- answer formatting (presentation only) ---------- */
const BULLET = /^([-*•●▪◦]|\d+[.)])\s+/
const ABBR = /\b(Dr|Mr|Mrs|Ms|Prof|St|No|Sri|Smt)\.$/

function renderInline(text) {
  return text.split(/(\*\*[^*]+\*\*|https?:\/\/[^\s)]*[^\s).,;])/g).map((part, i) => {
    if (/^\*\*[^*]+\*\*$/.test(part)) return <strong key={i}>{part.slice(2, -2)}</strong>
    if (/^https?:\/\//.test(part))
      return <a key={i} href={part} target="_blank" rel="noopener noreferrer">{part}</a>
    return part
  })
}

function splitLabel(text) {
  const m =
    text.match(/^\*\*([^*]{2,40}?):\*\*\s*(.+)$/) ||
    text.match(/^\*\*([^*]{2,40}?)\*\*:\s*(.+)$/) ||
    text.match(/^([^:*]{2,40}):\s+(.+)$/)
  return m ? { label: m[1].trim(), value: m[2].trim() } : null
}

function splitSentences(text) {
  return text
    .split(/(?<=[a-z0-9)][.!?])\s+(?=[A-Z])/)
    .reduce((out, s) => {
      if (out.length && ABBR.test(out[out.length - 1])) out[out.length - 1] += ' ' + s
      else out.push(s)
      return out
    }, [])
}

function parseAnswer(text = '') {
  const blocks = []
  let block = null
  let list = null
  const ensure = () => {
    if (!block) { block = { heading: null, content: [] }; blocks.push(block) }
  }

  text.replace(/\t/g, '  ').split('\n').forEach((raw) => {
    const line = raw.trim()
    if (!line) return
    const indent = raw.length - raw.trimStart().length

    const md = line.match(/^#{1,6}\s+(.*)$/)
    const bold = line.match(/^\*\*([^*]+?)\*\*:?$/)
    const colon = line.endsWith(':') && !BULLET.test(line) && line.length < 80
    if (md || bold || colon) {
      const heading = (md ? md[1] : bold ? bold[1] : line.slice(0, -1)).replace(/\*\*/g, '')
      block = { heading, content: [] }
      blocks.push(block)
      list = null
      return
    }

    ensure()
    const m = line.match(BULLET)
    if (m) {
      const ordered = /^\d/.test(m[1])
      const item = { text: line.replace(BULLET, ''), sub: [] }
      if (indent >= 2 && list && list.items.length) {
        list.items[list.items.length - 1].sub.push(item)
      } else {
        if (!list || list.ordered !== ordered) {
          list = { type: 'list', ordered, start: ordered ? parseInt(m[1], 10) : 1, items: [] }
          block.content.push(list)
        }
        list.items.push(item)
      }
      return
    }

    list = null
    const sentences = splitSentences(line)
    if (sentences.length >= 3) {
      block.content.push({
        type: 'list', ordered: false, start: 1,
        items: sentences.map((s) => ({ text: s, sub: [] })),
      })
    } else {
      block.content.push({ type: 'p', text: line })
    }
  })
  return blocks
}

function Item({ item }) {
  const parts = splitLabel(item.text)
  return (
    <li>
      {parts ? (
        <>
          <span className="li-label">{parts.label}</span>
          <span className="li-value">{renderInline(parts.value)}</span>
        </>
      ) : (
        renderInline(item.text)
      )}
      {item.sub.length > 0 && (
        <ul>{item.sub.map((s, i) => <Item key={i} item={s} />)}</ul>
      )}
    </li>
  )
}

function headingMeta(h) {
  const clean = h.replace(/^[^\p{L}\p{N}]+/u, '').trim()
  const hasEmoji = clean !== h.trim()
  if (/^arts?\b/i.test(clean) && clean.length < 30)
    return { cls: 'arts', text: hasEmoji ? h : `📚 ${h.toUpperCase()}` }
  if (/^science\b/i.test(clean) && clean.length < 30)
    return { cls: 'science', text: hasEmoji ? h : `🔬 ${h.toUpperCase()}` }
  return { cls: '', text: h }
}

function FormattedAnswer({ text }) {
  const blocks = parseAnswer(text)
  if (!blocks.length) return <p>No answer was returned.</p>
  return (
    <div className="answer">
      {blocks.map((b, i) => {
        const meta = b.heading ? headingMeta(b.heading) : null
        return (
          <section key={i} className="fa-block">
            {meta && <h4 className={`fa-head ${meta.cls}`}>{meta.text}</h4>}
            {b.content.map((c, j) =>
              c.type === 'p' ? (
                <p key={j}>{renderInline(c.text)}</p>
              ) : c.ordered ? (
                <ol key={j} start={c.start}>{c.items.map((it, k) => <Item key={k} item={it} />)}</ol>
              ) : (
                <ul key={j}>{c.items.map((it, k) => <Item key={k} item={it} />)}</ul>
              )
            )}
          </section>
        )
      })}
    </div>
  )
}

function Sources({ sources }) {
  return (
    <div className="sources">
      <span className="sources-label">
        <Check /> Verified Source{sources.length > 1 ? 's' : ''}
      </span>
      <div className="chips-row">
        {sources.map((s, i) => {
          const obj = typeof s === 'string' ? { document: s } : s
          const name = obj.document || obj.title || obj.name || obj.url
          const label = [name, obj.section, obj.page ? `Page ${obj.page}` : null]
            .filter(Boolean).join(' — ')
          return obj.url ? (
            <a key={i} className="source" href={obj.url} target="_blank" rel="noopener noreferrer">{label}</a>
          ) : (
            <span key={i} className="source">{label}</span>
          )
        })}
      </div>
    </div>
  )
}

function Welcome() {
  return (
    <div className="msg assistant rise">
      <Avatar />
      <div className="bubble welcome">
        <strong className="who">GOKU Assistant</strong>
        <p className="welcome-title">Hello! I am the Karan Arts and Science College AI Helpdesk.</p>
        <p>
          Ask me about courses, departments, admissions, examinations, facilities, fees,
          contact information, or other college information.
        </p>
      </div>
    </div>
  )
}

/* ---------- app ---------- */
function App() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [sessionId, setSessionId] = useState(null)

  const chatRef = useRef(null)
  const taRef = useRef(null)
  const chatGen = useRef(0)
  const idRef = useRef(0)
  const nextId = () => ++idRef.current
  const desktop = () => window.matchMedia('(min-width: 769px)').matches

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  useEffect(() => {
    const ta = taRef.current
    if (!ta) return
    ta.style.height = 'auto'
    ta.style.height = Math.min(ta.scrollHeight, 140) + 'px'
  }, [input])

  useEffect(() => {
    if (desktop()) taRef.current?.focus()
  }, [])

  async function send(raw, { retry = false } = {}) {
    const text = raw.trim()
    if (!text || loading) return
    const gen = chatGen.current

    setMessages((prev) =>
      retry ? prev.filter((m) => !m.error) : [...prev, { id: nextId(), role: 'student', text }]
    )
    setInput('')
    setLoading(true)

    try {
      const response = await fetch(`${API}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      })
      if (!response.ok) throw new Error(`Server error: ${response.status}`)
      const data = await response.json()
      if (!data) throw new Error('The server returned an empty response.')
      if (gen !== chatGen.current) return

      if (data.session_id) setSessionId(data.session_id)
      const sources = data.sources || []
      setMessages((prev) => [
        ...prev,
        {
          id: nextId(),
          role: 'assistant',
          text: data.answer,
          sources,
          confidence: data.confidence,
          fallback: data.fallback,
          verified: data.verified === true || (!data.fallback && sources.length > 0),
        },
      ])
    } catch (error) {
      console.error(error)
      if (gen !== chatGen.current) return
      setMessages((prev) => [...prev, { id: nextId(), role: 'assistant', error: true, retryText: text }])
    } finally {
      if (gen === chatGen.current) {
        setLoading(false)
        if (desktop()) taRef.current?.focus()
      }
    }
  }

  function startNewChat() {
    chatGen.current += 1
    setMessages([])
    setSessionId(null)
    setInput('')
    setLoading(false)
    if (desktop()) taRef.current?.focus()
  }

  function onKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      send(input)
    }
  }

  return (
    <div className="stage">
      <main className="shell">
        <header className="topbar">
          <div className="brand">
            <span className="logo"><CapIcon /></span>
            <div>
              <h1>Karan Arts and Science College AI Helpdesk</h1>
              <p>Verified college information assistant</p>
            </div>
          </div>
          <div className="top-actions">
            <span className="status"><i /> AI Online</span>
            <button className="new-chat" onClick={startNewChat}>
              <PlusIcon /> New Chat
            </button>
          </div>
        </header>

        <section className="chat" ref={chatRef} aria-live="polite">
          <Welcome />

          {messages.map((m) =>
            m.error ? (
              <div key={m.id} className="msg assistant rise">
                <Avatar />
                <div className="bubble error">
                  <strong className="err-title"><WarnIcon /> Unable to connect to AI Helpdesk</strong>
                  <p>Please make sure the college helpdesk server is running.</p>
                  <button className="retry" onClick={() => send(m.retryText, { retry: true })} disabled={loading}>
                    Retry
                  </button>
                </div>
              </div>
            ) : m.role === 'student' ? (
              <div key={m.id} className="msg student rise">
                <div className="bubble"><p>{m.text}</p></div>
              </div>
            ) : (
              <div key={m.id} className="msg assistant rise">
                <Avatar />
                <div className="bubble">
                  <div className="who-row">
                    <strong className="who">GOKU Assistant</strong>
                    {m.verified && <span className="badge"><Check /> Verified</span>}
                  </div>
                  <FormattedAnswer text={m.text} />
                  {m.sources.length > 0 && <Sources sources={m.sources} />}
                </div>
              </div>
            )
          )}

          {loading && (
            <div className="msg assistant rise">
              <Avatar />
              <div className="bubble thinking">
                <span>GOKU Assistant is thinking</span>
                <span className="dots"><i /><i /><i /></span>
              </div>
            </div>
          )}
        </section>

        <footer className="dock">
          <div className="chips" role="list">
            {SUGGESTIONS.map(([label, q]) => (
              <button key={label} role="listitem" className="chip" disabled={loading} onClick={() => send(q)}>
                {label}
              </button>
            ))}
          </div>
          <form className="composer" onSubmit={(e) => { e.preventDefault(); send(input) }}>
            <textarea
              ref={taRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask about courses, admissions, departments, exams, facilities..."
              aria-label="Ask the college AI helpdesk"
            />
            <button type="submit" className="send" disabled={loading || !input.trim()} aria-label="Send message">
              <SendIcon />
            </button>
          </form>
        </footer>
      </main>
    </div>
  )
}

createRoot(document.getElementById('root')).render(<App />)