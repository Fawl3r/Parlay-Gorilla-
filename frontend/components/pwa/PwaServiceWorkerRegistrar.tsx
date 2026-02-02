'use client'

import { useEffect } from 'react'
import { registerServiceWorker } from '@/lib/pwa/registerServiceWorker'

/**
 * Registers the PWA service worker once on mount. Renders nothing.
 */
export function PwaServiceWorkerRegistrar() {
  useEffect(() => {
    registerServiceWorker()
  }, [])
  return null
}
