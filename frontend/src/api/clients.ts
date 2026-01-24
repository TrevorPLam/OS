import { useMutation, useQuery, useQueryClient, UseMutationResult, UseQueryResult } from '@tanstack/react-query'
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

const getListResults = <T>(data: { results?: T[] } | T[]): T[] => {
  if (Array.isArray(data)) {
    return data
  }

  return data.results ?? []
}

export const useClients = (): UseQueryResult<Client[], Error> => {
  return useQuery({
    queryKey: ['clients'],
    queryFn: async () => {
      const response = await apiClient.get('/clients/clients/')
      return getListResults<Client>(response.data)
    },
  })
}

export const useClient = (id?: number): UseQueryResult<Client, Error> => {
  return useQuery({
    queryKey: ['clients', id],
    queryFn: async () => {
      const response = await apiClient.get(`/clients/clients/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useCreateClient = (): UseMutationResult<Client, Error, Partial<Client>> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/clients/clients/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
    },
  })
}

export const useUpdateClient = (): UseMutationResult<
  Client,
  Error,
  { id: number; data: Partial<Client> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/clients/clients/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      queryClient.invalidateQueries({ queryKey: ['clients', variables.id] })
    },
  })
}

export const useDeleteClient = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/clients/clients/${id}/`)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['clients'] })
      queryClient.invalidateQueries({ queryKey: ['clients', id] })
    },
  })
}

export const usePortalUsers = (clientId?: number): UseQueryResult<ClientPortalUser[], Error> => {
  return useQuery({
    queryKey: ['portal-users', clientId ?? 'all'],
    queryFn: async () => {
      const url = clientId ? `/clients/portal-users/?client=${clientId}` : '/clients/portal-users/'
      const response = await apiClient.get(url)
      return getListResults<ClientPortalUser>(response.data)
    },
  })
}

export const useCreatePortalUser = (): UseMutationResult<
  ClientPortalUser,
  Error,
  Partial<ClientPortalUser>
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/clients/portal-users/', data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['portal-users'] })
      if (variables.client) {
        queryClient.invalidateQueries({ queryKey: ['portal-users', variables.client] })
      }
    },
  })
}

export const useUpdatePortalUser = (): UseMutationResult<
  ClientPortalUser,
  Error,
  { id: number; data: Partial<ClientPortalUser> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/clients/portal-users/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['portal-users'] })
      if (variables.data.client) {
        queryClient.invalidateQueries({ queryKey: ['portal-users', variables.data.client] })
      }
    },
  })
}

export const useDeletePortalUser = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/clients/portal-users/${id}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['portal-users'] })
    },
  })
}

export const useClientNotes = (clientId: number): UseQueryResult<ClientNote[], Error> => {
  return useQuery({
    queryKey: ['client-notes', clientId],
    queryFn: async () => {
      const response = await apiClient.get(`/clients/notes/?client=${clientId}`)
      return getListResults<ClientNote>(response.data)
    },
    enabled: typeof clientId === 'number',
  })
}

export const useCreateClientNote = (): UseMutationResult<
  ClientNote,
  Error,
  Partial<ClientNote>
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/clients/notes/', data)
      return response.data
    },
    onSuccess: (_, variables) => {
      if (variables.client) {
        queryClient.invalidateQueries({ queryKey: ['client-notes', variables.client] })
      }
    },
  })
}

export const useUpdateClientNote = (): UseMutationResult<
  ClientNote,
  Error,
  { id: number; data: Partial<ClientNote> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/clients/notes/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      if (variables.data.client) {
        queryClient.invalidateQueries({ queryKey: ['client-notes', variables.data.client] })
      }
    },
  })
}

export const useDeleteClientNote = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/clients/notes/${id}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['client-notes'] })
    },
  })
}

export const useClientEngagements = (
  clientId?: number
): UseQueryResult<ClientEngagement[], Error> => {
  return useQuery({
    queryKey: ['client-engagements', clientId ?? 'all'],
    queryFn: async () => {
      const url = clientId ? `/clients/engagements/?client=${clientId}` : '/clients/engagements/'
      const response = await apiClient.get(url)
      return getListResults<ClientEngagement>(response.data)
    },
  })
}

export const useClientEngagement = (id?: number): UseQueryResult<ClientEngagement, Error> => {
  return useQuery({
    queryKey: ['client-engagement', id],
    queryFn: async () => {
      const response = await apiClient.get(`/clients/engagements/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}
