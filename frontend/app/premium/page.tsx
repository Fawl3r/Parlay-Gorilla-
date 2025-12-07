"use client"

import { useState } from "react"
import { motion } from "framer-motion"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useAuth } from "@/lib/auth-context"
import { useSubscription } from "@/lib/subscription-context"
import { 
  Crown, 
  Check, 
  Zap, 
  Shield, 
  TrendingUp, 
  BarChart3,
  Target,
  Sparkles,
  ArrowRight,
  Star,
  Lock,
  Unlock,
  CreditCard,
  Bitcoin
} from "lucide-react"

const PLANS = [
  {
    name: "Monthly",
    price: "$19.99",
    period: "/month",
    description: "Perfect for trying out Parlay Gorilla",
    popular: false,
    features: [
      "Unlimited AI parlays",
      "Custom parlay builder",
      "Gorilla Upset Finder",
      "Full parlay history",
      "Multi-sport mixing",
      "Priority support"
    ]
  },
  {
    name: "Annual",
    price: "$149.99",
    period: "/year",
    description: "Best value - save 37%",
    popular: true,
    originalPrice: "$239.88",
    features: [
      "Everything in Monthly",
      "2 months free",
      "Early access to new features",
      "Exclusive Discord access",
      "Annual member badge",
      "Lifetime price lock"
    ]
  }
]

const FREE_VS_PREMIUM = [
  {
    feature: "Game Analysis Pages",
    free: true,
    premium: true,
    freeText: "Unlimited",
    premiumText: "Unlimited"
  },
  {
    feature: "AI Parlay Builder",
    free: true,
    premium: true,
    freeText: "1 per day",
    premiumText: "Unlimited"
  },
  {
    feature: "Custom Parlay Builder",
    free: false,
    premium: true,
    freeText: "Locked",
    premiumText: "Full access"
  },
  {
    feature: "Gorilla Upset Finder",
    free: false,
    premium: true,
    freeText: "Locked",
    premiumText: "Full access"
  },
  {
    feature: "Multi-Sport Parlays",
    free: false,
    premium: true,
    freeText: "Locked",
    premiumText: "Mix any sports"
  },
  {
    feature: "Parlay History",
    free: true,
    premium: true,
    freeText: "Last 5",
    premiumText: "Unlimited"
  },
  {
    feature: "EV Filters & Tools",
    free: false,
    premium: true,
    freeText: "Locked",
    premiumText: "Full access"
  },
  {
    feature: "Ads",
    free: true,
    premium: false,
    freeText: "Yes",
    premiumText: "No ads"
  }
]

const TESTIMONIALS = [
  {
    quote: "The Gorilla Upset Finder alone paid for my subscription in the first week. 🦍",
    author: "Mike R.",
    winnings: "+$2,340"
  },
  {
    quote: "Finally an AI that actually explains WHY each pick is strong. Game changer.",
    author: "Sarah K.",
    winnings: "+$890"
  },
  {
    quote: "Mixed a 12-leg parlay across NFL, NBA, and NHL. Hit for +8500. Insane.",
    author: "James T.",
    winnings: "+$4,250"
  }
]

export default function PremiumPage() {
  const { user } = useAuth()
  const { isPremium } = useSubscription()
  const [selectedPlan, setSelectedPlan] = useState<"monthly" | "annual">("annual")
  const [paymentMethod, setPaymentMethod] = useState<"card" | "crypto">("card")

  const handleSubscribe = async () => {
    // In production, this would redirect to LemonSqueezy or Coinbase Commerce
    if (paymentMethod === "card") {
      // Redirect to LemonSqueezy checkout
      window.open("https://parlaygorilla.lemonsqueezy.com/checkout", "_blank")
    } else {
      // Redirect to Coinbase Commerce
      window.open("https://commerce.coinbase.com/checkout/parlay-gorilla", "_blank")
    }
  }

  if (isPremium) {
    return (
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 flex items-center justify-center">
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="text-center max-w-md mx-auto px-4"
          >
            <div className="w-20 h-20 rounded-full bg-gradient-to-br from-emerald-400 to-green-500 flex items-center justify-center mx-auto mb-6">
              <Crown className="h-10 w-10 text-black" />
            </div>
            <h1 className="text-3xl font-black text-white mb-4">You're Already Premium!</h1>
            <p className="text-gray-400 mb-6">
              Enjoy unlimited access to all Parlay Gorilla features.
            </p>
            <Link href="/build">
              <Button className="bg-emerald-500 hover:bg-emerald-600 text-black">
                Start Building Parlays
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            </Link>
          </motion.div>
        </main>
        <Footer />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      
      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-20 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-b from-emerald-950/50 via-black/50 to-black/30" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-emerald-500/10 rounded-full blur-[150px]" />
          
          <div className="container mx-auto px-4 relative z-10">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center max-w-3xl mx-auto"
            >
              <Badge className="mb-4 bg-emerald-500/20 text-emerald-400 border-emerald-500/30">
                <Sparkles className="h-3 w-3 mr-1" />
                Unlock Full Power
              </Badge>
              
              <h1 className="text-4xl md:text-5xl lg:text-6xl font-black mb-6">
                <span className="text-white">Go </span>
                <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 via-green-400 to-cyan-400">
                  Premium
                </span>
              </h1>
              
              <p className="text-xl text-gray-300 mb-8">
                Unlimited AI parlays, exclusive tools, and the edge you need to win bigger.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Pricing Cards */}
        <section className="py-12 bg-black/30 backdrop-blur-sm">
          <div className="container mx-auto px-4">
            <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
              {PLANS.map((plan, index) => (
                <motion.div
                  key={plan.name}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  onClick={() => setSelectedPlan(plan.name.toLowerCase() as any)}
                  className={`relative rounded-2xl p-6 cursor-pointer transition-all ${
                    selectedPlan === plan.name.toLowerCase()
                      ? "bg-emerald-500/10 border-2 border-emerald-500"
                      : "bg-white/[0.02] border-2 border-white/10 hover:border-white/20"
                  }`}
                >
                  {plan.popular && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <Badge className="bg-emerald-500 text-black font-bold">
                        <Star className="h-3 w-3 mr-1" />
                        Most Popular
                      </Badge>
                    </div>
                  )}
                  
                  <div className="text-center mb-6">
                    <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                    <div className="flex items-baseline justify-center gap-1">
                      {plan.originalPrice && (
                        <span className="text-gray-500 line-through text-lg">{plan.originalPrice}</span>
                      )}
                      <span className="text-4xl font-black text-emerald-400">{plan.price}</span>
                      <span className="text-gray-400">{plan.period}</span>
                    </div>
                    <p className="text-sm text-gray-400 mt-2">{plan.description}</p>
                  </div>
                  
                  <ul className="space-y-3">
                    {plan.features.map((feature) => (
                      <li key={feature} className="flex items-center gap-3 text-sm text-gray-300">
                        <Check className="h-4 w-4 text-emerald-400 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </motion.div>
              ))}
            </div>
            
            {/* Payment Method Selection */}
            <div className="max-w-md mx-auto mt-8">
              <p className="text-sm text-gray-400 text-center mb-3">Pay with</p>
              <div className="flex gap-3">
                <button
                  onClick={() => setPaymentMethod("card")}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg transition-all ${
                    paymentMethod === "card"
                      ? "bg-white/10 border-2 border-emerald-500 text-white"
                      : "bg-white/5 border-2 border-white/10 text-gray-400 hover:border-white/20"
                  }`}
                >
                  <CreditCard className="h-4 w-4" />
                  <span className="font-medium">Card</span>
                </button>
                <button
                  onClick={() => setPaymentMethod("crypto")}
                  className={`flex-1 flex items-center justify-center gap-2 py-3 rounded-lg transition-all ${
                    paymentMethod === "crypto"
                      ? "bg-white/10 border-2 border-emerald-500 text-white"
                      : "bg-white/5 border-2 border-white/10 text-gray-400 hover:border-white/20"
                  }`}
                >
                  <Bitcoin className="h-4 w-4" />
                  <span className="font-medium">Crypto</span>
                </button>
              </div>
              
              <Button
                onClick={handleSubscribe}
                className="w-full mt-4 bg-emerald-500 hover:bg-emerald-600 text-black font-bold py-6 text-lg"
              >
                <Crown className="h-5 w-5 mr-2" />
                Upgrade to Premium
              </Button>
              
              <p className="text-xs text-gray-500 text-center mt-3">
                Cancel anytime. No questions asked.
              </p>
            </div>
          </div>
        </section>

        {/* Free vs Premium Comparison */}
        <section className="py-16 bg-gradient-to-b from-black/30 to-emerald-950/20">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-black text-center mb-12">
              <span className="text-white">Free vs </span>
              <span className="text-emerald-400">Premium</span>
            </h2>
            
            <div className="max-w-3xl mx-auto">
              <div className="rounded-xl overflow-hidden border border-white/10">
                {/* Header */}
                <div className="grid grid-cols-3 bg-white/5 p-4">
                  <div className="text-sm font-medium text-gray-400">Feature</div>
                  <div className="text-sm font-medium text-gray-400 text-center">Free</div>
                  <div className="text-sm font-medium text-emerald-400 text-center">Premium</div>
                </div>
                
                {/* Rows */}
                {FREE_VS_PREMIUM.map((row, index) => (
                  <div
                    key={row.feature}
                    className={`grid grid-cols-3 p-4 ${
                      index % 2 === 0 ? "bg-white/[0.02]" : ""
                    }`}
                  >
                    <div className="text-sm text-white">{row.feature}</div>
                    <div className="text-center">
                      {row.free ? (
                        <span className="text-sm text-gray-400">{row.freeText}</span>
                      ) : (
                        <Lock className="h-4 w-4 text-gray-600 mx-auto" />
                      )}
                    </div>
                    <div className="text-center">
                      {row.premium ? (
                        <span className="text-sm text-emerald-400 font-medium">{row.premiumText}</span>
                      ) : (
                        <Check className="h-4 w-4 text-emerald-400 mx-auto" />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        {/* Benefits Grid */}
        <section className="py-16 bg-black/30 backdrop-blur-sm">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-black text-center mb-12">
              <span className="text-white">Why Go </span>
              <span className="text-emerald-400">Premium?</span>
            </h2>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto">
              {[
                {
                  icon: <Zap className="h-6 w-6" />,
                  title: "Unlimited AI Parlays",
                  description: "Generate as many AI-optimized parlays as you want. No daily limits."
                },
                {
                  icon: <Target className="h-6 w-6" />,
                  title: "Gorilla Upset Finder",
                  description: "Exclusive tool that finds high-value underdogs the market is sleeping on."
                },
                {
                  icon: <TrendingUp className="h-6 w-6" />,
                  title: "Multi-Sport Mixing",
                  description: "Build parlays across NFL, NBA, NHL, MLB, and Soccer simultaneously."
                },
                {
                  icon: <BarChart3 className="h-6 w-6" />,
                  title: "Advanced EV Tools",
                  description: "See expected value, edge percentages, and bust risk for every leg."
                },
                {
                  icon: <Shield className="h-6 w-6" />,
                  title: "Full Parlay History",
                  description: "Track all your parlays, see what hit, and learn from past picks."
                },
                {
                  icon: <Sparkles className="h-6 w-6" />,
                  title: "No Ads",
                  description: "Enjoy a clean, distraction-free experience without any advertisements."
                }
              ].map((benefit, index) => (
                <motion.div
                  key={benefit.title}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="p-6 rounded-xl bg-white/[0.02] border border-white/10"
                >
                  <div className="w-12 h-12 rounded-xl bg-emerald-500/20 flex items-center justify-center text-emerald-400 mb-4">
                    {benefit.icon}
                  </div>
                  <h3 className="text-lg font-bold text-white mb-2">{benefit.title}</h3>
                  <p className="text-sm text-gray-400">{benefit.description}</p>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Testimonials */}
        <section className="py-16 bg-gradient-to-b from-black/30 to-emerald-950/20">
          <div className="container mx-auto px-4">
            <h2 className="text-3xl font-black text-center mb-12">
              <span className="text-white">What Members </span>
              <span className="text-emerald-400">Say</span>
            </h2>
            
            <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
              {TESTIMONIALS.map((testimonial, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: index * 0.1 }}
                  className="p-6 rounded-xl bg-white/[0.02] border border-white/10"
                >
                  <p className="text-gray-300 mb-4 italic">"{testimonial.quote}"</p>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-500">— {testimonial.author}</span>
                    <span className="text-sm font-bold text-emerald-400">{testimonial.winnings}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Final CTA */}
        <section className="py-20 relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-emerald-950/50 via-black/50 to-cyan-950/50" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-emerald-500/10 rounded-full blur-[120px]" />
          
          <div className="container mx-auto px-4 relative z-10 text-center">
            <h2 className="text-4xl md:text-5xl font-black mb-6">
              <span className="text-white">Ready to Win </span>
              <span className="text-emerald-400">Bigger?</span>
            </h2>
            <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
              Join thousands of bettors using Parlay Gorilla Premium to build smarter, more profitable parlays.
            </p>
            <Button
              onClick={handleSubscribe}
              size="lg"
              className="bg-emerald-500 hover:bg-emerald-600 text-black font-bold px-8 py-6 text-lg"
            >
              <Crown className="h-5 w-5 mr-2" />
              Upgrade Now
              <ArrowRight className="h-5 w-5 ml-2" />
            </Button>
          </div>
        </section>
      </main>
      
      <Footer />
    </div>
  )
}

