import axios from 'axios'
import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type {
  GorillaBotChatRequest,
  GorillaBotChatResponse,
  GorillaBotConversationDetail,
  GorillaBotConversationSummary,
} from '@/lib/api/types'

export class GorillaBotApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async chat(request: GorillaBotChatRequest): Promise<GorillaBotChatResponse> {
    try {
      const response = await this.clients.apiClient.post<GorillaBotChatResponse>('/api/gorilla-bot/chat', request)
      return response.data
    } catch (error) {
      this.handleError(error, 'Unable to reach Gorilla Bot right now.')
      throw error
    }
  }

  async listConversations(limit: number = 20): Promise<GorillaBotConversationSummary[]> {
    try {
      const response = await this.clients.apiClient.get<GorillaBotConversationSummary[]>(
        '/api/gorilla-bot/conversations',
        { params: { limit } }
      )
      return response.data
    } catch (error) {
      this.handleError(error, 'Unable to load Gorilla Bot conversations.')
      throw error
    }
  }

  async getConversation(conversationId: string): Promise<GorillaBotConversationDetail> {
    try {
      const response = await this.clients.apiClient.get<GorillaBotConversationDetail>(
        `/api/gorilla-bot/conversations/${conversationId}`
      )
      return response.data
    } catch (error) {
      this.handleError(error, 'Unable to load Gorilla Bot conversation.')
      throw error
    }
  }

  async deleteConversation(conversationId: string): Promise<void> {
    try {
      await this.clients.apiClient.delete(`/api/gorilla-bot/conversations/${conversationId}`)
    } catch (error) {
      this.handleError(error, 'Unable to remove Gorilla Bot conversation.')
      throw error
    }
  }

  private handleError(error: unknown, fallbackMessage: string) {
    if (axios.isAxiosError(error)) {
      const detail = (error.response?.data as any)?.detail
      const message = typeof detail === 'string' ? detail : fallbackMessage
      const typedError: any = new Error(message)
      typedError.status = error.response?.status
      typedError.data = error.response?.data
      throw typedError
    }
  }
}
