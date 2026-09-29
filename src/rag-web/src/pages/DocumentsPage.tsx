import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { toast } from 'sonner'
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useDeleteDocument, useDocuments, useUploadDocument } from '@/hooks/documents'
import type { DocumentItem, DocumentStatus } from '@/types'

const ACCEPTED_EXTENSIONS = {
  'text/plain': ['.txt'],
  'text/markdown': ['.md'],
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
}
const MAX_UPLOAD_BYTES = 50 * 1024 * 1024

const STATUS_STYLES: Record<DocumentStatus, string> = {
  pending: 'bg-muted text-muted-foreground',
  processing: 'bg-amber-500/15 text-amber-300',
  indexed: 'bg-emerald-500/15 text-emerald-300',
  failed: 'bg-red-500/15 text-red-300',
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} kB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

function StatusBadge({ status }: { status: DocumentStatus }) {
  return <Badge className={STATUS_STYLES[status]}>{status}</Badge>
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
          toast.error(`${file.name}: file too large (max 50 MB)`)
          continue
        }
        uploadMutation.mutate(file, {
          onSuccess: () => toast.success(`${file.name}: upload accepted`),
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
      onSuccess: () => toast.success(`${document.original_filename} deleted`),
      onError: (error) => toast.error(error.message),
      onSettled: () => setPendingDelete(null),
    })
  }

  return (
    <div className="space-y-6">
      <h1 className="text-lg font-semibold">Documents</h1>

      <div
        {...getRootProps()}
        className={`rounded-lg border-2 border-dashed p-8 text-center transition-colors ${
          isDragActive ? 'border-emerald-500 bg-emerald-500/5' : 'border-input'
        }`}
      >
        <input {...getInputProps()} />
        <p className="text-sm text-muted-foreground">
          {isDragActive
            ? 'Drop the files here…'
            : 'Drag & drop files here, or click to select — txt, md, pdf, docx (max 50 MB)'}
        </p>
      </div>

      {isError && (
        <p className="text-sm text-red-400">Failed to load documents — is the API running?</p>
      )}

      {isLoading ? (
        <p className="text-sm text-muted-foreground">Loading documents…</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Name</TableHead>
              <TableHead>Format</TableHead>
              <TableHead>Size</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Uploaded</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(documents ?? []).map((document) => (
              <TableRow key={document.id}>
                <TableCell className="font-medium">{document.original_filename}</TableCell>
                <TableCell>{document.mime_type}</TableCell>
                <TableCell>{formatSize(document.size_bytes)}</TableCell>
                <TableCell>
                  <StatusBadge status={document.status} />
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {new Date(document.created_at).toLocaleString()}
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => setPendingDelete(document)}
                  >
                    Delete
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}

      <Dialog
        open={pendingDelete !== null}
        onOpenChange={(open) => !open && setPendingDelete(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete document</DialogTitle>
            <DialogDescription>
              This permanently removes {pendingDelete?.original_filename}, its chunks and
              embeddings.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={confirmDelete}>
              Delete
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
