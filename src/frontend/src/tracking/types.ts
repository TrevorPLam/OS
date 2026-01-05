export type ConsentState = 'pending' | 'granted' | 'denied'

export type TrackingEventType = 'page_view' | 'custom_event' | 'identity'

export interface TrackingClientOptions {
  endpoint: string
  siteMessageEndpoint?: string
  siteMessageManifestEndpoint?: string
  firmSlug: string
  trackingKey: string
  trackingKeyId?: string
  configVersion?: number
  siteMessageCacheTtlMs?: number
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

export interface SiteMessageDeliveryRequest {
  url: string
  visitor_id: string
  session_id?: string
  contact_id?: number
  segments?: string[]
  behaviors?: Record<string, unknown>
  message_types?: Array<'modal' | 'slide_in' | 'banner'>
  limit?: number
  page_view_count?: number
  session_count?: number
  recent_events?: string[]
  consent_state?: ConsentState
}

export interface SiteMessageManifestEntry {
  id: number
  name: string
  message_type: 'modal' | 'slide_in' | 'banner'
  updated_at: string
  active_from?: string | null
  active_until?: string | null
}

export interface SiteMessageManifestResponse {
  manifest: SiteMessageManifestEntry[]
  signature: string
  config_version: number
  generated_at: string
}
