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
  auto_tasks: any[]
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
  created_at: string
  updated_at: string
  created_by?: number
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
  custom_fields?: Record<string, any>
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

export const crmApi = {
  // Leads
  getLeads: async (): Promise<Lead[]> => {
    const response = await apiClient.get('/crm/leads/')
    return response.data.results || response.data
  },

  getLead: async (id: number): Promise<Lead> => {
    const response = await apiClient.get(`/crm/leads/${id}/`)
    return response.data
  },

  createLead: async (data: Partial<Lead>): Promise<Lead> => {
    const response = await apiClient.post('/crm/leads/', data)
    return response.data
  },

  updateLead: async (id: number, data: Partial<Lead>): Promise<Lead> => {
    const response = await apiClient.put(`/crm/leads/${id}/`, data)
    return response.data
  },

  deleteLead: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/leads/${id}/`)
  },

  convertLeadToProspect: async (id: number, data?: { close_date_estimate?: string }): Promise<{ message: string; prospect: Prospect }> => {
    const response = await apiClient.post(`/crm/leads/${id}/convert_to_prospect/`, data || {})
    return response.data
  },

  // Prospects
  getProspects: async (): Promise<Prospect[]> => {
    const response = await apiClient.get('/crm/prospects/')
    return response.data.results || response.data
  },

  getProspect: async (id: number): Promise<Prospect> => {
    const response = await apiClient.get(`/crm/prospects/${id}/`)
    return response.data
  },

  createProspect: async (data: Partial<Prospect>): Promise<Prospect> => {
    const response = await apiClient.post('/crm/prospects/', data)
    return response.data
  },

  updateProspect: async (id: number, data: Partial<Prospect>): Promise<Prospect> => {
    const response = await apiClient.put(`/crm/prospects/${id}/`, data)
    return response.data
  },

  deleteProspect: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/prospects/${id}/`)
  },

  getPipelineReport: async (): Promise<{
    pipeline: Array<{ pipeline_stage: string; count: number; total_value: string }>
    total_prospects: number
    total_pipeline_value: string
  }> => {
    const response = await apiClient.get('/crm/prospects/pipeline_report/')
    return response.data
  },

  // Campaigns
  getCampaigns: async (): Promise<Campaign[]> => {
    const response = await apiClient.get('/crm/campaigns/')
    return response.data.results || response.data
  },

  getCampaign: async (id: number): Promise<Campaign> => {
    const response = await apiClient.get(`/crm/campaigns/${id}/`)
    return response.data
  },

  createCampaign: async (data: Partial<Campaign>): Promise<Campaign> => {
    const response = await apiClient.post('/crm/campaigns/', data)
    return response.data
  },

  updateCampaign: async (id: number, data: Partial<Campaign>): Promise<Campaign> => {
    const response = await apiClient.put(`/crm/campaigns/${id}/`, data)
    return response.data
  },

  deleteCampaign: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/campaigns/${id}/`)
  },

  getCampaignPerformance: async (id: number): Promise<{
    campaign: Campaign
    metrics: {
      roi: number
      cost_per_lead: number
      conversion_rate: number
    }
  }> => {
    const response = await apiClient.get(`/crm/campaigns/${id}/performance/`)
    return response.data
  },

  // Proposals
  getProposals: async (): Promise<Proposal[]> => {
    const response = await apiClient.get('/crm/proposals/')
    return response.data.results || response.data
  },

  getProposal: async (id: number): Promise<Proposal> => {
    const response = await apiClient.get(`/crm/proposals/${id}/`)
    return response.data
  },

  createProposal: async (data: Partial<Proposal>): Promise<Proposal> => {
    const response = await apiClient.post('/crm/proposals/', data)
    return response.data
  },

  updateProposal: async (id: number, data: Partial<Proposal>): Promise<Proposal> => {
    const response = await apiClient.put(`/crm/proposals/${id}/`, data)
    return response.data
  },

  deleteProposal: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/proposals/${id}/`)
  },

  sendProposal: async (id: number): Promise<{ message: string; proposal: Proposal }> => {
    const response = await apiClient.post(`/crm/proposals/${id}/send/`)
    return response.data
  },

  acceptProposal: async (id: number): Promise<{ message: string; proposal: Proposal }> => {
    const response = await apiClient.post(`/crm/proposals/${id}/accept/`)
    return response.data
  },

  // Contracts
  getContracts: async (): Promise<Contract[]> => {
    const response = await apiClient.get('/crm/contracts/')
    return response.data.results || response.data
  },

  getContract: async (id: number): Promise<Contract> => {
    const response = await apiClient.get(`/crm/contracts/${id}/`)
    return response.data
  },

  createContract: async (data: Partial<Contract>): Promise<Contract> => {
    const response = await apiClient.post('/crm/contracts/', data)
    return response.data
  },

  updateContract: async (id: number, data: Partial<Contract>): Promise<Contract> => {
    const response = await apiClient.put(`/crm/contracts/${id}/`, data)
    return response.data
  },

  deleteContract: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/contracts/${id}/`)
  },

  // Pipelines
  getPipelines: async (): Promise<Pipeline[]> => {
    const response = await apiClient.get('/crm/pipelines/')
    return response.data.results || response.data
  },

  getPipeline: async (id: number): Promise<Pipeline> => {
    const response = await apiClient.get(`/crm/pipelines/${id}/`)
    return response.data
  },

  getPipelineAnalytics: async (id: number): Promise<any> => {
    const response = await apiClient.get(`/crm/pipelines/${id}/analytics/`)
    return response.data
  },

  createPipeline: async (data: Partial<Pipeline>): Promise<Pipeline> => {
    const response = await apiClient.post('/crm/pipelines/', data)
    return response.data
  },

  updatePipeline: async (id: number, data: Partial<Pipeline>): Promise<Pipeline> => {
    const response = await apiClient.put(`/crm/pipelines/${id}/`, data)
    return response.data
  },

  deletePipeline: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/pipelines/${id}/`)
  },

  setDefaultPipeline: async (id: number): Promise<{ message: string; pipeline: Pipeline }> => {
    const response = await apiClient.post(`/crm/pipelines/${id}/set_default/`)
    return response.data
  },

  // Pipeline Stages
  getPipelineStages: async (pipelineId?: number): Promise<PipelineStage[]> => {
    const url = pipelineId ? `/crm/pipeline-stages/?pipeline=${pipelineId}` : '/crm/pipeline-stages/'
    const response = await apiClient.get(url)
    return response.data.results || response.data
  },

  getPipelineStage: async (id: number): Promise<PipelineStage> => {
    const response = await apiClient.get(`/crm/pipeline-stages/${id}/`)
    return response.data
  },

  createPipelineStage: async (data: Partial<PipelineStage>): Promise<PipelineStage> => {
    const response = await apiClient.post('/crm/pipeline-stages/', data)
    return response.data
  },

  updatePipelineStage: async (id: number, data: Partial<PipelineStage>): Promise<PipelineStage> => {
    const response = await apiClient.put(`/crm/pipeline-stages/${id}/`, data)
    return response.data
  },

  deletePipelineStage: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/pipeline-stages/${id}/`)
  },

  // Deals
  getDeals: async (filters?: { pipeline?: number; stage?: number; owner?: number; is_active?: boolean }): Promise<Deal[]> => {
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
    return response.data.results || response.data
  },

  getDeal: async (id: number): Promise<Deal> => {
    const response = await apiClient.get(`/crm/deals/${id}/`)
    return response.data
  },

  forecast: async (): Promise<any> => {
    const response = await apiClient.get('/crm/deals/forecast/')
    return response.data
  },

  winLossReport: async (): Promise<any> => {
    const response = await apiClient.get('/crm/deals/win_loss_report/')
    return response.data
  },

  createDeal: async (data: Partial<Deal>): Promise<Deal> => {
    const response = await apiClient.post('/crm/deals/', data)
    return response.data
  },

  updateDeal: async (id: number, data: Partial<Deal>): Promise<Deal> => {
    const response = await apiClient.put(`/crm/deals/${id}/`, data)
    return response.data
  },

  deleteDeal: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/deals/${id}/`)
  },

  moveDealToStage: async (id: number, stageId: number, notes?: string): Promise<Deal> => {
    const response = await apiClient.post(`/crm/deals/${id}/move_stage/`, {
      stage_id: stageId,
      notes: notes || '',
    })
    return response.data
  },

  markDealWon: async (id: number): Promise<Deal> => {
    const response = await apiClient.post(`/crm/deals/${id}/mark_won/`)
    return response.data
  },

  markDealLost: async (id: number, reason: string): Promise<Deal> => {
    const response = await apiClient.post(`/crm/deals/${id}/mark_lost/`, {
      lost_reason: reason
    })
    return response.data
  },

  convertDealToProject: async (id: number, projectData?: any): Promise<{ status: string; project_id: number; project_name: string }> => {
    const response = await apiClient.post(`/crm/deals/${id}/convert_to_project/`, projectData || {})
    return response.data
  },

  getStaleDeals: async (): Promise<Deal[]> => {
    const response = await apiClient.get('/crm/deals/stale/')
    return response.data
  },

  getDealForecast: async (): Promise<{
    total_pipeline_value: number
    total_weighted_value: number
    monthly_forecast: Array<{
      month: string
      deal_count: number
      total_value: number
      weighted_value: number
    }>
  }> => {
    const response = await apiClient.get('/crm/deals/forecast/')
    return response.data
  },

  // Deal Tasks
  getDealTasks: async (dealId?: number): Promise<DealTask[]> => {
    const url = dealId ? `/crm/deal-tasks/?deal=${dealId}` : '/crm/deal-tasks/'
    const response = await apiClient.get(url)
    return response.data.results || response.data
  },

  getDealTask: async (id: number): Promise<DealTask> => {
    const response = await apiClient.get(`/crm/deal-tasks/${id}/`)
    return response.data
  },

  createDealTask: async (data: Partial<DealTask>): Promise<DealTask> => {
    const response = await apiClient.post('/crm/deal-tasks/', data)
    return response.data
  },

  updateDealTask: async (id: number, data: Partial<DealTask>): Promise<DealTask> => {
    const response = await apiClient.put(`/crm/deal-tasks/${id}/`, data)
    return response.data
  },

  deleteDealTask: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/deal-tasks/${id}/`)
  },

  // Contact Graph View (CRM-INT-1)
  getContactGraphView: async (params?: {
    contact_id?: number
    depth?: number
    include_inactive?: boolean
  }): Promise<ContactGraphData> => {
    const queryParams = new URLSearchParams()
    if (params?.contact_id) queryParams.append('contact_id', params.contact_id.toString())
    if (params?.depth) queryParams.append('depth', params.depth.toString())
    if (params?.include_inactive) queryParams.append('include_inactive', 'true')
    
    const response = await apiClient.get(`/crm/account-contacts/graph_view/?${queryParams}`)
    return response.data
  },
}
