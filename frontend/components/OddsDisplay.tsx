"use client"

import { MarketResponse } from "@/lib/api"
import { Badge } from "@/components/ui/badge"
import { formatOdds } from "@/lib/utils"

interface OddsDisplayProps {
  markets: MarketResponse[]
}

export function OddsDisplay({ markets }: OddsDisplayProps) {
  const getMarketLabel = (marketType: string): string => {
    switch (marketType) {
      case "h2h":
        return "Moneyline"
      case "spreads":
        return "Spread"
      case "totals":
        return "Total"
      default:
        return marketType
    }
  }

  const getOutcomeLabel = (outcome: string, marketType: string): string => {
    if (marketType === "h2h") {
      return outcome === "home" ? "Home" : "Away"
    }
    return outcome
  }

  if (markets.length === 0) {
    return (
      <div className="text-sm text-muted-foreground">No odds available</div>
    )
  }

  return (
    <div className="space-y-4">
      {markets.map((market) => (
        <div key={market.id} className="space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium">{getMarketLabel(market.market_type)}</h4>
            <Badge variant="outline" className="text-xs">
              {market.book}
            </Badge>
          </div>
          <div className="grid grid-cols-2 gap-2">
            {market.odds.map((odd) => (
              <div
                key={odd.id}
                className="flex items-center justify-between rounded-md border p-2"
              >
                <span className="text-sm text-muted-foreground">
                  {getOutcomeLabel(odd.outcome, market.market_type)}
                </span>
                <span className="font-semibold">{formatOdds(odd.price)}</span>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

