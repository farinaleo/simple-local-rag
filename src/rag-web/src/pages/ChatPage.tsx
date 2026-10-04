import { motion } from 'framer-motion'
import Markdown from 'react-markdown'
import { useRef, useState } from 'react'

import { PageHeader, PageTransition } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
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
    <p className="px-1 text-[11px] text-zinc-500">
      📎 Source{sources.length > 1 ? 's' : ''} :{' '}
      {sources.map((source, index) => (
        <span key={`${source.document.id}-${source.ordinal}`}>
          {index > 0 && ', '}
          <span className="text-violet-300">
            {source.document.original_filename} #{source.ordinal}
          </span>
        </span>
      ))}
    </p>
  )
}

function MessageBubble({ message }: { message: ChatMessage }) {
  return (
    <div className="space-y-1.5">
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25 }}
        className="flex justify-end"
      >
        <div className="max-w-[80%] rounded-2xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-4 py-2.5 text-sm leading-relaxed text-white shadow-lg shadow-violet-600/20">
          {message.question}
        </div>
      </motion.div>
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, delay: 0.05 }}
        className="flex justify-start"
      >
        <div className="max-w-[80%] space-y-1.5">
          <div className="rounded-2xl border border-white/10 bg-zinc-800/80 px-4 py-2.5 text-sm leading-relaxed text-zinc-100">
            {message.error ? (
              <p className="text-red-400">{message.answer}</p>
            ) : (
              <Markdown>{message.answer}</Markdown>
            )}
            {message.streaming && (
              <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse rounded bg-violet-400 align-middle" />
            )}
          </div>
          {!message.streaming && <SourcesList sources={message.sources} />}
        </div>
      </motion.div>
    </div>
  )
}

function HistoryCard({ item, onClick }: { item: QueryHistoryItem; onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group w-full cursor-pointer rounded-2xl border border-white/10 bg-white/5 p-4 text-left backdrop-blur transition-all hover:border-violet-500/40 hover:bg-white/[0.08]"
    >
      <p className="truncate font-medium text-zinc-100">{item.question}</p>
      <p className="mt-0.5 truncate text-xs text-zinc-400">
        {new Date(item.created_at).toLocaleDateString('fr-FR')} · {item.sources.length} source
        {item.sources.length > 1 ? 's' : ''}
      </p>
    </button>
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
          answer: "Connexion à l'API impossible — le backend est-il lancé ?",
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
    <PageTransition>
      <div className="space-y-6">
        <PageHeader
          title="Chats"
          subtitle="Discutez avec votre RAG et retrouvez vos dernières discussions."
        />

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.08 }}
          className="flex h-[560px] flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur"
        >
          <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-sm shadow-lg shadow-violet-600/25">
              💬
            </div>
            <div className="min-w-0 flex-1">
              <h2 className="truncate font-semibold text-zinc-100">Discussion en cours</h2>
              <p className="text-xs text-zinc-400">{new Date().toLocaleDateString('fr-FR')}</p>
            </div>
          </div>

          <ScrollArea className="flex-1 px-4">
            <div className="space-y-4 py-4">
              {messages.length === 0 && (
                <div className="py-16 text-center text-sm text-zinc-500">
                  Posez votre première question sur vos documents ✨
                </div>
              )}
              {messages.map((message, index) => (
                <MessageBubble key={index} message={message} />
              ))}
              <div ref={listEndRef} />
            </div>
          </ScrollArea>

          <div className="flex gap-2 border-t border-white/10 p-3">
            <Input
              className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100 placeholder:text-zinc-500 focus-visible:ring-violet-500/50"
              value={question}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={(event) => event.key === 'Enter' && void send()}
              placeholder="Posez une question sur vos documents…"
              disabled={isStreaming}
            />
            <Button
              className="rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-600/25 transition-transform hover:scale-[1.03] hover:from-violet-500 hover:to-fuchsia-500"
              onClick={() => void send()}
              disabled={isStreaming || question.trim() === ''}
            >
              Envoyer ↑
            </Button>
          </div>
        </motion.div>

        <div className="space-y-3">
          <h2 className="px-1 text-xs font-semibold uppercase tracking-wider text-zinc-500">
            Dernières discussions
          </h2>
          <div className="space-y-2">
            {(history ?? []).slice(0, 5).map((item) => (
              <HistoryCard key={item.id} item={item} onClick={() => restoreHistory(item)} />
            ))}
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
