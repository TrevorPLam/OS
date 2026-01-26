import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  useLeads,
  useLead,
  useCreateLead,
  useUpdateLead,
  useDeleteLead,
  useProspects,
  useProspect,
  useCreateProspect,
  useUpdateProspect,
  useDeleteProspect,
  useDeals,
  useDeal,
  useCreateDeal,
  useUpdateDeal,
  useDeleteDeal,
  usePipelines,
  usePipeline,
  useCreatePipeline,
  useUpdatePipeline,
  useDeletePipeline,
  useCampaigns,
  useCampaign,
  useCreateCampaign,
  useUpdateCampaign,
  useDeleteCampaign,
  useProposals,
  useProposal,
  useCreateProposal,
  useUpdateProposal,
  useDeleteProposal,
  useContracts,
  useContract,
  useCreateContract,
  useUpdateContract,
  useDeleteContract,
} from '../crm'
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

describe('CRM API - Leads', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useLeads fetches all leads', async () => {
    const mockLeads = [
      {
        id: 1,
        company_name: 'Acme Corp',
        contact_name: 'John Doe',
        contact_email: 'john@acme.com',
        source: 'Website',
        status: 'new',
        lead_score: 75,
        captured_date: '2024-01-01',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockLeads })

    const { result } = renderHook(() => useLeads(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockLeads)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/leads/')
  })

  it('useLead fetches single lead', async () => {
    const mockLead = {
      id: 1,
      company_name: 'Acme Corp',
      contact_name: 'John Doe',
      contact_email: 'john@acme.com',
      source: 'Website',
      status: 'new',
      lead_score: 75,
      captured_date: '2024-01-01',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockLead })

    const { result } = renderHook(() => useLead(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockLead)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/leads/1/')
  })

  it('useCreateLead creates a new lead', async () => {
    const newLead = {
      company_name: 'New Corp',
      contact_name: 'Jane Smith',
      contact_email: 'jane@newcorp.com',
      source: 'Referral',
      status: 'new',
      lead_score: 50,
      captured_date: '2024-01-15',
    }
    const createdLead = {
      ...newLead,
      id: 2,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdLead })

    const { result } = renderHook(() => useCreateLead(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newLead)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdLead)
    expect(apiClient.post).toHaveBeenCalledWith('/crm/leads/', newLead)
  })

  it('useUpdateLead updates a lead', async () => {
    const updatedLead = {
      id: 1,
      company_name: 'Acme Corp',
      contact_name: 'John Doe',
      contact_email: 'john@acme.com',
      source: 'Website',
      status: 'qualified',
      lead_score: 85,
      captured_date: '2024-01-01',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedLead })

    const { result } = renderHook(() => useUpdateLead(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { status: 'qualified', lead_score: 85 } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedLead)
    expect(apiClient.put).toHaveBeenCalledWith('/crm/leads/1/', { status: 'qualified', lead_score: 85 })
  })

  it('useDeleteLead deletes a lead', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeleteLead(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/crm/leads/1/')
  })
})

describe('CRM API - Prospects', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useProspects fetches all prospects', async () => {
    const mockProspects = [
      {
        id: 1,
        company_name: 'Tech Solutions',
        primary_contact_name: 'Alice Johnson',
        primary_contact_email: 'alice@techsolutions.com',
        pipeline_stage: 'discovery',
        probability: 25,
        estimated_value: '50000',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockProspects })

    const { result } = renderHook(() => useProspects(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockProspects)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/prospects/')
  })

  it('useProspect fetches single prospect', async () => {
    const mockProspect = {
      id: 1,
      company_name: 'Tech Solutions',
      primary_contact_name: 'Alice Johnson',
      primary_contact_email: 'alice@techsolutions.com',
      pipeline_stage: 'discovery',
      probability: 25,
      estimated_value: '50000',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockProspect })

    const { result } = renderHook(() => useProspect(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockProspect)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/prospects/1/')
  })

  it('useCreateProspect creates a new prospect', async () => {
    const newProspect = {
      company_name: 'New Tech',
      primary_contact_name: 'Bob Williams',
      primary_contact_email: 'bob@newtech.com',
      pipeline_stage: 'initial_contact',
      probability: 10,
      estimated_value: '25000',
    }
    const createdProspect = {
      ...newProspect,
      id: 2,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdProspect })

    const { result } = renderHook(() => useCreateProspect(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newProspect)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdProspect)
    expect(apiClient.post).toHaveBeenCalledWith('/crm/prospects/', newProspect)
  })

  it('useUpdateProspect updates a prospect', async () => {
    const updatedProspect = {
      id: 1,
      company_name: 'Tech Solutions',
      primary_contact_name: 'Alice Johnson',
      primary_contact_email: 'alice@techsolutions.com',
      pipeline_stage: 'proposal',
      probability: 50,
      estimated_value: '50000',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedProspect })

    const { result } = renderHook(() => useUpdateProspect(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { pipeline_stage: 'proposal', probability: 50 } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedProspect)
    expect(apiClient.put).toHaveBeenCalledWith('/crm/prospects/1/', { pipeline_stage: 'proposal', probability: 50 })
  })

  it('useDeleteProspect deletes a prospect', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeleteProspect(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/crm/prospects/1/')
  })
})

describe('CRM API - Deals', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useDeals fetches all deals', async () => {
    const mockDeals = [
      {
        id: 1,
        name: 'Big Deal',
        pipeline: 1,
        stage: 1,
        value: '100000',
        probability: 75,
        weighted_value: '75000',
        expected_close_date: '2024-03-01',
        status: 'in_progress',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockDeals })

    const { result } = renderHook(() => useDeals(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockDeals)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/deals/')
  })

  it('useDeals with filters', async () => {
    const mockDeals = [
      {
        id: 1,
        name: 'Pipeline Deal',
        pipeline: 2,
        stage: 3,
        value: '50000',
        probability: 50,
        weighted_value: '25000',
        expected_close_date: '2024-02-15',
        status: 'in_progress',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockDeals })

    const { result } = renderHook(() => useDeals({ pipeline: 2 }), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockDeals)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/deals/?pipeline=2')
  })

  it('useDeal fetches single deal', async () => {
    const mockDeal = {
      id: 1,
      name: 'Big Deal',
      pipeline: 1,
      stage: 1,
      value: '100000',
      probability: 75,
      weighted_value: '75000',
      expected_close_date: '2024-03-01',
      status: 'in_progress',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockDeal })

    const { result } = renderHook(() => useDeal(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockDeal)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/deals/1/')
  })

  it('useCreateDeal creates a new deal', async () => {
    const newDeal = {
      name: 'New Deal',
      pipeline: 1,
      stage: 1,
      value: '75000',
      probability: 50,
      expected_close_date: '2024-04-01',
    }
    const createdDeal = {
      ...newDeal,
      id: 2,
      weighted_value: '37500',
      status: 'in_progress',
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdDeal })

    const { result } = renderHook(() => useCreateDeal(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newDeal)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdDeal)
    expect(apiClient.post).toHaveBeenCalledWith('/crm/deals/', newDeal)
  })

  it('useUpdateDeal updates a deal', async () => {
    const updatedDeal = {
      id: 1,
      name: 'Big Deal',
      pipeline: 1,
      stage: 2,
      value: '100000',
      probability: 85,
      weighted_value: '85000',
      expected_close_date: '2024-03-01',
      status: 'in_progress',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedDeal })

    const { result } = renderHook(() => useUpdateDeal(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { stage: 2, probability: 85 } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedDeal)
    expect(apiClient.put).toHaveBeenCalledWith('/crm/deals/1/', { stage: 2, probability: 85 })
  })

  it('useDeleteDeal deletes a deal', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeleteDeal(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/crm/deals/1/')
  })
})

describe('CRM API - Pipelines', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('usePipelines fetches all pipelines', async () => {
    const mockPipelines = [
      {
        id: 1,
        name: 'Sales Pipeline',
        description: 'Main sales pipeline',
        is_active: true,
        is_default: true,
        display_order: 1,
        stages: [],
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockPipelines })

    const { result } = renderHook(() => usePipelines(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockPipelines)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/pipelines/')
  })

  it('usePipeline fetches single pipeline', async () => {
    const mockPipeline = {
      id: 1,
      name: 'Sales Pipeline',
      description: 'Main sales pipeline',
      is_active: true,
      is_default: true,
      display_order: 1,
      stages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockPipeline })

    const { result } = renderHook(() => usePipeline(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockPipeline)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/pipelines/1/')
  })

  it('useCreatePipeline creates a new pipeline', async () => {
    const newPipeline = {
      name: 'Enterprise Pipeline',
      description: 'For enterprise deals',
      is_active: true,
      display_order: 2,
    }
    const createdPipeline = {
      ...newPipeline,
      id: 2,
      is_default: false,
      stages: [],
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdPipeline })

    const { result } = renderHook(() => useCreatePipeline(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newPipeline)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdPipeline)
    expect(apiClient.post).toHaveBeenCalledWith('/crm/pipelines/', newPipeline)
  })

  it('useUpdatePipeline updates a pipeline', async () => {
    const updatedPipeline = {
      id: 1,
      name: 'Sales Pipeline - Updated',
      description: 'Main sales pipeline',
      is_active: true,
      is_default: true,
      display_order: 1,
      stages: [],
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedPipeline })

    const { result } = renderHook(() => useUpdatePipeline(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { name: 'Sales Pipeline - Updated' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedPipeline)
    expect(apiClient.put).toHaveBeenCalledWith('/crm/pipelines/1/', { name: 'Sales Pipeline - Updated' })
  })

  it('useDeletePipeline deletes a pipeline', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeletePipeline(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/crm/pipelines/1/')
  })
})

describe('CRM API - Campaigns', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useCampaigns fetches all campaigns', async () => {
    const mockCampaigns = [
      {
        id: 1,
        name: 'Q1 Campaign',
        type: 'email',
        status: 'active',
        budget: '10000',
        actual_cost: '8500',
        targeted_clients: [],
        target_leads: 100,
        leads_generated: 75,
        opportunities_created: 20,
        clients_contacted: 50,
        renewal_proposals_sent: 10,
        renewals_won: 5,
        revenue_generated: '50000',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockCampaigns })

    const { result } = renderHook(() => useCampaigns(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockCampaigns)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/campaigns/')
  })

  it('useCampaign fetches single campaign', async () => {
    const mockCampaign = {
      id: 1,
      name: 'Q1 Campaign',
      type: 'email',
      status: 'active',
      budget: '10000',
      actual_cost: '8500',
      targeted_clients: [],
      target_leads: 100,
      leads_generated: 75,
      opportunities_created: 20,
      clients_contacted: 50,
      renewal_proposals_sent: 10,
      renewals_won: 5,
      revenue_generated: '50000',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockCampaign })

    const { result } = renderHook(() => useCampaign(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockCampaign)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/campaigns/1/')
  })

  it('useCreateCampaign creates a new campaign', async () => {
    const newCampaign = {
      name: 'Q2 Campaign',
      type: 'social_media',
      status: 'planning',
      budget: '15000',
      actual_cost: '0',
      targeted_clients: [],
      target_leads: 150,
      leads_generated: 0,
      opportunities_created: 0,
      clients_contacted: 0,
      renewal_proposals_sent: 0,
      renewals_won: 0,
      revenue_generated: '0',
    }
    const createdCampaign = {
      ...newCampaign,
      id: 2,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdCampaign })

    const { result } = renderHook(() => useCreateCampaign(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newCampaign)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdCampaign)
    expect(apiClient.post).toHaveBeenCalledWith('/crm/campaigns/', newCampaign)
  })

  it('useUpdateCampaign updates a campaign', async () => {
    const updatedCampaign = {
      id: 1,
      name: 'Q1 Campaign',
      type: 'email',
      status: 'completed',
      budget: '10000',
      actual_cost: '9500',
      targeted_clients: [],
      target_leads: 100,
      leads_generated: 85,
      opportunities_created: 25,
      clients_contacted: 60,
      renewal_proposals_sent: 12,
      renewals_won: 7,
      revenue_generated: '65000',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedCampaign })

    const { result } = renderHook(() => useUpdateCampaign(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { status: 'completed', actual_cost: '9500' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedCampaign)
    expect(apiClient.put).toHaveBeenCalledWith('/crm/campaigns/1/', { status: 'completed', actual_cost: '9500' })
  })

  it('useDeleteCampaign deletes a campaign', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeleteCampaign(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/crm/campaigns/1/')
  })
})

describe('CRM API - Proposals', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useProposals fetches all proposals', async () => {
    const mockProposals = [
      {
        id: 1,
        proposal_type: 'prospective_client' as const,
        proposal_number: 'PROP-001',
        title: 'Website Redesign Proposal',
        description: 'Complete website redesign',
        status: 'draft',
        total_value: '50000',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockProposals })

    const { result } = renderHook(() => useProposals(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockProposals)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/proposals/')
  })

  it('useProposal fetches single proposal', async () => {
    const mockProposal = {
      id: 1,
      proposal_type: 'prospective_client' as const,
      proposal_number: 'PROP-001',
      title: 'Website Redesign Proposal',
      description: 'Complete website redesign',
      status: 'draft',
      total_value: '50000',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockProposal })

    const { result } = renderHook(() => useProposal(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockProposal)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/proposals/1/')
  })

  it('useCreateProposal creates a new proposal', async () => {
    const newProposal = {
      proposal_type: 'prospective_client' as const,
      proposal_number: 'PROP-002',
      title: 'Mobile App Development',
      description: 'Custom mobile app',
      status: 'draft',
      total_value: '75000',
    }
    const createdProposal = {
      ...newProposal,
      id: 2,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdProposal })

    const { result } = renderHook(() => useCreateProposal(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newProposal)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdProposal)
    expect(apiClient.post).toHaveBeenCalledWith('/crm/proposals/', newProposal)
  })

  it('useUpdateProposal updates a proposal', async () => {
    const updatedProposal = {
      id: 1,
      proposal_type: 'prospective_client' as const,
      proposal_number: 'PROP-001',
      title: 'Website Redesign Proposal',
      description: 'Complete website redesign',
      status: 'sent',
      total_value: '50000',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedProposal })

    const { result } = renderHook(() => useUpdateProposal(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { status: 'sent' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedProposal)
    expect(apiClient.put).toHaveBeenCalledWith('/crm/proposals/1/', { status: 'sent' })
  })

  it('useDeleteProposal deletes a proposal', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeleteProposal(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/crm/proposals/1/')
  })
})

describe('CRM API - Contracts', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('useContracts fetches all contracts', async () => {
    const mockContracts = [
      {
        id: 1,
        contract_number: 'CONT-001',
        title: 'Service Agreement',
        status: 'active',
        contract_value: '100000',
        start_date: '2024-01-01',
        end_date: '2024-12-31',
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
    ]
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockContracts })

    const { result } = renderHook(() => useContracts(), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockContracts)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/contracts/')
  })

  it('useContract fetches single contract', async () => {
    const mockContract = {
      id: 1,
      contract_number: 'CONT-001',
      title: 'Service Agreement',
      status: 'active',
      contract_value: '100000',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-01T00:00:00Z',
    }
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockContract })

    const { result } = renderHook(() => useContract(1), {
      wrapper: createQueryWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockContract)
    expect(apiClient.get).toHaveBeenCalledWith('/crm/contracts/1/')
  })

  it('useCreateContract creates a new contract', async () => {
    const newContract = {
      contract_number: 'CONT-002',
      title: 'Consulting Agreement',
      status: 'draft',
      contract_value: '50000',
      start_date: '2024-02-01',
      end_date: '2024-07-31',
    }
    const createdContract = {
      ...newContract,
      id: 2,
      created_at: '2024-01-15T00:00:00Z',
      updated_at: '2024-01-15T00:00:00Z',
    }
    vi.mocked(apiClient.post).mockResolvedValue({ data: createdContract })

    const { result } = renderHook(() => useCreateContract(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(newContract)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(createdContract)
    expect(apiClient.post).toHaveBeenCalledWith('/crm/contracts/', newContract)
  })

  it('useUpdateContract updates a contract', async () => {
    const updatedContract = {
      id: 1,
      contract_number: 'CONT-001',
      title: 'Service Agreement',
      status: 'renewed',
      contract_value: '120000',
      start_date: '2024-01-01',
      end_date: '2024-12-31',
      created_at: '2024-01-01T00:00:00Z',
      updated_at: '2024-01-20T00:00:00Z',
    }
    vi.mocked(apiClient.put).mockResolvedValue({ data: updatedContract })

    const { result } = renderHook(() => useUpdateContract(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate({ id: 1, data: { status: 'renewed', contract_value: '120000' } })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(updatedContract)
    expect(apiClient.put).toHaveBeenCalledWith('/crm/contracts/1/', { status: 'renewed', contract_value: '120000' })
  })

  it('useDeleteContract deletes a contract', async () => {
    vi.mocked(apiClient.delete).mockResolvedValue({ data: null })

    const { result } = renderHook(() => useDeleteContract(), {
      wrapper: createQueryWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(apiClient.delete).toHaveBeenCalledWith('/crm/contracts/1/')
  })
})
