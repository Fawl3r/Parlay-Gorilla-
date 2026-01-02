"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Brain, TrendingUp, Target, AlertTriangle, 
  Lock, RefreshCw, ChevronDown, ChevronUp,
  Loader2, Crown, ArrowRight
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useSubscription } from "@/lib/subscription-context";
import { api } from "@/lib/api";
import Link from "next/link";
import { PremiumBlurOverlay } from "@/components/paywall/PremiumBlurOverlay";

interface LiveInsights {
  game_id: string;
  matchup: string;
  score: string;
  status: string;
  period?: string;
  time_remaining?: string;
  insights: {
    momentum?: string;
    key_factors?: string;
    probability_shift?: string;
    matchup_analysis?: string;
    betting_angles?: string;
  };
  is_preview?: boolean;
  upgrade_message?: string;
}

interface LiveInsightsPanelProps {
  gameId?: string;
  className?: string;
  compact?: boolean;
}

export function LiveInsightsPanel({ gameId, className = "", compact = false }: LiveInsightsPanelProps) {
  const { user } = useAuth();
  const { isPremium, isCreditUser } = useSubscription();
  const [insights, setInsights] = useState<LiveInsights | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(!compact);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  // Fetch insights
  const fetchInsights = async () => {
    if (!gameId) return;

    try {
      setLoading(true);
      setError(null);

      const endpoint = isPremium 
        ? `/api/live-insights/${gameId}`
        : `/api/live-insights/${gameId}/preview`;

      const response = await api.get(endpoint);
      setInsights(response.data);
      setLastUpdated(new Date());
    } catch (err: any) {
      console.error("Failed to fetch insights:", err);
      if (err.response?.status === 403) {
        setError("upgrade_required");
      } else {
        setError(err.message || "Failed to load insights");
      }
    } finally {
      setLoading(false);
    }
  };

  // Fetch on mount and when gameId changes
  useEffect(() => {
    fetchInsights();
  }, [gameId, isPremium]);

  // Auto-refresh every 60 seconds for premium users
  useEffect(() => {
    if (!isPremium || !gameId) return;

    const interval = setInterval(fetchInsights, 60000);
    return () => clearInterval(interval);
  }, [gameId, isPremium]);

  // If no game ID, show placeholder
  if (!gameId) {
    return (
      <div className={`bg-[#111118] rounded-xl border border-emerald-900/30 p-6 ${className}`}>
        <div className="flex items-center gap-3 mb-4">
          <Brain className="w-5 h-5 text-emerald-400" />
          <h3 className="font-bold text-white">AI Live Insights</h3>
          {!isPremium && (
            <span className="px-2 py-0.5 text-xs font-bold text-emerald-400 bg-emerald-500/20 rounded-full">
              PREMIUM
            </span>
          )}
        </div>
        <p className="text-gray-400 text-sm">
          Select a live game to see AI-powered insights and analysis.
        </p>
      </div>
    );
  }

  // Upgrade required view
  if (error === "upgrade_required" || (!isPremium && !insights?.is_preview)) {
    return (
      <div className={`bg-gradient-to-br from-emerald-900/20 to-green-900/10 rounded-xl border border-emerald-500/30 p-6 ${className}`}>
        <div className="flex items-center gap-3 mb-4">
          <Lock className="w-5 h-5 text-emerald-400" />
          <h3 className="font-bold text-white">AI Live Insights</h3>
          <span className="px-2 py-0.5 text-xs font-bold text-emerald-400 bg-emerald-500/20 rounded-full">
            PREMIUM
          </span>
        </div>
        <p className="text-gray-400 text-sm mb-4">
          Get real-time AI analysis, momentum breakdowns, and betting angles as the game unfolds.
        </p>
        <Link
          href="/pricing"
          className="inline-flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-lg hover:shadow-lg hover:shadow-emerald-500/30 transition-all text-sm"
        >
          <Crown className="w-4 h-4" />
          Upgrade to Premium
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    );
  }

  // Loading state
  if (loading && !insights) {
    return (
      <div className={`bg-[#111118] rounded-xl border border-emerald-900/30 p-6 ${className}`}>
        <div className="flex items-center justify-center gap-2 text-emerald-400">
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Loading insights...</span>
        </div>
      </div>
    );
  }

  // Error state
  if (error && error !== "upgrade_required") {
    return (
      <div className={`bg-[#111118] rounded-xl border border-red-500/30 p-6 ${className}`}>
        <div className="flex items-center gap-3 mb-2">
          <AlertTriangle className="w-5 h-5 text-red-400" />
          <span className="text-red-400">Failed to load insights</span>
        </div>
        <button
          onClick={fetchInsights}
          className="text-sm text-emerald-400 hover:underline"
        >
          Try again
        </button>
      </div>
    );
  }

  // Main insights view
  return (
    <div className={`relative bg-[#111118] rounded-xl border border-emerald-900/30 overflow-hidden ${className}`}>
      {/* Header */}
      <div 
        className="p-4 border-b border-emerald-900/20 flex items-center justify-between cursor-pointer hover:bg-emerald-900/10 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <Brain className="w-5 h-5 text-emerald-400" />
          <div>
            <h3 className="font-bold text-white">AI Live Insights</h3>
            {insights && (
              <p className="text-xs text-gray-400">{insights.matchup} • {insights.score}</p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {loading && <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />}
          <button
            onClick={(e) => {
              e.stopPropagation();
              fetchInsights();
            }}
            className="p-1 hover:bg-emerald-900/20 rounded"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4 text-gray-400" />
          </button>
          {compact && (expanded ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />)}
        </div>
      </div>

      {/* Content */}
      <AnimatePresence>
        {expanded && insights && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4 space-y-4">
              {/* Game Status */}
              <div className="flex items-center gap-2 text-sm">
                <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                  insights.status === "in_progress" 
                    ? "bg-red-500/20 text-red-400" 
                    : insights.status === "final"
                    ? "bg-gray-500/20 text-gray-400"
                    : "bg-emerald-500/20 text-emerald-400"
                }`}>
                  {insights.status === "in_progress" ? "LIVE" : insights.status?.toUpperCase()}
                </span>
                {insights.period && <span className="text-gray-400">{insights.period}</span>}
                {insights.time_remaining && <span className="text-gray-400">• {insights.time_remaining}</span>}
              </div>

              {/* Insights Sections */}
              {insights.insights.momentum && (
                <InsightSection 
                  icon={TrendingUp}
                  title="Momentum"
                  content={insights.insights.momentum}
                  locked={insights.insights.momentum.includes("🔒")}
                />
              )}

              {insights.insights.key_factors && (
                <InsightSection 
                  icon={Target}
                  title="Key Factors"
                  content={insights.insights.key_factors}
                  locked={insights.insights.key_factors.includes("🔒")}
                />
              )}

              {insights.insights.probability_shift && (
                <InsightSection 
                  icon={TrendingUp}
                  title="Probability Shift"
                  content={insights.insights.probability_shift}
                  locked={insights.insights.probability_shift.includes("🔒")}
                />
              )}

              {insights.insights.matchup_analysis && (
                <InsightSection 
                  icon={Brain}
                  title="Matchup Analysis"
                  content={insights.insights.matchup_analysis}
                  locked={insights.insights.matchup_analysis.includes("🔒")}
                />
              )}

              {insights.insights.betting_angles && isPremium && (
                <InsightSection 
                  icon={AlertTriangle}
                  title="Betting Angles"
                  content={insights.insights.betting_angles}
                  highlight
                />
              )}

              {/* Preview upgrade message */}
              {insights.is_preview && (
                <div className="p-3 bg-emerald-500/10 rounded-lg border border-emerald-500/20">
                  <p className="text-sm text-emerald-400 mb-2">{insights.upgrade_message}</p>
                  <Link
                    href="/pricing"
                    className="text-xs text-emerald-300 hover:underline flex items-center gap-1"
                  >
                    Upgrade to Premium <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              )}

              {/* Last updated */}
              {lastUpdated && (
                <p className="text-xs text-gray-500">
                  Last updated: {lastUpdated.toLocaleTimeString()}
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {!isPremium && isCreditUser && (
        <PremiumBlurOverlay
          variant="container"
          title="Premium Feature"
          message="Credits can be used on the Gorilla Parlay Generator and 🦍 Gorilla Parlay Builder 🦍 only. Upgrade to unlock Live Insights."
        />
      )}
    </div>
  );
}

// Insight section component
function InsightSection({ 
  icon: Icon, 
  title, 
  content, 
  locked = false,
  highlight = false 
}: { 
  icon: any; 
  title: string; 
  content: string; 
  locked?: boolean;
  highlight?: boolean;
}) {
  return (
    <div className={`p-3 rounded-lg ${
      highlight 
        ? "bg-amber-500/10 border border-amber-500/20" 
        : locked 
        ? "bg-[#121212]/50 border border-white/10" 
        : "bg-[#00FF5E]/10 border border-[#00FF5E]/20"
    }`}>
      <div className="flex items-center gap-2 mb-2">
        <Icon className={`w-4 h-4 ${
          highlight ? "text-amber-400" : locked ? "text-white/40" : "text-[#00FF5E]"
        }`} />
        <span className={`text-sm font-medium ${
          highlight ? "text-amber-400" : locked ? "text-white/40" : "text-[#00FF5E]"
        }`}>
          {title}
        </span>
        {locked && <Lock className="w-3 h-3 text-white/40" />}
      </div>
      <p className={`text-sm leading-relaxed ${locked ? "text-white/40" : "text-white/60"}`}>
        {content}
      </p>
    </div>
  );
}

export default LiveInsightsPanel;

