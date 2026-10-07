import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { API_BASE_URL, getCsrfToken } from '@/api'
import { toApiError } from '@/lib/apiError'
import type { DocumentItem } from '@/types'

const documentsKey = ['documents'] as const

async function fetchDocuments(): Promise<DocumentItem[]> {
  const response = await fetch(`${API_BASE_URL}/api/documents/`, {
    credentials: 'include',
  })
  if (!response.ok) throw await toApiError(response)
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
        credentials: 'include',
        headers: { 'X-CSRFToken': getCsrfToken() },
        body,
      })
      const payload = await response.json().catch(() => null)
      if (!response.ok) {
        throw await toApiError(response)
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
        credentials: 'include',
        headers: { 'X-CSRFToken': getCsrfToken() },
      })
      if (!response.ok && response.status !== 404) {
        throw await toApiError(response)
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
