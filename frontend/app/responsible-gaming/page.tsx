"use client"

import { motion } from "framer-motion"
import { Heart, AlertTriangle, Shield, Phone, Mail, ExternalLink, CheckCircle } from "lucide-react"
import Link from "next/link"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"

export default function ResponsibleGamingPage() {
  return (
    <div className="min-h-screen flex flex-col bg-[#0a0a0f]">
      <Header />
      
      <main className="flex-1 py-20">
        <div className="container mx-auto px-4 max-w-4xl">
          {/* Header */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-center mb-12"
          >
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-600 mb-6">
              <Heart className="h-8 w-8 text-black" />
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black mb-4">
              <span className="text-white">Responsible </span>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Gaming</span>
            </h1>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Your well-being is our priority. We're committed to promoting safe and responsible sports betting.
            </p>
          </motion.div>

          {/* Warning Banner */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="bg-red-500/10 border-2 border-red-500/30 rounded-2xl p-6 mb-8"
          >
            <div className="flex items-start gap-4">
              <AlertTriangle className="h-6 w-6 text-red-400 flex-shrink-0 mt-1" />
              <div>
                <h2 className="text-xl font-bold text-red-400 mb-2">Important Warning</h2>
                <p className="text-red-300 leading-relaxed">
                  Sports betting should be fun and entertaining, not a way to make money or solve financial problems. 
                  Gambling can be addictive and may cause harm. If you feel you may have a gambling problem, please seek help immediately.
                </p>
              </div>
            </div>
          </motion.div>

          {/* Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-8"
          >
            {/* Our Commitment */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <Shield className="h-6 w-6 text-emerald-400" />
                Our Commitment to Responsible Gaming
              </h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  At Parlay Gorilla, we take responsible gaming seriously. We are committed to:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Providing tools and resources to help you gamble responsibly</li>
                  <li>Promoting awareness of problem gambling</li>
                  <li>Supporting organizations that help those affected by gambling addiction</li>
                  <li>Ensuring our service is not used by minors or self-excluded individuals</li>
                  <li>Providing clear information about the risks of gambling</li>
                </ul>
              </div>
            </section>

            {/* Signs of Problem Gambling */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Recognizing Problem Gambling</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>Problem gambling can affect anyone. Watch for these warning signs:</p>
                <div className="grid md:grid-cols-2 gap-4 mt-4">
                  <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-red-400 mb-2">Behavioral Signs</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-300">
                      <li>Betting more than you can afford</li>
                      <li>Chasing losses with bigger bets</li>
                      <li>Lying about gambling activities</li>
                      <li>Neglecting work, family, or responsibilities</li>
                      <li>Borrowing money to gamble</li>
                    </ul>
                  </div>
                  <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4">
                    <h3 className="text-lg font-semibold text-red-400 mb-2">Emotional Signs</h3>
                    <ul className="list-disc list-inside space-y-1 text-sm text-gray-300">
                      <li>Feeling anxious or depressed about gambling</li>
                      <li>Mood swings related to wins/losses</li>
                      <li>Feeling guilty or ashamed</li>
                      <li>Inability to stop or control gambling</li>
                      <li>Gambling to escape problems or feelings</li>
                    </ul>
                  </div>
                </div>
              </div>
            </section>

            {/* Self-Assessment */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Self-Assessment Questions</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>Ask yourself these questions honestly:</p>
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-6 mt-4">
                  <ul className="space-y-3">
                    {[
                      "Do you bet more than you originally planned?",
                      "Do you need to bet more money to feel the same excitement?",
                      "Have you tried to stop or cut back but couldn't?",
                      "Do you feel restless or irritable when not gambling?",
                      "Do you gamble to escape problems or relieve stress?",
                      "Have you lied to family or friends about your gambling?",
                      "Have you jeopardized relationships or opportunities because of gambling?",
                      "Do you rely on others to pay gambling debts?"
                    ].map((question, index) => (
                      <li key={index} className="flex items-start gap-3">
                        <span className="text-amber-400 font-bold mt-0.5">{index + 1}.</span>
                        <span className="text-gray-300">{question}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <p className="mt-4 text-white font-semibold">
                  If you answered "yes" to several of these questions, you may have a gambling problem and should seek help.
                </p>
              </div>
            </section>

            {/* Tools & Resources */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Tools for Responsible Gaming</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>We encourage you to use these strategies to gamble responsibly:</p>
                <div className="grid md:grid-cols-2 gap-4 mt-4">
                  {[
                    {
                      title: "Set Limits",
                      description: "Decide how much time and money you can afford to spend before you start. Stick to these limits."
                    },
                    {
                      title: "Never Chase Losses",
                      description: "Accept losses as part of gambling. Trying to win back losses usually leads to bigger losses."
                    },
                    {
                      title: "Don't Bet Under Influence",
                      description: "Never gamble when you're upset, depressed, or under the influence of alcohol or drugs."
                    },
                    {
                      title: "Take Regular Breaks",
                      description: "Step away from betting regularly. Don't let gambling become your only form of entertainment."
                    },
                    {
                      title: "Keep It Fun",
                      description: "Gambling should be entertainment, not a way to make money or solve financial problems."
                    },
                    {
                      title: "Track Your Spending",
                      description: "Keep a record of how much you spend and win. This helps you stay aware of your gambling habits."
                    }
                  ].map((tool, index) => (
                    <div key={index} className="bg-emerald-500/5 border border-emerald-500/20 rounded-lg p-4">
                      <h3 className="text-lg font-semibold text-emerald-400 mb-2">{tool.title}</h3>
                      <p className="text-sm text-gray-300">{tool.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            </section>

            {/* Self-Exclusion */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Self-Exclusion</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  If you feel you need to take a break from gambling, you can self-exclude from our service. 
                  To self-exclude:
                </p>
                <ol className="list-decimal list-inside space-y-2 ml-4">
                  <li>Contact us at <a href="mailto:contact@f3ai.dev" className="text-emerald-400 hover:text-emerald-300">contact@f3ai.dev</a></li>
                  <li>Request account suspension or deletion</li>
                  <li>We will process your request immediately</li>
                </ol>
                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mt-4">
                  <p className="text-blue-300 text-sm">
                    <strong className="text-blue-400">Note:</strong> Parlay Gorilla is an informational tool. 
                    You must also self-exclude from the sportsbooks where you place bets. Contact each sportsbook 
                    directly to set up self-exclusion.
                  </p>
                </div>
              </div>
            </section>

            {/* Getting Help */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Getting Help</h2>
              <div className="space-y-6 text-gray-400 leading-relaxed">
                <p>
                  If you or someone you know has a gambling problem, help is available. These organizations provide 
                  free, confidential support:
                </p>
                
                <div className="space-y-4">
                  <div className="bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/30 rounded-lg p-6">
                    <h3 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
                      <Phone className="h-5 w-5 text-emerald-400" />
                      National Council on Problem Gambling
                    </h3>
                    <p className="text-gray-300 mb-3">
                      Provides resources, support, and treatment referrals for problem gambling.
                    </p>
                    <div className="flex flex-wrap gap-4">
                      <a 
                        href="https://www.ncpgambling.org" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 font-medium"
                      >
                        Visit Website
                        <ExternalLink className="h-4 w-4" />
                      </a>
                      <a 
                        href="tel:1-800-522-4700" 
                        className="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 font-medium"
                      >
                        Call: 1-800-522-4700
                      </a>
                    </div>
                  </div>

                  <div className="bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/30 rounded-lg p-6">
                    <h3 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
                      <Phone className="h-5 w-5 text-emerald-400" />
                      Gamblers Anonymous
                    </h3>
                    <p className="text-gray-300 mb-3">
                      A fellowship of men and women who share their experience, strength, and hope to solve their common problem.
                    </p>
                    <a 
                      href="https://www.gamblersanonymous.org" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 font-medium"
                    >
                      Visit Website
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>

                  <div className="bg-gradient-to-r from-emerald-500/10 to-cyan-500/10 border border-emerald-500/30 rounded-lg p-6">
                    <h3 className="text-xl font-bold text-white mb-3 flex items-center gap-2">
                      <Mail className="h-5 w-5 text-emerald-400" />
                      Gam-Anon
                    </h3>
                    <p className="text-gray-300 mb-3">
                      Support group for family and friends of problem gamblers.
                    </p>
                    <a 
                      href="https://www.gam-anon.org" 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-emerald-400 hover:text-emerald-300 font-medium"
                    >
                      Visit Website
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </div>
              </div>
            </section>

            {/* Additional Resources */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Additional Resources</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>More organizations that can help:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>
                    <strong className="text-white">Crisis Text Line:</strong> Text HOME to 741741
                  </li>
                  <li>
                    <strong className="text-white">National Suicide Prevention Lifeline:</strong> 988
                  </li>
                  <li>
                    <strong className="text-white">SAMHSA National Helpline:</strong> 1-800-662-4357
                  </li>
                </ul>
              </div>
            </section>

            {/* Contact */}
            <section className="bg-gradient-to-br from-emerald-950/50 to-cyan-950/50 border border-emerald-500/20 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">Need Immediate Help?</h2>
              <div className="space-y-4 text-gray-300 leading-relaxed">
                <p>
                  If you're in crisis or need immediate support, please reach out:
                </p>
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-emerald-400" />
                  <a href="mailto:contact@f3ai.dev" className="text-emerald-400 hover:text-emerald-300 font-medium">
                    contact@f3ai.dev
                  </a>
                </div>
                <p className="text-sm text-gray-400 mt-4">
                  We can help you self-exclude from our service or connect you with resources for problem gambling support.
                </p>
              </div>
            </section>
          </motion.div>
        </div>
      </main>
      
      <Footer />
    </div>
  )
}

