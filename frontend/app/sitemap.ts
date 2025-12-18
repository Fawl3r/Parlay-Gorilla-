import { MetadataRoute } from 'next'

const BASE_URL = process.env.NEXT_PUBLIC_SITE_URL || 'https://parlaygorilla.com'

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    {
      url: BASE_URL,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 1,
    },
    {
      url: `${BASE_URL}/sports`,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 0.9,
    },
    {
      url: `${BASE_URL}/analysis`,
      lastModified: new Date(),
      changeFrequency: 'hourly',
      priority: 0.9,
    },
    {
      url: `${BASE_URL}/premium`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.85,
    },
    {
      url: `${BASE_URL}/pricing`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.8,
    },
    {
      url: `${BASE_URL}/tools/odds-heatmap`,
      lastModified: new Date(),
      changeFrequency: 'hourly',
      priority: 0.75,
    },
    {
      url: `${BASE_URL}/docs`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.7,
    },
    {
      url: `${BASE_URL}/privacy`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.3,
    },
    {
      url: `${BASE_URL}/terms`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.3,
    },
    {
      url: `${BASE_URL}/responsible-gaming`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.4,
    },
    {
      url: `${BASE_URL}/support`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.5,
    },
    {
      url: `${BASE_URL}/development-news`,
      lastModified: new Date(),
      changeFrequency: 'weekly',
      priority: 0.6,
    },
    {
      url: `${BASE_URL}/report-bug`,
      lastModified: new Date(),
      changeFrequency: 'monthly',
      priority: 0.3,
    },
  ]

  // Dynamic analysis pages (best-effort).
  let analysisPages: MetadataRoute.Sitemap = []
  
  const backendBaseUrl = process.env.PG_BACKEND_URL || process.env.NEXT_PUBLIC_API_URL
  const apiOriginRaw = backendBaseUrl || BASE_URL
  const apiOrigin = apiOriginRaw.includes('://') ? apiOriginRaw : `http://${apiOriginRaw}`
  const sports = ['nfl', 'nba', 'mlb', 'nhl']

  async function fetchJsonWithTimeout<T>(url: string, timeoutMs: number): Promise<T | null> {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs)
    try {
      const response = await fetch(url, {
        signal: controller.signal,
        next: { revalidate: 3600 },
      })
      if (!response.ok) return null
      return (await response.json()) as T
    } catch {
      return null
    } finally {
      clearTimeout(timeoutId)
    }
  }

  for (const sport of sports) {
    // Use backend list endpoint that always returns games (even if analyses aren’t pre-generated yet).
    const url = `${apiOrigin}/api/analysis/${sport}/upcoming?limit=50`
    const analyses = await fetchJsonWithTimeout<Array<{ slug: string; generated_at: string }>>(url, 4000)
    if (!analyses) continue

    const sportPages: MetadataRoute.Sitemap = analyses.map((analysis) => ({
      url: `${BASE_URL}/analysis/${analysis.slug}`,
      lastModified: new Date(analysis.generated_at),
      changeFrequency: 'daily' as const,
      priority: 0.8,
    }))
    analysisPages = [...analysisPages, ...sportPages]
  }

  return [...staticPages, ...analysisPages]
}

