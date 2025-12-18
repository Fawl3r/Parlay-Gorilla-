"use client"

import { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

class TeaserEngine {
  static adjustLine(baseLine: number, teaserPoints: number, isFavorite: boolean) {
    return isFavorite ? baseLine - teaserPoints : baseLine + teaserPoints
  }
}

export function TeaserAdjuster() {
  const [baseLine, setBaseLine] = useState(-7)
  const [teaserPoints, setTeaserPoints] = useState(6)
  const [betSide, setBetSide] = useState<"favorite" | "underdog">("favorite")
  const [betType, setBetType] = useState<"spread" | "total">("spread")

  const adjusted = useMemo(() => {
    if (betType === "total") {
      return betSide === "favorite" ? baseLine - teaserPoints : baseLine + teaserPoints
    }
    return TeaserEngine.adjustLine(baseLine, teaserPoints, betSide === "favorite")
  }, [baseLine, teaserPoints, betSide, betType])

  return (
    <Card className="bg-card/80 border-border/50">
      <CardHeader>
        <CardTitle>Teaser Builder</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Bet Type</Label>
            <Select value={betType} onValueChange={(value: "spread" | "total") => setBetType(value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select bet type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="spread">Spread</SelectItem>
                <SelectItem value="total">Total</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Side</Label>
            <Select value={betSide} onValueChange={(value: "favorite" | "underdog") => setBetSide(value)}>
              <SelectTrigger>
                <SelectValue placeholder="Select side" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="favorite">Favorite</SelectItem>
                <SelectItem value="underdog">Underdog</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Base line</Label>
            <Input type="number" step="0.5" value={baseLine} onChange={(e) => setBaseLine(Number(e.target.value))} />
          </div>
          <div className="space-y-2">
            <Label>Teaser points</Label>
            <Input type="number" step="0.5" value={teaserPoints} onChange={(e) => setTeaserPoints(Number(e.target.value))} />
          </div>
        </div>
        <div className="rounded-lg border border-border/60 bg-muted/30 p-4 text-sm">
          <p className="text-muted-foreground mb-1">Adjusted line</p>
          <p className="text-2xl font-semibold text-foreground">
            {adjusted > 0 ? `+${adjusted.toFixed(1)}` : adjusted.toFixed(1)}
          </p>
        </div>
      </CardContent>
    </Card>
  )
}

