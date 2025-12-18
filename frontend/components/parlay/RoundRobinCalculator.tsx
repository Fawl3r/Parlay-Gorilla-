"use client"

import { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

class RoundRobinEngine {
  static combinations(n: number, k: number): number {
    if (k > n) return 0
    let result = 1
    for (let i = 1; i <= k; i++) {
      result = (result * (n - i + 1)) / i
    }
    return Math.floor(result)
  }

  static payout(decimalOdds: number, stakePerCombo: number, combos: number) {
    const gross = decimalOdds * stakePerCombo * combos
    return {
      combos,
      totalStake: stakePerCombo * combos,
      grossReturn: gross,
      netProfit: gross - stakePerCombo * combos,
    }
  }
}

export function RoundRobinCalculator() {
  const [numLegs, setNumLegs] = useState(4)
  const [legsPerBet, setLegsPerBet] = useState(2)
  const [decimalOdds, setDecimalOdds] = useState(2.0)
  const [stakePerCombo, setStakePerCombo] = useState(5)

  const summary = useMemo(() => {
    const combos = RoundRobinEngine.combinations(numLegs, legsPerBet)
    return RoundRobinEngine.payout(decimalOdds, stakePerCombo, combos)
  }, [numLegs, legsPerBet, decimalOdds, stakePerCombo])

  return (
    <Card className="bg-card/80 border-border/50">
      <CardHeader>
        <CardTitle>Round Robin Calculator</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Total legs</Label>
            <Input type="number" min={2} max={10} value={numLegs} onChange={(e) => setNumLegs(Number(e.target.value))} />
          </div>
          <div className="space-y-2">
            <Label>Legs per bet</Label>
            <Input type="number" min={2} max={numLegs} value={legsPerBet} onChange={(e) => setLegsPerBet(Number(e.target.value))} />
          </div>
          <div className="space-y-2">
            <Label>Avg decimal odds</Label>
            <Input type="number" step="0.01" min={1.01} value={decimalOdds} onChange={(e) => setDecimalOdds(Number(e.target.value))} />
          </div>
          <div className="space-y-2">
            <Label>Stake per combo</Label>
            <Input type="number" step="1" min={1} value={stakePerCombo} onChange={(e) => setStakePerCombo(Number(e.target.value))} />
          </div>
        </div>
        <div className="rounded-lg border border-border/60 bg-muted/30 p-4 space-y-2 text-sm">
          <p>Combos: <span className="font-semibold">{summary.combos}</span></p>
          <p>Total stake: <span className="font-semibold">${summary.totalStake.toFixed(2)}</span></p>
          <p>Gross return: <span className="font-semibold">${summary.grossReturn.toFixed(2)}</span></p>
          <p>Net profit: <span className="font-semibold">${summary.netProfit.toFixed(2)}</span></p>
        </div>
      </CardContent>
    </Card>
  )
}

