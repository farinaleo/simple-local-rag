import { toast } from 'sonner'
import Markdown from 'react-markdown'
import { useRef, useState } from 'react'
import { Plus, Send, Trash2 } from 'lucide-react'
import { PageHeader, PageTransition } from '@/components/Layout'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
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
    <div className="mt-2 flex flex-wrap gap-1.5">
      {sources.map((source) => (
        <span
          key={`${source.document.id}-${source.ordinal}`}
          className="rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground"
        >
          {source.document.original_filename} · passage {source.ordinal}
        </span>
      ))}
    </div>
  )
}

function MessageItem({ message }: { message: ChatMessage }) {
  return (
    <div className="space-y-3">
      <p className="text-right text-sm font-medium text-muted-foreground">{message.question}</p>
      <div className="max-w-prose space-y-1">
        <div className="text-sm leading-relaxed [&_p:first-child]:mt-0 [&_p]:mt-2 [&_p:last-child]:mb-0">
          {message.error ? (
            <p className="text-destructive">{message.answer}</p>
          ) : (
            <Markdown>{message.answer}</Markdown>
          )}
          {message.streaming && (
            <span className="ml-0.5 inline-block h-3.5 w-1 animate-pulse rounded-sm bg-primary align-middle" />
          )}
        </div>
        {!message.streaming && <SourcesList sources={message.sources} />}
      </div>
    </div>
  )
}

function ConversationItem({
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
      className={`group relative flex w-full cursor-pointer items-center rounded-lg border px-3 py-2 text-left transition-colors ${
        active ? 'border-primary/30 bg-accent' : 'border-transparent bg-card hover:bg-muted'
      }`}
      onClick={onClick}
    >
      <p className="min-w-0 flex-1 truncate text-sm font-medium">{title}</p>
      <p className="ml-2 shrink-0 text-xs text-muted-foreground transition-opacity group-hover:opacity-0">
        {new Date(updatedAt).toLocaleDateString('fr-FR')}
      </p>
      <button
        type="button"
        aria-label="Supprimer la conversation"
        className="absolute right-2 flex size-6 items-center justify-center rounded-md text-muted-foreground opacity-0 transition-opacity hover:bg-destructive/10 hover:text-destructive group-hover:opacity-100"
        onClick={(event) => {
          event.stopPropagation()
          onDelete()
        }}
      >
        <Trash2 className="size-3.5" />
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
      <div className="space-y-5">
        <PageHeader
          title="Chats"
          subtitle="Discutez avec votre RAG et retrouvez vos conversations."
        />
        <div className="grid grid-cols-1 gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
          <div className="flex flex-col space-y-3 lg:h-[calc(100vh-170px)]">
            <Button
              variant="outline"
              className="w-full"
              onClick={startNewConversation}
              disabled={isStreaming}
            >
              <Plus className="size-4" aria-hidden />
              Nouvelle discussion
            </Button>
            <h2 className="px-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              Conversations
            </h2>
            <div className="min-h-0 flex-1 space-y-1.5 overflow-y-auto pr-0.5">
              {(conversations ?? []).map((conversation) => (
                <ConversationItem
                  key={conversation.id}
                  title={conversation.title}
                  updatedAt={conversation.updated_at}
                  active={conversation.id === conversationId}
                  onClick={() => setConversationId(conversation.id)}
                  onDelete={() => removeConversation(conversation.id)}
                />
              ))}
              {conversations?.length === 0 && (
                <p className="px-1 py-8 text-center text-xs text-muted-foreground">
                  Aucune conversation pour l&apos;instant.
                </p>
              )}
            </div>
          </div>
          <div className="mx-auto flex w-full max-w-[760px] flex-col overflow-hidden rounded-lg border bg-card lg:h-[calc(100vh-170px)]">
            <div className="flex items-center gap-3 border-b px-4 py-2.5">
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-sm font-semibold">
                  {conversationDetail?.title ?? 'Nouvelle discussion'}
                </h2>
                <p className="text-xs text-muted-foreground">
                  {conversationId === null
                    ? 'Une question ouvrira une nouvelle conversation'
                    : 'Reprenez la discussion là où vous l’aviez laissée'}
                </p>
              </div>
            </div>
            <div className="min-h-0 flex-1 overflow-y-auto px-4">
              <div className="mx-auto max-w-prose space-y-5 py-4">
                {loadedMessages.length + streamed.length === 0 && (
                  <div className="py-16 text-center text-sm text-muted-foreground">
                    Posez votre première question sur vos documents.
                  </div>
                )}
                {[...loadedMessages, ...streamed].map((message, index) => (
                  <MessageItem key={index} message={message} />
                ))}
                <div ref={listEndRef} />
              </div>
            </div>
            <div className="flex gap-2 border-t p-3">
              <Input
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                onKeyDown={(event) => event.key === 'Enter' && void send()}
                placeholder="Posez une question sur vos documents…"
                disabled={isStreaming}
              />
              <Button
                size="icon"
                onClick={() => void send()}
                disabled={isStreaming || question.trim() === ''}
                aria-label="Envoyer"
              >
                <Send className="size-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </PageTransition>
  )
}
