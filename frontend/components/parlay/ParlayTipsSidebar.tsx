"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  Lightbulb, Crown, ChevronDown, ChevronUp, 
  Loader2, RefreshCw, ArrowRight, Sparkles,
  Lock
} from "lucide-react";
import { useAuth } from "@/lib/auth-context";
import { useSubscription } from "@/lib/subscription-context";
import { api } from "@/lib/api";
import Link from "next/link";

interface Tip {
  id: string;
  category: string;
  title: string;
  tip: string;
  icon: string;
}

interface TipsResponse {
  tier: "free" | "premium";
  tips: Tip[];
  personalized: boolean;
  message?: string;
  profile_summary?: string;
  upgrade_cta: boolean;
}

interface ParlayTipsSidebarProps {
  sport?: string;
  className?: string;
  collapsible?: boolean;
  defaultExpanded?: boolean;
}

export function ParlayTipsSidebar({ 
  sport, 
  className = "", 
  collapsible = true,
  defaultExpanded = true 
}: ParlayTipsSidebarProps) {
  const { user } = useAuth();
  const { isPremium } = useSubscription();
  const [tips, setTips] = useState<Tip[]>([]);
  const [tipsData, setTipsData] = useState<TipsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(defaultExpanded);

  const fetchTips = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams({ limit: "5" });
      if (sport) params.append("sport", sport);

      const response = await api.get(`/api/parlay-tips?${params}`);
      setTipsData(response.data);
      setTips(response.data.tips || []);
    } catch (err: any) {
      console.error("Failed to fetch tips:", err);
      setError(err.message || "Failed to load tips");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTips();
  }, [sport, isPremium]);

  // Get emoji from icon string or default
  const getIcon = (iconStr: string) => {
    // If it's already an emoji, return it
    if (/\p{Emoji}/u.test(iconStr)) {
      return iconStr;
    }
    return "💡";
  };

  // Get category color
  const getCategoryColor = (category: string) => {
    switch (category) {
      case "bankroll": return "text-amber-400";
      case "strategy": return "text-emerald-400";
      case "value": return "text-cyan-400";
      case "research": return "text-purple-400";
      case "timing": return "text-orange-400";
      case "mindset": return "text-pink-400";
      case "markets": return "text-blue-400";
      case "personalized": return "text-emerald-400";
      default: return "text-gray-400";
    }
  };

  return (
    <div className={`bg-[#111118] rounded-xl border border-emerald-900/30 overflow-hidden ${className}`}>
      {/* Header */}
      <div 
        className={`p-4 border-b border-emerald-900/20 flex items-center justify-between ${
          collapsible ? "cursor-pointer hover:bg-emerald-900/10 transition-colors" : ""
        }`}
        onClick={() => collapsible && setExpanded(!expanded)}
      >
        <div className="flex items-center gap-3">
          <Lightbulb className="w-5 h-5 text-amber-400" />
          <div>
            <h3 className="font-bold text-white">Parlay Tips</h3>
            {tipsData && (
              <p className="text-xs text-gray-400">
                {tipsData.personalized ? "Personalized for you" : "General tips"}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {tipsData?.tier === "premium" && (
            <span className="px-2 py-0.5 text-xs font-bold text-emerald-400 bg-emerald-500/20 rounded-full flex items-center gap-1">
              <Sparkles className="w-3 h-3" />
              AI
            </span>
          )}
          {loading && <Loader2 className="w-4 h-4 text-emerald-400 animate-spin" />}
          <button
            onClick={(e) => {
              e.stopPropagation();
              fetchTips();
            }}
            className="p-1 hover:bg-emerald-900/20 rounded"
            title="Refresh tips"
          >
            <RefreshCw className="w-4 h-4 text-gray-400" />
          </button>
          {collapsible && (
            expanded 
              ? <ChevronUp className="w-5 h-5 text-gray-400" /> 
              : <ChevronDown className="w-5 h-5 text-gray-400" />
          )}
        </div>
      </div>

      {/* Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden"
          >
            <div className="p-4">
              {/* Profile Summary (Premium) */}
              {tipsData?.profile_summary && (
                <div className="mb-4 p-3 bg-emerald-900/20 rounded-lg border border-emerald-500/20">
                  <p className="text-xs text-emerald-400 flex items-center gap-1">
                    <Sparkles className="w-3 h-3" />
                    {tipsData.profile_summary}
                  </p>
                </div>
              )}

              {/* Loading State */}
              {loading && tips.length === 0 && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-emerald-400 animate-spin" />
                </div>
              )}

              {/* Error State */}
              {error && (
                <div className="text-center py-4">
                  <p className="text-red-400 text-sm mb-2">{error}</p>
                  <button
                    onClick={fetchTips}
                    className="text-sm text-emerald-400 hover:underline"
                  >
                    Try again
                  </button>
                </div>
              )}

              {/* Tips List */}
              {!loading && !error && (
                <div className="space-y-3">
                  {tips.map((tip, index) => (
                    <motion.div
                      key={tip.id}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="p-3 bg-[#0a0a0f] rounded-lg border border-emerald-900/20 hover:border-emerald-900/40 transition-colors"
                    >
                      <div className="flex items-start gap-3">
                        <span className="text-xl">{getIcon(tip.icon)}</span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="text-sm font-medium text-white truncate">
                              {tip.title}
                            </h4>
                            <span className={`text-xs ${getCategoryColor(tip.category)}`}>
                              {tip.category}
                            </span>
                          </div>
                          <p className="text-xs text-gray-400 leading-relaxed">
                            {tip.tip}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              )}

              {/* Upgrade CTA */}
              {tipsData?.upgrade_cta && (
                <div className="mt-4 p-3 bg-gradient-to-r from-emerald-900/20 to-green-900/10 rounded-lg border border-emerald-500/30">
                  <div className="flex items-center gap-2 mb-2">
                    <Crown className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm font-medium text-white">Get AI-Personalized Tips</span>
                  </div>
                  <p className="text-xs text-gray-400 mb-3">
                    {tipsData.message || "Upgrade to Premium for tips tailored to your betting style."}
                  </p>
                  <Link
                    href="/pricing"
                    className="inline-flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors"
                  >
                    Upgrade Now <ArrowRight className="w-3 h-3" />
                  </Link>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default ParlayTipsSidebar;

