"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { 
  Crown, Zap, Target, TrendingUp, Sparkles, 
  CreditCard, Bitcoin, ArrowRight, CheckCircle,
  Brain, Radio, BarChart2, Shield
} from "lucide-react";
import { useRouter } from "next/navigation";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { PricingTable } from "@/components/pricing/PricingTable";
import { useSubscription } from "@/lib/subscription-context";
import { useAuth } from "@/lib/auth-context";
import { 
  PREMIUM_LEMONSQUEEZY_URL, 
  PREMIUM_CRYPTO_URL,
  FEATURE_HIGHLIGHTS 
} from "@/lib/pricingConfig";

export default function PricingPage() {
  const router = useRouter();
  const { user } = useAuth();
  const { isPremium, createCheckout } = useSubscription();
  const [loading, setLoading] = useState<string | null>(null);

  const handleUpgradeCard = async () => {
    if (!user) {
      sessionStorage.setItem("redirectAfterLogin", "/pricing");
      router.push("/auth/login");
      return;
    }

    try {
      setLoading("card");
      const checkoutUrl = await createCheckout("lemonsqueezy", "PG_PREMIUM_MONTHLY");
      if (checkoutUrl) {
        window.location.href = checkoutUrl;
      }
    } catch (error) {
      console.error("Checkout error:", error);
      // Fallback to direct URL
      window.location.href = PREMIUM_LEMONSQUEEZY_URL;
    } finally {
      setLoading(null);
    }
  };

  const handleUpgradeCrypto = async () => {
    if (!user) {
      sessionStorage.setItem("redirectAfterLogin", "/pricing");
      router.push("/auth/login");
      return;
    }

    try {
      setLoading("crypto");
      const checkoutUrl = await createCheckout("coinbase", "PG_LIFETIME");
      if (checkoutUrl) {
        window.location.href = checkoutUrl;
      }
    } catch (error) {
      console.error("Checkout error:", error);
      // Fallback to direct URL
      window.location.href = PREMIUM_CRYPTO_URL;
    } finally {
      setLoading(null);
    }
  };

  // Get icon component for feature highlight
  const getFeatureIcon = (iconStr: string) => {
    switch (iconStr) {
      case "🧠": return Brain;
      case "📡": return Radio;
      case "🎯": return Target;
      case "📈": return BarChart2;
      default: return Sparkles;
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-[#0a0a0f] via-[#0d1117] to-[#0a0a0f]">
      <Header />

      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-16 md:py-24 overflow-hidden">
          {/* Background Effects */}
          <div className="absolute inset-0 bg-gradient-to-b from-emerald-500/5 via-transparent to-transparent" />
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-emerald-500/10 blur-[120px] rounded-full" />

          <div className="container mx-auto px-4 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center max-w-4xl mx-auto"
            >
              {/* Badge */}
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-6">
                <Crown className="w-4 h-4 text-emerald-400" />
                <span className="text-sm text-emerald-400 font-medium">Parlay Gorilla Premium</span>
              </div>

              {/* Main Title */}
              <h1 className="text-4xl md:text-6xl font-black text-white mb-6 leading-tight">
                Choose Your Lane.{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-400">
                  Let the Gorilla Cook.
                </span>
              </h1>

              {/* Subtitle */}
              <p className="text-lg md:text-xl text-gray-400 mb-8 max-w-3xl mx-auto leading-relaxed">
                Start free and build your first parlays. Upgrade to Premium when you're ready for 
                real AI firepower — live insights, scoring updates, unlimited parlays, and the 
                full Parlay Gorilla experience.
              </p>

              {/* Feature Bullets */}
              <div className="flex flex-wrap justify-center gap-4 mb-10">
                {[
                  { icon: Zap, text: "AI-powered parlay creation" },
                  { icon: Radio, text: "Live game updates + drive-by-drive scoring" },
                  { icon: TrendingUp, text: "Deep analysis & confidence breakdowns" },
                  { icon: Brain, text: "Gorilla-grade strategies & betting tips" },
                ].map((item, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.2 + i * 0.1 }}
                    className="flex items-center gap-2 px-4 py-2 bg-white/5 rounded-lg border border-white/10"
                  >
                    <item.icon className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm text-gray-300">{item.text}</span>
                  </motion.div>
                ))}
              </div>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleUpgradeCard}
                  disabled={loading === "card"}
                  className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <CreditCard className="w-5 h-5" />
                  {loading === "card" ? "Loading..." : "Upgrade with Card"}
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleUpgradeCrypto}
                  disabled={loading === "crypto"}
                  className="w-full sm:w-auto px-8 py-4 border-2 border-emerald-500/50 text-emerald-400 font-bold rounded-xl hover:bg-emerald-500/10 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Bitcoin className="w-5 h-5" />
                  {loading === "crypto" ? "Loading..." : "Upgrade with Crypto"}
                </motion.button>
                <button
                  onClick={() => router.push("/app")}
                  className="text-gray-400 hover:text-white transition-colors flex items-center gap-1"
                >
                  Continue Free
                  <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </motion.div>
          </div>
        </section>

        {/* Two Tiers Section */}
        <section className="py-16 relative">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl md:text-4xl font-black text-white mb-4">
                Two Tiers. One Goal.{" "}
                <span className="text-emerald-400">Win Smarter. Bet Sharper.</span>
              </h2>
              <p className="text-gray-400 max-w-2xl mx-auto">
                Whether you're a casual bettor or a full-blown degen chasing clean slips, 
                Parlay Gorilla gives you the tools to take your game to the next level. 
                Start free — and when you're ready, unleash Premium.
              </p>
            </motion.div>

            {/* Pricing Table */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ delay: 0.2 }}
            >
              <PricingTable 
                onUpgradeCard={handleUpgradeCard}
                onUpgradeCrypto={handleUpgradeCrypto}
              />
            </motion.div>
          </div>
        </section>

        {/* Feature Highlights Grid */}
        <section className="py-16 bg-gradient-to-b from-transparent via-emerald-900/5 to-transparent">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="text-center mb-12"
            >
              <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
                What You Get
              </h2>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              {FEATURE_HIGHLIGHTS.map((feature, index) => {
                const Icon = getFeatureIcon(feature.icon || "✨");
                return (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, y: 20 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true }}
                    transition={{ delay: index * 0.1 }}
                    className={`p-6 rounded-xl border ${
                      feature.isPremium 
                        ? "bg-gradient-to-br from-emerald-900/20 to-green-900/10 border-emerald-500/30" 
                        : "bg-white/5 border-white/10"
                    }`}
                  >
                    <div className="flex items-start gap-4">
                      <div className={`p-3 rounded-lg ${
                        feature.isPremium ? "bg-emerald-500/20" : "bg-white/10"
                      }`}>
                        <Icon className={`w-6 h-6 ${
                          feature.isPremium ? "text-emerald-400" : "text-gray-400"
                        }`} />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-2">
                          <h3 className="text-lg font-bold text-white">{feature.title}</h3>
                          {feature.isPremium && (
                            <span className="px-2 py-0.5 text-xs font-bold text-emerald-400 bg-emerald-500/20 rounded-full">
                              PREMIUM
                            </span>
                          )}
                        </div>
                        <p className="text-gray-400 text-sm leading-relaxed">
                          {feature.description}
                        </p>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </div>
        </section>

        {/* Why Premium Section */}
        <section className="py-16">
          <div className="container mx-auto px-4">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="max-w-3xl mx-auto text-center"
            >
              <h2 className="text-3xl md:text-4xl font-black text-white mb-6">
                Why Go Premium?{" "}
                <span className="text-emerald-400">Simple — More Wins. Better Picks. Faster Info.</span>
              </h2>
              <p className="text-gray-400 text-lg leading-relaxed mb-8">
                Parlay Gorilla Premium isn't just more features. It's a full upgrade in how you 
                see the game — momentum shifts, sharper parlays, faster reactions, and deeper analytics. 
                Whether you're tightening your slips or chasing moonshot 8-leg bangers, Premium gives you an edge.
              </p>
              
              {/* Benefits List */}
              <div className="flex flex-wrap justify-center gap-3">
                {[
                  "Unlimited AI Parlays",
                  "Live Game Insights",
                  "Telegram Alerts",
                  "Full History",
                  "ROI Tracking",
                  "No Ads",
                ].map((benefit, i) => (
                  <div key={i} className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 rounded-full">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span className="text-sm text-emerald-400">{benefit}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </section>

        {/* Final CTA Section */}
        <section className="py-20 relative overflow-hidden">
          {/* Background */}
          <div className="absolute inset-0 bg-gradient-to-t from-emerald-500/10 via-transparent to-transparent" />
          
          <div className="container mx-auto px-4 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              className="max-w-2xl mx-auto text-center"
            >
              <div className="text-6xl mb-6">🦍</div>
              <h2 className="text-3xl md:text-4xl font-black text-white mb-4">
                Ready to Cook With the{" "}
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-green-400">
                  Big Gorilla?
                </span>
              </h2>
              <p className="text-gray-400 mb-8">
                Unlock real-time scoring, deep analytics, and unlimited parlays.
              </p>

              {/* CTA Buttons */}
              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleUpgradeCard}
                  disabled={loading === "card"}
                  className="w-full sm:w-auto px-8 py-4 bg-gradient-to-r from-emerald-500 to-green-500 text-black font-bold rounded-xl hover:shadow-lg hover:shadow-emerald-500/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <CreditCard className="w-5 h-5" />
                  Upgrade with Card
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.02 }}
                  whileTap={{ scale: 0.98 }}
                  onClick={handleUpgradeCrypto}
                  disabled={loading === "crypto"}
                  className="w-full sm:w-auto px-8 py-4 border-2 border-emerald-500/50 text-emerald-400 font-bold rounded-xl hover:bg-emerald-500/10 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                >
                  <Bitcoin className="w-5 h-5" />
                  Upgrade with Crypto
                </motion.button>
              </div>
              <button
                onClick={() => router.push("/app")}
                className="mt-4 text-gray-400 hover:text-white transition-colors"
              >
                Continue Free →
              </button>
            </motion.div>
          </div>
        </section>

        {/* Disclaimer */}
        <section className="py-8 border-t border-white/5">
          <div className="container mx-auto px-4">
            <p className="text-center text-xs text-gray-500 max-w-2xl mx-auto">
              Parlay Gorilla provides AI-generated sports analytics for entertainment and 
              informational purposes only. Parlay Gorilla is not a sportsbook and does not 
              accept or place bets. Always gamble responsibly.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
