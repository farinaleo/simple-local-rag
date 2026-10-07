const STATUS_MESSAGES: Record<number, string> = {
  400: 'Requête invalide',
  401: 'Session expirée, reconnecte-toi',
  403: 'Action non autorisée',
  404: 'Ressource introuvable',
  409: 'Conflit : la ressource existe déjà',
  413: 'Fichier trop lourd (max 5 Mo)',
  429: 'Trop de requêtes, réessaie dans un instant',
  500: 'Erreur interne du serveur',
  502: 'Service indisponible, réessaie plus tard',
  503: 'Service indisponible, réessaie plus tard',
  504: 'Le serveur ne répond pas, réessaie plus tard',
}

export class ApiError extends Error {
  status: number

  constructor(status: number, detail: string | null) {
    super(detail ?? STATUS_MESSAGES[status] ?? `Erreur ${status}`)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function toApiError(response: Response): Promise<ApiError> {
  const payload = await response.json().catch(() => null)
  const detail =
    payload && typeof payload === 'object' && 'detail' in payload ? String(payload.detail) : null
  return new ApiError(response.status, detail)
}
