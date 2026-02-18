/**
 * V2 SETTINGS PAGE
 * Route: /v2/app/settings
 */

'use client'

import { GlassCard } from '@/components/v2/GlassCard'
import { AnimatedPage } from '@/components/v2/AnimatedPage'

export default function V2SettingsPage() {
  return (
    <AnimatedPage>
      <div className="max-w-4xl mx-auto p-4 lg:p-6 space-y-6">
        <div>
          <h2 className="text-2xl font-bold text-white mb-1">Settings</h2>
          <p className="text-white/60 text-sm">Manage your account and preferences</p>
        </div>

        <GlassCard padding="lg" hover>
          <h3 className="text-lg font-bold text-white mb-4">Account</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-white/50 mb-2">Username</label>
              <input
                type="text"
                defaultValue="Demo User"
                className="w-full px-4 py-3 bg-white/5 text-white rounded-lg border border-[rgba(255,255,255,0.08)] focus:border-[#00FF5E] focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-white/50 mb-2">Email</label>
              <input
                type="email"
                defaultValue="demo@parlaygorilla.com"
                className="w-full px-4 py-3 bg-white/5 text-white rounded-lg border border-[rgba(255,255,255,0.08)] focus:border-[#00FF5E] focus:outline-none"
              />
            </div>
          </div>
        </GlassCard>

        <GlassCard padding="lg" hover>
          <h3 className="text-lg font-bold text-white mb-4">Notifications</h3>
          <div className="space-y-3">
            {[
              { label: 'New AI Picks', desc: 'Get notified when new picks are available' },
              { label: 'Bet Results', desc: 'Receive updates on your bet outcomes' },
              { label: 'Weekly Summary', desc: 'Get a weekly performance report' },
            ].map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 rounded-lg bg-white/5 border border-[rgba(255,255,255,0.08)]">
                <div>
                  <div className="text-sm font-medium text-white">{item.label}</div>
                  <div className="text-xs text-white/50">{item.desc}</div>
                </div>
                <button className="relative w-12 h-6 bg-[#00FF5E] rounded transition-colors">
                  <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded" />
                </button>
              </div>
            ))}
          </div>
        </GlassCard>

        <GlassCard padding="lg" hover>
          <h3 className="text-lg font-bold text-white mb-4">Display</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-white">Dark Mode</div>
                <div className="text-xs text-white/50">Currently enabled</div>
              </div>
              <button className="relative w-12 h-6 bg-[#00FF5E] rounded transition-colors">
                <div className="absolute right-1 top-1 w-4 h-4 bg-white rounded" />
              </button>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium text-white">Odds Format</div>
                <div className="text-xs text-white/50">American (-110, +150)</div>
              </div>
              <select className="px-3 py-2 bg-white/5 text-white rounded-lg border border-[rgba(255,255,255,0.08)] focus:border-[#00FF5E] focus:outline-none text-sm">
                <option>American</option>
                <option>Decimal</option>
                <option>Fractional</option>
              </select>
            </div>
          </div>
        </GlassCard>

        <GlassCard padding="lg" hover>
        <h3 className="text-lg font-bold text-white mb-4">Subscription</h3>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-sm font-medium text-white">Current Plan</div>
            <div className="text-xs text-white/50">Free Tier</div>
          </div>
          <span className="px-3 py-1 bg-white/10 text-white/80 rounded text-sm font-semibold">
            Free
          </span>
        </div>
        <button className="w-full min-h-[44px] px-4 py-3 bg-[#00FF5E] hover:bg-[#22FF6E] text-black font-semibold rounded-lg v2-transition-colors v2-press-scale">
          Upgrade to Pro
        </button>
      </GlassCard>

        <GlassCard padding="lg" hover>
          <h3 className="text-lg font-bold text-red-400 mb-4">Danger Zone</h3>
          <div className="space-y-3">
            <button className="w-full px-4 py-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 font-semibold rounded-lg border border-red-500/50 v2-transition-colors">
              Reset All Data
            </button>
            <button className="w-full px-4 py-3 bg-red-500/10 hover:bg-red-500/20 text-red-400 font-semibold rounded-lg border border-red-500/50 v2-transition-colors">
              Delete Account
            </button>
          </div>
        </GlassCard>
      </div>
    </AnimatedPage>
  )
}
