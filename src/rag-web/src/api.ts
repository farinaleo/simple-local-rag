export const API_BASE_URL = import.meta.env.VITE_API_URL ?? ''

export function getCsrfToken(): string {
  return (
    document.cookie
      .split('; ')
      .find((cookie) => cookie.startsWith('csrftoken='))
      ?.split('=')[1] ?? ''
  )
}
