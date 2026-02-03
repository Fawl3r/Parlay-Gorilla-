/**
 * Event Tracking Helper for Parlay Gorilla Analytics
 * 
 * Provides client-side event tracking that sends to our PostgreSQL backend.
 * No external analytics dependencies - all data stays in our database.
 */

import { api } from './api';

// Session ID persists across page loads but resets on browser close.
// Stored as pg_session_id in sessionStorage; appended to every event for Template Completion Rate (template_applied → analyze_clicked within 2 min).
let sessionId: string | null = null;

/**
 * Get or create a session ID for anonymous tracking.
 * Enables clean joins (e.g. Template Completion Rate by session) without fuzzy time-window logic.
 */
function getSessionId(): string {
  if (sessionId) return sessionId;

  if (typeof window !== 'undefined') {
    sessionId = sessionStorage.getItem('pg_session_id');
    if (!sessionId) {
      sessionId = crypto.randomUUID();
      sessionStorage.setItem('pg_session_id', sessionId);
    }
  } else {
    sessionId = crypto.randomUUID();
  }

  return sessionId;
}

/**
 * Event types supported by the tracking system
 */
export type EventType =
  | 'view_analysis'
  | 'build_parlay'
  | 'view_parlay_result'
  | 'click_upset_finder'
  | 'click_sportsbook_affiliate'
  | 'page_view'
  | 'share_parlay'
  | 'save_parlay'
  | 'signup_start'
  | 'signup_complete'
  | 'login'
  | 'upgrade_click'
  | 'pwa_install_prompted'
  | 'pwa_install_accepted'
  | 'pwa_install_dismissed'
  | 'pwa_cta_shown'
  | 'pwa_cta_clicked'
  | 'pwa_howto_opened'
  | 'ai_picks_generate_fail'
  | 'ai_picks_generate_fail_reason'
  | 'ai_picks_fallback_used'
  | 'ai_picks_generate_success'
  | 'ai_picks_generate_attempt'
  | 'ai_picks_quick_action_clicked'
  | 'ai_picks_quick_action_result'
  | 'triple_selected'
  | 'triple_available'
  | 'triple_disabled'
  | 'triple_generated'
  | 'triple_downgraded_to_double'
  | 'triple_failed_no_legs'
  | 'beginner_graduation_nudge_shown'
  | 'beginner_graduation_nudge_clicked'
  // Growth System v1 — onboarding & premium
  | 'app_opened'
  | 'onboarding_quick_start_shown'
  | 'onboarding_quick_start_clicked'
  | 'activation_success'
  | 'onboarding_return_session'
  | 'premium_upsell_shown'
  | 'premium_upgrade_clicked'
  // Custom Builder funnel
  | 'custom_builder_opened'
  | 'custom_builder_pick_added'
  | 'custom_builder_pick_removed'
  | 'custom_builder_analyze_clicked'
  | 'custom_builder_analyze_success'
  | 'custom_builder_analyze_fail'
  | 'custom_builder_save_clicked'
  | 'custom_builder_save_success'
  | 'custom_builder_save_fail'
  | 'custom_builder_paywall_shown'
  | 'custom_builder_upgrade_clicked'
  | 'custom_builder_clear_slip'
  // Custom Builder QuickStart templates
  | 'custom_builder_template_clicked'
  | 'custom_builder_template_partial'
  | 'custom_builder_template_applied'
  | 'custom_builder_template_followthrough_shown'
  // Custom Builder hedge (Counter Ticket + Coverage Pack)
  | 'custom_builder_counter_generate_clicked'
  | 'custom_builder_counter_generate_success'
  | 'custom_builder_counter_generate_fail'
  | 'custom_builder_coverage_generate_clicked'
  | 'custom_builder_coverage_generate_success'
  | 'custom_builder_coverage_generate_fail'
  | 'custom_builder_hedge_apply_clicked';

/**
 * Parlay types for parlay-specific tracking
 */
export type ParlayType = 'safe' | 'balanced' | 'degen' | 'custom';

/**
 * Metadata for generic events
 */
export interface EventMetadata {
  sport?: string;
  matchup?: string;
  team?: string;
  [key: string]: string | number | boolean | undefined;
}

/**
 * Track a generic analytics event
 * 
 * @param eventType - Type of event (view_analysis, build_parlay, etc.)
 * @param metadata - Optional additional data about the event
 * 
 * @example
 * // Track analysis page view
 * trackEvent('view_analysis', { sport: 'nfl', matchup: 'bears-vs-packers' });
 * 
 * // Track feature click
 * trackEvent('click_upset_finder');
 */
export async function trackEvent(
  eventType: EventType,
  metadata?: EventMetadata
): Promise<void> {
  try {
    const payload = {
      event_type: eventType,
      session_id: getSessionId(),
      metadata: metadata || {},
      page_url: typeof window !== 'undefined' ? window.location.href : undefined,
      referrer: typeof document !== 'undefined' ? document.referrer : undefined,
    };

    // Fire and forget - don't await to avoid blocking UI
    api.post('/events', payload).catch(err => {
      // Silent fail - analytics shouldn't break the app
      if (process.env.NODE_ENV === 'development') {
        console.warn('Event tracking failed:', err);
      }
    });
  } catch (err) {
    // Silent fail
    if (process.env.NODE_ENV === 'development') {
      console.warn('Event tracking error:', err);
    }
  }
}

/**
 * Parlay event tracking data
 */
export interface ParlayEventData {
  parlayType: ParlayType;
  legsCount: number;
  parlayId?: string;
  sportFilters?: string[];
  expectedValue?: number;
  combinedOdds?: number;
  hitProbability?: number;
  legsBreakdown?: {
    moneyline?: number;
    spread?: number;
    total?: number;
    upsets?: number;
  };
  wasSaved?: boolean;
  wasShared?: boolean;
  buildMethod?: 'auto_generated' | 'user_built' | 'ai_assisted';
}

/**
 * Track a parlay-specific event
 * 
 * @param data - Parlay event data
 * 
 * @example
 * trackParlayEvent({
 *   parlayType: 'balanced',
 *   legsCount: 5,
 *   expectedValue: 0.12,
 *   combinedOdds: 25.5,
 *   buildMethod: 'auto_generated',
 * });
 */
export async function trackParlayEvent(data: ParlayEventData): Promise<void> {
  try {
    const payload = {
      parlay_type: data.parlayType,
      legs_count: data.legsCount,
      session_id: getSessionId(),
      parlay_id: data.parlayId,
      sport_filters: data.sportFilters,
      expected_value: data.expectedValue,
      combined_odds: data.combinedOdds,
      hit_probability: data.hitProbability,
      legs_breakdown: data.legsBreakdown,
      was_saved: data.wasSaved || false,
      was_shared: data.wasShared || false,
      build_method: data.buildMethod,
    };

    // Fire and forget
    api.post('/events/parlay', payload).catch(err => {
      if (process.env.NODE_ENV === 'development') {
        console.warn('Parlay event tracking failed:', err);
      }
    });
  } catch (err) {
    if (process.env.NODE_ENV === 'development') {
      console.warn('Parlay event tracking error:', err);
    }
  }
}

/**
 * Track a page view event
 * 
 * Call this in page components or layout to track page visits.
 * 
 * @param pageName - Optional page name for categorization
 */
export function trackPageView(pageName?: string): void {
  trackEvent('page_view', pageName ? { page: pageName } : undefined);
}

/**
 * Track analysis page view with matchup details
 * 
 * @param sport - Sport code (nfl, nba, etc.)
 * @param matchup - Matchup slug (team1-vs-team2)
 */
export function trackAnalysisView(sport: string, matchup: string): void {
  trackEvent('view_analysis', { sport, matchup });
}

/**
 * Track parlay builder session start
 * 
 * @param sport - Optional initial sport filter
 */
export function trackParlayBuilderOpen(sport?: string): void {
  trackEvent('build_parlay', sport ? { sport } : undefined);
}

/**
 * Track upset finder feature usage
 */
export function trackUpsetFinderClick(): void {
  trackEvent('click_upset_finder');
}

/**
 * Track share action
 * 
 * @param parlayId - ID of the shared parlay
 */
export function trackShareParlay(parlayId: string): void {
  trackEvent('share_parlay', { parlay_id: parlayId });
}

/**
 * Track save action
 * 
 * @param parlayId - ID of the saved parlay
 */
export function trackSaveParlay(parlayId: string): void {
  trackEvent('save_parlay', { parlay_id: parlayId });
}

/**
 * Track upgrade button click
 *
 * @param source - Where the click originated (header, paywall, etc.)
 */
export function trackUpgradeClick(source: string): void {
  trackEvent('upgrade_click', { source });
}

// --- Growth System v1: onboarding funnel & premium ---

export type AppOpenedSource = 'direct' | 'pwa' | 'share' | 'bookmark';

export function trackAppOpened(payload: {
  beginner_mode: boolean;
  is_pwa: boolean;
  source?: AppOpenedSource;
}): void {
  trackEvent('app_opened', payload);
}

export function trackOnboardingQuickStartShown(): void {
  trackEvent('onboarding_quick_start_shown', { beginner_mode: true });
}

export type QuickStartOption = 'nfl' | 'nba' | 'confidence_mode' | 'all_sports';

export function trackOnboardingQuickStartClicked(option: QuickStartOption): void {
  trackEvent('onboarding_quick_start_clicked', { option, beginner_mode: true });
}

export type AiPicksRequestMode = 'SINGLE' | 'DOUBLE' | 'TRIPLE';

export function trackAiPicksGenerateAttempt(payload: {
  beginner_mode: boolean;
  request_mode: AiPicksRequestMode;
  num_picks: number;
  selected_sports: string[];
}): void {
  trackEvent('ai_picks_generate_attempt', payload);
}

export function trackAiPicksGenerateSuccess(payload: {
  beginner_mode: boolean;
  request_mode: AiPicksRequestMode;
  num_picks: number;
  fallback_used: boolean;
  downgraded: boolean;
  time_to_success_ms: number;
}): void {
  trackEvent('ai_picks_generate_success', payload);
}

export function trackActivationSuccess(payload: {
  beginner_mode: boolean;
  used_quick_start: boolean;
  request_mode: 'SINGLE' | 'TRIPLE';
  time_to_first_success_ms: number;
}): void {
  trackEvent('activation_success', payload);
}

export function trackOnboardingReturnSession(payload: {
  hours_since_last_session: number;
  beginner_mode: boolean;
}): void {
  trackEvent('onboarding_return_session', payload);
}

export type PremiumUpsellTrigger = 'confidence_disabled' | 'mixed_sports_locked' | 'thin_slate';
export type PremiumUpsellVariant = 'A' | 'B' | 'C';

export function trackPremiumUpsellShown(payload: {
  trigger: PremiumUpsellTrigger;
  variant: PremiumUpsellVariant;
}): void {
  trackEvent('premium_upsell_shown', payload);
}

export function trackPremiumUpgradeClicked(payload: { trigger: string; variant: string }): void {
  trackEvent('premium_upgrade_clicked', payload);
}

// --- Custom Builder funnel ---

export function trackCustomBuilderOpened(payload: {
  sport: string;
  is_premium: boolean;
  credits: number;
}): void {
  trackEvent('custom_builder_opened', payload);
}

export function trackCustomBuilderPickAdded(payload: {
  sport: string;
  market_type: string;
  is_premium: boolean;
}): void {
  trackEvent('custom_builder_pick_added', payload);
}

export function trackCustomBuilderPickRemoved(payload: {
  sport: string;
  market_type: string;
  is_premium: boolean;
}): void {
  trackEvent('custom_builder_pick_removed', payload);
}

export function trackCustomBuilderAnalyzeClicked(payload: {
  sport: string;
  pick_count: number;
  has_player_props: boolean;
  is_premium: boolean;
}): void {
  trackEvent('custom_builder_analyze_clicked', payload);
}

export function trackCustomBuilderAnalyzeSuccess(payload: {
  sport: string;
  pick_count: number;
  has_player_props: boolean;
  is_premium: boolean;
  verification_created: boolean;
}): void {
  trackEvent('custom_builder_analyze_success', payload);
}

export function trackCustomBuilderAnalyzeFail(payload: {
  sport: string;
  pick_count: number;
  is_premium: boolean;
  reason: 'paywall' | 'validation' | 'network' | 'unknown';
  error_code?: string;
}): void {
  trackEvent('custom_builder_analyze_fail', payload);
}

export function trackCustomBuilderSaveClicked(payload: {
  sport: string;
  pick_count: number;
  is_premium: boolean;
}): void {
  trackEvent('custom_builder_save_clicked', payload);
}

export function trackCustomBuilderSaveSuccess(payload: {
  sport: string;
  pick_count: number;
  is_premium: boolean;
}): void {
  trackEvent('custom_builder_save_success', payload);
}

export function trackCustomBuilderSaveFail(payload: {
  sport: string;
  pick_count: number;
  is_premium: boolean;
}): void {
  trackEvent('custom_builder_save_fail', payload);
}

export function trackCustomBuilderPaywallShown(payload: {
  reason: 'weekly_limit' | 'premium_required' | 'credits_needed' | 'unknown';
  tier?: string;
}): void {
  trackEvent('custom_builder_paywall_shown', payload);
}

export function trackCustomBuilderUpgradeClicked(payload: {
  source: 'custom_builder_overlay' | 'custom_builder_modal';
}): void {
  trackEvent('custom_builder_upgrade_clicked', payload);
}

export function trackCustomBuilderClearSlip(payload: { sport: string; pick_count: number }): void {
  trackEvent('custom_builder_clear_slip', payload);
}

export function trackCustomBuilderTemplateClicked(payload: {
  template_id: string;
  sport: string;
  is_premium: boolean;
  credits: number;
}): void {
  trackEvent('custom_builder_template_clicked', payload);
}

export function trackCustomBuilderTemplatePartial(payload: {
  template_id: string;
  found: number;
  needed: number;
}): void {
  trackEvent('custom_builder_template_partial', payload);
}

export function trackCustomBuilderTemplateApplied(payload: {
  template_id: string;
  pick_count: number;
  sport: string;
  is_premium: boolean;
}): void {
  trackEvent('custom_builder_template_applied', payload);
}

export function trackCustomBuilderTemplateFollowthroughShown(): void {
  trackEvent('custom_builder_template_followthrough_shown', {});
}

// --- Custom Builder hedge (Counter Ticket + Coverage Pack) ---

export function trackCustomBuilderCounterGenerateClicked(payload: {
  sport: string
  pick_count: number
  mode: string
  is_premium: boolean
  credits: number
}): void {
  trackEvent('custom_builder_counter_generate_clicked', payload)
}

export function trackCustomBuilderCounterGenerateSuccess(payload: {
  sport: string
  pick_count: number
  mode: string
  is_premium: boolean
  credits: number
  ticket_count?: number
}): void {
  trackEvent('custom_builder_counter_generate_success', payload)
}

export function trackCustomBuilderCounterGenerateFail(payload: {
  sport: string
  pick_count: number
  is_premium: boolean
  reason: string
}): void {
  trackEvent('custom_builder_counter_generate_fail', payload)
}

export function trackCustomBuilderCoverageGenerateClicked(payload: {
  sport: string
  pick_count: number
  is_premium: boolean
  credits: number
}): void {
  trackEvent('custom_builder_coverage_generate_clicked', payload)
}

export function trackCustomBuilderCoverageGenerateSuccess(payload: {
  sport: string
  pick_count: number
  ticket_count: number
  is_premium: boolean
}): void {
  trackEvent('custom_builder_coverage_generate_success', payload)
}

export function trackCustomBuilderCoverageGenerateFail(payload: {
  sport: string
  pick_count: number
  is_premium: boolean
  reason: string
}): void {
  trackEvent('custom_builder_coverage_generate_fail', payload)
}

export function trackCustomBuilderHedgeApplyClicked(payload: {
  sport: string
  pick_count: number
  ticket_label: string
  is_premium: boolean
  credits: number
}): void {
  trackEvent('custom_builder_hedge_apply_clicked', payload)
}
