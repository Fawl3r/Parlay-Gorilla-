import type { CustomParlayLeg } from "@/lib/api"

export interface SelectedPick extends CustomParlayLeg {
  gameDisplay: string
  pickDisplay: string
  homeTeam: string
  awayTeam: string
  sport: string
  oddsDisplay: string
}




