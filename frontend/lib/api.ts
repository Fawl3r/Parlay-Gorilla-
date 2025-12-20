import { ApiBaseUrlResolver } from './api/internal/ApiBaseUrlResolver'
import { ApiHttpClientsProvider } from './api/internal/ApiHttpClientsProvider'
import { HttpApi } from './api/internal/HttpApi'
import { ApiFacade } from './api/ApiFacade'
import { GamesApi } from './api/services/GamesApi'
import { ParlayApi } from './api/services/ParlayApi'
import { AnalysisApi } from './api/services/AnalysisApi'
import { AuthApi } from './api/services/AuthApi'
import { ProfileApi } from './api/services/ProfileApi'
import { SubscriptionApi } from './api/services/SubscriptionApi'
import { AnalyticsApi } from './api/services/AnalyticsApi'
import { AdminApi } from './api/services/AdminApi'
import { AffiliateApi } from './api/services/AffiliateApi'
import { NotificationsApi } from './api/services/NotificationsApi'

export * from './api/types'

const resolver = new ApiBaseUrlResolver()
const axiosBaseUrl = resolver.resolveAxiosBaseUrl()
const debugBaseUrl = resolver.resolveDebugBaseUrl()

// Expose for mobile debugging. In proxy mode, this will be the frontend origin.
if (typeof window !== 'undefined') {
  ;(window as any).__API_URL = debugBaseUrl
}

const clients = new ApiHttpClientsProvider(axiosBaseUrl).create()

export const api = new ApiFacade(
  new HttpApi(clients.apiClient),
  new GamesApi(clients),
  new ParlayApi(clients),
  new AnalysisApi(clients),
  new AuthApi(clients),
  new ProfileApi(clients),
  new SubscriptionApi(clients),
  new AnalyticsApi(clients),
  new AdminApi(clients),
  new AffiliateApi(clients),
  new NotificationsApi(clients)
)




