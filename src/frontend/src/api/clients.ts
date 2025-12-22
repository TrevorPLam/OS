import apiClient from './client'

// Clients Module Interfaces (Post-Sale)

export interface Client {
  id: number
  source_prospect?: number
  source_proposal?: number
  company_name: string
  industry?: string
  primary_contact_name: string
  primary_contact_email: string
  primary_contact_phone?: string
  street_address?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  website?: string
  employee_count?: number
  account_manager?: number
  account_manager_name?: string
  assigned_team: number[]
  client_since: string
  status: string
  portal_enabled: boolean
  total_lifetime_value: string
  active_projects_count: number
  notes?: string
  created_at: string
  updated_at: string
}

export interface ClientPortalUser {
  id: number
  client: number
  client_name?: string
  user: number
  role: string
  is_primary_contact: boolean
  can_view_financials: boolean
  can_upload_documents: boolean
  can_approve_deliverables: boolean
  created_at: string
}

export interface ClientNote {
  id: number
  client: number
  created_by: number
  created_by_name?: string
  note: string
  is_internal: boolean
  created_at: string
  updated_at: string
}

export interface ClientEngagement {
  id: number
  client: number
  client_name?: string
  contract: number
  contract_number?: string
  status: string
  version: number
  parent_engagement?: number
  start_date: string
  end_date: string
  contracted_value: string
  actual_revenue: string
  notes?: string
  created_at: string
  updated_at: string
}

export const clientsApi = {
  // Clients
  getClients: async (): Promise<Client[]> => {
    const response = await apiClient.get('/clients/clients/')
    return response.data.results || response.data
  },

  getClient: async (id: number): Promise<Client> => {
    const response = await apiClient.get(`/clients/clients/${id}/`)
    return response.data
  },

  createClient: async (data: Partial<Client>): Promise<Client> => {
    const response = await apiClient.post('/clients/clients/', data)
    return response.data
  },

  updateClient: async (id: number, data: Partial<Client>): Promise<Client> => {
    const response = await apiClient.put(`/clients/clients/${id}/`, data)
    return response.data
  },

  deleteClient: async (id: number): Promise<void> => {
    await apiClient.delete(`/clients/clients/${id}/`)
  },

  // Portal Users
  getPortalUsers: async (clientId?: number): Promise<ClientPortalUser[]> => {
    const url = clientId ? `/clients/portal-users/?client=${clientId}` : '/clients/portal-users/'
    const response = await apiClient.get(url)
    return response.data.results || response.data
  },

  createPortalUser: async (data: Partial<ClientPortalUser>): Promise<ClientPortalUser> => {
    const response = await apiClient.post('/clients/portal-users/', data)
    return response.data
  },

  updatePortalUser: async (id: number, data: Partial<ClientPortalUser>): Promise<ClientPortalUser> => {
    const response = await apiClient.put(`/clients/portal-users/${id}/`, data)
    return response.data
  },

  deletePortalUser: async (id: number): Promise<void> => {
    await apiClient.delete(`/clients/portal-users/${id}/`)
  },

  // Client Notes
  getNotes: async (clientId: number): Promise<ClientNote[]> => {
    const response = await apiClient.get(`/clients/notes/?client=${clientId}`)
    return response.data.results || response.data
  },

  createNote: async (data: Partial<ClientNote>): Promise<ClientNote> => {
    const response = await apiClient.post('/clients/notes/', data)
    return response.data
  },

  updateNote: async (id: number, data: Partial<ClientNote>): Promise<ClientNote> => {
    const response = await apiClient.put(`/clients/notes/${id}/`, data)
    return response.data
  },

  deleteNote: async (id: number): Promise<void> => {
    await apiClient.delete(`/clients/notes/${id}/`)
  },

  // Client Engagements
  getEngagements: async (clientId?: number): Promise<ClientEngagement[]> => {
    const url = clientId ? `/clients/engagements/?client=${clientId}` : '/clients/engagements/'
    const response = await apiClient.get(url)
    return response.data.results || response.data
  },

  getEngagement: async (id: number): Promise<ClientEngagement> => {
    const response = await apiClient.get(`/clients/engagements/${id}/`)
    return response.data
  },
}
