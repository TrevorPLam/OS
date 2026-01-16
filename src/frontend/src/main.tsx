import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import * as Sentry from '@sentry/react'
import App from './App.tsx'
import { TrackingClient, createTrackingClient } from './tracking/client'
import { captureWebVitals } from './tracking/webVitals'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
})

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.MODE,
    tracesSampleRate: Number(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE ?? 0),
  })
}

declare global {
  interface Window {
    consultantProTracking?: TrackingClient
  }
}

const trackingKey = import.meta.env.VITE_TRACKING_KEY
const trackingFirmSlug = import.meta.env.VITE_TRACKING_FIRM_SLUG
const trackingEndpoint = import.meta.env.VITE_TRACKING_ENDPOINT ?? '/api/v1/tracking/collect/'

if (trackingKey && trackingFirmSlug && typeof window !== 'undefined') {
  const tracker = createTrackingClient({
    endpoint: trackingEndpoint,
    firmSlug: trackingFirmSlug,
    trackingKey,
    transport: 'beacon',
  })
  tracker.setConsent('granted')
  tracker.startPageTracking()
  captureWebVitals({ tracker })
  window.consultantProTracking = tracker
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>,
)
