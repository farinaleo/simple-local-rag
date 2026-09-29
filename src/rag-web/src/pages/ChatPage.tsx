import { useRef, useState } from 'react'
import Markdown from 'react-markdown'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { streamQuery, useQueryHistory } from '@/hooks/queries'
import type { QueryHistoryItem, QuerySource, StreamEvent } from '@/types'

interface ChatMessage {
  question: string
  answer: string
  sources: QuerySource[]
  error: boolean
  streaming: boolean
}

function SourcesList({ sources }: { sources: QuerySource[] }) {
  if (sources.length === 0) return null
  return (
    <div className="mt-2 flex flex-wrap gap-1.5">
      {sources.map((source) => (
        <a
          key={`${source.document.id}-${source.ordinal}`}
          href="/documents"
          className="rounded-md bg-muted px-2 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-accent-foreground"
          title={source.content}
        >
          {source.document.original_filename} #{source.ordinal}
        </a>
      ))}
    </div>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  return (
    <div className="space-y-2">
      <p className="ml-auto max-w-[80%] rounded-lg bg-primary px-3 py-2 text-sm text-primary-foreground">
        {message.question}
      </p>
      <div className="max-w-[80%] rounded-lg bg-muted px-3 py-2 text-sm">
        {message.error ? (
          <p className="text-red-400">{message.answer}</p>
        ) : (
          <Markdown>{message.answer}</Markdown>
        )}
        {message.streaming && <span className="animate-pulse">▍</span>}
        <SourcesList sources={message.sources} />
      </div>
    </div>
  )
}

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const { data: history } = useQueryHistory()
  const listEndRef = useRef<HTMLDivElement | null>(null)

  const send = async () => {
    const trimmed = question.trim()
    if (!trimmed || isStreaming) return
    setQuestion('')
    setIsStreaming(true)
    const index = messages.length
    setMessages((prev) => [
      ...prev,
      { question: trimmed, answer: '', sources: [], error: false, streaming: true },
    ])
    try {
      await streamQuery(trimmed, (event: StreamEvent) => {
        setMessages((prev) => {
          const next = [...prev]
          const current = { ...next[index] }
          if (event.type === 'token') current.answer += event.text
          else if (event.type === 'sources') {
            current.sources = event.sources
            current.streaming = false
          } else if (event.type === 'error') {
            current.answer = event.detail
            current.error = true
            current.streaming = false
          }
          next[index] = current
          return next
        })
        listEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      })
    } catch {
      setMessages((prev) => {
        const next = [...prev]
        next[index] = {
          ...next[index],
          answer: 'Connection to the API failed — is the backend running?',
          error: true,
          streaming: false,
        }
        return next
      })
    } finally {
      setIsStreaming(false)
      listEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const restoreHistory = (item: QueryHistoryItem) => {
    if (isStreaming) return
    setMessages([
      {
        question: item.question,
        answer: item.answer,
        sources: item.sources,
        error: item.answer.startsWith('[generation failed]'),
        streaming: false,
      },
    ])
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[1fr_240px]">
      <div className="flex min-h-[60vh] flex-col space-y-4">
        <h1 className="text-lg font-semibold">Chat</h1>
        <div className="flex flex-1 flex-col gap-4">
          {messages.length === 0 && (
            <p className="text-sm text-muted-foreground">
              Ask a question about your indexed documents…
            </p>
          )}
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}
          <div ref={listEndRef} />
        </div>
        <form
          className="flex gap-2"
          onSubmit={(event) => {
            event.preventDefault()
            void send()
          }}
        >
          <Input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Ask a question…"
            disabled={isStreaming}
          />
          <Button type="submit" disabled={isStreaming || question.trim() === ''}>
            Send
          </Button>
        </form>
      </div>
      <aside className="space-y-2">
        <h2 className="text-sm font-semibold">History</h2>
        <div className="space-y-1">
          {(history ?? []).map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => restoreHistory(item)}
              className="w-full truncate rounded-md px-2 py-1.5 text-left text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
              title={item.question}
            >
              {item.question}
            </button>
          ))}
        </div>
      </aside>
    </div>
  )
}
