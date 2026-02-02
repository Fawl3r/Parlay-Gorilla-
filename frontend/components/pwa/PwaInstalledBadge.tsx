'use client'

import { Check } from 'lucide-react'
import { usePwaInstallContext } from '@/lib/pwa/PwaInstallContext'
import { cn } from '@/lib/utils'

export interface PwaInstalledBadgeProps {
  className?: string
}

/**
 * Subtle "Installed" badge shown in settings/profile when the app is running as an installed PWA.
 * Renders nothing when not installed.
 */
export function PwaInstalledBadge({ className }: PwaInstalledBadgeProps) {
  const { isInstalled } = usePwaInstallContext()

  if (!isInstalled) return null

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-medium',
        'border border-[#00e676]/30 bg-[#00e676]/10 text-[#00e676]',
        className
      )}
      aria-label="App installed on this device"
    >
      <Check className="h-3.5 w-3.5 shrink-0" />
      Installed · App Mode
    </span>
  )
}
