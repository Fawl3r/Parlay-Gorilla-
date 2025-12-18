"use client"

import { Header } from "@/components/Header"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { CustomParlayBuilder } from "@/components/CustomParlayBuilder"
import { Card, CardContent } from "@/components/ui/card"

export default function SameGameParlayPage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#0a0a0f]">
        <Header />
        <main className="container mx-auto px-4 py-8 space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-foreground">Same-Game Parlay Builder</h1>
            <p className="text-muted-foreground">
              Pick multiple markets from the same matchup and run AI analysis before you lock it in.
            </p>
          </div>
          <Card className="bg-card/80 border-border/50">
            <CardContent className="py-4">
              <CustomParlayBuilder />
            </CardContent>
          </Card>
        </main>
      </div>
    </ProtectedRoute>
  )
}

