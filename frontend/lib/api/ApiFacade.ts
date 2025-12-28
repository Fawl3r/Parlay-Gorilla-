import type {
  CustomParlayAnalysisResponse,
  CustomParlayLeg,
  CounterParlayRequest,
  CounterParlayResponse,
  ParlayCoverageRequest,
  ParlayCoverageResponse,
  GameAnalysisListItem,
  GameAnalysisResponse,
  GameResponse,
  NFLWeeksResponse,
  ParlayRequest,
  ParlayResponse,
  SaveAiParlayRequest,
  SaveCustomParlayRequest,
  SavedParlayResponse,
  TripleParlayRequest,
  TripleParlayResponse,
  UpsetFinderResponse,
  UpsetRiskTier,
  WebPushSubscribeRequest,
  WebPushSubscribeResponse,
  WebPushUnsubscribeResponse,
  WebPushVapidPublicKeyResponse,
} from '@/lib/api/types'
import { HttpApi } from '@/lib/api/internal/HttpApi'
import { GamesApi } from '@/lib/api/services/GamesApi'
import { ParlayApi } from '@/lib/api/services/ParlayApi'
import { AnalysisApi } from '@/lib/api/services/AnalysisApi'
import { AuthApi } from '@/lib/api/services/AuthApi'
import { ProfileApi } from '@/lib/api/services/ProfileApi'
import { SubscriptionApi } from '@/lib/api/services/SubscriptionApi'
import { AnalyticsApi } from '@/lib/api/services/AnalyticsApi'
import { AdminApi } from '@/lib/api/services/AdminApi'
import { AffiliateApi } from '@/lib/api/services/AffiliateApi'
import { NotificationsApi } from '@/lib/api/services/NotificationsApi'

export class ApiFacade {
  constructor(
    private readonly http: HttpApi,
    private readonly gamesApi: GamesApi,
    private readonly parlayApi: ParlayApi,
    private readonly analysisApi: AnalysisApi,
    private readonly authApi: AuthApi,
    private readonly profileApi: ProfileApi,
    private readonly subscriptionApi: SubscriptionApi,
    private readonly analyticsApi: AnalyticsApi,
    private readonly adminApi: AdminApi,
    private readonly affiliateApi: AffiliateApi,
    private readonly notificationsApi: NotificationsApi
  ) {}

  // Games
  getGames(sport: string = 'nfl', week?: number, forceRefresh: boolean = false): Promise<GameResponse[]> {
    return this.gamesApi.getGames(sport, week, forceRefresh)
  }
  warmupCache(): Promise<void> {
    return this.gamesApi.warmupCache()
  }
  getNFLWeeks(): Promise<NFLWeeksResponse> {
    return this.gamesApi.getNFLWeeks()
  }
  getNFLGames(): Promise<GameResponse[]> {
    return this.gamesApi.getNFLGames()
  }
  listSports(): Promise<
    Array<{
      slug: string
      code: string
      display_name: string
      default_markets: string[]
      in_season?: boolean
      status_label?: string
      upcoming_games?: number
    }>
  > {
    return this.gamesApi.listSports()
  }
  healthCheck(): Promise<{ status: string; timestamp: string; service: string }> {
    return this.gamesApi.healthCheck()
  }

  // Parlays
  suggestParlay(request: ParlayRequest): Promise<ParlayResponse> {
    return this.parlayApi.suggestParlay(request)
  }
  suggestTripleParlay(request?: TripleParlayRequest): Promise<TripleParlayResponse> {
    return this.parlayApi.suggestTripleParlay(request)
  }
  analyzeCustomParlay(legs: CustomParlayLeg[]): Promise<CustomParlayAnalysisResponse> {
    return this.parlayApi.analyzeCustomParlay(legs)
  }
  buildCounterParlay(request: CounterParlayRequest): Promise<CounterParlayResponse> {
    return this.parlayApi.buildCounterParlay(request)
  }
  buildCoveragePack(request: ParlayCoverageRequest): Promise<ParlayCoverageResponse> {
    return this.parlayApi.buildCoveragePack(request)
  }
  getUpsets(options: {
    sport: string
    min_edge?: number
    max_results?: number
    risk_tier?: UpsetRiskTier
    week?: number
  }): Promise<UpsetFinderResponse> {
    return this.parlayApi.getUpsets(options)
  }

  // Saved Parlays
  saveCustomParlay(request: SaveCustomParlayRequest): Promise<SavedParlayResponse> {
    return this.parlayApi.saveCustomParlay(request)
  }
  saveAiParlay(request: SaveAiParlayRequest): Promise<SavedParlayResponse> {
    return this.parlayApi.saveAiParlay(request)
  }
  listSavedParlays(type: 'all' | 'custom' | 'ai' = 'all', limit: number = 50): Promise<SavedParlayResponse[]> {
    return this.parlayApi.listSavedParlays(type, limit)
  }
  retryParlayInscription(savedParlayId: string): Promise<SavedParlayResponse> {
    return this.parlayApi.retryParlayInscription(savedParlayId)
  }

  // Analysis
  getAnalysis(sport: string, slug: string, refresh = false): Promise<GameAnalysisResponse> {
    return this.analysisApi.getAnalysis(sport, slug, refresh)
  }
  listUpcomingAnalyses(sport: string, limit: number = 20): Promise<GameAnalysisListItem[]> {
    return this.analysisApi.listUpcomingAnalyses(sport, limit)
  }
  getTeamPhoto(sport: string, teamName: string, opponent?: string): Promise<string | null> {
    return this.analysisApi.getTeamPhoto(sport, teamName, opponent)
  }
  getTeamPhotos(sport: string, teamName: string, opponent?: string): Promise<string[]> {
    return this.analysisApi.getTeamPhotos(sport, teamName, opponent)
  }

  // Auth
  login(email: string, password: string) {
    return this.authApi.login(email, password)
  }
  register(email: string, password: string, username?: string) {
    return this.authApi.register(email, password, username)
  }
  getCurrentUser() {
    return this.authApi.getCurrentUser()
  }
  verifyEmail(token: string) {
    return this.authApi.verifyEmail(token)
  }
  resendVerificationEmail() {
    return this.authApi.resendVerificationEmail()
  }
  forgotPassword(email: string) {
    return this.authApi.forgotPassword(email)
  }
  resetPassword(token: string, password: string) {
    return this.authApi.resetPassword(token, password)
  }
  logout() {
    return this.authApi.logout()
  }

  // Profile
  getMyProfile() {
    return this.profileApi.getMyProfile()
  }
  updateProfile(data: {
    display_name?: string
    avatar_url?: string
    bio?: string
    timezone?: string
    default_risk_profile?: 'conservative' | 'balanced' | 'degen'
    favorite_teams?: string[]
    favorite_sports?: string[]
  }) {
    return this.profileApi.updateProfile(data)
  }
  completeProfileSetup(data: {
    display_name: string
    avatar_url?: string
    bio?: string
    timezone?: string
    default_risk_profile?: 'conservative' | 'balanced' | 'degen'
    favorite_teams?: string[]
    favorite_sports?: string[]
  }) {
    return this.profileApi.completeProfileSetup(data)
  }
  getMyBadges() {
    return this.profileApi.getMyBadges()
  }

  // Subscription
  getMySubscription() {
    return this.subscriptionApi.getMySubscription()
  }
  getSubscriptionHistory(limit: number = 20, offset: number = 0) {
    return this.subscriptionApi.getSubscriptionHistory(limit, offset)
  }
  cancelSubscription() {
    return this.subscriptionApi.cancelSubscription()
  }

  // Analytics
  getAnalyticsPerformance(riskProfile?: string) {
    return this.analyticsApi.getAnalyticsPerformance(riskProfile)
  }
  getMyParlays(limit: number = 50) {
    return this.analyticsApi.getMyParlays(limit)
  }

  // Admin
  adminWalletLogin(walletAddress: string, message: string) {
    return this.adminApi.adminWalletLogin(walletAddress, message)
  }

  // Generic HTTP helpers (used by several pages)
  get(url: string, config?: any) {
    return this.http.get(url, config)
  }
  post(url: string, data?: any, config?: any) {
    return this.http.post(url, data, config)
  }
  patch(url: string, data?: any, config?: any) {
    return this.http.patch(url, data, config)
  }
  delete(url: string, config?: any) {
    return this.http.delete(url, config)
  }

  // Affiliate
  getTaxFormStatus() {
    return this.affiliateApi.getTaxFormStatus()
  }
  submitW9TaxForm(formData: {
    legal_name: string
    business_name?: string
    tax_classification: 'Individual' | 'Partnership' | 'C-Corp' | 'S-Corp' | 'LLC' | 'Other'
    address_street: string
    address_city: string
    address_state: string
    address_zip: string
    address_country?: string
    tax_id_number: string
    tax_id_type: 'ssn' | 'ein'
  }) {
    return this.affiliateApi.submitW9TaxForm(formData)
  }
  submitW8BENTaxForm(formData: {
    legal_name: string
    business_name?: string
    country_of_residence: string
    foreign_tax_id?: string
    address_street: string
    address_city: string
    address_state?: string
    address_zip: string
    address_country: string
  }) {
    return this.affiliateApi.submitW8BENTaxForm(formData)
  }

  // Notifications (Web Push)
  getWebPushVapidPublicKey(): Promise<WebPushVapidPublicKeyResponse> {
    return this.notificationsApi.getWebPushVapidPublicKey()
  }
  subscribeWebPush(payload: WebPushSubscribeRequest): Promise<WebPushSubscribeResponse> {
    return this.notificationsApi.subscribeWebPush(payload)
  }
  unsubscribeWebPush(endpoint: string): Promise<WebPushUnsubscribeResponse> {
    return this.notificationsApi.unsubscribeWebPush(endpoint)
  }
}


