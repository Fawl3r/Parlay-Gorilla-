import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type { SystemStatusResponse } from '@/lib/api/types/system'

export class SystemApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getSystemStatus(): Promise<SystemStatusResponse> {
    const response = await this.clients.apiClient.get<SystemStatusResponse>('/api/v1/system/status')
    return response.data
  }
}
