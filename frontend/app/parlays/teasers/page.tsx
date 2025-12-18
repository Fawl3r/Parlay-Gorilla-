"use client"

import { Header } from "@/components/Header"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { Card, CardContent } from "@/components/ui/card"
import { TeaserAdjuster } from "@/components/parlay/TeaserAdjuster"
import { CustomParlayBuilder } from "@/components/CustomParlayBuilder"

export default function TeaserParlayPage() {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-[#0a0a0f]">
        <Header />
        <main className="container mx-auto px-4 py-8 space-y-6">
          <div className="space-y-2">
            <h1 className="text-3xl font-bold text-foreground">Teaser Builder</h1>
            <p className="text-muted-foreground">
              Adjust lines with teaser points and analyze your legs before placing the ticket.
            </p>
          </div>

          <TeaserAdjuster />

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

