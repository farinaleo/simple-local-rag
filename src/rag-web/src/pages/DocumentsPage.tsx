import { AnimatePresence, motion } from 'framer-motion'
import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { toast } from 'sonner'

import { PageHeader, PageTransition } from '@/components/Layout'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { useDeleteDocument, useDocuments, useUploadDocument } from '@/hooks/documents'
import type { DocumentItem, DocumentStatus } from '@/types'

const ACCEPTED_EXTENSIONS = {
  'text/plain': ['.txt'],
  'text/markdown': ['.md'],
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
}

const MAX_UPLOAD_BYTES = 50 * 1024 * 1024

const STATUS_STYLES: Record<DocumentStatus, { label: string; className: string }> = {
  indexed: {
    label: 'Indexé',
    className: 'bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/15',
  },
  processing: {
    label: 'Traitement…',
    className: 'bg-amber-500/15 text-amber-300 hover:bg-amber-500/15',
  },
  pending: {
    label: 'En attente',
    className: 'bg-zinc-500/15 text-zinc-300 hover:bg-zinc-500/15',
  },
  failed: {
    label: 'Échec',
    className: 'bg-red-500/15 text-red-300 hover:bg-red-500/15',
  },
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`.replace('.', ',')
}

function FileIcon({ mimeType, name }: { mimeType: string; name: string }) {
  const extension = name.toLowerCase().endsWith('.pdf') || mimeType === 'application/pdf'
  if (extension) {
    return (
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-rose-500 to-red-600 text-[10px] font-bold text-white shadow-lg shadow-rose-500/25">
        PDF
      </div>
    )
  }
  if (mimeType.includes('word')) {
    return (
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-sky-500 to-blue-600 text-[10px] font-bold text-white shadow-lg shadow-sky-500/25">
        DOCX
      </div>
    )
  }
  return (
    <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-violet-500 to-fuchsia-600 text-sm font-bold text-white shadow-lg shadow-violet-500/25">
      📄
    </div>
  )
}

export default function DocumentsPage() {
  const { data: documents, isLoading, isError } = useDocuments()
  const uploadMutation = useUploadDocument()
  const deleteMutation = useDeleteDocument()
  const [pendingDelete, setPendingDelete] = useState<DocumentItem | null>(null)

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      for (const file of acceptedFiles) {
        if (file.size > MAX_UPLOAD_BYTES) {
          toast.error(`${file.name}: fichier trop volumineux (max 50 Mo)`)
          continue
        }
        uploadMutation.mutate(file, {
          onSuccess: () => toast.success(`${file.name}: upload accepté`),
          onError: (error) => toast.error(`${file.name}: ${error.message}`),
        })
      }
    },
    [uploadMutation],
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED_EXTENSIONS,
    maxSize: MAX_UPLOAD_BYTES,
  })

  const confirmDelete = () => {
    if (!pendingDelete) return
    const document = pendingDelete
    deleteMutation.mutate(document.id, {
      onSuccess: () => toast.success(`${document.original_filename} supprimé`),
      onError: (error) => toast.error(error.message),
      onSettled: () => setPendingDelete(null),
    })
  }

  return (
    <PageTransition>
      <div className="space-y-6">
        <PageHeader
          title="Documents"
          subtitle="Gérez les fichiers indexés dans votre base RAG."
          action={
            <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-zinc-300">
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
              {(documents ?? []).length} fichier{((documents ?? []).length ?? 0) > 1 ? 's' : ''}
            </div>
          }
        />

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.35, delay: 0.08 }}
          className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur"
        >
          <div
            {...getRootProps()}
            className={`w-full cursor-pointer rounded-xl border border-dashed px-4 py-8 text-center text-sm transition-all ${
              isDragActive
                ? 'border-violet-500 bg-violet-500/10 text-zinc-100'
                : 'border-white/15 bg-zinc-900/60 text-zinc-400 hover:border-violet-500/40 hover:text-zinc-200'
            }`}
          >
            <input {...getInputProps()} />
            {isDragActive
              ? 'Déposez les fichiers ici…'
              : '📂 Glissez-déposez des fichiers ici, ou cliquez pour sélectionner — txt, md, pdf, docx (max 50 Mo)'}
          </div>
        </motion.div>

        {isError && (
          <p className="text-sm text-red-400">
            Impossible de charger les documents — l'API est-elle lancée ?
          </p>
        )}
        {isLoading ? (
          <p className="text-sm text-zinc-400">Chargement des documents…</p>
        ) : (
          <div className="space-y-2">
            <AnimatePresence initial={false}>
              {(documents ?? []).map((document, i) => (
                <motion.div
                  key={document.id}
                  layout
                  initial={{ opacity: 0, y: -8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, x: 24, scale: 0.96 }}
                  transition={{ duration: 0.25, delay: i * 0.03 }}
                  className="group flex items-center gap-4 rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur transition-all hover:border-violet-500/40 hover:bg-white/[0.08]"
                >
                  <FileIcon mimeType={document.mime_type} name={document.original_filename} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-zinc-100">
                      {document.original_filename}
                    </p>
                    <p className="mt-0.5 text-xs text-zinc-400">
                      {formatSize(document.size_bytes)} ·{' '}
                      {new Date(document.created_at).toLocaleDateString('fr-FR')}
                    </p>
                  </div>
                  <Badge
                    variant="secondary"
                    className={`hidden rounded-full sm:inline-flex ${STATUS_STYLES[document.status].className}`}
                  >
                    {document.status === 'processing' && (
                      <span className="mr-1 h-1.5 w-1.5 animate-pulse rounded-full bg-amber-400" />
                    )}
                    {STATUS_STYLES[document.status].label}
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="rounded-lg text-zinc-400 opacity-0 transition-all hover:bg-red-500/15 hover:text-red-400 group-hover:opacity-100"
                    onClick={() => setPendingDelete(document)}
                  >
                    Supprimer
                  </Button>
                </motion.div>
              ))}
            </AnimatePresence>
            {(documents ?? []).length === 0 && (
              <div className="rounded-2xl border border-dashed border-white/15 p-12 text-center">
                <p className="text-4xl">📄</p>
                <p className="mt-3 text-sm text-zinc-400">
                  Aucun document. Ajoutez un fichier pour l'indexer.
                </p>
              </div>
            )}
          </div>
        )}

        <Dialog
          open={pendingDelete !== null}
          onOpenChange={(open) => !open && setPendingDelete(null)}
        >
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Supprimer le document</DialogTitle>
              <DialogDescription>
                Cette action supprime définitivement {pendingDelete?.original_filename}, ses chunks
                et ses embeddings.
              </DialogDescription>
            </DialogHeader>
            <DialogFooter>
              <Button variant="outline" onClick={() => setPendingDelete(null)}>
                Annuler
              </Button>
              <Button
                className="bg-gradient-to-r from-red-600 to-rose-600 text-white hover:from-red-500 hover:to-rose-500"
                onClick={confirmDelete}
              >
                Supprimer
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </PageTransition>
  )
}
