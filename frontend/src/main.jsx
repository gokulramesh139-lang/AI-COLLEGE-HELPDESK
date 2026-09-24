import React, { useState } from 'react'
import { createRoot } from 'react-dom/client'
import './style.css'

const API = 'http://127.0.0.1:8000'

function App() {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      text: 'Hello! I am the Karan Arts and Science College AI Helpdesk. Ask me about courses, facilities, admissions, contact information, examination, or other college information.',
    },
  ])

  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  // Store the conversation session ID
  const [sessionId, setSessionId] = useState(null)

  async function sendMessage(e) {
    e.preventDefault()

    const text = input.trim()

    if (!text || loading) {
      return
    }

    // Display student's question immediately
    setMessages(prev => [
      ...prev,
      {
        role: 'student',
        text: text,
      },
    ])

    setInput('')
    setLoading(true)

    try {
      const response = await fetch(
        `${API}/api/v1/chat`,
        {
          method: 'POST',

          headers: {
            'Content-Type': 'application/json',
          },

          body: JSON.stringify({
            message: text,
            session_id: sessionId,
          }),
        }
      )

      if (!response.ok) {
        throw new Error(
          `Server error: ${response.status}`
        )
      }

      const data = await response.json()

if (!data) {
  throw new Error(
    'The server returned an empty response.'
  )
}

// Save the session ID returned by backend
if (data.session_id) {
  setSessionId(data.session_id)
}
      // Add AI response
      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text: data.answer,
          sources: data.sources || [],
          confidence: data.confidence,
          fallback: data.fallback,
        },
      ])

    } catch (error) {

      console.error(error)

      setMessages(prev => [
        ...prev,
        {
          role: 'assistant',
          text:
            'The helpdesk server could not be reached. Please make sure the FastAPI backend is running.',
          fallback: true,
        },
      ])

    } finally {

      setLoading(false)

    }
  }

  function startNewChat() {

    setMessages([
      {
        role: 'assistant',
        text:
          'Hello! I am the Karan Arts and Science College AI Helpdesk. How can I help you today?',
      },
    ])

    setSessionId(null)
    setInput('')
  }

  return (
    <main className="app">

      {/* HEADER */}

      <header>

        <div>

          <h1>
            🎓 Karan Arts and Science College
            AI Helpdesk
          </h1>

          <p>
            Verified college information assistant
          </p>

        </div>

        <div className="header-actions">

          <span className="status">
            ● Online
          </span>

          <button
            className="new-chat"
            onClick={startNewChat}
          >
            New Chat
          </button>

        </div>

      </header>


      {/* CHAT AREA */}

      <section
        className="chat"
        aria-live="polite"
      >

        {messages.map((message, index) => (

          <div
            key={index}
            className={`message ${message.role}`}
          >

            <div className="bubble">

              <strong>

                {message.role === 'student'
                  ? 'You'
                  : 'GOKU Assistant'}

              </strong>

              <p>
                {message.text}
              </p>


              {/* SOURCES */}

              {message.sources &&
                message.sources.length > 0 && (

                <div className="sources">

                  <b>
                    📚 Sources
                  </b>

                  {message.sources.map(
                    (source, sourceIndex) => (

                    <div
                      key={sourceIndex}
                    >

                      📄{' '}

                      {source.document}

                      {source.section
                        ? ` — ${source.section}`
                        : ''}

                      {source.page
                        ? ` — Page ${source.page}`
                        : ''}

                    </div>

                  ))}

                </div>

              )}


              {/* CONFIDENCE */}

              

            </div>

          </div>

        ))}


        {/* LOADING */}

        {loading && (

          <div className="message assistant">

            <div className="bubble">

              <strong>
                AI Assistant
              </strong>

              <p>
                Searching the college
                knowledge base...
              </p>

            </div>

          </div>

        )}

      </section>


      {/* MESSAGE BOX */}

      <form
        className="composer"
        onSubmit={sendMessage}
      >

        <input
          value={input}

          onChange={e =>
            setInput(e.target.value)
          }

          placeholder="Ask about courses, admissions, exams, facilities..."

          aria-label="Ask the college AI helpdesk"

          disabled={loading}
        />

        <button
          type="submit"
          disabled={
            loading ||
            !input.trim()
          }
        >
          {loading
            ? 'Searching...'
            : 'Send'}
        </button>

      </form>

    </main>
  )
}


createRoot(
  document.getElementById('root')
).render(
  <App />
)