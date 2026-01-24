import { useMutation, useQuery, useQueryClient, UseMutationResult, UseQueryResult } from '@tanstack/react-query'
import apiClient from './client'

// CRM Module Interfaces (Pre-Sale & Client-Facing Sales)

export interface Lead {
  id: number
  company_name: string
  industry?: string
  website?: string
  contact_name: string
  contact_email: string
  contact_phone?: string
  contact_title?: string
  source: string
  status: string
  lead_score: number
  campaign?: number
  campaign_name?: string
  assigned_to?: number
  assigned_to_name?: string
  captured_date: string
  first_contacted?: string
  qualified_date?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface Prospect {
  id: number
  lead?: number
  lead_company?: string
  company_name: string
  industry?: string
  website?: string
  employee_count?: number
  annual_revenue?: string
  primary_contact_name: string
  primary_contact_email: string
  primary_contact_phone?: string
  primary_contact_title?: string
  street_address?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  pipeline_stage: string
  probability: number
  estimated_value: string
  close_date_estimate?: string
  assigned_to?: number
  assigned_to_name?: string
  last_activity_date?: string
  won_date?: string
  lost_date?: string
  lost_reason?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface Campaign {
  id: number
  name: string
  description?: string
  type: string
  status: string
  start_date?: string
  end_date?: string
  budget: string
  actual_cost: string
  targeted_clients: number[]
  target_leads: number
  leads_generated: number
  opportunities_created: number
  clients_contacted: number
  renewal_proposals_sent: number
  renewals_won: number
  revenue_generated: string
  owner?: number
  owner_name?: string
  created_at: string
  updated_at: string
}

export interface Proposal {
  id: number
  proposal_type: 'prospective_client' | 'update_client' | 'renewal_client'
  prospect?: number
  prospect_name?: string
  client?: number
  client_name?: string
  created_by?: number
  created_by_name?: string
  proposal_number: string
  title: string
  description: string
  status: string
  total_value: string
  currency: string
  valid_until: string
  estimated_start_date?: string
  estimated_end_date?: string
  converted_to_engagement: boolean
  auto_create_project: boolean
  enable_portal_on_acceptance: boolean
  sent_at?: string
  accepted_at?: string
  created_at: string
  updated_at: string
}

export interface Contract {
  id: number
  client: number
  client_name?: string
  proposal?: number
  proposal_number?: string
  signed_by?: number
  signed_by_name?: string
  contract_number: string
  title: string
  description: string
  status: string
  total_value: string
  currency: string
  payment_terms: string
  start_date: string
  end_date: string
  signed_date?: string
  contract_file_url?: string
  notes?: string
  created_at: string
  updated_at: string
}

export interface PipelineStageAutoTask {
  title?: string
  description?: string
  due_days?: number
  assigned_to_role?: string
  [key: string]: unknown
}

export interface PipelineStage {
  id: number
  pipeline: number
  name: string
  description?: string
  probability: number
  is_active: boolean
  is_closed_won: boolean
  is_closed_lost: boolean
  display_order: number
  auto_tasks: PipelineStageAutoTask[]
  deal_count?: number
  created_at: string
  updated_at: string
}

export interface Pipeline {
  id: number
  name: string
  description?: string
  is_active: boolean
  is_default: boolean
  display_order: number
  stages?: PipelineStage[]
  deal_count?: number
  total_value?: number
  created_at: string
  updated_at: string
  created_by?: number
  created_by_name?: string
}

export interface Deal {
  id: number
  pipeline: number
  pipeline_name?: string
  stage: number
  stage_name?: string
  name: string
  description?: string
  account?: number
  account_name?: string
  contact?: number
  contact_name?: string
  value: string
  currency: string
  probability: number
  weighted_value: string
  expected_close_date: string
  actual_close_date?: string
  owner?: number
  owner_name?: string
  team_members: number[]
  split_percentage: Record<string, number>
  source?: string
  campaign?: number
  campaign_name?: string
  contacts?: number[]
  is_active: boolean
  is_won: boolean
  is_lost: boolean
  lost_reason?: string
  last_activity_date?: string
  is_stale: boolean
  stale_days_threshold: number
  converted_to_project: boolean
  project?: number
  created_at: string
  updated_at: string
  created_by?: number
  stale_days?: number
  tags?: string[]
  custom_fields?: Record<string, unknown>
}

export interface DealTask {
  id: number
  deal: number
  deal_name?: string
  title: string
  description?: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled'
  assigned_to?: number
  assigned_to_name?: string
  due_date?: string
  completed_at?: string
  created_at: string
  updated_at: string
}

export interface PipelineReport {
  pipeline: Array<{ pipeline_stage: string; count: number; total_value: string }>
  total_prospects: number
  total_pipeline_value: string
}

export interface CampaignPerformance {
  campaign: Campaign
  metrics: {
    roi: number
    cost_per_lead: number
    conversion_rate: number
  }
}

export interface PipelineAnalyticsData {
  total_deals: number
  total_value: number
  total_weighted_value: number
  average_deal_value: number
  average_probability: number
  stage_breakdown: Array<{
    stage_id: number
    stage_name: string
    deal_count: number
    total_value: number
    weighted_value: number
  }>
}

export interface ForecastData {
  total_pipeline_value: number
  total_weighted_value: number
  monthly_forecast: Array<{
    month: string | null
    deal_count: number
    total_value: number
    weighted_value: number
  }>
}

export interface WinLossReport {
  summary: {
    total_closed: number
    won_count: number
    lost_count: number
    win_rate: number
    loss_rate: number
    won_value: number
    lost_value: number
    avg_won_deal: number
    avg_lost_deal: number
  }
  monthly_won: Array<{
    month: string
    deal_count: number
    total_value: number
  }>
  monthly_lost: Array<{
    month: string
    deal_count: number
    total_value: number
  }>
  top_loss_reasons: Array<{
    lost_reason: string
    count: number
  }>
}

export interface DealConversionProjectData {
  project_name?: string
  description?: string
  start_date?: string
  end_date?: string
  [key: string]: unknown
}

export interface DealConversionResult {
  status: string
  project_id: number
  project_name: string
}

// Contact Graph View Interfaces (CRM-INT-1)
export interface ContactGraphNode {
  id: string
  type: 'contact' | 'account'
  data: {
    contact_id?: number
    account_id?: number
    name: string
    email?: string
    job_title?: string
    is_primary?: boolean
    is_decision_maker?: boolean
    account_name?: string
    account_type?: string
    industry?: string
  }
  strength: number
}

export interface ContactGraphEdge {
  id: string
  source: string
  target: string
  type: 'belongs_to' | 'relationship'
  relationship_type?: string
  strength: number
}

export interface ContactGraphData {
  nodes: ContactGraphNode[]
  edges: ContactGraphEdge[]
  metadata: {
    total_contacts: number
    total_accounts: number
    total_relationships: number
    focus_contact_id?: string
  }
}

const getListResults = <T>(data: { results?: T[] } | T[]): T[] => {
  if (Array.isArray(data)) {
    return data
  }

  return data.results ?? []
}

export const useLeads = (): UseQueryResult<Lead[], Error> => {
  return useQuery({
    queryKey: ['crm', 'leads'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/leads/')
      return getListResults<Lead>(response.data)
    },
  })
}

export const useLead = (id?: number): UseQueryResult<Lead, Error> => {
  return useQuery({
    queryKey: ['crm', 'leads', id],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/leads/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useCreateLead = (): UseMutationResult<Lead, Error, Partial<Lead>> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/crm/leads/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'leads'] })
    },
  })
}

export const useUpdateLead = (): UseMutationResult<Lead, Error, { id: number; data: Partial<Lead> }> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/crm/leads/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'leads'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'leads', variables.id] })
    },
  })
}

export const useDeleteLead = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/crm/leads/${id}/`)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'leads'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'leads', id] })
    },
  })
}

export const useConvertLeadToProspect = (): UseMutationResult<
  { message: string; prospect: Prospect },
  Error,
  { id: number; data?: { close_date_estimate?: string } }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.post(`/crm/leads/${id}/convert_to_prospect/`, data || {})
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'leads'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'prospects'] })
    },
  })
}

export const useProspects = (): UseQueryResult<Prospect[], Error> => {
  return useQuery({
    queryKey: ['crm', 'prospects'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/prospects/')
      return getListResults<Prospect>(response.data)
    },
  })
}

export const useProspect = (id?: number): UseQueryResult<Prospect, Error> => {
  return useQuery({
    queryKey: ['crm', 'prospects', id],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/prospects/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useCreateProspect = (): UseMutationResult<Prospect, Error, Partial<Prospect>> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/crm/prospects/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'prospects'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipeline-report'] })
    },
  })
}

export const useUpdateProspect = (): UseMutationResult<
  Prospect,
  Error,
  { id: number; data: Partial<Prospect> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/crm/prospects/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'prospects'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'prospects', variables.id] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipeline-report'] })
    },
  })
}

export const useDeleteProspect = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/crm/prospects/${id}/`)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'prospects'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'prospects', id] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipeline-report'] })
    },
  })
}

export const usePipelineReport = (): UseQueryResult<PipelineReport, Error> => {
  return useQuery({
    queryKey: ['crm', 'pipeline-report'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/prospects/pipeline_report/')
      return response.data
    },
  })
}

export const useCampaigns = (): UseQueryResult<Campaign[], Error> => {
  return useQuery({
    queryKey: ['crm', 'campaigns'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/campaigns/')
      return getListResults<Campaign>(response.data)
    },
  })
}

export const useCampaign = (id?: number): UseQueryResult<Campaign, Error> => {
  return useQuery({
    queryKey: ['crm', 'campaigns', id],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/campaigns/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useCreateCampaign = (): UseMutationResult<Campaign, Error, Partial<Campaign>> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/crm/campaigns/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'campaigns'] })
    },
  })
}

export const useUpdateCampaign = (): UseMutationResult<
  Campaign,
  Error,
  { id: number; data: Partial<Campaign> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/crm/campaigns/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'campaigns'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'campaigns', variables.id] })
    },
  })
}

export const useDeleteCampaign = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/crm/campaigns/${id}/`)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'campaigns'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'campaigns', id] })
    },
  })
}

export const useCampaignPerformance = (id?: number): UseQueryResult<CampaignPerformance, Error> => {
  return useQuery({
    queryKey: ['crm', 'campaigns', id, 'performance'],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/campaigns/${id}/performance/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useProposals = (): UseQueryResult<Proposal[], Error> => {
  return useQuery({
    queryKey: ['crm', 'proposals'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/proposals/')
      return getListResults<Proposal>(response.data)
    },
  })
}

export const useProposal = (id?: number): UseQueryResult<Proposal, Error> => {
  return useQuery({
    queryKey: ['crm', 'proposals', id],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/proposals/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useCreateProposal = (): UseMutationResult<Proposal, Error, Partial<Proposal>> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/crm/proposals/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'proposals'] })
    },
  })
}

export const useUpdateProposal = (): UseMutationResult<
  Proposal,
  Error,
  { id: number; data: Partial<Proposal> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/crm/proposals/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'proposals'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'proposals', variables.id] })
    },
  })
}

export const useDeleteProposal = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/crm/proposals/${id}/`)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'proposals'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'proposals', id] })
    },
  })
}

export const useSendProposal = (): UseMutationResult<{ message: string; proposal: Proposal }, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.post(`/crm/proposals/${id}/send/`)
      return response.data
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'proposals'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'proposals', id] })
    },
  })
}

export const useAcceptProposal = (): UseMutationResult<{ message: string; proposal: Proposal }, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.post(`/crm/proposals/${id}/accept/`)
      return response.data
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'proposals'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'proposals', id] })
    },
  })
}

export const useContracts = (): UseQueryResult<Contract[], Error> => {
  return useQuery({
    queryKey: ['crm', 'contracts'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/contracts/')
      return getListResults<Contract>(response.data)
    },
  })
}

export const useContract = (id?: number): UseQueryResult<Contract, Error> => {
  return useQuery({
    queryKey: ['crm', 'contracts', id],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/contracts/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useCreateContract = (): UseMutationResult<Contract, Error, Partial<Contract>> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/crm/contracts/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'contracts'] })
    },
  })
}

export const useUpdateContract = (): UseMutationResult<
  Contract,
  Error,
  { id: number; data: Partial<Contract> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/crm/contracts/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'contracts'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'contracts', variables.id] })
    },
  })
}

export const useDeleteContract = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/crm/contracts/${id}/`)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'contracts'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'contracts', id] })
    },
  })
}

export const usePipelines = (): UseQueryResult<Pipeline[], Error> => {
  return useQuery({
    queryKey: ['crm', 'pipelines'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/pipelines/')
      return getListResults<Pipeline>(response.data)
    },
  })
}

export const usePipeline = (id?: number): UseQueryResult<Pipeline, Error> => {
  return useQuery({
    queryKey: ['crm', 'pipelines', id],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/pipelines/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const usePipelineAnalytics = (id?: number): UseQueryResult<PipelineAnalyticsData, Error> => {
  return useQuery({
    queryKey: ['crm', 'pipelines', id, 'analytics'],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/pipelines/${id}/analytics/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useCreatePipeline = (): UseMutationResult<Pipeline, Error, Partial<Pipeline>> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/crm/pipelines/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipelines'] })
    },
  })
}

export const useUpdatePipeline = (): UseMutationResult<
  Pipeline,
  Error,
  { id: number; data: Partial<Pipeline> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/crm/pipelines/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipelines'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipelines', variables.id] })
    },
  })
}

export const useDeletePipeline = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/crm/pipelines/${id}/`)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipelines'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipelines', id] })
    },
  })
}

export const useSetDefaultPipeline = (): UseMutationResult<
  { message: string; pipeline: Pipeline },
  Error,
  number
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.post(`/crm/pipelines/${id}/set_default/`)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipelines'] })
    },
  })
}

export const usePipelineStages = (pipelineId?: number): UseQueryResult<PipelineStage[], Error> => {
  return useQuery({
    queryKey: ['crm', 'pipeline-stages', pipelineId ?? 'all'],
    queryFn: async () => {
      const url = pipelineId ? `/crm/pipeline-stages/?pipeline=${pipelineId}` : '/crm/pipeline-stages/'
      const response = await apiClient.get(url)
      return getListResults<PipelineStage>(response.data)
    },
  })
}

export const usePipelineStage = (id?: number): UseQueryResult<PipelineStage, Error> => {
  return useQuery({
    queryKey: ['crm', 'pipeline-stages', id],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/pipeline-stages/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useCreatePipelineStage = (): UseMutationResult<
  PipelineStage,
  Error,
  Partial<PipelineStage>
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/crm/pipeline-stages/', data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipeline-stages'] })
      if (variables.pipeline) {
        queryClient.invalidateQueries({ queryKey: ['crm', 'pipeline-stages', variables.pipeline] })
      }
    },
  })
}

export const useUpdatePipelineStage = (): UseMutationResult<
  PipelineStage,
  Error,
  { id: number; data: Partial<PipelineStage> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/crm/pipeline-stages/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipeline-stages'] })
      if (variables.data.pipeline) {
        queryClient.invalidateQueries({ queryKey: ['crm', 'pipeline-stages', variables.data.pipeline] })
      }
    },
  })
}

export const useDeletePipelineStage = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/crm/pipeline-stages/${id}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'pipeline-stages'] })
    },
  })
}

export interface DealFilters {
  pipeline?: number
  stage?: number
  owner?: number
  is_active?: boolean
}

export const useDeals = (filters?: DealFilters): UseQueryResult<Deal[], Error> => {
  return useQuery({
    queryKey: ['crm', 'deals', filters ?? {}],
    queryFn: async () => {
      const params = new URLSearchParams()

      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value !== undefined && value !== null) {
            params.append(key, String(value))
          }
        })
      }

      const queryString = params.toString()
      const url = queryString ? `/crm/deals/?${queryString}` : '/crm/deals/'
      const response = await apiClient.get(url)
      return getListResults<Deal>(response.data)
    },
  })
}

export const useDeal = (id?: number): UseQueryResult<Deal, Error> => {
  return useQuery({
    queryKey: ['crm', 'deals', id],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/deals/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useForecast = (): UseQueryResult<ForecastData, Error> => {
  return useQuery({
    queryKey: ['crm', 'deals', 'forecast'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/deals/forecast/')
      return response.data
    },
  })
}

export const useWinLossReport = (): UseQueryResult<WinLossReport, Error> => {
  return useQuery({
    queryKey: ['crm', 'deals', 'win-loss-report'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/deals/win_loss_report/')
      return response.data
    },
  })
}

export const useCreateDeal = (): UseMutationResult<Deal, Error, Partial<Deal>> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/crm/deals/', data)
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals'] })
    },
  })
}

export const useUpdateDeal = (): UseMutationResult<Deal, Error, { id: number; data: Partial<Deal> }> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/crm/deals/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals', variables.id] })
    },
  })
}

export const useDeleteDeal = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/crm/deals/${id}/`)
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals', id] })
    },
  })
}

export const useMoveDealToStage = (): UseMutationResult<
  Deal,
  Error,
  { id: number; stageId: number; notes?: string }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, stageId, notes }) => {
      const response = await apiClient.post(`/crm/deals/${id}/move_stage/`, {
        stage_id: stageId,
        notes: notes || '',
      })
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals', variables.id] })
    },
  })
}

export const useMarkDealWon = (): UseMutationResult<Deal, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      const response = await apiClient.post(`/crm/deals/${id}/mark_won/`)
      return response.data
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals', id] })
    },
  })
}

export const useMarkDealLost = (): UseMutationResult<Deal, Error, { id: number; reason: string }> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, reason }) => {
      const response = await apiClient.post(`/crm/deals/${id}/mark_lost/`, {
        lost_reason: reason,
      })
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals'] })
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals', variables.id] })
    },
  })
}

export const useConvertDealToProject = (): UseMutationResult<
  DealConversionResult,
  Error,
  { id: number; projectData?: DealConversionProjectData }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, projectData }) => {
      const response = await apiClient.post(`/crm/deals/${id}/convert_to_project/`, projectData || {})
      return response.data
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deals'] })
    },
  })
}

export const useStaleDeals = (): UseQueryResult<Deal[], Error> => {
  return useQuery({
    queryKey: ['crm', 'deals', 'stale'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/deals/stale/')
      return response.data
    },
  })
}

export const useDealForecast = (): UseQueryResult<ForecastData, Error> => {
  return useQuery({
    queryKey: ['crm', 'deals', 'forecast'],
    queryFn: async () => {
      const response = await apiClient.get('/crm/deals/forecast/')
      return response.data
    },
  })
}

export const useDealTasks = (dealId?: number): UseQueryResult<DealTask[], Error> => {
  return useQuery({
    queryKey: ['crm', 'deal-tasks', dealId ?? 'all'],
    queryFn: async () => {
      const url = dealId ? `/crm/deal-tasks/?deal=${dealId}` : '/crm/deal-tasks/'
      const response = await apiClient.get(url)
      return getListResults<DealTask>(response.data)
    },
  })
}

export const useDealTask = (id?: number): UseQueryResult<DealTask, Error> => {
  return useQuery({
    queryKey: ['crm', 'deal-tasks', id],
    queryFn: async () => {
      const response = await apiClient.get(`/crm/deal-tasks/${id}/`)
      return response.data
    },
    enabled: typeof id === 'number',
  })
}

export const useCreateDealTask = (): UseMutationResult<DealTask, Error, Partial<DealTask>> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data) => {
      const response = await apiClient.post('/crm/deal-tasks/', data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deal-tasks'] })
      if (variables.deal) {
        queryClient.invalidateQueries({ queryKey: ['crm', 'deal-tasks', variables.deal] })
      }
    },
  })
}

export const useUpdateDealTask = (): UseMutationResult<
  DealTask,
  Error,
  { id: number; data: Partial<DealTask> }
> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, data }) => {
      const response = await apiClient.put(`/crm/deal-tasks/${id}/`, data)
      return response.data
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deal-tasks'] })
      if (variables.data.deal) {
        queryClient.invalidateQueries({ queryKey: ['crm', 'deal-tasks', variables.data.deal] })
      }
    },
  })
}

export const useDeleteDealTask = (): UseMutationResult<void, Error, number> => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (id) => {
      await apiClient.delete(`/crm/deal-tasks/${id}/`)
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm', 'deal-tasks'] })
    },
  })
}

export const useContactGraphView = (params?: {
  contact_id?: number
  depth?: number
  include_inactive?: boolean
}): UseQueryResult<ContactGraphData, Error> => {
  return useQuery({
    queryKey: ['crm', 'contact-graph', params ?? {}],
    queryFn: async () => {
      const queryParams = new URLSearchParams()
      if (params?.contact_id) queryParams.append('contact_id', params.contact_id.toString())
      if (params?.depth) queryParams.append('depth', params.depth.toString())
      if (params?.include_inactive) queryParams.append('include_inactive', 'true')

      const suffix = queryParams.toString()
      const url = suffix ? `/crm/account-contacts/graph_view/?${suffix}` : '/crm/account-contacts/graph_view/'
      const response = await apiClient.get(url)
      return response.data
    },
  })
}
