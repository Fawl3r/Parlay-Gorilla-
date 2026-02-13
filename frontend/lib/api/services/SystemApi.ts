import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type { SystemStatusResponse, SafetySnapshotResponse } from '@/lib/api/types/system'

export class SystemApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getSystemStatus(): Promise<SystemStatusResponse> {
    const response = await this.clients.apiClient.get<SystemStatusResponse>('/api/v1/system/status')
    return response.data
  }

  /** Public Safety Mode snapshot for banner (GET /ops/safety). */
  async getSafetySnapshot(): Promise<SafetySnapshotResponse> {
    const response = await this.clients.apiClient.get<SafetySnapshotResponse>('/ops/safety', { timeout: 5000 })
    return response.data
  }
}
