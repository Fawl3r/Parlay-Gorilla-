import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type { HeatmapProbabilityResponse } from '@/lib/api/types/tools'

export class ToolsApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getHeatmapProbabilities(sport: string): Promise<HeatmapProbabilityResponse[]> {
    try {
      console.log(`[TOOLS] Fetching heatmap probabilities for ${sport.toUpperCase()}...`)
      const startTime = Date.now()

      const response = await this.clients.apiClient.get<HeatmapProbabilityResponse[]>(
        `/api/tools/odds-heatmap-probabilities`,
        {
          params: { sport },
          timeout: 30000,
        }
      )

      const elapsed = Date.now() - startTime
      console.log(
        `[TOOLS] Heatmap probabilities fetched in ${elapsed}ms, received ${response.data.length} games`
      )
      return response.data
    } catch (error: any) {
      console.error('[TOOLS] Error fetching heatmap probabilities:', error)
      throw error
    }
  }
}
