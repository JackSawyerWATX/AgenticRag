import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import './knowledge-app.css'

type Message = {
  role: 'user' | 'assistant'
  content: string
}

function KnowledgeApp() {
  const [messages, setMessages] = useState<Message[]>([])
  const [question, setQuestion] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [serviceStatus, setServiceStatus] = useState('CONNECTING')

  useEffect(() => {
    fetch('/api/health')
      .then((response) => setServiceStatus(response.ok ? 'SYSTEM READY' : 'SERVICE OFFLINE'))
      .catch(() => setServiceStatus('SERVICE OFFLINE'))
  }, [])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const message = question.trim()

    if (!message || isLoading) {
      return
    }

    setMessages((currentMessages) => [...currentMessages, { role: 'user', content: message }])
    setQuestion('')
    setIsLoading(true)

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
      })
      const data = (await response.json()) as { answer?: string; detail?: string }

      if (!response.ok || !data.answer) {
        throw new Error(data.detail ?? 'The knowledge service could not complete the request.')
      }

      setMessages((currentMessages) => [...currentMessages, { role: 'assistant', content: data.answer! }])
    } catch (error) {
      const content = error instanceof Error ? error.message : 'The knowledge service is unavailable.'
      setMessages((currentMessages) => [...currentMessages, { role: 'assistant', content }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="knowledge-shell">
      <aside className="knowledge-sidebar">
        <a className="knowledge-wordmark" href="https://syntroniclabs.dev" target="_blank" rel="noreferrer">
          SYNTRONIC <span>LABS</span>
        </a>
        <div className="knowledge-sidebar-copy">
          <p className="knowledge-label">Knowledge system</p>
          <p>Document-grounded AI for focused research and retrieval.</p>
        </div>
        <button className="knowledge-clear" type="button" onClick={() => setMessages([])} disabled={!messages.length}>
          Clear session
        </button>
        <p className="knowledge-footer">LOCAL ENVIRONMENT / 01</p>
      </aside>

      <section className="knowledge-workspace">
        <header className="knowledge-header">
          <p className="knowledge-label">Research interface / 01</p>
          <h1>Context, <span>retrieved.</span></h1>
          <p>Ask questions against the documents indexed in this knowledge system.</p>
        </header>
        <div className={`knowledge-status ${serviceStatus === 'SYSTEM READY' ? 'is-ready' : ''}`}>
          <span aria-hidden="true"></span>{serviceStatus} / SUPABASE VECTOR INDEX
        </div>

        <section className="knowledge-conversation" aria-live="polite">
          {!messages.length && (
            <div className="knowledge-empty">
              <h2>What do you need to know?</h2>
              <p>Start a conversation below. Responses are grounded in the indexed document collection.</p>
            </div>
          )}
          {messages.map((message, index) => (
            <article className={`knowledge-message ${message.role}`} key={`${message.role}-${index}`}>
              <p className="knowledge-label">{message.role === 'user' ? 'Your query' : 'Knowledge system'}</p>
              <p>{message.content}</p>
            </article>
          ))}
          {isLoading && <article className="knowledge-message assistant knowledge-loading"><p>Searching indexed context</p></article>}
        </section>

        <form className="knowledge-composer" onSubmit={handleSubmit}>
          <label className="knowledge-sr-only" htmlFor="question">Ask the knowledge system</label>
          <textarea id="question" value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask the knowledge system" rows={1} disabled={isLoading} />
          <button type="submit" disabled={!question.trim() || isLoading}>Send</button>
        </form>
      </section>
    </main>
  )
}

export default KnowledgeApp