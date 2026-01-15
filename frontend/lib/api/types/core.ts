export interface OddsResponse {
  id: string
  outcome: string
  price: string
  decimal_price: number
  implied_prob: number
  created_at: string
}

export interface MarketResponse {
  id: string
  market_type: string
  book: string
  odds: OddsResponse[]
}

export interface GameResponse {
  id: string
  external_game_id: string
  sport: string
  home_team: string
  away_team: string
  start_time: string
  status: string
  week?: number | null
  markets: MarketResponse[]
}

export interface NFLWeekInfo {
  week: number
  label: string
  is_current: boolean
  is_available: boolean
  start_date?: string
  end_date?: string
}

export interface NFLWeeksResponse {
  current_week: number | null
  season_year: number
  weeks: NFLWeekInfo[]
}
