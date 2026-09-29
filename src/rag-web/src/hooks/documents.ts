import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { API_BASE_URL } from '@/api'
import type { DocumentItem } from '@/types'

const documentsKey = ['documents'] as const

async function fetchDocuments(): Promise<DocumentItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/`)
  if (!response.ok) throw new Error(`documents: ${response.status}`)
  return response.json()
}

export function useDocuments() {
  return useQuery({
    queryKey: documentsKey,
    queryFn: fetchDocuments,
    refetchInterval: (query) => {
      const documents = query.state.data ?? []
      const hasActiveIngestion = documents.some((document) =>
        ['pending', 'processing'].includes(document.status),
      )
      return hasActiveIngestion ? 2000 : false
    },
  })
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (file: File) => {
      const body = new FormData()
      body.append('file', file)
      const response = await fetch(`${API_BASE_URL}/api/documents/`, {
        method: 'POST',
        body,
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) {
        throw new Error(payload?.detail ?? `upload failed (${response.status})`)
      }
      return payload as DocumentItem
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: documentsKey }),
  })
}

export function useDeleteDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id: number) => {
      const response = await fetch(`${API_BASE_URL}/api/documents/${id}/`, {
        method: 'DELETE',
      })
      if (!response.ok && response.status !== 404) {
        throw new Error(`delete failed (${response.status})`)
      }
    },
    onMutate: async (id: number) => {
      await queryClient.cancelQueries({ queryKey: documentsKey })
      const previous = queryClient.getQueryData<DocumentItem[]>(documentsKey)
      queryClient.setQueryData<DocumentItem[]>(documentsKey, (documents) =>
        (documents ?? []).filter((document) => document.id !== id),
      )
      return { previous }
    },
    onError: (_error, _id, context) => {
      queryClient.setQueryData(documentsKey, context?.previous)
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: documentsKey }),
  })
}
