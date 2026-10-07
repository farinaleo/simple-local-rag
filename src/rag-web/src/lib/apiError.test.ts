import { describe, expect, it } from 'vitest'
import { ApiError, toApiError } from '@/lib/apiError'

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('toApiError', () => {
  it('maps a 413 without detail to a clear file size message', async () => {
    const error = await toApiError(new Response(null, { status: 413 }))
    expect(error).toBeInstanceOf(ApiError)
    expect(error.status).toBe(413)
    expect(error.message).toBe('Fichier trop lourd (max 5 Mo)')
  })

  it('keeps the backend detail when present', async () => {
    const error = await toApiError(
      jsonResponse(400, { detail: 'avatar must be a png or jpeg image' }),
    )
    expect(error.message).toBe('avatar must be a png or jpeg image')
  })

  it('falls back to a generic message for unknown statuses', async () => {
    const error = await toApiError(new Response(null, { status: 418 }))
    expect(error.message).toBe('Erreur 418')
  })

  it('prefers the backend detail over the mapped status message', async () => {
    const error = await toApiError(jsonResponse(413, { detail: 'document too large (max 50 MB)' }))
    expect(error.message).toBe('document too large (max 50 MB)')
  })
})
