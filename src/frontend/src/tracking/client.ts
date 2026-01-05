import {
  BaseEventPayload,
  ConsentState,
  SiteMessageDeliveryRequest,
  SiteMessageManifestResponse,
  TrackingClientOptions,
  TrackingEnvelope,
  TrackingIdentifiers,
} from './types'

const VISITOR_KEY = 'cp_track_id'
const SESSION_KEY = 'cp_session_id'
const SESSION_LAST_SEEN_KEY = 'cp_session_last_seen'
const SESSION_TIMEOUT_MINUTES_DEFAULT = 30
const SITE_MESSAGE_CACHE_TTL_DEFAULT = 5 * 60 * 1000

const generateId = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

const nowIso = () => new Date().toISOString()

const persist = (key: string, value: string) => {
  try {
    localStorage.setItem(key, value)
  } catch {
    // ignore storage failures (private mode, disabled storage)
  }
}

const read = (key: string) => {
  try {
    return localStorage.getItem(key) || undefined
  } catch {
    return undefined
  }
}

const hashPayload = (payload: object) => {
  const raw = JSON.stringify(payload)
  let hash = 0
  for (let i = 0; i < raw.length; i += 1) {
    hash = (hash << 5) - hash + raw.charCodeAt(i)
    hash |= 0
  }
  return Math.abs(hash).toString(16)
}

export class TrackingClient {
  private options: Required<Omit<TrackingClientOptions, 'transport'>> & { transport: 'fetch' | 'beacon' }
  private queue: TrackingEnvelope[] = []
  private consent: ConsentState = 'pending'
  private identifiers: TrackingIdentifiers
  private flushTimer: number | null = null

  constructor(options: TrackingClientOptions) {
    this.options = {
      sessionTimeoutMinutes: options.sessionTimeoutMinutes ?? SESSION_TIMEOUT_MINUTES_DEFAULT,
      debug: options.debug ?? false,
      transport: options.transport ?? 'fetch',
      endpoint: options.endpoint,
      siteMessageEndpoint: options.siteMessageEndpoint ?? '/api/v1/tracking/site-messages/display/',
      siteMessageManifestEndpoint: options.siteMessageManifestEndpoint ?? '/api/v1/tracking/site-messages/manifest/',
      firmSlug: options.firmSlug,
      trackingKey: options.trackingKey,
      trackingKeyId: options.trackingKeyId ?? '',
      configVersion: options.configVersion ?? 1,
      siteMessageCacheTtlMs: options.siteMessageCacheTtlMs ?? SITE_MESSAGE_CACHE_TTL_DEFAULT,
    }
    this.identifiers = this.ensureIdentifiers()
  }

  /**
   * Update consent state. `granted` will flush any queued events.
   */
  setConsent(state: ConsentState) {
    this.consent = state
    if (this.options.debug) {
      // eslint-disable-next-line no-console
      console.debug('[tracking] consent updated', state)
    }
    if (state === 'granted') {
      this.flush()
    } else if (state === 'denied') {
      this.queue = []
    }
  }

  identify(contactId: string) {
    this.enqueue({
      event_type: 'identity',
      name: 'identify',
      contact_id: contactId,
    })
  }

  trackPageView(data?: Partial<BaseEventPayload>) {
    const payload: BaseEventPayload = {
      event_type: 'page_view',
      name: data?.name || document.title || 'page_view',
      url: data?.url || window.location.href,
      referrer: data?.referrer || document.referrer || undefined,
      properties: data?.properties,
      occurred_at: data?.occurred_at || nowIso(),
    }
    this.enqueue(payload)
  }

  trackEvent(name: string, properties?: Record<string, unknown>) {
    const payload: BaseEventPayload = {
      event_type: 'custom_event',
      name,
      properties,
      url: window.location.href,
      referrer: document.referrer || undefined,
      occurred_at: nowIso(),
    }
    this.enqueue(payload)
  }

  startPageTracking() {
    this.trackPageView()
    window.addEventListener('popstate', () => this.trackPageView())
    const origPush = history.pushState
    history.pushState = (...args: Parameters<History['pushState']>) => {
      const result = origPush.apply(history, args)
      this.trackPageView()
      return result
    }
  }

  private ensureIdentifiers(): TrackingIdentifiers {
    const storedVisitor = read(VISITOR_KEY)
    const storedSession = read(SESSION_KEY)
    const lastSeenRaw = read(SESSION_LAST_SEEN_KEY)
    const lastSeen = lastSeenRaw ? new Date(lastSeenRaw) : undefined
    const timeoutMs = this.options.sessionTimeoutMinutes * 60 * 1000
    const now = new Date()
    const sessionExpired = !lastSeen || now.getTime() - lastSeen.getTime() > timeoutMs

    const visitor_id = storedVisitor || generateId()
    const session_id = storedSession && !sessionExpired ? storedSession : generateId()

    persist(VISITOR_KEY, visitor_id)
    persist(SESSION_KEY, session_id)
    persist(SESSION_LAST_SEEN_KEY, nowIso())

    return { visitor_id, session_id }
  }

  private enqueue(event: BaseEventPayload) {
    if (this.consent === 'denied') {
      return
    }

    this.identifiers = this.ensureIdentifiers()
    const envelope: TrackingEnvelope = {
      ...event,
      firm_slug: this.options.firmSlug,
      tracking_key: this.options.trackingKey,
      consent_state: this.consent,
      visitor_id: this.identifiers.visitor_id,
      session_id: this.identifiers.session_id,
      occurred_at: event.occurred_at || nowIso(),
      user_agent: navigator.userAgent,
    }

    if (this.consent === 'pending') {
      this.queue.push(envelope)
      return
    }

    this.queue.push(envelope)
    if (this.queue.length >= 10) {
      this.flush()
    } else if (!this.flushTimer) {
      this.flushTimer = window.setTimeout(() => this.flush(), 1500)
    }
  }

  async flush() {
    if (!this.queue.length) return
    const batch = [...this.queue]
    this.queue = []
    if (this.flushTimer) {
      clearTimeout(this.flushTimer)
      this.flushTimer = null
    }

    try {
      if (this.options.transport === 'beacon' && navigator.sendBeacon) {
        const success = navigator.sendBeacon(this.options.endpoint, JSON.stringify({ events: batch }))
        if (success) {
          return
        }
        // fall through to fetch if beacon fails
      }

      const response = await fetch(this.options.endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ events: batch }),
        keepalive: true,
      })

      if (!response.ok && this.options.debug) {
        // eslint-disable-next-line no-console
        console.error('[tracking] failed to send batch', response.statusText)
      }
    } catch (error) {
      if (this.options.debug) {
        // eslint-disable-next-line no-console
        console.error('[tracking] transport error', error)
      }
      this.queue.unshift(...batch.slice(0, 50))
    }
  }

  async fetchSiteMessages(payload: SiteMessageDeliveryRequest) {
    const requestPayload = {
      firm_slug: this.options.firmSlug,
      visitor_id: payload.visitor_id,
      session_id: payload.session_id,
      contact_id: payload.contact_id,
      url: payload.url,
      segments: payload.segments,
      behaviors: payload.behaviors,
      message_types: payload.message_types,
      limit: payload.limit,
      page_view_count: payload.page_view_count,
      session_count: payload.session_count,
      recent_events: payload.recent_events,
      consent_state: payload.consent_state,
    }

    const cacheKey = this.cacheKey(requestPayload)
    const cached = this.readCache(cacheKey)

    const manifest = await this.fetchManifest()
    if (cached && manifest && cached.manifestSignature === manifest.signature && !this.isCacheExpired(cached)) {
      return cached.messages
    }

    try {
      const response = await fetch(this.options.siteMessageEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestPayload),
      })
      if (!response.ok) {
        throw new Error(`Site message fetch failed: ${response.status}`)
      }
      const data = await response.json()
      const messages = data.messages ?? []
      this.writeCache(cacheKey, {
        manifestSignature: manifest?.signature ?? '',
        messages,
        storedAt: Date.now(),
      })
      return messages
    } catch (error) {
      if (this.options.debug) {
        // eslint-disable-next-line no-console
        console.error('[tracking] site message fetch failed', error)
      }
      if (cached && !this.isCacheExpired(cached)) {
        return cached.messages
      }
      return []
    }
  }

  private async fetchManifest(): Promise<SiteMessageManifestResponse | null> {
    try {
      const response = await fetch(this.options.siteMessageManifestEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          firm_slug: this.options.firmSlug,
          tracking_key: this.options.trackingKey,
          tracking_key_id: this.options.trackingKeyId || undefined,
        }),
      })
      if (!response.ok) {
        throw new Error(`Manifest fetch failed: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
      if (this.options.debug) {
        // eslint-disable-next-line no-console
        console.error('[tracking] manifest fetch failed', error)
      }
      return null
    }
  }

  private cacheKey(requestPayload: Record<string, unknown>) {
    return `cp_site_messages:${this.options.firmSlug}:${this.options.configVersion}:${hashPayload(requestPayload)}`
  }

  private readCache(cacheKey: string) {
    try {
      const raw = localStorage.getItem(cacheKey)
      if (!raw) return null
      return JSON.parse(raw) as {
        manifestSignature: string
        messages: unknown[]
        storedAt: number
      }
    } catch {
      return null
    }
  }

  private writeCache(
    cacheKey: string,
    payload: { manifestSignature: string; messages: unknown[]; storedAt: number }
  ) {
    try {
      localStorage.setItem(cacheKey, JSON.stringify(payload))
    } catch {
      // ignore storage failures
    }
  }

  private isCacheExpired(cacheEntry: { storedAt: number }) {
    return Date.now() - cacheEntry.storedAt > this.options.siteMessageCacheTtlMs
  }
}

export const createTrackingClient = (options: TrackingClientOptions) => new TrackingClient(options)
