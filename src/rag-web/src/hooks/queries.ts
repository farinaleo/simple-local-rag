import { useQuery } from '@tanstack/react-query'
import { API_BASE_URL, getCsrfToken } from '@/api'
import type { QueryHistoryItem, QuerySource, StreamEvent } from '@/types'

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
    sources: payload.sources as QuerySource[],
  }
}

export async function streamQuery(
  question: string,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/query/`, {
    credentials: 'include',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify({ question }),
  })
  if (!response.ok || !response.body) {
    throw new Error(`Query failed (${response.status})`)
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
