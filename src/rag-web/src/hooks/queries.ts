import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { API_BASE_URL, getCsrfToken } from '@/api'
import { toApiError } from '@/lib/apiError'
import type {
  ConversationDetail,
  ConversationItem,
  QueryHistoryItem,
  QuerySource,
  StreamEvent,
} from '@/types'

const conversationsKey = ['conversations'] as const

export function useQueryHistory() {
  return useQuery<QueryHistoryItem[]>({
    queryKey: ['query-history'],
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/query/history/`, {
        credentials: 'include',
      })
      if (!response.ok) throw new Error('Failed to load history')
      return response.json()
    },
  })
}

export function useConversations(enabled: boolean) {
  return useQuery<ConversationItem[]>({
    queryKey: conversationsKey,
    enabled,
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/query/conversations/`, {
        credentials: 'include',
      })
      if (!response.ok) throw await toApiError(response)
      return response.json()
    },
  })
}

export function useConversation(id: number | null, enabled: boolean) {
  return useQuery<ConversationDetail>({
    queryKey: ['conversation', id],
    enabled: enabled && id !== null,
    queryFn: async () => {
      const response = await fetch(`${API_BASE_URL}/api/query/conversations/${id}/`, {
        credentials: 'include',
      })
      if (!response.ok) throw await toApiError(response)
      return response.json()
    },
  })
}

export function useDeleteConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (id: number) => {
      const response = await fetch(`${API_BASE_URL}/api/query/conversations/${id}/`, {
        method: 'DELETE',
        credentials: 'include',
        headers: { 'X-CSRFToken': getCsrfToken() },
      })
      if (response.status !== 204 && !response.ok) throw await toApiError(response)
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: conversationsKey }),
  })
}

export function parseSseChunk(raw: string): StreamEvent | null {
  let event = ''
  const dataLines: string[] = []
  for (const line of raw.split('\n')) {
    if (line.startsWith('event:')) event = line.slice(6).trim()
    else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim())
  }
  if (!event || dataLines.length === 0) return null
  const payload = JSON.parse(dataLines.join('\n')) as Record<string, unknown>
  if (event === 'token') return { type: 'token', text: String(payload.text) }
  if (event === 'error') return { type: 'error', detail: String(payload.detail) }
  return {
    type: 'sources',
    queryId: Number(payload.query_id),
    conversationId:
      payload.conversation_id === null || payload.conversation_id === undefined
        ? null
        : Number(payload.conversation_id),
    sources: payload.sources as QuerySource[],
  }
}

export async function streamQuery(
  question: string,
  conversationId: number | null,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/query/`, {
    credentials: 'include',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify(
      conversationId === null ? { question } : { question, conversation_id: conversationId },
    ),
  })
  if (!response.ok || !response.body) {
    throw await toApiError(response)
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  for (;;) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() ?? ''
    for (const part of parts) {
      const parsed = parseSseChunk(part)
      if (parsed) onEvent(parsed)
    }
  }
}
