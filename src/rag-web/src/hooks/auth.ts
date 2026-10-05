import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { API_BASE_URL, getCsrfToken } from '@/api'

const sessionKey = ['session'] as const

export interface SessionUser {
  id: number
  username: string
  role: string
  must_change_password: boolean
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

async function adminFetch(path: string, init?: RequestInit) {
  const response = await fetch(`${API_BASE_URL}/api/auth${path}`, {
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    ...init,
  })
  if (!response.ok) {
    const detail = (await response.json().catch(() => null))?.detail
    throw new Error(detail ?? `admin request failed (${response.status})`)
  }
  return response.status === 204 ? null : response.json()
}

export interface AdminUser {
  id: number
  username: string
  role: string
  is_active: boolean
  must_change_password: boolean
}

export function useAdminUsers(enabled: boolean) {
  return useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminFetch('/admin/users/') as Promise<AdminUser[]>,
    enabled,
  })
}

export function useCreateAdminUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { username: string; role: string }) =>
      adminFetch('/admin/users/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  })
}

export function useUpdateAdminUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      id,
      ...payload
    }: {
      id: number
      is_active?: boolean
      reset_password?: boolean
    }) =>
      adminFetch(`/admin/users/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  })
}

export function useDeleteAdminUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => adminFetch(`/admin/users/${id}/`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  })
}

export function useChangePassword() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { new_password: string }) =>
      adminFetch('/password/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: sessionKey }),
  })
}

export interface ProfileData {
  id: number
  username: string
  display_name: string
  avatar_url: string | null
  role: string
}

async function profileFetch(path: string, init?: RequestInit) {
  const isFormData = init?.body instanceof FormData
  const headers: Record<string, string> = { 'X-CSRFToken': getCsrfToken() }
  if (!isFormData) headers['Content-Type'] = 'application/json'
  const response = await fetch(`${API_BASE_URL}/api/auth${path}`, {
    credentials: 'include',
    headers,
    ...init,
  })
  if (!response.ok) {
    const detail = (await response.json().catch(() => null))?.detail
    throw new Error(detail ?? `profile request failed (${response.status})`)
  }
  return response.status === 204 ? null : response.json()
}

export function useProfile(enabled: boolean) {
  return useQuery({
    queryKey: ['profile'],
    queryFn: () => profileFetch('/profile/') as Promise<ProfileData>,
    enabled,
  })
}

export function useUpdateProfile() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { display_name?: string; avatar?: File }) => {
      if (payload.avatar) {
        const form = new FormData()
        if (payload.display_name !== undefined) form.append('display_name', payload.display_name)
        form.append('avatar', payload.avatar)
        return profileFetch('/profile/', { method: 'PATCH', body: form })
      }
      return profileFetch('/profile/', {
        method: 'PATCH',
        body: JSON.stringify({ display_name: payload.display_name }),
      })
    },
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['profile'] }),
  })
}

export function useChangePasswordSecure() {
  return useMutation({
    mutationFn: (payload: { old_password: string; new_password: string }) =>
      profileFetch('/password/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
  })
}

export interface TokenData {
  id: number
  name: string
  scopes: string[]
  created_at: string
  last_used_at: string | null
  is_active: boolean
  expires_at: string | null
  expired: boolean
  status: string
}

export function useTokens(enabled: boolean) {
  return useQuery({
    queryKey: ['tokens'],
    queryFn: () => adminFetch('/tokens/') as Promise<TokenData[]>,
    enabled,
  })
}

export function useCreateToken() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (payload: { name: string; scopes: string[] }) =>
      adminFetch('/tokens/', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tokens'] }),
  })
}

export function useUpdateToken() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...payload }: { id: number; is_active?: boolean }) =>
      adminFetch(`/tokens/${id}/`, {
        method: 'PATCH',
        body: JSON.stringify(payload),
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tokens'] }),
  })
}

export function useDeleteToken() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => adminFetch(`/tokens/${id}/`, { method: 'DELETE' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['tokens'] }),
  })
}
