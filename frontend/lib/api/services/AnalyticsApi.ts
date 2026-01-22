import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type { AnalyticsResponse } from '@/lib/api/types/analytics'

export class AnalyticsApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getAnalyticsPerformance(riskProfile?: string) {
    const params = riskProfile ? { risk_profile: riskProfile } : {}
    const response = await this.clients.apiClient.get('/api/analytics/performance', { params })
    return response.data
  }

  async getMyParlays(limit: number = 50) {
    const response = await this.clients.apiClient.get('/api/analytics/my-parlays', {
      params: { limit },
    })
    return response.data
  }

  async getAnalyticsGames(sport?: string, marketType: string = 'moneyline'): Promise<AnalyticsResponse> {
    const params: Record<string, string> = { market_type: marketType }
    if (sport) params.sport = sport
    const response = await this.clients.apiClient.get<AnalyticsResponse>('/api/analytics/games', { params })
    return response.data
  }
}




