export interface UiQuickTake {
  sport_icon?: string
  favored_team?: string
  confidence_percent?: number
  confidence_level?: "Low" | "Medium" | "High" | string
  risk_level?: "Low" | "Medium" | "High" | string
  recommendation?: string
  why?: string
  limited_data_note?: string
}

export interface UiKeyDrivers {
  positives?: string[]
  risks?: string[]
}

export interface UiBetOption {
  id?: string
  market_type?: string
  label?: string
  lean?: string
  confidence_level?: "Low" | "Medium" | "High" | string
  risk_level?: "Low" | "Medium" | "High" | string
  explanation?: string
}

export interface UiMatchupCard {
  title?: string
  summary?: string
  bullets?: string[]
}


