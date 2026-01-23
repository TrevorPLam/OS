import { Metric, onCLS, onFCP, onFID, onINP, onLCP, onTTFB } from 'web-vitals'
import { TrackingClient } from './client'

// Commentary:
// - Functionality: Capture Core Web Vitals in the browser and ship them as tracking events.
// - Mapping: Each metric becomes a `web_vital` custom event with structured properties.
// - Reasoning: Keeping the payload consistent allows backend percentile aggregation and alerting.

const WEB_VITAL_EVENT_NAME = 'web_vital'

const WEB_VITAL_UNITS: Record<string, 'ms' | 'score'> = {
  CLS: 'score',
  FCP: 'ms',
  FID: 'ms',
  INP: 'ms',
  LCP: 'ms',
  TTFB: 'ms',
  TTI: 'ms',
}

type WebVitalSource = 'web-vitals' | 'tti-estimate'

export interface WebVitalPayload {
  metric: string
  value: number
  delta: number
  rating: string
  id: string
  navigation_type?: string
  unit: 'ms' | 'score'
  source: WebVitalSource
}

export interface CaptureWebVitalsOptions {
  tracker?: TrackingClient
  onReport?: (payload: WebVitalPayload) => void
  eventName?: string
}

const buildPayload = (metric: Metric, source: WebVitalSource): WebVitalPayload => {
  const navigationType = (metric as Metric & { navigationType?: string }).navigationType

  return {
    metric: metric.name,
    value: metric.value,
    delta: metric.delta,
    rating: metric.rating,
    id: metric.id,
    navigation_type: navigationType,
    unit: WEB_VITAL_UNITS[metric.name] ?? 'ms',
    source,
  }
}

const reportMetric = (
  metric: Metric,
  source: WebVitalSource,
  tracker: TrackingClient | undefined,
  eventName: string,
  onReport?: (payload: WebVitalPayload) => void
) => {
  const payload = buildPayload(metric, source)

  // Commentary: We normalize every web-vitals callback into a single tracking event name
  // so the backend can aggregate percentiles by `properties.metric` without additional
  // ingestion routes.
  tracker?.trackEvent(eventName, payload)
  onReport?.(payload)
}

const estimateTTI = (): number | undefined => {
  const navigationEntries = performance.getEntriesByType('navigation') as PerformanceNavigationTiming[]
  if (navigationEntries.length > 0) {
    return navigationEntries[0].domInteractive
  }

  const legacyTiming = performance.timing
  if (legacyTiming) {
    return legacyTiming.domInteractive - legacyTiming.navigationStart
  }

  return undefined
}

export const captureWebVitals = ({ tracker, onReport, eventName = WEB_VITAL_EVENT_NAME }: CaptureWebVitalsOptions = {}) => {
  if (typeof window === 'undefined') {
    return
  }

  const handler = (metric: Metric) => reportMetric(metric, 'web-vitals', tracker, eventName, onReport)

  onCLS(handler)
  onFCP(handler)
  onFID(handler)
  onINP(handler)
  onLCP(handler)
  onTTFB(handler)

  const reportTTI = () => {
    const tti = estimateTTI()
    if (typeof tti !== 'number') {
      return
    }

    reportMetric(
      {
        name: 'TTI',
        value: tti,
        delta: 0,
        rating: 'unknown',
        id: `tti-${Date.now()}`,
        entries: [],
      },
      'tti-estimate',
      tracker,
      eventName,
      onReport
    )
  }

  if (document.readyState === 'complete') {
    reportTTI()
  } else {
    window.addEventListener('load', reportTTI, { once: true })
  }
}
