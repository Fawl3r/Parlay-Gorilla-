"use client"

import { motion } from "framer-motion"
import { FileText, Shield, AlertTriangle, CheckCircle } from "lucide-react"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"

export default function TermsPage() {
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
              <FileText className="h-8 w-8 text-black" />
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black mb-4">
              <span className="text-white">Terms of </span>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Service</span>
            </h1>
            <p className="text-gray-400">
              Last Updated: {new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}
            </p>
          </motion.div>

          {/* Content */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="space-y-8"
          >
            {/* Introduction */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">1. Agreement to Terms</h2>
              <p className="text-gray-400 leading-relaxed mb-4">
                By accessing or using Parlay Gorilla ("we," "us," or "our"), you agree to be bound by these Terms of Service ("Terms"). 
                If you disagree with any part of these terms, you may not access the service.
              </p>
              <p className="text-gray-400 leading-relaxed">
                These Terms apply to all visitors, users, and others who access or use our service. By using our service, 
                you represent that you are at least 18 years of age (or the legal age for gambling in your jurisdiction) 
                and have the legal capacity to enter into these Terms.
              </p>
            </section>

            {/* Eligibility */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <Shield className="h-6 w-6 text-emerald-400" />
                2. Eligibility and Age Requirements
              </h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  You must be at least 18 years of age (or the legal age for gambling in your jurisdiction) to use Parlay Gorilla. 
                  By using our service, you represent and warrant that:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>You are of legal age to gamble in your jurisdiction</li>
                  <li>You are not located in a jurisdiction where online gambling is prohibited</li>
                  <li>You are not self-excluded from any gambling activities</li>
                  <li>You have the legal capacity to enter into binding agreements</li>
                  <li>You will not use our service for any illegal or unauthorized purpose</li>
                </ul>
                <p className="mt-4">
                  We reserve the right to verify your age and eligibility at any time. If we determine that you do not meet 
                  these requirements, we may suspend or terminate your account immediately.
                </p>
              </div>
            </section>

            {/* Service Description */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">3. Service Description</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  Parlay Gorilla is an AI-powered platform that provides sports betting parlay suggestions, analysis, and insights. 
                  Our service includes:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>AI-generated parlay recommendations based on statistical analysis</li>
                  <li>Real-time odds from multiple sportsbooks</li>
                  <li>Win probability calculations and confidence scores</li>
                  <li>Performance tracking and analytics</li>
                  <li>Educational content about sports betting</li>
                </ul>
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mt-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-amber-400 font-semibold mb-1">Important Notice</p>
                      <p className="text-amber-300 text-sm">
                        Parlay Gorilla does not accept bets or process payments. We are an informational and analytical tool only. 
                        You must place all bets through licensed sportsbooks. We are not responsible for any losses incurred from 
                        following our suggestions.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* User Accounts */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">4. User Accounts</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  To access certain features, you must create an account. You agree to:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Provide accurate, current, and complete information during registration</li>
                  <li>Maintain and update your account information to keep it accurate</li>
                  <li>Maintain the security of your account credentials</li>
                  <li>Accept responsibility for all activities under your account</li>
                  <li>Notify us immediately of any unauthorized use of your account</li>
                </ul>
                <p className="mt-4">
                  You may not share your account with others or use another person's account. We reserve the right to suspend 
                  or terminate accounts that violate these Terms or engage in fraudulent activity.
                </p>
              </div>
            </section>

            {/* No Guarantees */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">5. No Guarantees or Warranties</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  <strong className="text-white">Parlay Gorilla makes no guarantees about the accuracy, reliability, or success of any parlay suggestions.</strong> 
                  All recommendations are based on statistical analysis and AI algorithms, but sports betting outcomes are inherently uncertain.
                </p>
                <p>
                  Our service is provided "as is" without warranties of any kind, either express or implied, including but not limited to:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Warranties of merchantability or fitness for a particular purpose</li>
                  <li>Warranties that our service will be uninterrupted, secure, or error-free</li>
                  <li>Warranties regarding the accuracy or reliability of any information provided</li>
                  <li>Warranties that any parlay will win or be profitable</li>
                </ul>
                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 mt-4">
                  <p className="text-red-400 font-semibold mb-2">Gambling Risk Warning</p>
                  <p className="text-red-300 text-sm">
                    Sports betting involves risk of loss. Past performance does not guarantee future results. 
                    You may lose money when betting on sports. Only bet what you can afford to lose.
                  </p>
                </div>
              </div>
            </section>

            {/* Limitation of Liability */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">6. Limitation of Liability</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  To the maximum extent permitted by law, Parlay Gorilla, its affiliates, and their respective officers, 
                  directors, employees, and agents shall not be liable for any indirect, incidental, special, consequential, 
                  or punitive damages, including but not limited to:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Loss of profits, revenue, or data</li>
                  <li>Losses incurred from following our parlay suggestions</li>
                  <li>Losses due to errors, omissions, or inaccuracies in our service</li>
                  <li>Losses resulting from service interruptions or technical issues</li>
                </ul>
                <p className="mt-4">
                  Our total liability to you for any claims arising from or related to your use of our service shall not exceed 
                  the amount you paid to us in the 12 months preceding the claim, or $100, whichever is greater.
                </p>
              </div>
            </section>

            {/* Intellectual Property */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">7. Intellectual Property</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  All content, features, and functionality of Parlay Gorilla, including but not limited to text, graphics, 
                  logos, icons, images, audio clips, and software, are owned by us or our licensors and are protected by 
                  copyright, trademark, and other intellectual property laws.
                </p>
                <p>
                  You may not:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Copy, modify, or distribute our content without permission</li>
                  <li>Use our service for commercial purposes without authorization</li>
                  <li>Reverse engineer or attempt to extract our algorithms or data</li>
                  <li>Remove any copyright or proprietary notices from our content</li>
                </ul>
              </div>
            </section>

            {/* Prohibited Uses */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">8. Prohibited Uses</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>You agree not to use our service to:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Violate any applicable laws or regulations</li>
                  <li>Engage in any fraudulent, deceptive, or illegal activity</li>
                  <li>Harass, abuse, or harm other users</li>
                  <li>Transmit viruses, malware, or other harmful code</li>
                  <li>Attempt to gain unauthorized access to our systems</li>
                  <li>Interfere with or disrupt our service or servers</li>
                  <li>Use automated systems to scrape or collect data</li>
                  <li>Impersonate any person or entity</li>
                </ul>
              </div>
            </section>

            {/* Termination */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">9. Termination</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  We may terminate or suspend your account and access to our service immediately, without prior notice, 
                  for any reason, including if you breach these Terms.
                </p>
                <p>
                  Upon termination, your right to use the service will cease immediately. We may delete your account and 
                  all associated data. You may also terminate your account at any time by contacting us.
                </p>
              </div>
            </section>

            {/* Changes to Terms */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">10. Changes to Terms</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  We reserve the right to modify these Terms at any time. We will notify users of material changes by 
                  posting the new Terms on this page and updating the "Last Updated" date.
                </p>
                <p>
                  Your continued use of our service after any changes constitutes acceptance of the new Terms. If you do not 
                  agree to the modified Terms, you must stop using our service.
                </p>
              </div>
            </section>

            {/* Governing Law */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">11. Governing Law</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  These Terms shall be governed by and construed in accordance with the laws of the jurisdiction in which 
                  Parlay Gorilla operates, without regard to its conflict of law provisions.
                </p>
                <p>
                  Any disputes arising from these Terms or your use of our service shall be resolved through binding arbitration 
                  or in the courts of our jurisdiction, as applicable.
                </p>
              </div>
            </section>

            {/* Contact */}
            <section className="bg-gradient-to-br from-emerald-950/50 to-cyan-950/50 border border-emerald-500/20 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">12. Contact Information</h2>
              <div className="space-y-4 text-gray-300 leading-relaxed">
                <p>
                  If you have any questions about these Terms, please contact us at:
                </p>
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-5 w-5 text-emerald-400" />
                  <a href="mailto:contact@f3ai.dev" className="text-emerald-400 hover:text-emerald-300 font-medium">
                    contact@f3ai.dev
                  </a>
                </div>
              </div>
            </section>
          </motion.div>
        </div>
      </main>
      
      <Footer />
    </div>
  )
}

