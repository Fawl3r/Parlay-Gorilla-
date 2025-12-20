import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'

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
}




