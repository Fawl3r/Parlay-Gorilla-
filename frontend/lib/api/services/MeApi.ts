import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type { EntitlementsResponse } from '@/lib/api/types'

export class MeApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getEntitlements(): Promise<EntitlementsResponse> {
    const response = await this.clients.apiClient.get<EntitlementsResponse>('/api/me/entitlements')
    return response.data
  }
}
