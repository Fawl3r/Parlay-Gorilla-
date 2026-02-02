/**
 * Event Tracking Helper for Parlay Gorilla Analytics
 * 
 * Provides client-side event tracking that sends to our PostgreSQL backend.
 * No external analytics dependencies - all data stays in our database.
 */

import { api } from './api';

// Session ID persists across page loads but resets on browser close
let sessionId: string | null = null;

/**
 * Get or create a session ID for anonymous tracking
 */
function getSessionId(): string {
  if (sessionId) return sessionId;
  
  // Try to get from sessionStorage
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
  | 'pwa_install_dismissed';

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

