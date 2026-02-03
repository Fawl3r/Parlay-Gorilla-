'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { toast } from 'sonner'
import { Share, Plus, Smartphone } from 'lucide-react'
import { usePwaInstallContext } from '@/lib/pwa/PwaInstallContext'
import { trackEvent } from '@/lib/track-event'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { cn } from '@/lib/utils'

const TITLE = 'Install Parlay Gorilla'
const BODY = 'Add it to your home screen for quick launch and a more app-like experience.'
const PRIMARY_INSTALL = 'Install App'
const PRIMARY_HOW_TO = 'How to Install'
const SECONDARY = 'Not now'
const TOAST_INSTALLED = 'Installed. You can launch from your home screen.'
const TOAST_DISMISSED = 'No worries—remind me later.'
const IOS_STEP_1 = 'Tap the Share icon (square with arrow)'

export interface PwaInstallCtaProps {
  variant?: 'banner' | 'card' | 'inline'
  context?: 'dashboard' | 'landing' | 'connect'
  className?: string
}

export function PwaInstallCta({
  variant = 'inline',
  context = 'dashboard',
  className,
}: PwaInstallCtaProps) {
  const {
    isInstallable,
    isIOS,
    shouldShowInstallCta,
    promptInstall,
    dismiss,
  } = usePwaInstallContext()
  const [howToOpen, setHowToOpen] = useState(false)

  // Instrument: CTA shown
  useEffect(() => {
    if (shouldShowInstallCta) {
      trackEvent('pwa_cta_shown', { context })
    }
  }, [shouldShowInstallCta, context])

  if (!shouldShowInstallCta) {
    return null
  }

  const isHowToMode = isIOS && !isInstallable
  const primaryLabel = isHowToMode ? PRIMARY_HOW_TO : PRIMARY_INSTALL

  const handlePrimary = async () => {
    trackEvent('pwa_cta_clicked', { context })
    if (isHowToMode) {
      trackEvent('pwa_howto_opened', { context: 'ios' })
      setHowToOpen(true)
      return
    }
    const outcome = await promptInstall()
    if (outcome === 'accepted') {
      toast.success(TOAST_INSTALLED)
    } else if (outcome === 'dismissed') {
      dismiss(14)
      toast(TOAST_DISMISSED)
    }
  }

  const handleNotNow = () => {
    dismiss(14)
    setHowToOpen(false)
  }

  const baseClasses =
    'rounded-lg border border-white/10 bg-black/40 backdrop-blur-md text-left flex items-center justify-between gap-3'
  const variantClasses = {
    banner: 'w-full px-4 py-3',
    card: 'p-4 sm:p-5 max-w-md',
    inline: 'px-3 py-2 shrink-0',
  }
  const wrapperClass = cn(baseClasses, variantClasses[variant], className)

  return (
    <>
      <div
        className={wrapperClass}
        data-testid="pwa-install-cta"
        data-context={context}
      >
        <div className="flex items-center gap-2 min-w-0 flex-1">
          <div className="relative w-8 h-8 shrink-0 rounded-lg overflow-hidden bg-white/5">
            <Image
              src="/icons/icon-192.png"
              alt=""
              width={32}
              height={32}
              className="object-contain"
            />
          </div>
          <div className="min-w-0">
            {(variant === 'card' || variant === 'banner') && (
              <>
                <p className="font-semibold text-white text-sm sm:text-base truncate">
                  {TITLE}
                </p>
                <p className="text-gray-400 text-xs sm:text-sm mt-0.5 line-clamp-2">
                  {BODY}
                </p>
              </>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={handlePrimary}
            className={cn(
              'px-3 py-1.5 sm:px-4 sm:py-2 rounded-lg font-medium text-sm',
              'bg-[#00e676] text-black hover:bg-[#00ff85] transition-colors',
              'focus:outline-none focus:ring-2 focus:ring-[#00e676]/50 focus:ring-offset-2 focus:ring-offset-black'
            )}
            aria-label={primaryLabel}
          >
            {primaryLabel}
          </button>
          <button
            type="button"
            onClick={handleNotNow}
            className="px-2 py-1.5 sm:px-3 sm:py-2 rounded-lg font-medium text-sm text-gray-400 hover:text-white border border-white/10 hover:border-white/20 transition-colors focus:outline-none focus:ring-2 focus:ring-white/20 focus:ring-offset-2 focus:ring-offset-black"
            aria-label={SECONDARY}
          >
            {SECONDARY}
          </button>
        </div>
      </div>

      <Dialog open={howToOpen} onOpenChange={setHowToOpen}>
        <DialogContent
          className="z-[100] bg-[#0a0a0f] border-white/10 text-white max-w-sm sm:max-w-md rounded-xl mx-3"
          overlayClassName="z-[100]"
          aria-describedby="pwa-how-to-desc"
        >
          <DialogHeader>
            <DialogTitle className="text-white">{TITLE}</DialogTitle>
            <DialogDescription id="pwa-how-to-desc" className="text-gray-400">
              {BODY}
            </DialogDescription>
          </DialogHeader>
          <ol className="space-y-4 py-2 text-sm text-gray-300" role="list">
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#00e676]/20 text-[#00e676] font-semibold">
                1
              </span>
              <span className="flex items-center gap-2 pt-0.5">
                <Share className="h-4 w-4 shrink-0 text-[#00e676]" />
                {IOS_STEP_1}
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#00e676]/20 text-[#00e676] font-semibold">
                2
              </span>
              <span className="flex items-center gap-2 pt-0.5">
                <Plus className="h-4 w-4 shrink-0 text-[#00e676]" />
                Tap <strong className="text-white">Add to Home Screen</strong>
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-[#00e676]/20 text-[#00e676] font-semibold">
                3
              </span>
              <span className="flex items-center gap-2 pt-0.5">
                <Smartphone className="h-4 w-4 shrink-0 text-[#00e676]" />
                Launch from Home Screen
              </span>
            </li>
          </ol>
          <DialogFooter className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={handleNotNow}
              className="px-4 py-2 rounded-lg font-medium text-sm text-gray-400 hover:text-white border border-white/10 hover:border-white/20 transition-colors"
              aria-label={SECONDARY}
            >
              {SECONDARY}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
