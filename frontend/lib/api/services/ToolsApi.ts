import { ApiHttpClients } from '@/lib/api/internal/ApiHttpClientsProvider'
import type {
  HeatmapProbabilityResponse,
  UpsetFinderToolsResponse,
} from '@/lib/api/types/tools'

export class ToolsApi {
  constructor(private readonly clients: ApiHttpClients) {}

  async getUpsets(options: {
    sport: string
    days?: number
    min_edge?: number
    max_results?: number
    min_underdog_odds?: number
    meta_only?: 0 | 1
    force?: 0 | 1
  }): Promise<UpsetFinderToolsResponse> {
    const params: Record<string, string | number> = {
      sport: options.sport || 'nba',
      days: options.days ?? 7,
      min_edge: options.min_edge ?? 3,
      max_results: options.max_results ?? 20,
    }
    if (options.min_underdog_odds != null) params.min_underdog_odds = options.min_underdog_odds
    if (options.meta_only != null) params.meta_only = options.meta_only
    if (options.force != null) params.force = options.force
    const response = await this.clients.apiClient.get<UpsetFinderToolsResponse>(
      '/api/tools/upsets',
      { params, timeout: 30000 }
    )
    return response.data
  }

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
