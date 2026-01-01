import apiClient from './client'

export interface OAuthConnection {
  connection_id: number
  provider: 'google' | 'microsoft' | 'apple'
  provider_email: string
  sync_enabled: boolean
  sync_window_days: number
  last_sync_at: string | null
  status: 'active' | 'expired' | 'revoked' | 'error'
  error_message: string | null
  created_at: string
  updated_at: string
}

export interface OAuthInitiateResponse {
  authorization_url: string
  state: string
  provider: string
}

export interface SyncStatusResponse {
  connection: OAuthConnection
  last_sync_at: string | null
  sync_enabled: boolean
  status: string
  error_message: string | null
  is_token_expired: boolean
  needs_refresh: boolean
}

export interface SyncNowResponse {
  message: string
  pulled: number
  pushed: number
  last_sync_at: string
}

export const calendarApi = {
  // Get all OAuth connections
  getConnections: async (): Promise<OAuthConnection[]> => {
    const response = await apiClient.get('/calendar/oauth-connections/')
    return response.data.results || response.data
  },

  // Initiate Google OAuth flow
  initiateGoogleOAuth: async (): Promise<OAuthInitiateResponse> => {
    const response = await apiClient.post('/calendar/oauth-connections/initiate_google_oauth/')
    return response.data
  },

  // Initiate Microsoft OAuth flow
  initiateMicrosoftOAuth: async (): Promise<OAuthInitiateResponse> => {
    const response = await apiClient.post('/calendar/oauth-connections/initiate_microsoft_oauth/')
    return response.data
  },

  // Handle OAuth callback
  handleOAuthCallback: async (code: string, state: string) => {
    const response = await apiClient.post('/calendar/oauth-connections/oauth_callback/', {
      code,
      state,
    })
    return response.data
  },

  // Disconnect calendar
  disconnectCalendar: async (connectionId: number): Promise<OAuthConnection> => {
    const response = await apiClient.post(`/calendar/oauth-connections/${connectionId}/disconnect/`)
    return response.data.connection
  },

  // Trigger manual sync
  syncNow: async (connectionId: number): Promise<SyncNowResponse> => {
    const response = await apiClient.post(`/calendar/oauth-connections/${connectionId}/sync_now/`)
    return response.data
  },

  // Get sync status
  getSyncStatus: async (connectionId: number): Promise<SyncStatusResponse> => {
    const response = await apiClient.get(`/calendar/oauth-connections/${connectionId}/sync_status/`)
    return response.data
  },

  // Update connection settings
  updateConnection: async (
    connectionId: number,
    data: Partial<OAuthConnection>
  ): Promise<OAuthConnection> => {
    const response = await apiClient.patch(`/calendar/oauth-connections/${connectionId}/`, data)
    return response.data
  },
}
