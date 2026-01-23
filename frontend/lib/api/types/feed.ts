export interface FeedEventResponse {
  id: string
  event_type: string
  sport: string | null
  summary: string
  created_at: string
  metadata: Record<string, any>
}

export interface WinWallResponse {
  id: string
  parlay_type: string
  legs_count: number
  odds: string
  user_alias: string | null
  settled_at: string
  summary: string
}
