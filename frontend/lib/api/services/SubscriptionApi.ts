import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'

export class SubscriptionApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getMySubscription() {
    const response = await this.clients.apiClient.get('/api/subscription/me')
    return response.data
  }

  async getSubscriptionHistory(limit: number = 20, offset: number = 0) {
    const response = await this.clients.apiClient.get('/api/subscription/history', {
      params: { limit, offset },
    })
    return response.data
  }

  async cancelSubscription() {
    const response = await this.clients.apiClient.post('/api/subscription/cancel')
    return response.data
  }
}




