import { describe, expect, it } from 'vitest'

import { parseSseChunk } from '@/hooks/queries'
import type { QuerySource, StreamEvent } from '@/types'

describe('parseSseChunk', () => {
  it('parses a token event', () => {
    const raw = 'event: token\ndata: {"text": "hello"}'
    const event = parseSseChunk(raw)
    expect(event).toEqual({ type: 'token', text: 'hello' })
  })

  it('parses a sources event with chunk references', () => {
    const sources: QuerySource[] = [
      { id: 1, ordinal: 2, content: 'chunk text', document: { id: 3, original_filename: 'a.pdf' } },
    ]
    const raw = `event: sources\ndata: ${JSON.stringify({
      query_id: 7,
      sources,
    })}`
    const event = parseSseChunk(raw)
    expect(event).toEqual({
      type: 'sources',
      queryId: 7,
      conversationId: null,
      sources,
    } satisfies StreamEvent)
  })

  it('parses an error event', () => {
    const raw = 'event: error\ndata: {"detail": "boom"}'
    const event = parseSseChunk(raw)
    expect(event).toEqual({ type: 'error', detail: 'boom' })
  })

  it('returns null when the chunk has no event', () => {
    expect(parseSseChunk('data: {"text": "orphan"}')).toBeNull()
  })

  it('returns null when the chunk has no data', () => {
    expect(parseSseChunk('event: token')).toBeNull()
  })
})
