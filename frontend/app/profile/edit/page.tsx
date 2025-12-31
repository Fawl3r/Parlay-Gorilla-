"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"
import { Loader2, ArrowLeft, Save } from "lucide-react"
import Link from "next/link"
import { useAuth } from "@/lib/auth-context"
import { api } from "@/lib/api"
import { AnimatedBackground } from "@/components/AnimatedBackground"
import { Header } from "@/components/Header"
import { ALL_TEAMS } from "@/lib/teams"

const SPORTS = ["NFL", "NBA", "NHL", "MLB", "NCAAF", "NCAAB", "Soccer"]
const BETTING_STYLES = [
  { value: "conservative", label: "Conservative", icon: "🛡️", description: "Safe, steady wins" },
  { value: "balanced", label: "Balanced", icon: "⚖️", description: "Mix of safe and risk" },
  { value: "degen", label: "Degen", icon: "🔥", description: "High risk, high reward" },
]

export default function ProfileEditPage() {
  const { user, refreshUser } = useAuth()
  const router = useRouter()
  
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  
  // Form data
  const [displayName, setDisplayName] = useState("")
  const [bio, setBio] = useState("")
  const [favoriteSports, setFavoriteSports] = useState<string[]>([])
  const [favoriteTeams, setFavoriteTeams] = useState<string[]>([])
  const [bettingStyle, setBettingStyle] = useState("balanced")
  const [openDropdowns, setOpenDropdowns] = useState<Record<string, boolean>>({})
  const [teamSearch, setTeamSearch] = useState<Record<string, string>>({})

  // Load current profile data
  useEffect(() => {
    if (!user) {
      router.push("/auth/login")
      return
    }

    loadProfile()
  }, [user, router])

  const loadProfile = async () => {
    try {
      setLoading(true)
      setError(null)
      const profile = await api.getMyProfile()
      
      setDisplayName(profile.user.display_name || "")
      setBio(profile.user.bio || "")
      setFavoriteSports(profile.user.favorite_sports || [])
      setFavoriteTeams(profile.user.favorite_teams || [])
      setBettingStyle(profile.user.default_risk_profile || "balanced")
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to load profile")
    } finally {
      setLoading(false)
    }
  }

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!displayName.trim()) {
      setError("Display name is required")
      return
    }

    setSaving(true)
    setError(null)
    setSuccess(false)

    try {
      await api.updateProfile({
        display_name: displayName.trim(),
        bio: bio.trim() || undefined,
        favorite_sports: favoriteSports,
        favorite_teams: favoriteTeams,
        default_risk_profile: bettingStyle as 'conservative' | 'balanced' | 'degen',
      })

      // Refresh user data
      await refreshUser()
      setSuccess(true)
      
      // Redirect back to profile after a short delay
      setTimeout(() => {
        router.push("/profile")
      }, 1500)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || "Failed to update profile")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center relative">
        <AnimatedBackground variant="subtle" />
        <Loader2 className="h-8 w-8 animate-spin text-emerald-500 relative z-10" />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col relative" style={{ backgroundColor: "#0a0a0f" }}>
      <AnimatedBackground variant="subtle" />
      <Header />

      <main className="flex-1 py-8 px-4 relative z-10">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Back Button */}
          <Link
            href="/profile"
            className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to Profile
          </Link>

          {/* Header */}
          <div>
            <h1 className="text-3xl font-bold text-white mb-2">Edit Profile</h1>
            <p className="text-gray-400">Update your profile information</p>
          </div>

          {/* Success Message */}
          {success && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 rounded-lg bg-emerald-500/20 border border-emerald-500/40 text-emerald-300"
            >
              Profile updated successfully! Redirecting...
            </motion.div>
          )}

          {/* Error Message */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              className="p-4 rounded-lg bg-red-500/20 border border-red-500/40 text-red-300"
            >
              {error}
            </motion.div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Display Name */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
              <label className="block text-sm font-semibold text-white mb-2">
                Display Name *
              </label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                placeholder="Enter your display name"
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/30"
                maxLength={100}
                required
              />
              <p className="text-xs text-gray-400 mt-1">This will be shown on your profile and leaderboards</p>
            </div>

            {/* Bio */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
              <label className="block text-sm font-semibold text-white mb-2">
                Bio
              </label>
              <textarea
                value={bio}
                onChange={(e) => setBio(e.target.value)}
                placeholder="Tell us about yourself..."
                rows={4}
                className="w-full px-4 py-3 bg-black/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/30 resize-none"
                maxLength={500}
              />
              <p className="text-xs text-gray-400 mt-1">{bio.length}/500 characters</p>
            </div>

            {/* Favorite Sports */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
              <label className="block text-sm font-semibold text-white mb-4">
                Favorite Sports
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                {SPORTS.map((sport) => (
                  <button
                    key={sport}
                    type="button"
                    onClick={() => toggleSport(sport)}
                    className={`p-3 rounded-lg border transition-all ${
                      favoriteSports.includes(sport)
                        ? "bg-emerald-500/20 border-emerald-500/50 text-white"
                        : "bg-black/40 border-white/10 text-gray-300 hover:border-emerald-500/40 hover:text-white"
                    }`}
                  >
                    <span className="font-medium">{sport}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Favorite Teams */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
              <label className="block text-sm font-semibold text-white mb-4">
                Favorite Teams
              </label>
              
              {/* Selected Teams */}
              {favoriteTeams.length > 0 && (
                <div className="mb-4">
                  <div className="flex flex-wrap gap-2">
                    {favoriteTeams.map((team) => (
                      <span
                        key={team}
                        className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-emerald-500/20 border border-emerald-500/50 text-white"
                      >
                        {team}
                        <button
                          type="button"
                          onClick={() => removeTeam(team)}
                          className="hover:text-red-400 transition-colors"
                        >
                          ×
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

                  return (
                    <div key={sport} className="relative">
                      <button
                        type="button"
                        onClick={() => toggleDropdown(sport)}
                        className="w-full flex items-center justify-between p-3 bg-black/40 border border-white/10 rounded-lg hover:border-emerald-500/40 transition-all"
                      >
                        <span className="font-medium text-white">{sport}</span>
                        <span className="text-gray-400">{isOpen ? "−" : "+"}</span>
                      </button>

                      {isOpen && (
                        <div className="mt-2 bg-black/50 border border-white/10 rounded-lg p-3 max-h-64 overflow-y-auto">
                          <input
                            type="text"
                            placeholder={`Search ${sport} teams...`}
                            value={teamSearch[sport] || ""}
                            onChange={(e) => setTeamSearch(prev => ({ ...prev, [sport]: e.target.value }))}
                            className="w-full px-3 py-2 mb-3 bg-black/40 border border-white/10 rounded-lg text-white placeholder-gray-500 focus:outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/30 text-sm"
                          />
                          <div className="space-y-1">
                            {teams.map((team) => {
                              const isSelected = favoriteTeams.includes(team)
                              return (
                                <button
                                  key={team}
                                  type="button"
                                  onClick={() => toggleTeam(team)}
                                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-all ${
                                    isSelected
                                      ? "bg-emerald-500/20 border border-emerald-500/50 text-white"
                                      : "bg-black/30 text-gray-300 hover:bg-black/50 hover:text-white"
                                  }`}
                                >
                                  {team}
                                </button>
                              )
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  )
                })}
              </div>
            </div>

            {/* Betting Style */}
            <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-6">
              <label className="block text-sm font-semibold text-white mb-4">
                Default Betting Style
              </label>
              <div className="space-y-3">
                {BETTING_STYLES.map((style) => (
                  <button
                    key={style.value}
                    type="button"
                    onClick={() => setBettingStyle(style.value)}
                    className={`w-full p-4 rounded-lg border text-left transition-all ${
                      bettingStyle === style.value
                        ? "bg-emerald-500/20 border-emerald-500/50"
                        : "bg-black/40 border-white/10 hover:border-emerald-500/40"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">{style.icon}</span>
                      <div>
                        <p className="font-medium text-white">{style.label}</p>
                        <p className="text-sm text-gray-300">{style.description}</p>
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Submit Button */}
            <div className="flex gap-3">
              <Link
                href="/profile"
                className="px-6 py-3 rounded-lg border border-white/10 bg-black/40 text-white hover:bg-black/60 transition-colors"
              >
                Cancel
              </Link>
              <button
                type="submit"
                disabled={saving || !displayName.trim()}
                className="flex-1 flex items-center justify-center gap-2 px-6 py-3 rounded-lg bg-emerald-500 text-black font-bold hover:bg-emerald-400 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="h-4 w-4" />
                    Save Changes
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      </main>
    </div>
  )
}

