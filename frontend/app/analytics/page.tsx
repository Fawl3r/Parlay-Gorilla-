"use client"

import { useEffect, useState } from "react"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Loader2, AlertCircle, TrendingUp, TrendingDown, Target, BarChart3, LogIn } from "lucide-react"
import { cn } from "@/lib/utils"
import Link from "next/link"

interface PerformanceStats {
  total_parlays: number
  hits: number
  misses: number
  hit_rate: number
  avg_predicted_prob: number
  avg_actual_prob: number
  avg_calibration_error: number
}

interface ParlayHistory {
  id: string
  num_legs: number
  risk_profile: string
  parlay_hit_prob: number
  created_at: string | null
}

// Helper function to get auth token from localStorage
function getAuthToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem('auth_token')
}

// Import cached authenticated fetch
import { cachedAuthenticatedFetch } from '@/lib/analytics-cache'

// Helper function to make authenticated fetch request (now with caching)
async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
  return cachedAuthenticatedFetch(url, options)
}

export default function AnalyticsPage() {
  const [stats, setStats] = useState<PerformanceStats | null>(null)
  const [history, setHistory] = useState<ParlayHistory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
  const [selectedRiskProfile, setSelectedRiskProfile] = useState<string | null>(null)

  useEffect(() => {
    // Check if user is authenticated
    const token = getAuthToken()
    setIsAuthenticated(!!token)

    async function fetchAnalytics() {
      try {
        setLoading(true)
        setError(null)

        const token = getAuthToken()
        if (!token) {
          setError('authentication_required')
          setLoading(false)
          return
        }

        // Fetch performance stats (requires auth)
        // Same-origin fetch; Next.js rewrites proxy /api/* to backend in dev (also works on tunnels/mobile).
        const statsResponse = await authenticatedFetch(
          `/api/analytics/performance${selectedRiskProfile ? `?risk_profile=${selectedRiskProfile}` : ''}`
        )
        
        if (statsResponse.status === 401) {
          setError('authentication_required')
          setIsAuthenticated(false)
          setLoading(false)
          return
        }
        
        if (!statsResponse.ok) {
          const errorData = await statsResponse.json().catch(() => ({}))
          throw new Error(errorData.detail || 'Failed to fetch analytics')
        }
        
        const statsData = await statsResponse.json()
        setStats(statsData)

        // Fetch parlay history (requires auth)
        const historyResponse = await authenticatedFetch(`/api/analytics/my-parlays?limit=50`)
        
        if (historyResponse.ok) {
          const historyData = await historyResponse.json()
          setHistory(historyData)
        } else if (historyResponse.status === 401) {
          setError('authentication_required')
          setIsAuthenticated(false)
        }
      } catch (err: unknown) {
        console.error('Error fetching analytics:', err)
        if (err instanceof Error && err.message === 'Authentication required') {
          setError('authentication_required')
          setIsAuthenticated(false)
        } else {
          const message = err instanceof Error ? err.message : "Failed to fetch analytics"
          setError(message)
        }
      } finally {
        setLoading(false)
      }
    }

    if (token) {
      fetchAnalytics()
    } else {
      setError('authentication_required')
      setLoading(false)
    }
  }, [selectedRiskProfile])

  if (loading) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <Card>
            <CardContent className="flex items-center justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              <span className="ml-2 text-muted-foreground">Loading analytics...</span>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </div>
    )
  }

  if (error === 'authentication_required' || (!isAuthenticated && !loading)) {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <Card className="max-w-md">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <LogIn className="h-5 w-5" />
                Authentication Required
              </CardTitle>
              <CardDescription>
                You must be signed in to view analytics
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-muted-foreground">
                Analytics dashboard requires authentication to track your personal parlay performance and history.
              </p>
              <div className="flex gap-2">
                <Button className="flex-1" asChild>
                  <Link href="/#builder">Sign In</Link>
                </Button>
                <Button variant="outline" className="flex-1" asChild>
                  <Link href="/">Go Home</Link>
                </Button>
              </div>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </div>
    )
  }

  if (error && error !== 'authentication_required') {
    return (
      <div className="flex min-h-screen flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <Card>
            <CardContent className="flex items-center justify-center gap-3 py-12">
              <AlertCircle className="h-8 w-8 text-destructive" />
              <div>
                <h3 className="font-semibold text-destructive">Error loading analytics</h3>
                <p className="text-sm text-muted-foreground">{error}</p>
              </div>
            </CardContent>
          </Card>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col">
      <Header />
      <main className="flex-1">
        <section className="py-20 relative">
          <div className="absolute inset-0 dark-overlay-strong z-0" />
          <div className="container relative z-10 px-4">
            <div className="mb-12 text-center">
              <h1 className="mb-3 text-4xl font-extrabold tracking-tight sm:text-5xl">
                <span className="gradient-text">Analytics Dashboard</span>
              </h1>
              <p className="text-lg text-foreground/90 max-w-2xl mx-auto font-medium">
                Track your parlay performance and insights
              </p>
            </div>

            {/* Risk Profile Filter */}
            <div className="mb-8 flex justify-center gap-2">
              <button
                onClick={() => setSelectedRiskProfile(null)}
                className={cn(
                  "px-4 py-2 rounded-md border-2 transition-colors",
                  selectedRiskProfile === null
                    ? "border-primary bg-primary/10"
                    : "border-border hover:border-primary/50"
                )}
              >
                All Profiles
              </button>
              {["conservative", "balanced", "degen"].map((profile) => (
                <button
                  key={profile}
                  onClick={() => setSelectedRiskProfile(profile)}
                  className={cn(
                    "px-4 py-2 rounded-md border-2 transition-colors capitalize",
                    selectedRiskProfile === profile
                      ? "border-primary bg-primary/10"
                      : "border-border hover:border-primary/50"
                  )}
                >
                  {profile}
                </button>
              ))}
            </div>

            {/* Performance Stats */}
            {stats && (
              <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4 mb-8">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Total Parlays
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{stats.total_parlays}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Hit Rate
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-2">
                      <div className="text-3xl font-bold">
                        {(stats.hit_rate * 100).toFixed(1)}%
                      </div>
                      {stats.hit_rate > 0.5 ? (
                        <TrendingUp className="h-5 w-5 text-green-500" />
                      ) : (
                        <TrendingDown className="h-5 w-5 text-red-500" />
                      )}
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      {stats.hits} hits / {stats.misses} misses
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Avg Predicted Prob
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {(stats.avg_predicted_prob * 100).toFixed(1)}%
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm font-medium text-muted-foreground">
                      Calibration Error
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      {(stats.avg_calibration_error * 100).toFixed(2)}%
                    </div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Lower is better
                    </p>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Parlay History */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Recent Parlays
                </CardTitle>
                <CardDescription>
                  Your parlay history and performance
                </CardDescription>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <div className="text-center py-12">
                    <Target className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">No parlay history yet</p>
                    <p className="text-sm text-muted-foreground mt-2">
                      Start building parlays to see your analytics here
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {history.map((parlay) => (
                      <div
                        key={parlay.id}
                        className="border rounded-lg p-4 bg-muted/30"
                      >
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="flex items-center gap-2 mb-2">
                              <span className="font-semibold text-primary">
                                {parlay.num_legs}-Leg Parlay
                              </span>
                              <span className="text-xs px-2 py-1 rounded-full bg-primary/20 text-primary capitalize">
                                {parlay.risk_profile}
                              </span>
                            </div>
                            <p className="text-sm text-muted-foreground">
                              Hit Probability: {(parlay.parlay_hit_prob * 100).toFixed(1)}%
                            </p>
                            {parlay.created_at && (
                              <p className="text-xs text-muted-foreground mt-1">
                                {new Date(parlay.created_at).toLocaleDateString()}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </section>
      </main>
      <Footer />
    </div>
  )
}

