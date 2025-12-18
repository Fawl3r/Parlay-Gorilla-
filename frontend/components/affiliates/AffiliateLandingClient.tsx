"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";

import { Footer } from "@/components/Footer";
import { Header } from "@/components/Header";
import { useAuth } from "@/lib/auth-context";
import { api } from "@/lib/api";

import type { AffiliateTier } from "./types";
import { AffiliateBenefitsSection } from "./sections/AffiliateBenefitsSection";
import { AffiliateCTASection } from "./sections/AffiliateCTASection";
import { AffiliateEarningsExamplesSection } from "./sections/AffiliateEarningsExamplesSection";
import { AffiliateHeroSection } from "./sections/AffiliateHeroSection";
import { AffiliateHowItWorksSection } from "./sections/AffiliateHowItWorksSection";
import { AffiliateTiersSection } from "./sections/AffiliateTiersSection";

const FALLBACK_TIERS: AffiliateTier[] = [
  {
    tier: "rookie",
    name: "Rookie",
    revenue_threshold: 0,
    commission_rate_sub_first: 0.2,
    commission_rate_sub_recurring: 0.0,
    commission_rate_credits: 0.2,
    badge_color: "#9ca3af",
  },
  {
    tier: "pro",
    name: "Pro",
    revenue_threshold: 200,
    commission_rate_sub_first: 0.2,
    commission_rate_sub_recurring: 0.1,
    commission_rate_credits: 0.25,
    badge_color: "#3b82f6",
  },
  {
    tier: "all_star",
    name: "All-Star",
    revenue_threshold: 1000,
    commission_rate_sub_first: 0.2,
    commission_rate_sub_recurring: 0.1,
    commission_rate_credits: 0.3,
    badge_color: "#8b5cf6",
  },
  {
    tier: "hall_of_fame",
    name: "Hall of Fame",
    revenue_threshold: 5000,
    commission_rate_sub_first: 0.4,
    commission_rate_sub_recurring: 0.1,
    commission_rate_credits: 0.35,
    badge_color: "#f59e0b",
  },
];

export function AffiliateLandingClient() {
  const router = useRouter();
  const { user } = useAuth();

  const [tiers, setTiers] = useState<AffiliateTier[]>([]);
  const [isAffiliate, setIsAffiliate] = useState(false);

  useEffect(() => {
    void loadTiersAndCheck();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id]);

  const loadTiersAndCheck = async () => {
    try {
      const tiersRes = await api.get("/api/affiliates/tiers");
      setTiers(tiersRes.data.tiers || []);

      if (user) {
        try {
          await api.get("/api/affiliates/me");
          setIsAffiliate(true);
        } catch {
          setIsAffiliate(false);
        }
      } else {
        setIsAffiliate(false);
      }
    } catch (err) {
      console.error("Error loading affiliate data:", err);
    }
  };

  const handleJoinClick = () => {
    if (!user) {
      sessionStorage.setItem("redirectAfterLogin", "/affiliates/dashboard");
      router.push("/auth/signup");
      return;
    }

    if (isAffiliate) {
      router.push("/affiliates/dashboard");
      return;
    }

    router.push("/affiliates/join");
  };

  const ctaText = useMemo(() => {
    if (!user) return "Sign Up & Join the Squad";
    if (isAffiliate) return "Open Affiliate Dashboard";
    return "Join the Affiliate Program";
  }, [isAffiliate, user]);

  const displayTiers = tiers.length > 0 ? tiers : FALLBACK_TIERS;

  return (
    <div className="min-h-screen flex flex-col bg-[#0A0F0A] overflow-hidden">
      <Header />

      <main className="flex-1">
        <AffiliateHeroSection ctaText={ctaText} onJoinClick={handleJoinClick} />
        <AffiliateHowItWorksSection />
        <AffiliateTiersSection tiers={displayTiers} />
        <AffiliateEarningsExamplesSection />
        <AffiliateBenefitsSection />
        <AffiliateCTASection ctaText={ctaText} onJoinClick={handleJoinClick} />
      </main>

      <Footer />
    </div>
  );
}



