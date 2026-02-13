/**
 * Admin API Client for Parlay Gorilla
 * 
 * Provides typed access to admin endpoints.
 * All requests require admin authentication.
 */

import { api } from './api';
import type { SafetySnapshotResponse } from './api/types/system';

// ==========================================
// Types
// ==========================================

export interface TimeRange {
  start: string;
  end: string;
}

export interface OverviewMetrics {
  total_users: number;
  dau: number;
  total_parlays: number;
  model_accuracy: number | null;
  total_revenue: number;
  api_health: {
    total_logs: number;
    errors: number;
    error_rate: number;
    status: 'healthy' | 'degraded';
  };
  period: TimeRange;
  time_range: string;
}

export interface UserMetrics {
  total_users: number;
  new_users: number;
  dau: number;
  wau: number;
  mau: number;
  users_by_plan: Record<string, number>;
  users_by_role: Record<string, number>;
  active_vs_inactive: { active: number; inactive: number };
  signups_over_time: Array<{ date: string; count: number }>;
  time_range: string;
}

export interface TemplateMetrics {
  time_range: string;
  clicks_by_template: Record<string, number>;
  applied_by_template: Record<string, number>;
  partial_by_template: Record<string, number>;
  partial_rate_by_template: Record<string, number>;
  period: { start: string; end: string };
}

export interface UsageMetrics {
  analysis_views: number;
  parlay_sessions: number;
  upset_finder_usage: number;
  parlays_by_type: Record<string, number>;
  parlays_by_sport: Record<string, number>;
  avg_legs: { avg: number; min: number; max: number };
  feature_usage: Record<string, number>;
  time_range: string;
}

export interface RevenueMetrics {
  total_revenue: number;
  revenue_by_plan: Record<string, number>;
  active_subscriptions: number;
  new_subscriptions: number;
  churned_subscriptions: number;
  conversion_rate: number;
  revenue_over_time: Array<{ date: string; amount: number }>;
  recent_payments: PaymentRecord[];
  time_range: string;
}

export interface PaymentRecord {
  id: string;
  user_id: string;
  amount: number;
  currency: string;
  plan: string;
  provider: string;
  status: string;
  created_at: string;
  paid_at?: string;
}

export interface User {
  id: string;
  email: string;
  username?: string;
  role: 'user' | 'mod' | 'admin';
  plan: 'free' | 'standard' | 'elite';
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface UsersListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface UserUpdateData {
  role?: string;
  plan?: string;
  is_active?: boolean;
}

export interface FeatureFlag {
  id: string;
  key: string;
  name?: string;
  description?: string;
  enabled: boolean;
  category?: string;
  targeting_rules?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface TrafficMetrics {
  unique_sessions: number;
  top_pages: Array<{ page: string; views: number }>;
  referrer_breakdown: Record<string, number>;
  event_counts: Record<string, number>;
}

export interface AffiliateStats {
  clicks: number;
  referrals: number;
  conversion_rate: number;
  revenue: number;
  commission_earned: number;
  commission_paid: number;
  pending_commission: number;
}

export interface AffiliateListItem {
  id: string;
  user_id: string;
  email: string | null;
  username?: string | null;
  referral_code: string;
  lemonsqueezy_affiliate_code?: string | null;
  tier: string;
  created_at: string | null;
  is_active: boolean;
  stats: AffiliateStats;
}

export interface AffiliateListResponse {
  total: number;
  page: number;
  page_size: number;
  time_range: string;
  start: string;
  end: string;
  items: AffiliateListItem[];
}

export interface LogEntry {
  id: string;
  source: string;
  level: string;
  message: string;
  metadata?: Record<string, unknown>;
  error_type?: string;
  request_id?: string;
  created_at: string;
}

export interface LogStats {
  total: number;
  by_source: Record<string, number>;
  by_level: Record<string, number>;
  error_rate: number;
}

// ==========================================
// Admin API Client
// ==========================================

export const adminApi = {
  // ==========================================
  // Safety Mode (admin dashboard)
  // ==========================================

  async getSafetySnapshot(): Promise<SafetySnapshotResponse> {
    const { data } = await api.get<SafetySnapshotResponse>('/api/admin/safety');
    return data;
  },

  // ==========================================
  // Metrics
  // ==========================================
  
  async getOverviewMetrics(timeRange: string = '7d'): Promise<OverviewMetrics> {
    const { data } = await api.get(`/api/admin/metrics/overview?time_range=${timeRange}`);
    return data;
  },

  async getUserMetrics(timeRange: string = '30d'): Promise<UserMetrics> {
    const { data } = await api.get(`/api/admin/metrics/users?time_range=${timeRange}`);
    return data;
  },

  async getUsageMetrics(timeRange: string = '30d'): Promise<UsageMetrics> {
    const { data } = await api.get(`/api/admin/metrics/usage?time_range=${timeRange}`);
    return data;
  },

  async getRevenueMetrics(timeRange: string = '30d'): Promise<RevenueMetrics> {
    const { data } = await api.get(`/api/admin/metrics/revenue?time_range=${timeRange}`);
    return data;
  },

  async getModelPerformance(sport?: string, lookbackDays: number = 30) {
    const params = new URLSearchParams({ lookback_days: String(lookbackDays) });
    if (sport) params.append('sport', sport);
    const { data } = await api.get(`/api/admin/metrics/model-performance?${params}`);
    return data;
  },

  async getTemplateMetrics(timeRange: string = '30d'): Promise<TemplateMetrics> {
    const { data } = await api.get(`/api/admin/metrics/templates?time_range=${timeRange}`);
    return data;
  },

  // ==========================================
  // Affiliates
  // ==========================================

  async getAffiliates(params: {
    timeRange?: string;
    page?: number;
    pageSize?: number;
    search?: string;
    sort?: string;
  } = {}): Promise<AffiliateListResponse> {
    const query = new URLSearchParams();
    if (params.timeRange) query.append('time_range', params.timeRange);
    if (params.page) query.append('page', String(params.page));
    if (params.pageSize) query.append('page_size', String(params.pageSize));
    if (params.search) query.append('search', params.search);
    if (params.sort) query.append('sort', params.sort);
    const suffix = query.toString() ? `?${query.toString()}` : '';
    const { data } = await api.get(`/api/admin/affiliates${suffix}`);
    return data;
  },

  async updateAffiliateLemonSqueezyAffiliateCode(
    affiliateId: string,
    lemonsqueezyAffiliateCode: string | null
  ): Promise<{ success: boolean; affiliate_id: string; lemonsqueezy_affiliate_code: string | null }> {
    const { data } = await api.patch(`/api/admin/affiliates/${affiliateId}/lemonsqueezy-affiliate-code`, {
      lemonsqueezy_affiliate_code: lemonsqueezyAffiliateCode,
    });
    return data;
  },

  // ==========================================
  // Users
  // ==========================================

  async getUsers(params: {
    page?: number;
    pageSize?: number;
    search?: string;
    role?: string;
    plan?: string;
    isActive?: boolean;
  } = {}): Promise<UsersListResponse> {
    const queryParams = new URLSearchParams();
    if (params.page) queryParams.append('page', String(params.page));
    if (params.pageSize) queryParams.append('page_size', String(params.pageSize));
    if (params.search) queryParams.append('search', params.search);
    if (params.role) queryParams.append('role', params.role);
    if (params.plan) queryParams.append('plan', params.plan);
    if (params.isActive !== undefined) queryParams.append('is_active', String(params.isActive));
    
    const { data } = await api.get(`/api/admin/users?${queryParams}`);
    return data;
  },

  async getUser(userId: string): Promise<User> {
    const { data } = await api.get(`/api/admin/users/${userId}`);
    return data;
  },

  async updateUser(userId: string, updateData: UserUpdateData): Promise<User> {
    const { data } = await api.patch(`/api/admin/users/${userId}`, updateData);
    return data;
  },

  // ==========================================
  // Feature Flags
  // ==========================================

  async getFeatureFlags(): Promise<FeatureFlag[]> {
    const { data } = await api.get('/api/admin/feature-flags');
    return data;
  },

  async getFeatureFlag(key: string): Promise<FeatureFlag> {
    const { data } = await api.get(`/api/admin/feature-flags/${key}`);
    return data;
  },

  async createFeatureFlag(flag: Partial<FeatureFlag>): Promise<FeatureFlag> {
    const { data } = await api.post('/api/admin/feature-flags', flag);
    return data;
  },

  async updateFeatureFlag(key: string, updates: Partial<FeatureFlag>): Promise<FeatureFlag> {
    const { data } = await api.patch(`/api/admin/feature-flags/${key}`, updates);
    return data;
  },

  async toggleFeatureFlag(key: string): Promise<FeatureFlag> {
    const { data } = await api.post(`/api/admin/feature-flags/${key}/toggle`);
    return data;
  },

  async deleteFeatureFlag(key: string): Promise<void> {
    await api.delete(`/api/admin/feature-flags/${key}`);
  },

  // ==========================================
  // Events & Traffic
  // ==========================================

  async getEvents(params: {
    eventType?: string;
    userId?: string;
    limit?: number;
    offset?: number;
  } = {}) {
    const queryParams = new URLSearchParams();
    if (params.eventType) queryParams.append('event_type', params.eventType);
    if (params.userId) queryParams.append('user_id', params.userId);
    if (params.limit) queryParams.append('limit', String(params.limit));
    if (params.offset) queryParams.append('offset', String(params.offset));
    
    const { data } = await api.get(`/api/admin/events?${queryParams}`);
    return data;
  },

  async getEventCounts(timeRange: string = '7d'): Promise<{ counts: Record<string, number> }> {
    const { data } = await api.get(`/api/admin/events/counts?time_range=${timeRange}`);
    return data;
  },

  async getTrafficMetrics(timeRange: string = '7d'): Promise<TrafficMetrics> {
    const { data } = await api.get(`/api/admin/events/traffic?time_range=${timeRange}`);
    return data;
  },

  // ==========================================
  // Payments
  // ==========================================

  async getPayments(params: {
    status?: string;
    provider?: string;
    timeRange?: string;
    limit?: number;
  } = {}): Promise<PaymentRecord[]> {
    const queryParams = new URLSearchParams();
    if (params.status) queryParams.append('status_filter', params.status);
    if (params.provider) queryParams.append('provider', params.provider);
    if (params.timeRange) queryParams.append('time_range', params.timeRange);
    if (params.limit) queryParams.append('limit', String(params.limit));
    
    const { data } = await api.get(`/api/admin/payments?${queryParams}`);
    return data;
  },

  async getPaymentStats(timeRange: string = '30d') {
    const { data } = await api.get(`/api/admin/payments/stats?time_range=${timeRange}`);
    return data;
  },

  async manualUpgrade(userId: string, plan: string, durationDays: number = 30, isLifetime: boolean = false) {
    const { data } = await api.post('/api/admin/payments/manual-upgrade', {
      user_id: userId,
      plan,
      duration_days: isLifetime ? 0 : durationDays,
      is_lifetime: isLifetime,
    });
    return data;
  },

  // ==========================================
  // Logs
  // ==========================================

  async getLogs(params: {
    source?: string;
    level?: string;
    search?: string;
    timeRange?: string;
    limit?: number;
  } = {}): Promise<LogEntry[]> {
    const queryParams = new URLSearchParams();
    if (params.source) queryParams.append('source', params.source);
    if (params.level) queryParams.append('level', params.level);
    if (params.search) queryParams.append('search', params.search);
    if (params.timeRange) queryParams.append('time_range', params.timeRange);
    if (params.limit) queryParams.append('limit', String(params.limit));
    
    const { data } = await api.get(`/api/admin/logs?${queryParams}`);
    return data;
  },

  async getLogStats(timeRange: string = '24h'): Promise<LogStats> {
    const { data } = await api.get(`/api/admin/logs/stats?time_range=${timeRange}`);
    return data;
  },

  async getLogSources(): Promise<string[]> {
    const { data } = await api.get('/api/admin/logs/sources');
    return data;
  },

  // ==========================================
  // Model
  // ==========================================

  async getModelMetrics(params: {
    sport?: string;
    marketType?: string;
    lookbackDays?: number;
    modelVersion?: string;
  } = {}) {
    const queryParams = new URLSearchParams();
    if (params.sport) queryParams.append('sport', params.sport);
    if (params.marketType) queryParams.append('market_type', params.marketType);
    if (params.lookbackDays) queryParams.append('lookback_days', String(params.lookbackDays));
    if (params.modelVersion) queryParams.append('model_version', params.modelVersion);
    
    const { data } = await api.get(`/api/admin/model/metrics?${queryParams}`);
    return data;
  },

  async getTeamBiases(sport: string) {
    const { data } = await api.get(`/api/admin/model/team-biases?sport=${sport}`);
    return data;
  },

  async triggerRecalibration(sport: string) {
    const { data } = await api.post(`/api/admin/model/recalibrate?sport=${sport}`);
    return data;
  },

  async getModelConfig() {
    const { data } = await api.get('/api/admin/model/config');
    return data;
  },

  async getSportsBreakdown(lookbackDays: number = 30) {
    const { data } = await api.get(`/api/admin/model/sports-breakdown?lookback_days=${lookbackDays}`);
    return data;
  },

  async getMarketBreakdown(sport?: string, lookbackDays: number = 30) {
    const params = new URLSearchParams({ lookback_days: String(lookbackDays) });
    if (sport) params.append('sport', sport);
    const { data } = await api.get(`/api/admin/model/market-breakdown?${params}`);
    return data;
  },
};

export default adminApi;

