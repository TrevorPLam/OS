export type ConsentState = 'pending' | 'granted' | 'denied'

export type TrackingEventType = 'page_view' | 'custom_event' | 'identity'

export interface TrackingClientOptions {
  endpoint: string
  firmSlug: string
  trackingKey: string
  sessionTimeoutMinutes?: number
  debug?: boolean
  transport?: 'fetch' | 'beacon'
}

export interface BaseEventPayload {
  event_type: TrackingEventType
  name: string
  url?: string
  referrer?: string
  properties?: Record<string, unknown>
  occurred_at?: string
  contact_id?: string
  consent_state?: ConsentState
}

export interface TrackingIdentifiers {
  visitor_id: string
  session_id: string
}

export interface TrackingEnvelope extends BaseEventPayload, TrackingIdentifiers {
  firm_slug: string
  tracking_key: string
  user_agent?: string
}
