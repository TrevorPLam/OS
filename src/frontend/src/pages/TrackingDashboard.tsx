import { useEffect, useMemo, useState } from 'react'
import { trackingApi, TrackingSummary } from '../api/tracking'

const formatNumber = (value: number | undefined) => value?.toLocaleString() ?? '0'

export const TrackingDashboard = () => {
  const [summary, setSummary] = useState<TrackingSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let isMounted = true

    const fetchData = async () => {
      try {
        const data = await trackingApi.getSummary()
        if (isMounted) {
          setSummary(data)
        }
      } catch (err) {
        if (isMounted) {
          setError('Unable to load tracking data. Please confirm tracking is enabled.')
        }
      } finally {
        if (isMounted) {
          setLoading(false)
        }
      }
    }

    fetchData()

    return () => {
      isMounted = false
    }
  }, [])

  const recentEvents = useMemo(() => summary?.recent_events ?? [], [summary])
  const topPages = useMemo(() => summary?.top_pages ?? [], [summary])
  const topEvents = useMemo(() => summary?.top_events ?? [], [summary])

  if (loading) {
    return <div>Loading tracking analytics...</div>
  }

  if (error) {
    return <div className="error-banner">{error}</div>
  }

  if (!summary) {
    return <div>No tracking data available yet.</div>
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <div>
          <h1>Site & Event Tracking</h1>
          <p className="text-muted">
            Monitor visitor sessions, page views, and custom events captured by the tracking snippet.
          </p>
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <p className="label">Page Views (30d)</p>
          <h2>{formatNumber(summary.page_views_30d)}</h2>
        </div>
        <div className="stat-card">
          <p className="label">Unique Visitors (30d)</p>
          <h2>{formatNumber(summary.unique_visitors_30d)}</h2>
        </div>
        <div className="stat-card">
          <p className="label">Custom Events (30d)</p>
          <h2>{formatNumber(summary.custom_events_30d)}</h2>
        </div>
      </div>

      <div className="grid two-columns">
        <div className="card">
          <div className="card-header">
            <h3>Top Pages</h3>
            <p className="text-muted">Most visited URLs in the last 30 days</p>
          </div>
          <ul className="list">
            {topPages.length === 0 && <li className="text-muted">No page views yet.</li>}
            {topPages.map((page) => (
              <li key={page.url} className="list-row">
                <div className="list-title">{page.url || 'Unknown URL'}</div>
                <div className="badge">{page.count}</div>
              </li>
            ))}
          </ul>
        </div>

        <div className="card">
          <div className="card-header">
            <h3>Top Events</h3>
            <p className="text-muted">Custom events fired by the tracking snippet</p>
          </div>
          <ul className="list">
            {topEvents.length === 0 && <li className="text-muted">No custom events yet.</li>}
            {topEvents.map((event) => (
              <li key={event.name} className="list-row">
                <div className="list-title">{event.name}</div>
                <div className="badge">{event.count}</div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h3>Recent Activity</h3>
          <p className="text-muted">Latest events with timestamps and context</p>
        </div>
        <div className="table">
          <div className="table-head">
            <div>Event</div>
            <div>Type</div>
            <div>URL</div>
            <div>When</div>
          </div>
          <div className="table-body">
            {recentEvents.length === 0 && <div className="text-muted">No activity yet.</div>}
            {recentEvents.map((event, index) => (
              <div key={`${event.name}-${index}`} className="table-row">
                <div>{event.name}</div>
                <div>
                  <span className="badge badge-muted">{event.event_type}</span>
                </div>
                <div className="text-truncate" title={event.url}>
                  {event.url || '—'}
                </div>
                <div>{new Date(event.occurred_at).toLocaleString()}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TrackingDashboard
