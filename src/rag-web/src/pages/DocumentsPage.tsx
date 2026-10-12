import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { toast } from 'sonner'
import { FileText, Image as ImageIcon, Upload } from 'lucide-react'
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
  'image/png': ['.png'],
  'image/jpeg': ['.jpg', '.jpeg'],
}
const MAX_UPLOAD_BYTES = 50 * 1024 * 1024

const STATUS_STYLES: Record<DocumentStatus, { label: string; className: string }> = {
  indexed: { label: 'Indexé', className: 'bg-emerald-700/10 text-emerald-700' },
  processing: { label: 'Traitement…', className: 'bg-amber-600/10 text-amber-700' },
  pending: { label: 'En attente', className: 'bg-zinc-500/10 text-zinc-600' },
  failed: { label: 'Échec', className: 'bg-red-600/10 text-red-700' },
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`
  return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`.replace('.', ',')
}

function FileIcon({ mimeType, name }: { mimeType: string; name: string }) {
  const isPdf = name.toLowerCase().endsWith('.pdf') || mimeType === 'application/pdf'
  const isImage = mimeType.startsWith('image/')
  const label = isPdf ? (
    'PDF'
  ) : isImage ? (
    <ImageIcon className="size-4" />
  ) : (
    <FileText className="size-4" />
  )
  return (
    <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-muted text-[10px] font-semibold text-muted-foreground">
      {label}
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
      <div className="space-y-5">
        <PageHeader
          title="Documents"
          subtitle="Gérez les fichiers indexés dans votre base RAG."
          action={
            <div className="text-xs text-muted-foreground">
              {(documents ?? []).length} fichier{((documents ?? []).length ?? 0) > 1 ? 's' : ''}
            </div>
          }
        />
        <div {...getRootProps()}>
          <input {...getInputProps()} />
          <div
            className={`flex cursor-pointer items-center justify-center gap-2.5 rounded-lg border border-dashed px-4 py-7 text-sm transition-colors ${
              isDragActive
                ? 'border-primary bg-accent text-accent-foreground'
                : 'border-input bg-card text-muted-foreground hover:border-primary/40 hover:text-foreground'
            }`}
          >
            <Upload className="size-4 shrink-0" aria-hidden />
            {isDragActive
              ? 'Déposez les fichiers ici…'
              : 'Glissez-déposez des fichiers, ou cliquez pour sélectionner (txt, md, pdf, docx, png, jpg — max 50 Mo)'}
          </div>
        </div>
        {isError && (
          <p className="text-sm text-destructive">
            Impossible de charger les documents — l&apos;API est-elle lancée ?
          </p>
        )}
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Chargement des documents…</p>
        ) : (
          <div className="space-y-2">
            {(documents ?? []).map((document) => (
              <div
                key={document.id}
                className="group flex flex-wrap items-center gap-x-4 gap-y-2 rounded-lg border bg-card p-3 transition-colors hover:border-primary/40"
              >
                <FileIcon mimeType={document.mime_type} name={document.original_filename} />
                <div className="min-w-0 flex-1 basis-40">
                  <p className="truncate text-sm font-medium">{document.original_filename}</p>
                  <p className="mt-0.5 text-xs text-muted-foreground">
                    {formatSize(document.size_bytes)} ·{' '}
                    {new Date(document.created_at).toLocaleDateString('fr-FR')}
                  </p>
                </div>
                <Badge
                  variant="secondary"
                  className={`hidden rounded-full sm:inline-flex ${STATUS_STYLES[document.status].className}`}
                >
                  {document.status === 'processing' && (
                    <span className="mr-1 size-1.5 animate-pulse rounded-full bg-amber-600" />
                  )}
                  {STATUS_STYLES[document.status].label}
                </Badge>
                <Button
                  variant="ghost"
                  size="sm"
                  className="text-muted-foreground hover:bg-destructive/10 hover:text-destructive sm:opacity-0 sm:group-hover:opacity-100"
                  onClick={() => setPendingDelete(document)}
                >
                  Supprimer
                </Button>
              </div>
            ))}
            {(documents ?? []).length === 0 && (
              <div className="rounded-lg border border-dashed p-10 text-center">
                <p className="text-sm text-muted-foreground">
                  Aucun document. Ajoutez un fichier pour l&apos;indexer.
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
              <Button variant="destructive" onClick={confirmDelete}>
                Supprimer
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    </PageTransition>
  )
}
