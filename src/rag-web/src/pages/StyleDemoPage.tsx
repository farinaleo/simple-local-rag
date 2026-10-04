import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useRef, useState } from 'react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { ScrollArea } from '@/components/ui/scroll-area'

/**
 * Interactive style mockup of the new design system (v3 direction).
 * Fully simulated data: no API calls. Remove after the real refactor.
 */

type DocStatus = 'pending' | 'processing' | 'indexed' | 'failed'

interface DemoDocument {
  id: number
  name: string
  size: string
  status: DocStatus
  date: string
}

interface DemoMessage {
  role: 'user' | 'assistant'
  text: string
  sources?: string[]
}

const seedDocuments: DemoDocument[] = [
  { id: 1, name: 'rapport-annuel-2025.pdf', size: '2,4 Mo', status: 'indexed', date: '02/10/2026' },
  { id: 2, name: 'contrat-fournisseur.pdf', size: '870 Ko', status: 'indexed', date: '28/09/2026' },
  {
    id: 3,
    name: 'specifications-produit.pdf',
    size: '1,1 Mo',
    status: 'processing',
    date: '15/09/2026',
  },
]

const cannedAnswer =
  "D'après rapport-annuel-2025.pdf, les points clés sont : croissance du CA de 12 %, ouverture de 3 nouveaux marchés, et une hausse des effectifs de 8 %."

const statusStyles: Record<DocStatus, { label: string; className: string }> = {
  indexed: {
    label: 'Indexé',
    className: 'bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/15',
  },
  processing: {
    label: 'Traitement…',
    className: 'bg-amber-500/15 text-amber-300 hover:bg-amber-500/15',
  },
  pending: { label: 'En attente', className: 'bg-zinc-500/15 text-zinc-300 hover:bg-zinc-500/15' },
  failed: { label: 'Échec', className: 'bg-red-500/15 text-red-300 hover:bg-red-500/15' },
}

function PdfIcon({ className = 'h-10 w-10' }: { className?: string }) {
  return (
    <div
      className={`${className} flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-rose-500 to-red-600 text-[10px] font-bold text-white shadow-lg shadow-rose-500/25`}
    >
      PDF
    </div>
  )
}

function uploadSimulation(setDocs: React.Dispatch<React.SetStateAction<DemoDocument[]>>) {
  const id = Date.now()
  const fake: DemoDocument = {
    id,
    name: `nouveau-document-${id % 1000}.pdf`,
    size: '1,3 Mo',
    status: 'processing',
    date: new Date().toLocaleDateString('fr-FR'),
  }
  setDocs((docs) => [fake, ...docs])
  setTimeout(() => {
    setDocs((docs) => docs.map((d) => (d.id === id ? { ...d, status: 'indexed' } : d)))
  }, 2500)
}

function DocumentsSection() {
  const [docs, setDocs] = useState(seedDocuments)

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <h2 className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
          Documents
        </h2>
        <p className="mt-1 text-sm text-zinc-400">
          Gérez les fichiers indexés dans votre base RAG (drag &amp; drop simulé ici).
        </p>
      </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35, delay: 0.08 }}
        className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur"
      >
        <button
          onClick={() => uploadSimulation(setDocs)}
          className="w-full rounded-xl border border-dashed border-white/15 bg-zinc-900/60 px-4 py-8 text-sm text-zinc-400 transition-all hover:border-violet-500/40 hover:text-zinc-200"
        >
          📂 Déposez un fichier PDF, TXT, MD ou DOCX — ou cliquez pour simuler un upload
        </button>
      </motion.div>

      <div className="space-y-2">
        <AnimatePresence initial={false}>
          {docs.map((doc, i) => (
            <motion.div
              key={doc.id}
              layout
              initial={{ opacity: 0, y: -8, scale: 0.98 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 24, scale: 0.96 }}
              transition={{ duration: 0.25, delay: i * 0.03 }}
              className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur transition-all hover:border-violet-500/40 hover:bg-white/[0.08]"
            >
              <PdfIcon />
              <div className="min-w-0 flex-1">
                <p className="truncate font-medium text-zinc-100">{doc.name}</p>
                <p className="mt-0.5 text-xs text-zinc-400">
                  {doc.size} · ajouté le {doc.date}
                </p>
              </div>
              <Badge
                variant="secondary"
                className={`hidden rounded-full sm:inline-flex ${statusStyles[doc.status].className}`}
              >
                {doc.status === 'processing' && (
                  <span className="mr-1 h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400" />
                )}
                {statusStyles[doc.status].label}
              </Badge>
              <Button
                variant="ghost"
                size="sm"
                className="rounded-lg text-zinc-400 opacity-0 transition-all hover:bg-red-500/15 hover:text-red-400 group-hover:opacity-100"
                onClick={() => setDocs((d) => d.filter((x) => x.id !== doc.id))}
              >
                Supprimer
              </Button>
            </motion.div>
          ))}
        </AnimatePresence>
        {docs.length === 0 && (
          <div className="rounded-2xl border border-dashed border-white/15 p-12 text-center">
            <p className="text-4xl">📄</p>
            <p className="mt-3 text-sm text-zinc-400">
              Aucun document. Ajoutez un fichier pour l'indexer.
            </p>
          </div>
        )}
      </div>
    </div>
  )
}

function ChatSection() {
  const [messages, setMessages] = useState<DemoMessage[]>([
    { role: 'user', text: 'Peux-tu résumer les points clés du rapport annuel ?' },
    { role: 'assistant', text: cannedAnswer, sources: ['rapport-annuel-2025.pdf'] },
  ])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = () => {
    const text = input.trim()
    if (!text || streaming) return
    setInput('')
    setMessages((m) => [...m, { role: 'user', text }])
    setStreaming(true)

    // Simulated SSE token streaming, as the real endpoint behaves.
    const words =
      '[Démo] Réponse simulée en streaming token par token, fidèle au comportement réel du endpoint SSE.'.split(
        ' ',
      )
    let acc = ''
    setMessages((m) => [...m, { role: 'assistant', text: '' }])
    words.forEach((word, i) => {
      setTimeout(() => {
        acc += `${word} `
        setMessages((m) =>
          m.map((msg, idx) => (idx === m.length - 1 ? { ...msg, text: acc } : msg)),
        )
        if (i === words.length - 1) {
          setMessages((m) =>
            m.map((msg, idx) =>
              idx === m.length - 1 ? { ...msg, sources: ['rapport-annuel-2025.pdf'] } : msg,
            ),
          )
          setStreaming(false)
        }
      }, 180 * i)
    })
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.35 }}
      >
        <h2 className="bg-gradient-to-r from-violet-400 to-fuchsia-400 bg-clip-text text-3xl font-bold tracking-tight text-transparent">
          Chats
        </h2>
        <p className="mt-1 text-sm text-zinc-400">
          Discutez avec votre RAG — streaming SSE simulé, sources citées.
        </p>
      </motion.div>

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
            <h3 className="truncate font-semibold text-zinc-100">Discussion en cours</h3>
            <p className="text-xs text-zinc-400">{new Date().toLocaleDateString('fr-FR')}</p>
          </div>
        </div>

        <ScrollArea className="flex-1 px-4">
          <div className="space-y-4 py-4">
            {messages.map((m, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25 }}
                className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] space-y-1.5 ${m.role === 'user' ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                      m.role === 'user'
                        ? 'bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-600/20'
                        : 'border border-white/10 bg-zinc-800/80 text-zinc-100'
                    }`}
                  >
                    {m.text}
                    {streaming && i === messages.length - 1 && m.role === 'assistant' && (
                      <span className="ml-0.5 inline-block h-3.5 w-1.5 animate-pulse rounded bg-violet-400 align-middle" />
                    )}
                  </div>
                  {m.role === 'assistant' && m.sources && (
                    <p className="px-1 text-[11px] text-zinc-500">
                      📎 Source : <span className="text-violet-300">{m.sources.join(', ')}</span>
                    </p>
                  )}
                </div>
              </motion.div>
            ))}
            <div ref={bottomRef} />
          </div>
        </ScrollArea>

        <div className="flex gap-2 border-t border-white/10 p-3">
          <Input
            className="rounded-xl border-white/10 bg-zinc-900/60 text-zinc-100 placeholder:text-zinc-500 focus-visible:ring-violet-500/50"
            placeholder="Posez une question sur vos documents…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
          />
          <Button
            className="rounded-xl bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white shadow-lg shadow-violet-600/25 transition-transform hover:scale-[1.03] hover:from-violet-500 hover:to-fuchsia-500"
            onClick={send}
            disabled={streaming}
          >
            Envoyer ↑
          </Button>
        </div>
      </motion.div>
    </div>
  )
}

export default function StyleDemoPage() {
  const [page, setPage] = useState<'documents' | 'chats'>('documents')

  const navItems = [
    { id: 'documents' as const, label: 'Documents', icon: '📄' },
    { id: 'chats' as const, label: 'Chats', icon: '💬' },
  ]

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <div className="pointer-events-none fixed inset-0 overflow-hidden">
        <div className="absolute -top-40 left-1/4 h-96 w-96 rounded-full bg-violet-600/20 blur-[128px]" />
        <div className="absolute -bottom-40 right-1/4 h-96 w-96 rounded-full bg-fuchsia-600/15 blur-[128px]" />
      </div>

      <div className="relative mx-auto flex max-w-5xl">
        <aside className="sticky top-0 flex h-screen w-60 shrink-0 flex-col border-r border-white/10 bg-zinc-900/40 p-5 backdrop-blur">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-violet-600 to-fuchsia-600 text-lg shadow-lg shadow-violet-600/30">
              📚
            </div>
            <div>
              <p className="font-bold tracking-tight">Mon RAG</p>
              <p className="text-[11px] text-zinc-500">Workspace</p>
            </div>
          </div>

          <nav className="mt-8 space-y-1.5">
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => setPage(item.id)}
                className={`flex w-full items-center gap-3 rounded-xl px-3.5 py-2.5 text-sm font-medium transition-all ${
                  page === item.id
                    ? 'bg-gradient-to-r from-violet-600/25 to-fuchsia-600/25 text-white shadow-inner ring-1 ring-violet-500/30'
                    : 'text-zinc-400 hover:bg-white/5 hover:text-zinc-200'
                }`}
              >
                <span className="text-base">{item.icon}</span>
                {item.label}
                {page === item.id && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-violet-400" />
                )}
              </button>
            ))}
          </nav>

          <div className="mt-auto rounded-2xl border border-white/10 bg-white/5 p-3.5">
            <p className="text-[11px] leading-relaxed text-zinc-400">
              <span className="font-semibold text-zinc-200">3 fichiers</span> indexés dans votre
              base. Vos conversations s'appuient sur ces documents.
            </p>
          </div>
        </aside>

        <main className="min-w-0 flex-1 p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={page}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.25 }}
            >
              {page === 'documents' ? <DocumentsSection /> : <ChatSection />}
            </motion.div>
          </AnimatePresence>
        </main>
      </div>
    </div>
  )
}
