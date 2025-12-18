"use client"

import { Header } from "@/components/Header"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { CustomParlayBuilder } from "@/components/CustomParlayBuilder"
import { Card, CardContent } from "@/components/ui/card"
import { RoundRobinCalculator } from "@/components/parlay/RoundRobinCalculator"

export default function RoundRobinParlayPage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#0a0a0f]">
        <Header />
        <main className="container mx-auto px-4 py-8 space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-foreground">Round Robin Builder</h1>
            <p className="text-muted-foreground">
              Build a pool of legs, analyze them, and use the calculator to size your round robin tickets.
            </p>
          </div>

          <Card className="bg-card/80 border-border/50">
            <CardContent className="py-4">
              <CustomParlayBuilder />
            </CardContent>
          </Card>

          <RoundRobinCalculator />
        </main>
      </div>
    </ProtectedRoute>
  )
}

