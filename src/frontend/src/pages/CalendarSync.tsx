import React, { useState, useEffect } from 'react'
import { calendarApi, OAuthConnection } from '../api/calendar'
import './CalendarSync.css'

const CalendarSync: React.FC = () => {
  const [connections, setConnections] = useState<OAuthConnection[]>([])
  const [loading, setLoading] = useState(true)
  const [syncing, setSyncing] = useState<number | null>(null)
  const [editingConnection, setEditingConnection] = useState<number | null>(null)
  const [editData, setEditData] = useState<Partial<OAuthConnection>>({})

  useEffect(() => {
    loadConnections()
  }, [])

  const loadConnections = async () => {
    try {
      const data = await calendarApi.getConnections()
      setConnections(data)
    } catch (error) {
      console.error('Failed to load calendar connections:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleConnectGoogle = async () => {
    try {
      const response = await calendarApi.initiateGoogleOAuth()
      // Redirect to OAuth authorization URL
      window.location.href = response.authorization_url
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to initiate Google OAuth')
    }
  }

  const handleConnectMicrosoft = async () => {
    try {
      const response = await calendarApi.initiateMicrosoftOAuth()
      // Redirect to OAuth authorization URL
      window.location.href = response.authorization_url
    } catch (error: any) {
      alert(error.response?.data?.error || 'Failed to initiate Microsoft OAuth')
    }
  }

  const handleDisconnect = async (connectionId: number) => {
    if (!window.confirm('Are you sure you want to disconnect this calendar?')) {
      return
    }

    try {
      await calendarApi.disconnectCalendar(connectionId)
      loadConnections()
    } catch (error) {
      console.error('Failed to disconnect calendar:', error)
      alert('Failed to disconnect calendar')
    }
  }

  const handleSyncNow = async (connectionId: number) => {
    setSyncing(connectionId)
    try {
      const result = await calendarApi.syncNow(connectionId)
      alert(
        `Sync completed!\nPulled: ${result.pulled} events\nPushed: ${result.pushed} events`
      )
      loadConnections()
    } catch (error: any) {
      alert(error.response?.data?.error || 'Sync failed')
    } finally {
      setSyncing(null)
    }
  }

  const handleEditConnection = (connection: OAuthConnection) => {
    setEditingConnection(connection.connection_id)
    setEditData({
      sync_enabled: connection.sync_enabled,
      sync_window_days: connection.sync_window_days,
    })
  }

  const handleSaveEdit = async (connectionId: number) => {
    try {
      await calendarApi.updateConnection(connectionId, editData)
      setEditingConnection(null)
      loadConnections()
    } catch (error) {
      console.error('Failed to update connection:', error)
      alert('Failed to update connection settings')
    }
  }

  const handleCancelEdit = () => {
    setEditingConnection(null)
    setEditData({})
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'Never'
    return new Date(dateString).toLocaleString()
  }

  const getStatusBadge = (status: string) => {
    const statusClasses: Record<string, string> = {
      active: 'status-active',
      expired: 'status-expired',
      revoked: 'status-revoked',
      error: 'status-error',
    }
    return <span className={`status-badge ${statusClasses[status]}`}>{status.toUpperCase()}</span>
  }

  const getProviderIcon = (provider: string) => {
    const icons: Record<string, string> = {
      google: '📅',
      microsoft: '📆',
      apple: '🍎',
    }
    return icons[provider] || '📅'
  }

  if (loading) {
    return <div className="loading">Loading calendar settings...</div>
  }

  return (
    <div className="calendar-sync-page">
      <div className="page-header">
        <h1>Calendar Sync Settings</h1>
        <p className="page-description">
          Connect your calendars to sync appointments automatically
        </p>
      </div>

      <div className="connect-section">
        <h2>Connect a Calendar</h2>
        <div className="connect-buttons">
          <button onClick={handleConnectGoogle} className="btn-connect btn-google">
            <span className="provider-icon">📅</span>
            Connect Google Calendar
          </button>
          <button onClick={handleConnectMicrosoft} className="btn-connect btn-microsoft">
            <span className="provider-icon">📆</span>
            Connect Microsoft Outlook
          </button>
        </div>
      </div>

      {connections.length > 0 && (
        <div className="connections-section">
          <h2>Connected Calendars</h2>
          <div className="connections-list">
            {connections.map((connection) => (
              <div key={connection.connection_id} className="connection-card">
                <div className="connection-header">
                  <div className="connection-title">
                    <span className="provider-icon-large">
                      {getProviderIcon(connection.provider)}
                    </span>
                    <div>
                      <h3>{connection.provider_email || 'Unknown'}</h3>
                      <p className="connection-provider">
                        {connection.provider === 'google'
                          ? 'Google Calendar'
                          : connection.provider === 'microsoft'
                          ? 'Microsoft Outlook'
                          : 'Apple Calendar'}
                      </p>
                    </div>
                  </div>
                  {getStatusBadge(connection.status)}
                </div>

                <div className="connection-details">
                  <div className="detail-row">
                    <span className="detail-label">Last Sync:</span>
                    <span className="detail-value">{formatDate(connection.last_sync_at)}</span>
                  </div>

                  {editingConnection === connection.connection_id ? (
                    <div className="edit-form">
                      <div className="form-group">
                        <label>
                          <input
                            type="checkbox"
                            checked={editData.sync_enabled}
                            onChange={(e) =>
                              setEditData({ ...editData, sync_enabled: e.target.checked })
                            }
                          />
                          <span>Enable Automatic Sync</span>
                        </label>
                      </div>
                      <div className="form-group">
                        <label>Sync Window (days):</label>
                        <input
                          type="number"
                          min="7"
                          max="365"
                          value={editData.sync_window_days}
                          onChange={(e) =>
                            setEditData({
                              ...editData,
                              sync_window_days: parseInt(e.target.value),
                            })
                          }
                        />
                        <small>Number of days to sync (past and future)</small>
                      </div>
                      <div className="edit-actions">
                        <button
                          onClick={() => handleSaveEdit(connection.connection_id)}
                          className="btn-save"
                        >
                          Save
                        </button>
                        <button onClick={handleCancelEdit} className="btn-cancel">
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      <div className="detail-row">
                        <span className="detail-label">Auto Sync:</span>
                        <span className="detail-value">
                          {connection.sync_enabled ? '✓ Enabled' : '✗ Disabled'}
                        </span>
                      </div>
                      <div className="detail-row">
                        <span className="detail-label">Sync Window:</span>
                        <span className="detail-value">{connection.sync_window_days} days</span>
                      </div>

                      {connection.error_message && (
                        <div className="error-message">
                          <strong>Error:</strong> {connection.error_message}
                        </div>
                      )}
                    </>
                  )}
                </div>

                <div className="connection-actions">
                  {connection.status === 'active' && editingConnection !== connection.connection_id && (
                    <>
                      <button
                        onClick={() => handleSyncNow(connection.connection_id)}
                        className="btn-action btn-sync"
                        disabled={syncing === connection.connection_id}
                      >
                        {syncing === connection.connection_id ? 'Syncing...' : '🔄 Sync Now'}
                      </button>
                      <button
                        onClick={() => handleEditConnection(connection)}
                        className="btn-action btn-edit"
                      >
                        ⚙️ Settings
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => handleDisconnect(connection.connection_id)}
                    className="btn-action btn-disconnect"
                  >
                    Disconnect
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {connections.length === 0 && (
        <div className="empty-state">
          <p>No calendars connected yet. Connect a calendar to start syncing appointments.</p>
        </div>
      )}
    </div>
  )
}

export default CalendarSync
