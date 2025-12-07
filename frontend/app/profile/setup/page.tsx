"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { 
  User, 
  ChevronRight, 
  ChevronLeft, 
  Loader2, 
  Check,
  Trophy,
  Heart,
  Zap,
  ChevronDown,
  X
} from "lucide-react"
import Image from "next/image"
import { ALL_TEAMS } from "@/lib/teams"

const SPORTS = ["NFL", "NBA", "NHL", "MLB", "NCAAF", "NCAAB", "Soccer"]
const BETTING_STYLES = [
  { value: "conservative", label: "Conservative", icon: "🛡️", description: "Safe, steady wins" },
  { value: "balanced", label: "Balanced", icon: "⚖️", description: "Mix of safe and risk" },
  { value: "degen", label: "Degen", icon: "🔥", description: "High risk, high reward" },
]

export default function ProfileSetupPage() {
  const { user, refreshUser } = useAuth()
  const router = useRouter()
  
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Form data
  const [displayName, setDisplayName] = useState("")
  const [favoriteSports, setFavoriteSports] = useState<string[]>([])
  const [favoriteTeams, setFavoriteTeams] = useState<string[]>([])
  const [bettingStyle, setBettingStyle] = useState("balanced")
  const [openDropdowns, setOpenDropdowns] = useState<Record<string, boolean>>({})
  const [teamSearch, setTeamSearch] = useState<Record<string, string>>({})

  // Redirect if profile already completed
  useEffect(() => {
    if (user?.profile_completed) {
      router.push("/app")
    }
  }, [user, router])

  // Pre-fill display name from username if available
  useEffect(() => {
    if (user?.username && !displayName) {
      setDisplayName(user.username)
    }
  }, [user])

  const toggleSport = (sport: string) => {
    setFavoriteSports(prev => 
      prev.includes(sport) 
        ? prev.filter(s => s !== sport)
        : [...prev, sport]
    )
  }

  const toggleTeam = (team: string) => {
    setFavoriteTeams(prev => 
      prev.includes(team) 
        ? prev.filter(t => t !== team)
        : [...prev, team]
    )
  }

  const toggleDropdown = (sport: string) => {
    setOpenDropdowns(prev => ({
      ...prev,
      [sport]: !prev[sport]
    }))
  }

  const getFilteredTeams = (sport: string): string[] => {
    const teams = ALL_TEAMS[sport] || []
    const search = teamSearch[sport]?.toLowerCase() || ""
    if (!search) return teams
    return teams.filter(team => team.toLowerCase().includes(search))
  }

  const removeTeam = (team: string) => {
    setFavoriteTeams(prev => prev.filter(t => t !== team))
  }

  const handleSubmit = async () => {
    if (!displayName.trim()) {
      setError("Display name is required")
      return
    }

    setLoading(true)
    setError(null)

    try {
      await api.completeProfileSetup({
        display_name: displayName.trim(),
        favorite_sports: favoriteSports,
        favorite_teams: favoriteTeams,
        default_risk_profile: bettingStyle as 'conservative' | 'balanced' | 'degen',
      })

      // Refresh user data to get updated profile_completed flag
      await refreshUser()
      
      // Redirect to app
      router.push("/app")
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to save profile")
    } finally {
      setLoading(false)
    }
  }

  const canProceed = () => {
    switch (step) {
      case 1: return displayName.trim().length > 0
      case 2: return true // Sports selection is optional
      case 3: return true // Teams selection is optional
      case 4: return true // Style is pre-selected
      default: return false
    }
  }

  const totalSteps = 4

  return (
    <div className="min-h-screen flex items-center justify-center p-4 relative">
      <AnimatedBackground variant="subtle" />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-lg relative z-10"
      >
        <div className="bg-white/[0.03] border border-white/10 rounded-2xl p-8 backdrop-blur-xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="flex items-center justify-center gap-2 mb-4">
              <div className="relative flex h-16 w-16 items-center justify-center rounded-xl overflow-hidden" style={{
                boxShadow: "0 4px 20px rgba(139, 92, 246, 0.4), 0 0 40px rgba(59, 130, 246, 0.3)",
              }}>
                <Image
                  src="/logoo.png"
                  alt="Parlay Gorilla Logo"
                  width={64}
                  height={64}
                  className="object-contain"
                  priority
                />
              </div>
            </div>
            <h1 className="text-2xl font-bold text-white mb-2">Complete Your Profile</h1>
            <p className="text-gray-400">
              Let&apos;s personalize your parlay experience
            </p>
          </div>

          {/* Progress Bar */}
          <div className="mb-8">
            <div className="flex justify-between mb-2">
              <span className="text-sm text-gray-400">Step {step} of {totalSteps}</span>
              <span className="text-sm text-emerald-400">{Math.round((step / totalSteps) * 100)}%</span>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-emerald-500 to-green-400"
                initial={{ width: 0 }}
                animate={{ width: `${(step / totalSteps) * 100}%` }}
                transition={{ duration: 0.3 }}
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              className="mb-6 p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm"
            >
              {error}
            </motion.div>
          )}

          {/* Step Content */}
          <AnimatePresence mode="wait">
            {step === 1 && (
              <motion.div
                key="step1"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <div className="text-center mb-6">
                  <User className="h-12 w-12 text-emerald-400 mx-auto mb-3" />
                  <h2 className="text-xl font-semibold text-white">What should we call you?</h2>
                </div>
                <input
                  type="text"
                  value={displayName}
                  onChange={(e) => setDisplayName(e.target.value)}
                  placeholder="Enter your display name"
                  className="w-full px-4 py-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50"
                  maxLength={50}
                />
                <p className="text-xs text-gray-500">This will be shown on your profile and leaderboards</p>
              </motion.div>
            )}

            {step === 2 && (
              <motion.div
                key="step2"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <div className="text-center mb-6">
                  <Trophy className="h-12 w-12 text-emerald-400 mx-auto mb-3" />
                  <h2 className="text-xl font-semibold text-white">Pick your sports</h2>
                  <p className="text-gray-400 text-sm">Select all that interest you</p>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  {SPORTS.map((sport) => (
                    <button
                      key={sport}
                      onClick={() => toggleSport(sport)}
                      className={`p-3 rounded-lg border transition-all ${
                        favoriteSports.includes(sport)
                          ? "bg-emerald-500/20 border-emerald-500/50 text-white"
                          : "bg-white/5 border-white/10 text-gray-400 hover:border-white/20"
                      }`}
                    >
                      <span className="font-medium">{sport}</span>
                      {favoriteSports.includes(sport) && (
                        <Check className="inline-block ml-2 h-4 w-4 text-emerald-400" />
                      )}
                    </button>
                  ))}
                </div>
              </motion.div>
            )}

            {step === 3 && (
              <motion.div
                key="step3"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <div className="text-center mb-6">
                  <Heart className="h-12 w-12 text-emerald-400 mx-auto mb-3" />
                  <h2 className="text-xl font-semibold text-white">Favorite teams?</h2>
                  <p className="text-gray-400 text-sm">Optional - helps personalize suggestions</p>
                </div>

                {/* Selected Teams Display */}
                {favoriteTeams.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-500 mb-2">Selected ({favoriteTeams.length})</p>
                    <div className="flex flex-wrap gap-2">
                      {favoriteTeams.map((team) => (
                        <span
                          key={team}
                          className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-emerald-500/20 border border-emerald-500/50 text-white"
                        >
                          {team}
                          <button
                            onClick={() => removeTeam(team)}
                            className="hover:text-red-400 transition-colors"
                          >
                            <X className="h-3 w-3" />
                          </button>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Team Dropdowns */}
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {(favoriteSports.length === 0 ? SPORTS : favoriteSports).map((sport) => {
                    const teams = getFilteredTeams(sport)
                    const isOpen = openDropdowns[sport]
                    const selectedCount = favoriteTeams.filter(t => 
                      ALL_TEAMS[sport]?.includes(t)
                    ).length

                    return (
                      <div key={sport} className="relative">
                        <button
                          onClick={() => toggleDropdown(sport)}
                          className="w-full flex items-center justify-between p-3 bg-white/5 border border-white/10 rounded-lg hover:border-white/20 transition-all"
                        >
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-white">{sport}</span>
                            {selectedCount > 0 && (
                              <span className="px-2 py-0.5 rounded-full text-xs bg-emerald-500/20 text-emerald-400">
                                {selectedCount}
                              </span>
                            )}
                          </div>
                          <ChevronDown 
                            className={`h-4 w-4 text-gray-400 transition-transform ${isOpen ? "rotate-180" : ""}`} 
                          />
                        </button>

                        {isOpen && (
                          <div className="mt-2 bg-white/[0.02] border border-white/5 rounded-lg p-3 max-h-64 overflow-y-auto">
                            {/* Search Input */}
                            <input
                              type="text"
                              placeholder={`Search ${sport} teams...`}
                              value={teamSearch[sport] || ""}
                              onChange={(e) => setTeamSearch(prev => ({ ...prev, [sport]: e.target.value }))}
                              className="w-full px-3 py-2 mb-3 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/50 text-sm"
                            />

                            {/* Team List */}
                            {teams.length > 0 ? (
                              <div className="space-y-1">
                                {teams.map((team) => {
                                  const isSelected = favoriteTeams.includes(team)
                                  return (
                                    <button
                                      key={team}
                                      onClick={() => toggleTeam(team)}
                                      className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                                        isSelected
                                          ? "bg-emerald-500/20 border border-emerald-500/50 text-white"
                                          : "bg-white/5 border border-transparent text-gray-300 hover:bg-white/10 hover:border-white/10"
                                      }`}
                                    >
                                      <div className="flex items-center justify-between">
                                        <span>{team}</span>
                                        {isSelected && (
                                          <Check className="h-4 w-4 text-emerald-400" />
                                        )}
                                      </div>
                                    </button>
                                  )
                                })}
                              </div>
                            ) : (
                              <p className="text-sm text-gray-500 text-center py-4">
                                No teams found matching &quot;{teamSearch[sport]}&quot;
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </motion.div>
            )}

            {step === 4 && (
              <motion.div
                key="step4"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="space-y-4"
              >
                <div className="text-center mb-6">
                  <Zap className="h-12 w-12 text-emerald-400 mx-auto mb-3" />
                  <h2 className="text-xl font-semibold text-white">Your betting style</h2>
                  <p className="text-gray-400 text-sm">This sets your default risk level</p>
                </div>
                <div className="space-y-3">
                  {BETTING_STYLES.map((style) => (
                    <button
                      key={style.value}
                      onClick={() => setBettingStyle(style.value)}
                      className={`w-full p-4 rounded-lg border text-left transition-all ${
                        bettingStyle === style.value
                          ? "bg-emerald-500/20 border-emerald-500/50"
                          : "bg-white/5 border-white/10 hover:border-white/20"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{style.icon}</span>
                        <div>
                          <p className="font-medium text-white">{style.label}</p>
                          <p className="text-sm text-gray-400">{style.description}</p>
                        </div>
                        {bettingStyle === style.value && (
                          <Check className="ml-auto h-5 w-5 text-emerald-400" />
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Navigation Buttons */}
          <div className="flex gap-3 mt-8">
            {step > 1 && (
              <button
                onClick={() => setStep(step - 1)}
                className="flex items-center gap-1 px-4 py-2 text-gray-400 hover:text-white transition-colors"
              >
                <ChevronLeft className="h-4 w-4" />
                Back
              </button>
            )}
            <div className="flex-1" />
            {step < totalSteps ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={!canProceed()}
                className="flex items-center gap-1 px-6 py-2 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Continue
                <ChevronRight className="h-4 w-4" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading || !canProceed()}
                className="flex items-center gap-2 px-6 py-2 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:from-emerald-400 hover:to-green-400 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    Complete Setup
                    <Check className="h-4 w-4" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  )
}

