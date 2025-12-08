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
  ]

  // Dynamic analysis pages - only fetch if API is available
  // Skip during build if API_URL is not accessible (e.g., during Vercel build)
  let analysisPages: MetadataRoute.Sitemap = []
  
  // Only try to fetch during runtime, not during build
  if (process.env.VERCEL_ENV !== 'production' && process.env.NODE_ENV !== 'production') {
    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      const sports = ['nfl', 'nba', 'mlb', 'nhl']
      
      // Use AbortController with timeout to prevent hanging
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 5000) // 5s timeout
      
      for (const sport of sports) {
        try {
          const response = await fetch(`${API_URL}/api/analysis/${sport}/list?limit=50`, {
            signal: controller.signal,
            next: { revalidate: 3600 },
          })
          
          if (response.ok) {
            const analyses = await response.json()
            
            const sportPages: MetadataRoute.Sitemap = analyses.map((analysis: { slug: string; generated_at: string }) => ({
              url: `${BASE_URL}/analysis/${analysis.slug}`,
              lastModified: new Date(analysis.generated_at),
              changeFrequency: 'daily' as const,
              priority: 0.8,
            }))
            
            analysisPages = [...analysisPages, ...sportPages]
          }
        } catch {
          // Individual sport fetch failed, continue with others
        }
      }
      
      clearTimeout(timeoutId)
    } catch {
      // Silently skip - API not available during build
    }
  }

  return [...staticPages, ...analysisPages]
}

