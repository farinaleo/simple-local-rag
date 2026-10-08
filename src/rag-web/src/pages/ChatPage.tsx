import { motion } from 'framer-motion'
import { toast } from 'sonner'
import Markdown from 'react-markdown'
import { useRef, useState } from 'react'
import { PageHeader, PageTransition } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'
import { useSession } from '@/hooks/auth'
import {
  streamQuery,
  useConversation,
  useConversations,
  useDeleteConversation,
} from '@/hooks/queries'
import type { ConversationDetail, QuerySource, StreamEvent } from '@/types'

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
        <div className="w-fit max-w-[80%] rounded-2xl bg-gradient-to-r from-violet-600 to-fuchsia-600 px-4 py-2.5 text-sm leading-relaxed text-white shadow-lg shadow-violet-600/20">
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
          <div className="w-fit max-w-full rounded-2xl border border-white/10 bg-zinc-800/80 px-4 py-2.5 text-sm leading-relaxed text-zinc-100 [&_p:first-child]:mt-0 [&_p]:mt-2 [&_p:last-child]:mb-0">
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

function ConversationCard({
  title,
  updatedAt,
  active,
  onClick,
  onDelete,
}: {
  title: string
  updatedAt: string
  active: boolean
  onClick: () => void
  onDelete: () => void
}) {
  return (
    <div
      className={`group relative flex h-10 w-full cursor-pointer items-center rounded-xl border px-3 text-left backdrop-blur transition-all ${
        active
          ? 'border-violet-500/60 bg-violet-500/10'
          : 'border-white/10 bg-white/5 hover:border-violet-500/40 hover:bg-white/[0.08]'
      }`}
      onClick={onClick}
    >
      <p className="min-w-0 flex-1 truncate text-sm font-medium text-zinc-100">{title}</p>
      <p className="ml-2 shrink-0 text-xs text-zinc-400 transition-all duration-200 group-hover:-translate-x-7 group-hover:opacity-0">
        {new Date(updatedAt).toLocaleDateString('fr-FR')}
      </p>
      <button
        type="button"
        aria-label="Supprimer la conversation"
        className="absolute right-2 top-1/2 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-lg text-xs text-zinc-500 opacity-0 transition-all duration-200 hover:bg-red-500/20 hover:text-red-400 group-hover:opacity-100"
        onClick={(event) => {
          event.stopPropagation()
          onDelete()
        }}
      >
        🗑
      </button>
    </div>
  )
}

function messagesFromConversation(detail: ConversationDetail): ChatMessage[] {
  return detail.messages.map((message) => ({
    question: message.question,
    answer: message.answer,
    sources: message.sources,
    error: message.answer.startsWith('[generation failed]'),
    streaming: false,
  }))
}

export default function ChatPage() {
  const [conversationId, setConversationId] = useState<number | null>(null)
  const [streamed, setStreamed] = useState<ChatMessage[]>([])
  const [question, setQuestion] = useState('')
  const [isStreaming, setIsStreaming] = useState(false)
  const { data: session } = useSession()
  const { data: conversations } = useConversations(!!session)
  const { data: conversationDetail } = useConversation(conversationId, !!session)
  const deleteConversation = useDeleteConversation()
  const listEndRef = useRef<HTMLDivElement | null>(null)

  const loadedMessages = conversationDetail ? messagesFromConversation(conversationDetail) : []

  const send = async () => {
    const trimmed = question.trim()
    if (!trimmed || isStreaming) return
    setQuestion('')
    setIsStreaming(true)
    const index = streamed.length
    setStreamed((prev) => [
      ...prev,
      { question: trimmed, answer: '', sources: [], error: false, streaming: true },
    ])
    try {
      await streamQuery(trimmed, conversationId, (event: StreamEvent) => {
        setStreamed((prev) => {
          const next = [...prev]
          const current = { ...next[index] }
          if (event.type === 'token') current.answer += event.text
          else if (event.type === 'sources') {
            current.sources = event.sources
            current.streaming = false
            if (conversationId === null && event.conversationId !== null) {
              setConversationId(event.conversationId)
            }
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
      setStreamed((prev) => {
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

  const startNewConversation = () => {
    if (isStreaming) return
    setConversationId(null)
    setStreamed([])
  }

  const removeConversation = (id: number) => {
    deleteConversation.mutate(id, {
      onSuccess: () => {
        toast.success('Conversation supprimée')
        if (conversationId === id) {
          setConversationId(null)
          setStreamed([])
        }
      },
      onError: (error) => toast.error(error.message),
    })
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <PageHeader
          title="Chats"
          subtitle="Discutez avec votre RAG et retrouvez vos conversations."
        />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-[240px_minmax(0,1fr)]">
          <motion.div
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.35 }}
            className="flex flex-col space-y-3 lg:h-[560px]"
          >
            <Button
              className="w-full rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-600/25 transition-transform hover:scale-[1.02] hover:from-violet-500 hover:to-fuchsia-500"
              onClick={startNewConversation}
              disabled={isStreaming}
            >
              ＋ Nouvelle discussion
            </Button>
            <h2 className="px-1 text-xs font-semibold uppercase tracking-wider text-zinc-500">
              Conversations
            </h2>
            <div className="min-h-0 flex-1 overflow-y-auto">
              <div className="space-y-2">
                {(conversations ?? []).map((conversation) => (
                  <ConversationCard
                    key={conversation.id}
                    title={conversation.title}
                    updatedAt={conversation.updated_at}
                    active={conversation.id === conversationId}
                    onClick={() => setConversationId(conversation.id)}
                    onDelete={() => removeConversation(conversation.id)}
                  />
                ))}
                {conversations?.length === 0 && (
                  <p className="px-1 py-8 text-center text-xs text-zinc-500">
                    Aucune conversation pour l'instant.
                  </p>
                )}
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.08 }}
            className="flex flex-col overflow-hidden rounded-2xl border border-white/10 bg-white/5 backdrop-blur lg:h-[560px]"
          >
            <div className="flex items-center gap-3 border-b border-white/10 px-4 py-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-sm shadow-lg shadow-violet-600/25">
                💬
              </div>
              <div className="min-w-0 flex-1">
                <h2 className="truncate font-semibold text-zinc-100">
                  {conversationDetail?.title ?? 'Nouvelle discussion'}
                </h2>
                <p className="text-xs text-zinc-400">
                  {conversationId === null
                    ? 'Une question ouvrira une nouvelle conversation'
                    : 'Reprenez la discussion là où vous l’avez laissée'}
                </p>
              </div>
            </div>
            <ScrollArea className="flex-1 px-4">
              <div className="space-y-4 py-4">
                {loadedMessages.length + streamed.length === 0 && (
                  <div className="py-16 text-center text-sm text-zinc-500">
                    Posez votre première question sur vos documents ✨
                  </div>
                )}
                {[...loadedMessages, ...streamed].map((message, index) => (
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
        </div>
      </div>
    </PageTransition>
  )
}
