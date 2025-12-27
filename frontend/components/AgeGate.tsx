"use client"

import { useState, useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { AlertTriangle } from "lucide-react"
import Image from "next/image"

const AGE_VERIFIED_KEY = "parlay_gorilla_age_verified"
const MIN_AGE = 21

export function AgeGate() {
  const [isVerified, setIsVerified] = useState<boolean>(false)
  const [showExitWarning, setShowExitWarning] = useState(false)
  const [isChecking, setIsChecking] = useState(true)
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    try {
      // Debug helper: allow forcing the age gate UI for screenshots or QA without clearing storage.
      // Example: `/any-page?force_age_gate=1`
      const forceAgeGate = new URLSearchParams(window.location.search).get("force_age_gate") === "1"
      if (forceAgeGate) {
        setIsVerified(false)
        setIsChecking(false)
        return
      }

      const verified = localStorage.getItem(AGE_VERIFIED_KEY)
      setIsVerified(verified === "true")
    } catch (error) {
      console.error("Error accessing localStorage:", error)
      setIsVerified(false)
    }
    setIsChecking(false)
  }, [])

  useEffect(() => {
    if (isChecking || isVerified === false) {
      // Completely prevent scrolling and hide content
      document.body.classList.add('age-gate-active')
      document.documentElement.classList.add('age-gate-active')
    } else {
      document.body.classList.remove('age-gate-active')
      document.documentElement.classList.remove('age-gate-active')
    }

    // Ensure the body becomes visible once this component mounts and let the CSS
    // class-based age gate control scroll locking (avoid relying on pre-hydration DOM mutations).
    if (!isChecking) {
      try {
        if (document.body) {
          // Make sure the age gate UI is visible
          document.body.style.visibility = 'visible'
          // Let CSS (age-gate-active) control scroll locking instead of inline styles
          document.body.style.overflow = ''
          if (isVerified) {
            // Clear any inline visibility override once verified
            document.body.style.visibility = ''
          }
        }
      } catch {
        // noop
      }
    }
    
    return () => {
      document.body.classList.remove('age-gate-active')
      document.documentElement.classList.remove('age-gate-active')
    }
  }, [isVerified, isChecking])

  const handleConfirm = () => {
    localStorage.setItem(AGE_VERIFIED_KEY, "true")
    setIsVerified(true)
  }

  const handleDecline = () => {
    setShowExitWarning(true)
  }

  const handleExit = () => {
    window.location.href = "https://www.ncpgambling.org"
  }

  if (!mounted || isChecking) {
    return (
      <div 
        data-age-gate
        className="fixed inset-0 z-[9999] bg-black flex items-center justify-center"
        style={{ pointerEvents: 'all' }}
      >
        <div className="text-white text-lg">Loading...</div>
      </div>
    )
  }

  if (isVerified) {
    return null
  }

  return (
    <AnimatePresence>
      <div 
        data-age-gate
        className="fixed inset-0 z-[9999] md:overflow-hidden overflow-y-auto"
        style={{ 
          pointerEvents: 'all',
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          width: '100vw',
          height: '100vh',
        }}
      >
        {/* Background Image - Full screen on all devices */}
        <div className="absolute inset-0 z-0">
          {/* Mobile: Better fit for mobile screens - focus on center content */}
          <div className="md:hidden absolute inset-0">
            <Image
              src="/images/Home page.png"
              alt="Background"
              fill
              className="object-cover"
              priority
              quality={90}
              sizes="100vw"
              style={{
                objectPosition: 'center 40%'
              }}
            />
            <div className="absolute inset-0 bg-black/75 backdrop-blur-md" />
          </div>
          
          {/* Desktop: Full screen */}
          <div className="hidden md:block absolute inset-0">
            <Image
              src="/images/Home page.png"
              alt="Background"
              fill
              className="object-cover"
              priority
              quality={90}
              sizes="100vw"
            />
            <div className="absolute inset-0 bg-black/75 backdrop-blur-md" />
          </div>
        </div>
        
        {/* Modal - Centered with Scroll */}
        <div className="absolute inset-0 z-10 flex items-center justify-center px-4 py-2 md:py-8 overflow-y-auto">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.3 }}
            className="w-full max-w-md sm:max-w-lg lg:max-w-xl max-h-[92vh] bg-[#0A0F0A]/95 border-2 border-[#00DD55]/50 rounded-xl p-4 sm:p-6 lg:p-8 shadow-2xl backdrop-blur-lg overflow-y-auto"
            style={{
              boxShadow: '0 0 6px rgba(0, 221, 85, 0.6), 0 0 10px rgba(0, 187, 68, 0.4), 0 0 15px rgba(34, 221, 102, 0.3)'
            }}
          >
            <div className="absolute inset-0 bg-[#00DD55]/5 rounded-xl blur-2xl" />
            
            <div className="relative z-10">
              {/* Age Badge - Top Right Corner */}
              <div className="absolute -top-3 -right-3 z-20">
                <div 
                  className="flex items-center justify-center w-12 h-12 rounded-full bg-[#00BB44]/20 border-3 border-[#00DD55]"
                  style={{
                    boxShadow: '0 0 2px rgba(0, 221, 85, 0.3)'
                  }}
                >
                  <span 
                    className="text-2xl font-black text-[#00DD55]"
                  >
                    {MIN_AGE}+
                  </span>
                </div>
              </div>

              {/* Logo - Centered with Subtle Neon Glow Animation */}
              <div className="flex justify-center mb-2 md:mb-6">
                <div className="relative flex items-center justify-center w-full max-w-[240px] sm:max-w-[300px] md:max-w-[340px]">
                  {/* Animated background glow layers */}
                  <motion.div 
                    className="absolute inset-0 blur-2xl"
                    animate={{
                      opacity: [0.4, 0.6, 0.5, 0.7, 0.4],
                    }}
                    transition={{
                      duration: 4,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                    style={{
                      background: 'radial-gradient(circle, rgba(0,221,85,0.5) 0%, transparent 70%)',
                    }}
                  />
                  <motion.div 
                    className="absolute inset-0 blur-3xl"
                    animate={{
                      opacity: [0.3, 0.5, 0.4, 0.6, 0.3],
                    }}
                    transition={{
                      duration: 5,
                      repeat: Infinity,
                      ease: "easeInOut",
                      delay: 0.5,
                    }}
                    style={{
                      background: 'radial-gradient(circle, rgba(0,221,85,0.4) 0%, transparent 60%)',
                    }}
                  />
                  
                  {/* Logo with subtle glow pulse */}
                  <motion.div
                    className="relative"
                    animate={{
                      filter: [
                        'brightness(1) drop-shadow(0 0 6px #00DD55) drop-shadow(0 0 12px #00DD55) drop-shadow(0 0 18px #00DD55)',
                        'brightness(1.05) drop-shadow(0 0 8px #00DD55) drop-shadow(0 0 15px #00DD55) drop-shadow(0 0 22px #00DD55)',
                        'brightness(1.02) drop-shadow(0 0 7px #00DD55) drop-shadow(0 0 13px #00DD55) drop-shadow(0 0 20px #00DD55)',
                        'brightness(1.08) drop-shadow(0 0 9px #00DD55) drop-shadow(0 0 16px #00DD55) drop-shadow(0 0 24px #00DD55)',
                        'brightness(1) drop-shadow(0 0 6px #00DD55) drop-shadow(0 0 12px #00DD55) drop-shadow(0 0 18px #00DD55)',
                      ],
                    }}
                    transition={{
                      duration: 3.5,
                      repeat: Infinity,
                      ease: "easeInOut",
                    }}
                  >
                    <Image
                      src="/images/newlogo.png"
                      alt="Parlay Gorilla Logo"
                      width={384}
                      height={160}
                      className="object-contain w-full h-auto"
                      priority
                      sizes="(max-width: 640px) 240px, (max-width: 768px) 300px, 340px"
                      style={{
                        filter: 'drop-shadow(0 0 6px #00DD55) drop-shadow(0 0 12px #00DD55) drop-shadow(0 0 18px #00DD55)',
                        willChange: 'filter',
                      }}
                    />
                  </motion.div>
                </div>
              </div>

              {/* Title - Centered */}
              <div className="text-center mb-2 md:mb-6">
                <h1 className="text-2xl md:text-3xl lg:text-4xl font-black text-white mb-1 md:mb-2">
                  Age Verification Required
                </h1>
                <p className="text-white/60 text-xs md:text-sm lg:text-base">
                  You must be {MIN_AGE} or older to access this site
                </p>
              </div>

              {!showExitWarning ? (
                <>
                  {/* Warning */}
                  <div className="bg-red-500/20 border border-red-500/40 rounded-lg p-2 md:p-4 mb-2 md:mb-4 backdrop-blur-sm">
                    <div className="flex items-start gap-2 md:gap-3">
                      <AlertTriangle className="h-4 w-4 md:h-5 md:w-5 text-red-300 flex-shrink-0 mt-0.5" />
                      <p className="text-xs md:text-sm text-red-100 leading-relaxed">
                        <strong className="text-red-200 font-semibold">Important:</strong> This website contains content related to sports betting and gambling. 
                        You must be at least {MIN_AGE} years of age to proceed.
                      </p>
                    </div>
                  </div>

                  {/* Legal Disclaimer */}
                  <div className="bg-[#121212]/60 border border-[#00DD55]/30 rounded-lg p-2 md:p-4 mb-2 md:mb-4 backdrop-blur-sm">
                    <p className="text-xs md:text-sm text-white/60 leading-relaxed text-center">
                      By clicking "I am {MIN_AGE} or older", you confirm that you are of legal gambling age in your jurisdiction 
                      and agree to our{" "}
                      <a href="/terms" className="text-[#00DD55] hover:text-[#22DD66] hover:underline transition-colors font-semibold" target="_blank" rel="noopener noreferrer">
                        Terms of Service
                      </a>
                      {" "}and{" "}
                      <a href="/privacy" className="text-[#00DD55] hover:text-[#22DD66] hover:underline transition-colors font-semibold" target="_blank" rel="noopener noreferrer">
                        Privacy Policy
                      </a>
                      .
                    </p>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-col gap-2 md:gap-3 mb-2 md:mb-4">
                    <motion.button
                      onClick={handleConfirm}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full py-2 md:py-4 px-4 bg-[#00DD55] text-black font-bold rounded-lg hover:bg-[#22DD66] transition-all text-sm md:text-base"
                      style={{
                        boxShadow: '0 0 8px rgba(0, 221, 85, 0.8), 0 0 12px rgba(0, 187, 68, 0.5), 0 0 20px rgba(34, 221, 102, 0.3)'
                      }}
                    >
                      I am {MIN_AGE} or older
                    </motion.button>
                    
                    <motion.button
                      onClick={handleDecline}
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      className="w-full py-2 md:py-4 px-4 bg-transparent border-2 border-[#00DD55] text-white font-semibold rounded-lg hover:bg-[#00DD55]/10 hover:border-[#22DD66] transition-all text-sm md:text-base"
                      style={{
                        boxShadow: '0 0 4px rgba(0, 221, 85, 0.4), 0 0 8px rgba(0, 187, 68, 0.2)'
                      }}
                    >
                      I am under {MIN_AGE}
                    </motion.button>
                  </div>

                  {/* Help Resources */}
                  <div className="text-center">
                    <p className="text-xs md:text-sm text-white/60 mb-1 md:mb-2">
                      Need help with gambling?
                    </p>
                    <div className="flex flex-wrap justify-center gap-2 md:gap-3 text-xs md:text-sm">
                      <a
                        href="https://www.ncpgambling.org"
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[#00DD55] hover:text-[#22DD66] hover:underline transition-colors font-semibold"
                      >
                        NCPG
                      </a>
                      <span className="text-white/40">•</span>
                      <a
                        href="tel:1-800-522-4700"
                        className="text-[#00DD55] hover:text-[#22DD66] hover:underline transition-colors font-semibold"
                      >
                        1-800-522-4700
                      </a>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  {/* Exit Warning */}
                  <div className="bg-red-500/25 border-2 border-red-500/50 rounded-lg p-3 md:p-4 lg:p-5 mb-3 md:mb-4 backdrop-blur-sm">
                    <div className="flex items-start gap-2 md:gap-3 mb-2 md:mb-3">
                      <AlertTriangle className="h-4 w-4 md:h-5 md:w-5 text-red-300 flex-shrink-0" />
                      <div>
                        <h2 className="text-base md:text-lg font-bold text-red-200 mb-1 md:mb-2">
                          Access Denied
                        </h2>
                        <p className="text-xs md:text-sm text-red-100 leading-relaxed">
                          You must be {MIN_AGE} or older to access Parlay Gorilla. 
                          This site contains content related to sports betting and gambling.
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* Help Resources */}
                  <div className="bg-[#121212]/60 border border-[#00DD55]/30 rounded-lg p-3 md:p-4 mb-3 md:mb-4 backdrop-blur-sm">
                    <h3 className="text-xs md:text-sm font-semibold text-white mb-2 md:mb-3">
                      Need Help with Problem Gambling?
                    </h3>
                    <div className="space-y-1 md:space-y-2 text-xs md:text-sm text-white/60">
                      <p>
                        <strong className="text-white">National Council on Problem Gambling:</strong>{" "}
                        <a
                          href="https://www.ncpgambling.org"
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-[#00DD55] hover:text-[#22DD66] hover:underline transition-colors font-semibold"
                        >
                          ncpgambling.org
                        </a>
                      </p>
                      <p>
                        <strong className="text-white">24/7 Helpline:</strong>{" "}
                        <a
                          href="tel:1-800-522-4700"
                          className="text-[#00DD55] hover:text-[#22DD66] hover:underline transition-colors font-semibold"
                        >
                          1-800-522-4700
                        </a>
                      </p>
                    </div>
                  </div>

                  {/* Exit Button */}
                  <motion.button
                    onClick={handleExit}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    className="w-full py-3 md:py-4 px-4 bg-transparent border-2 border-[#00DD55] text-white font-semibold rounded-lg hover:bg-[#00DD55]/10 hover:border-[#22DD66] transition-all text-sm md:text-base"
                    style={{
                      boxShadow: '0 0 4px rgba(0, 221, 85, 0.4), 0 0 8px rgba(0, 187, 68, 0.2)'
                    }}
                  >
                    Exit Site
                  </motion.button>
                </>
              )}
            </div>
          </motion.div>
        </div>
      </div>
    </AnimatePresence>
  )
}
