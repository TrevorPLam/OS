import apiClient from './client'

export interface TrackingSummary {
  page_views_30d: number
  unique_visitors_30d: number
  custom_events_30d: number
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

export const trackingApi = {
  async getSummary(): Promise<TrackingSummary> {
    const response = await apiClient.get('/tracking/summary/')
    return response.data
  },
  async getEvents(params?: Record<string, string | number>) {
    const response = await apiClient.get('/tracking/events/', { params })
    return response.data
  },
}
