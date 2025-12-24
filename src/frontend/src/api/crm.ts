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
}
