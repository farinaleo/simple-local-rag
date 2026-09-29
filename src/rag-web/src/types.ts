export type DocumentStatus = 'pending' | 'processing' | 'indexed' | 'failed'

export interface DocumentItem {
  id: number
  original_filename: string
  mime_type: string
  size_bytes: number
  status: DocumentStatus
  error_message: string | null
  created_at: string
  updated_at: string
}
