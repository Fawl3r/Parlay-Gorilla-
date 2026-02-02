import type { Metadata, Viewport } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
import { Suspense } from 'react'
import { readdir } from 'fs/promises'
import { join } from 'path'
import './globals.css'
import { ThemeProvider } from '@/components/ThemeProvider'
import { GlobalBackground } from '@/components/GlobalBackground'
import { AuthProvider } from '@/lib/auth-context'
import { SubscriptionProvider } from '@/lib/subscription-context'
import { SidebarProvider } from '@/lib/contexts/SidebarContext'
import { AffiliatePromoBanner } from '@/components/AffiliatePromoBanner'
import { ReferralTrackerClient } from '@/components/affiliates/ReferralTrackerClient'
import { MobileShell } from '@/components/navigation/MobileShell'
import { VerificationCelebrationProvider } from '@/components/verification/VerificationCelebrationProvider'
import { ClientRuntimeErrorReporter } from "@/components/debug/ClientRuntimeErrorReporter"
import { PwaServiceWorkerRegistrar } from '@/components/pwa/PwaServiceWorkerRegistrar'
import { PwaInstallProvider } from '@/lib/pwa/PwaInstallContext'
import { PwaAppModeAndToast } from '@/components/pwa/PwaAppModeAndToast'
import { GrowthAppOpenedTracker } from '@/components/onboarding/GrowthAppOpenedTracker'
import { Toaster } from 'sonner'

const inter = Inter({ subsets: ['latin'] })

function resolveSiteUrl(): string {
  const raw = process.env.NEXT_PUBLIC_SITE_URL || 'https://parlaygorilla.com'
  if (raw.includes('://')) return raw
  return `https://${raw}`
}

const SITE_URL = resolveSiteUrl()

// Folder containing preview images (relative to public directory)
const PREVIEW_IMAGES_FOLDER = 'images/preview-images'

// Supported image file extensions
const IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.webp', '.gif', '.svg']

/**
 * Loads all preview images from the preview-images folder.
 * Images are automatically discovered from the folder - just add images to the folder!
 */
async function loadPreviewImages(): Promise<string[]> {
  try {
    const publicPath = join(process.cwd(), 'public', PREVIEW_IMAGES_FOLDER)
    const files = await readdir(publicPath)
    
    // Filter for image files and sort alphabetically for consistent ordering
    const imageFiles = files
      .filter((file) => {
        const ext = file.toLowerCase().substring(file.lastIndexOf('.'))
        return IMAGE_EXTENSIONS.includes(ext)
      })
      .sort()
      .map((file) => `/${PREVIEW_IMAGES_FOLDER}/${file}`)
    
    return imageFiles.length > 0 ? imageFiles : ['/images/pgbb2.png'] // Fallback if folder is empty
  } catch (error) {
    // If folder doesn't exist or can't be read, fall back to default
    console.warn(`Could not load preview images from ${PREVIEW_IMAGES_FOLDER}:`, error)
    return ['/images/pgbb2.png']
  }
}

/**
 * Selects a preview image based on the current date.
 * The same image will be used throughout the day, then rotate to the next one.
 * This ensures consistency for social media caching while still rotating images.
 * 
 * To change rotation frequency:
 * - Daily (current): Uses dayOfYear
 * - Weekly: Use Math.floor(dayOfYear / 7) instead
 * - Hourly: Use Math.floor(now.getTime() / (1000 * 60 * 60)) instead
 */
async function getRotatingPreviewImage(): Promise<string> {
  const previewImages = await loadPreviewImages()
  
  // Use the day of the year (1-365/366) to cycle through images
  const now = new Date()
  const startOfYear = new Date(now.getFullYear(), 0, 0)
  const dayOfYear = Math.floor((now.getTime() - startOfYear.getTime()) / (1000 * 60 * 60 * 24))
  
  // Cycle through images based on day of year
  const imageIndex = dayOfYear % previewImages.length
  return previewImages[imageIndex] || previewImages[0]
}

export async function generateMetadata(): Promise<Metadata> {
  const previewImage = await getRotatingPreviewImage()
  
  return {
    metadataBase: new URL(SITE_URL),
    title: 'Parlay Gorilla - Make Smarter Parlays',
    description:
      'AI-assisted sports analytics and informational insights (probability analysis, risk indicators) for building and evaluating parlays. Not a sportsbook. 18+ only.',
    icons: {
      icon: '/images/newlogohead.png',
      shortcut: '/images/newlogohead.png',
      apple: '/images/newlogohead.png',
    },
    verification: {
      google: process.env.NEXT_PUBLIC_GOOGLE_SITE_VERIFICATION,
    },
    openGraph: {
      title: 'Parlay Gorilla - Make Smarter Parlays',
      description:
        'AI-assisted sports analytics and informational insights (probability analysis, risk indicators) for building and evaluating parlays. Not a sportsbook. 18+ only.',
      url: SITE_URL,
      siteName: 'Parlay Gorilla',
      images: [
        {
          url: previewImage,
          width: 1200,
          height: 630,
          alt: 'Parlay Gorilla - Make Smarter Parlays',
        },
      ],
      locale: 'en_US',
      type: 'website',
    },
    twitter: {
      card: 'summary_large_image',
      title: 'Parlay Gorilla - Make Smarter Parlays',
      description:
        'AI-assisted sports analytics and informational insights (probability analysis, risk indicators) for building and evaluating parlays. Not a sportsbook. 18+ only.',
      images: [previewImage],
    },
  }
}

// Viewport configuration for consistent scaling across localhost and production
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
}

// Google AdSense Client ID
const adsenseClientId = process.env.NEXT_PUBLIC_ADSENSE_CLIENT_ID

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        {/* PWA: manifest + theme + Apple install */}
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#00e676" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <link rel="apple-touch-icon" href="/icons/icon-192.png" />
        {/* Theme bootstrap (runs before React hydrates). Avoid mutating <body> here to prevent hydration mismatches. */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                // Apply theme
                const theme = localStorage.getItem('theme') || 'dark';
                const isDark = theme === 'dark' || (theme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
                if (isDark) {
                  document.documentElement.classList.add('dark');
                  document.documentElement.style.backgroundColor = '#0a0a0f';
                } else {
                  document.documentElement.classList.remove('dark');
                  document.documentElement.style.backgroundColor = '#e5e7eb';
                }
              })();
            `,
          }}
        />
        {/* Google AdSense Script - Only load in production with valid client ID */}
        {adsenseClientId && process.env.NODE_ENV === 'production' && (
          <Script
            id="google-adsense"
            async
            src={`https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${adsenseClientId}`}
            crossOrigin="anonymous"
            strategy="afterInteractive"
          />
        )}
      </head>
      <body className={inter.className}>
        <Suspense fallback={null}>
          <ReferralTrackerClient />
        </Suspense>
        <PwaServiceWorkerRegistrar />
        <ThemeProvider>
          <ClientRuntimeErrorReporter />
          <GrowthAppOpenedTracker />
          <GlobalBackground intensity="medium" />
          <AuthProvider>
            <SubscriptionProvider>
              <PwaInstallProvider>
                <PwaAppModeAndToast />
                <SidebarProvider>
                  <AffiliatePromoBanner variant="banner" />
                  <VerificationCelebrationProvider>
                    <MobileShell>{children}</MobileShell>
                  </VerificationCelebrationProvider>
                  <Toaster closeButton richColors position="top-center" theme="dark" />
                </SidebarProvider>
              </PwaInstallProvider>
            </SubscriptionProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  )
}

