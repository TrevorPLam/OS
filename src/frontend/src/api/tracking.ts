import apiClient from './client'

export interface TrackingSummary {
  page_views_30d: number
  unique_visitors_30d: number
  custom_events_30d: number
  default_key_warning?: boolean
  export_path?: string
  recent_events: Array<{
    name: string
    event_type: string
    url?: string
    referrer?: string
    occurred_at: string
    properties?: Record<string, unknown>
  }>
  top_pages: Array<{ url: string; count: number }>
  top_events: Array<{ name: string; count: number }>
}

export interface SiteMessagePayload {
  id?: number
  name: string
  message_type: 'modal' | 'slide_in' | 'banner'
  status: 'draft' | 'published' | 'archived'
  targeting_rules: Record<string, unknown>
  content: Record<string, unknown>
  personalization_tokens?: string[]
  form_schema?: Record<string, unknown>
  frequency_cap: number
  active_from?: string | null
  active_until?: string | null
}

export interface SiteMessage extends SiteMessagePayload {
  created_at: string
  updated_at: string
  delivery_id?: string
  variant?: string | null
}

export interface SiteMessageAnalyticsEntry {
  site_message_id: number
  site_message_name: string
  variant?: string
  delivered: number
  views: number
  clicks: number
  view_rate: number
  click_rate: number
}

export interface SiteMessageAnalyticsResponse {
  window_days: number
  rollups: SiteMessageAnalyticsEntry[]
  top_messages: SiteMessageAnalyticsEntry[]
  export_path?: string
}

export const trackingApi = {
  async getSummary(): Promise<TrackingSummary> {
    const response = await apiClient.get('/tracking/summary/')
    const data = response.data
    return {
      page_views_30d: data.page_views ?? data.page_views_30d ?? 0,
      unique_visitors_30d: data.unique_visitors ?? data.unique_visitors_30d ?? 0,
      custom_events_30d: data.custom_events ?? data.custom_events_30d ?? 0,
      recent_events: data.recent_events ?? [],
      top_pages: data.top_pages ?? [],
      top_events: data.top_events ?? [],
      default_key_warning: data.default_key_warning,
      export_path: data.export_path,
    }
  },

  async getEvents(params?: Record<string, string | number>) {
    const response = await apiClient.get('/tracking/events/', { params })
    return response.data
  },

  async listSiteMessages(): Promise<SiteMessage[]> {
    const response = await apiClient.get('/tracking/site-messages/')
    return response.data
  },

  async createSiteMessage(payload: SiteMessagePayload): Promise<SiteMessage> {
    const response = await apiClient.post('/tracking/site-messages/', payload)
    return response.data
  },

  async updateSiteMessage(id: number, payload: SiteMessagePayload): Promise<SiteMessage> {
    const response = await apiClient.put(`/tracking/site-messages/${id}/`, payload)
    return response.data
  },

  async evaluateMessages(payload: Record<string, unknown>): Promise<{ messages: SiteMessage[] }> {
    const response = await apiClient.post('/tracking/site-messages/display/', payload)
    return response.data
  },

  async getSiteMessageAnalytics(params?: Record<string, string | number>): Promise<SiteMessageAnalyticsResponse> {
    const response = await apiClient.get('/tracking/site-messages/analytics/', { params })
    return response.data
  },
}
