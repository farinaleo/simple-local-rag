import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { API_BASE_URL, getCsrfToken } from '@/api'

const sessionKey = ['session'] as const

export interface SessionUser {
  id: number
  username: string
}

async function fetchSession(): Promise<SessionUser | null> {
  const response = await fetch(`${API_BASE_URL}/api/auth/me/`, {
    credentials: 'include',
  })
  if (response.status === 403) return null
  if (!response.ok) throw new Error(`session: ${response.status}`)
  return response.json()
}

export function useSession() {
  return useQuery({
    queryKey: sessionKey,
    queryFn: fetchSession,
    retry: false,
  })
}

async function postAuth(endpoint: string, payload: Record<string, string>): Promise<SessionUser> {
  const response = await fetch(`${API_BASE_URL}/api/auth/${endpoint}/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    body: JSON.stringify(payload),
  })
  if (!response.ok) {
    const detail = (await response.json().catch(() => null))?.detail
    throw new Error(detail ?? `auth failed (${response.status})`)
  }
  return response.json()
}

export function useRegister() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { username: string; password: string }) => postAuth('register', payload),
    onSuccess: (user) => queryClient.setQueryData(sessionKey, user),
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { username: string; password: string }) => postAuth('login', payload),
    onSuccess: (user) => queryClient.setQueryData(sessionKey, user),
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      await fetch(`${API_BASE_URL}/api/auth/logout/`, {
        method: 'POST',
        credentials: 'include',
        headers: { 'X-CSRFToken': getCsrfToken() },
      })
    },
    onSuccess: () => queryClient.setQueryData(sessionKey, null),
  })
}
