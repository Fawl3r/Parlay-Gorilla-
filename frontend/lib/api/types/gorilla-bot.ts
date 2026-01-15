export interface GorillaBotCitation {
  title: string
  source_path: string
  source_url?: string | null
}

export interface GorillaBotChatRequest {
  message: string
  conversation_id?: string | null
}

export interface GorillaBotChatResponse {
  conversation_id: string
  message_id: string
  reply: string
  citations: GorillaBotCitation[]
}

export interface GorillaBotConversationSummary {
  id: string
  title?: string | null
  last_message_at?: string | null
  created_at: string
}

export interface GorillaBotMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  citations?: GorillaBotCitation[] | null
  created_at: string
}

export interface GorillaBotConversationDetail {
  conversation: GorillaBotConversationSummary
  messages: GorillaBotMessage[]
}
