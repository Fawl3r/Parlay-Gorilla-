"use client"

import { motion } from "framer-motion"
import { Shield, Lock, Eye, Database, CheckCircle, AlertCircle } from "lucide-react"
import { Header } from "@/components/Header"
import { Footer } from "@/components/Footer"

export default function PrivacyPage() {
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
              <Shield className="h-8 w-8 text-black" />
            </div>
            <h1 className="text-4xl md:text-5xl lg:text-6xl font-black mb-4">
              <span className="text-white">Privacy </span>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400">Policy</span>
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
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <Lock className="h-6 w-6 text-emerald-400" />
                1. Introduction
              </h2>
              <p className="text-gray-400 leading-relaxed mb-4">
                At Parlay Gorilla ("we," "us," or "our"), we are committed to protecting your privacy. This Privacy Policy 
                explains how we collect, use, disclose, and safeguard your information when you use our service.
              </p>
              <p className="text-gray-400 leading-relaxed">
                Please read this Privacy Policy carefully. By using our service, you consent to the data practices described 
                in this policy. If you do not agree with our policies and practices, please do not use our service.
              </p>
            </section>

            {/* Information We Collect */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <Database className="h-6 w-6 text-emerald-400" />
                2. Information We Collect
              </h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <div>
                  <h3 className="text-lg font-semibold text-white mb-2">Information You Provide</h3>
                  <p className="mb-2">We collect information that you voluntarily provide when you:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Create an account (email address, username, password)</li>
                    <li>Use our service (parlay preferences, betting history, settings)</li>
                    <li>Contact us (name, email, message content)</li>
                    <li>Subscribe to updates or newsletters</li>
                  </ul>
                </div>
                <div className="mt-4">
                  <h3 className="text-lg font-semibold text-white mb-2">Automatically Collected Information</h3>
                  <p className="mb-2">When you use our service, we automatically collect:</p>
                  <ul className="list-disc list-inside space-y-2 ml-4">
                    <li>Device information (device type, operating system, browser type)</li>
                    <li>Usage data (pages visited, features used, time spent)</li>
                    <li>IP address and approximate location</li>
                    <li>Cookies and similar tracking technologies</li>
                    <li>Error logs and performance data</li>
                  </ul>
                </div>
              </div>
            </section>

            {/* How We Use Information */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
                <Eye className="h-6 w-6 text-emerald-400" />
                3. How We Use Your Information
              </h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>We use the information we collect to:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Provide, maintain, and improve our service</li>
                  <li>Generate personalized parlay recommendations</li>
                  <li>Process your requests and transactions</li>
                  <li>Send you service-related communications</li>
                  <li>Respond to your inquiries and provide customer support</li>
                  <li>Detect and prevent fraud, abuse, and security issues</li>
                  <li>Analyze usage patterns to improve user experience</li>
                  <li>Comply with legal obligations</li>
                  <li>Send marketing communications (with your consent)</li>
                </ul>
              </div>
            </section>

            {/* Information Sharing */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">4. Information Sharing and Disclosure</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>We do not sell your personal information. We may share your information only in the following circumstances:</p>
                <div className="space-y-3">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-1">Service Providers</h3>
                    <p>We may share information with third-party service providers who perform services on our behalf, such as:</p>
                    <ul className="list-disc list-inside space-y-1 ml-4 mt-1">
                      <li>Cloud hosting and data storage</li>
                      <li>Analytics and performance monitoring</li>
                      <li>Email delivery services</li>
                      <li>Payment processing (if applicable)</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-1">Legal Requirements</h3>
                    <p>We may disclose information if required by law or in response to valid legal requests, such as:</p>
                    <ul className="list-disc list-inside space-y-1 ml-4 mt-1">
                      <li>Court orders or subpoenas</li>
                      <li>Government investigations</li>
                      <li>Protection of our rights and safety</li>
                    </ul>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-1">Business Transfers</h3>
                    <p>In the event of a merger, acquisition, or sale of assets, your information may be transferred to the acquiring entity.</p>
                  </div>
                </div>
              </div>
            </section>

            {/* Data Security */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">5. Data Security</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  We implement appropriate technical and organizational security measures to protect your information, including:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li>Encryption of data in transit and at rest</li>
                  <li>Secure authentication and access controls</li>
                  <li>Regular security assessments and updates</li>
                  <li>Limited access to personal information on a need-to-know basis</li>
                </ul>
                <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-4 mt-4">
                  <div className="flex items-start gap-3">
                    <AlertCircle className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-amber-400 font-semibold mb-1">No System is 100% Secure</p>
                      <p className="text-amber-300 text-sm">
                        While we strive to protect your information, no method of transmission over the internet or electronic 
                        storage is completely secure. We cannot guarantee absolute security.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* Cookies */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">6. Cookies and Tracking Technologies</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  We use cookies and similar tracking technologies to enhance your experience, analyze usage, and assist with 
                  our marketing efforts. Types of cookies we use include:
                </p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><strong className="text-white">Essential Cookies:</strong> Required for the service to function</li>
                  <li><strong className="text-white">Analytics Cookies:</strong> Help us understand how users interact with our service</li>
                  <li><strong className="text-white">Preference Cookies:</strong> Remember your settings and preferences</li>
                  <li><strong className="text-white">Marketing Cookies:</strong> Used to deliver relevant advertisements</li>
                </ul>
                <p className="mt-4">
                  You can control cookies through your browser settings. However, disabling certain cookies may limit your 
                  ability to use some features of our service.
                </p>
              </div>
            </section>

            {/* Your Rights */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">7. Your Privacy Rights</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>Depending on your location, you may have the following rights regarding your personal information:</p>
                <ul className="list-disc list-inside space-y-2 ml-4">
                  <li><strong className="text-white">Access:</strong> Request a copy of the personal information we hold about you</li>
                  <li><strong className="text-white">Correction:</strong> Request correction of inaccurate or incomplete information</li>
                  <li><strong className="text-white">Deletion:</strong> Request deletion of your personal information</li>
                  <li><strong className="text-white">Portability:</strong> Request transfer of your data to another service</li>
                  <li><strong className="text-white">Opt-Out:</strong> Unsubscribe from marketing communications</li>
                  <li><strong className="text-white">Objection:</strong> Object to certain processing of your information</li>
                </ul>
                <p className="mt-4">
                  To exercise these rights, please contact us at <a href="mailto:contact@f3ai.dev" className="text-emerald-400 hover:text-emerald-300">contact@f3ai.dev</a>. 
                  We will respond to your request within a reasonable timeframe.
                </p>
              </div>
            </section>

            {/* Data Retention */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">8. Data Retention</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  We retain your personal information for as long as necessary to fulfill the purposes outlined in this Privacy Policy, 
                  unless a longer retention period is required or permitted by law.
                </p>
                <p>
                  When you delete your account, we will delete or anonymize your personal information, except where we are required 
                  to retain it for legal, regulatory, or legitimate business purposes.
                </p>
              </div>
            </section>

            {/* Children's Privacy */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">9. Children's Privacy</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  Our service is not intended for individuals under the age of 18 (or the legal gambling age in your jurisdiction). 
                  We do not knowingly collect personal information from children.
                </p>
                <p>
                  If we become aware that we have collected personal information from a child without parental consent, we will 
                  take steps to delete that information immediately. If you believe we have collected information from a child, 
                  please contact us immediately.
                </p>
              </div>
            </section>

            {/* International Users */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">10. International Data Transfers</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  Your information may be transferred to and processed in countries other than your country of residence. These 
                  countries may have data protection laws that differ from those in your country.
                </p>
                <p>
                  By using our service, you consent to the transfer of your information to these countries. We take appropriate 
                  measures to ensure your information receives adequate protection in accordance with this Privacy Policy.
                </p>
              </div>
            </section>

            {/* Changes to Policy */}
            <section className="bg-white/[0.02] border border-white/10 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">11. Changes to This Privacy Policy</h2>
              <div className="space-y-4 text-gray-400 leading-relaxed">
                <p>
                  We may update this Privacy Policy from time to time. We will notify you of any material changes by posting 
                  the new Privacy Policy on this page and updating the "Last Updated" date.
                </p>
                <p>
                  We encourage you to review this Privacy Policy periodically. Your continued use of our service after any changes 
                  constitutes acceptance of the updated Privacy Policy.
                </p>
              </div>
            </section>

            {/* Contact */}
            <section className="bg-gradient-to-br from-emerald-950/50 to-cyan-950/50 border border-emerald-500/20 rounded-2xl p-8">
              <h2 className="text-2xl font-bold text-white mb-4">12. Contact Us</h2>
              <div className="space-y-4 text-gray-300 leading-relaxed">
                <p>
                  If you have any questions, concerns, or requests regarding this Privacy Policy or our data practices, please contact us:
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

