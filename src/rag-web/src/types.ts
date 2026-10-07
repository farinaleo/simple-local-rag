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

export interface QuerySource {
  id: number
  ordinal: number
  content: string
  document: {
    id: number
    original_filename: string
  }
}

export interface QueryHistoryItem {
  id: number
  question: string
  answer: string
  sources: QuerySource[]
  created_at: string
}

export interface ConversationItem {
  id: number
  title: string
  created_at: string
  updated_at: string
}

export interface ConversationDetail extends ConversationItem {
  messages: QueryHistoryItem[]
}

export type StreamEvent =
  | { type: 'token'; text: string }
  | {
      type: 'sources'
      queryId: number
      conversationId: number | null
      sources: QuerySource[]
    }
  | { type: 'error'; detail: string }
