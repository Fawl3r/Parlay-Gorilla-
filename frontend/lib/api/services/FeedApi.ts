import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type { FeedEventResponse, WinWallResponse } from '@/lib/api/types/feed'

export class FeedApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getMarqueeFeed(limit: number = 50): Promise<FeedEventResponse[]> {
    const response = await this.clients.apiClient.get<FeedEventResponse[]>('/api/v1/feed/marquee', {
      params: { limit },
    })
    return response.data
  }

  async getWinWall(limit: number = 50, type: 'AI' | 'CUSTOM' | 'ALL' = 'ALL'): Promise<WinWallResponse[]> {
    const response = await this.clients.apiClient.get<WinWallResponse[]>('/api/v1/feed/wins', {
      params: { limit, type },
    })
    return response.data
  }
}
