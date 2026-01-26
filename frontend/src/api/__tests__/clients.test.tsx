import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useClients,
  useClient,
  useCreateClient,
  useUpdateClient,
  useDeleteClient,
  usePortalUsers,
  useCreatePortalUser,
  useUpdatePortalUser,
  useDeletePortalUser,
  useClientNotes,
  useCreateClientNote,
  useUpdateClientNote,
  useDeleteClientNote,
  useClientEngagements,
  useClientEngagement,
} from '../clients'
import apiClient from '../client'
import type { ReactNode } from 'react'

vi.mock('../client')

const createQueryWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('Clients API - Clients', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useClients fetches all clients', async () => {
    const mockClients = [
      {
        id: 1,
        company_name: 'Acme Corp',
        primary_contact_name: 'John Doe',
        primary_contact_email: 'john@acme.com',
        assigned_team: [1, 2],
        client_since: '2024-01-01',
        status: 'active',
        portal_enabled: true,
        total_lifetime_value: '500000',
        active_projects_count: 3,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockClients })

    const { result } = renderHook(() => useClients(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockClients)
    expect(apiClient.get).toHaveBeenCalledWith('/clients/clients/')
  })

  it('useClients handles paginated results', async () => {
    const mockClients = [
      {
        id: 1,
        company_name: 'Acme Corp',
        primary_contact_name: 'John Doe',
        primary_contact_email: 'john@acme.com',
        assigned_team: [],
        client_since: '2024-01-01',
        status: 'active',
        portal_enabled: false,
        total_lifetime_value: '0',
        active_projects_count: 0,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: { results: mockClients } })

    const { result } = renderHook(() => useClients(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockClients)
  })

  it('useClient fetches single client', async () => {
    const mockClient = {
      id: 1,
      company_name: 'Acme Corp',
      industry: 'Technology',
      primary_contact_name: 'John Doe',
      primary_contact_email: 'john@acme.com',
      website: 'https://acme.com',
      assigned_team: [1, 2],
      client_since: '2024-01-01',
      status: 'active',
      portal_enabled: true,
      total_lifetime_value: '500000',
      active_projects_count: 3,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockClient })

    const { result } = renderHook(() => useClient(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockClient)
    expect(apiClient.get).toHaveBeenCalledWith('/clients/clients/1/')
  })

  it('useCreateClient creates a new client', async () => {
    const newClient = {
      company_name: 'New Corp',
      primary_contact_name: 'Jane Smith',
      primary_contact_email: 'jane@newcorp.com',
      assigned_team: [1],
      client_since: '2024-01-15',
      status: 'active',
      portal_enabled: false,
    }
    const createdClient = {
      ...newClient,
      id: 2,
      total_lifetime_value: '0',
      active_projects_count: 0,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdClient })

    const { result } = renderHook(() => useCreateClient(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newClient)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdClient)
    expect(apiClient.post).toHaveBeenCalledWith('/clients/clients/', newClient)
  })

  it('useUpdateClient updates a client', async () => {
    const updatedClient = {
      id: 1,
      company_name: 'Acme Corp',
      primary_contact_name: 'John Doe',
      primary_contact_email: 'john@acme.com',
      assigned_team: [1, 2, 3],
      client_since: '2024-01-01',
      status: 'active',
      portal_enabled: true,
      total_lifetime_value: '600000',
      active_projects_count: 4,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedClient })

    const { result } = renderHook(() => useUpdateClient(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { assigned_team: [1, 2, 3], portal_enabled: true } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedClient)
    expect(apiClient.put).toHaveBeenCalledWith('/clients/clients/1/', { assigned_team: [1, 2, 3], portal_enabled: true })
  })

  it('useDeleteClient deletes a client', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeleteClient(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/clients/clients/1/')
  })
})

describe('Clients API - Portal Users', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('usePortalUsers fetches portal users for a client', async () => {
    const mockPortalUsers = [
      {
        id: 1,
        client: 1,
        user: 10,
        role: 'admin',
        is_primary_contact: true,
        can_view_financials: true,
        can_upload_documents: true,
        can_approve_deliverables: true,
        created_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockPortalUsers })

    const { result } = renderHook(() => usePortalUsers(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockPortalUsers)
    expect(apiClient.get).toHaveBeenCalledWith('/clients/portal-users/?client=1')
  })

  it('useCreatePortalUser creates a new portal user', async () => {
    const newPortalUser = {
      client: 1,
      user: 11,
      role: 'viewer',
      is_primary_contact: false,
      can_view_financials: false,
      can_upload_documents: false,
      can_approve_deliverables: false,
    }
    const createdPortalUser = {
      ...newPortalUser,
      id: 2,
      created_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdPortalUser })

    const { result } = renderHook(() => useCreatePortalUser(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newPortalUser)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdPortalUser)
    expect(apiClient.post).toHaveBeenCalledWith('/clients/portal-users/', newPortalUser)
  })

  it('useUpdatePortalUser updates a portal user', async () => {
    const updatedPortalUser = {
      id: 1,
      client: 1,
      user: 10,
      role: 'admin',
      is_primary_contact: true,
      can_view_financials: true,
      can_upload_documents: true,
      can_approve_deliverables: true,
      created_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedPortalUser })

    const { result } = renderHook(() => useUpdatePortalUser(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { can_approve_deliverables: true } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedPortalUser)
    expect(apiClient.put).toHaveBeenCalledWith('/clients/portal-users/1/', { can_approve_deliverables: true })
  })

  it('useDeletePortalUser deletes a portal user', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeletePortalUser(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/clients/portal-users/1/')
  })
})

describe('Clients API - Notes', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useClientNotes fetches notes for a client', async () => {
    const mockNotes = [
      {
        id: 1,
        client: 1,
        created_by: 5,
        note: 'Initial consultation went well',
        is_internal: false,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockNotes })

    const { result } = renderHook(() => useClientNotes(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockNotes)
    expect(apiClient.get).toHaveBeenCalledWith('/clients/notes/?client=1')
  })

  it('useCreateClientNote creates a new note', async () => {
    const newNote = {
      client: 1,
      note: 'Follow up meeting scheduled',
      is_internal: true,
    }
    const createdNote = {
      ...newNote,
      id: 2,
      created_by: 5,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdNote })

    const { result } = renderHook(() => useCreateClientNote(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newNote)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdNote)
    expect(apiClient.post).toHaveBeenCalledWith('/clients/notes/', newNote)
  })

  it('useUpdateClientNote updates a note', async () => {
    const updatedNote = {
      id: 1,
      client: 1,
      created_by: 5,
      note: 'Initial consultation went very well - high potential',
      is_internal: false,
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedNote })

    const { result } = renderHook(() => useUpdateClientNote(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { note: 'Initial consultation went very well - high potential' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedNote)
    expect(apiClient.put).toHaveBeenCalledWith('/clients/notes/1/', { note: 'Initial consultation went very well - high potential' })
  })

  it('useDeleteClientNote deletes a note', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeleteClientNote(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/clients/notes/1/')
  })
})

describe('Clients API - Engagements', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useClientEngagements fetches engagements for a client', async () => {
    const mockEngagements = [
      {
        id: 1,
        client: 1,
        contract: 100,
        status: 'active',
        version: 1,
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        contracted_value: '100000',
        actual_revenue: '75000',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockEngagements })

    const { result } = renderHook(() => useClientEngagements(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockEngagements)
    expect(apiClient.get).toHaveBeenCalledWith('/clients/engagements/?client=1')
  })

  it('useClientEngagement fetches single engagement', async () => {
    const mockEngagement = {
      id: 1,
      client: 1,
      contract: 100,
      status: 'active',
      version: 1,
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      contracted_value: '100000',
      actual_revenue: '75000',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockEngagement })

    const { result } = renderHook(() => useClientEngagement(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockEngagement)
    expect(apiClient.get).toHaveBeenCalledWith('/clients/engagements/1/')
  })
})
