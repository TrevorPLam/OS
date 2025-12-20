import apiClient from './client'

export interface Client {
  id: number
  company_name: string
  industry: string
  status: string
  primary_contact_name: string
  primary_contact_email: string
  primary_contact_phone: string
  street_address?: string
  city?: string
  state?: string
  postal_code?: string
  country?: string
  website?: string
  created_at: string
}

export interface Proposal {
  id: number
  client: number
  client_name?: string
  proposal_number: string
  title: string
  description: string
  status: string
  total_value: string
  currency: string
  valid_until: string
  created_at: string
}

export interface Contract {
  id: number
  client: number
  client_name?: string
  contract_number: string
  title: string
  description: string
  status: string
  total_value: string
  currency: string
  payment_terms: string
  start_date: string
  end_date: string
  created_at: string
}

export const crmApi = {
  // Clients
  getClients: async (): Promise<Client[]> => {
    const response = await apiClient.get('/crm/clients/')
    return response.data.results || response.data
  },

  getClient: async (id: number): Promise<Client> => {
    const response = await apiClient.get(`/crm/clients/${id}/`)
    return response.data
  },

  createClient: async (data: Partial<Client>): Promise<Client> => {
    const response = await apiClient.post('/crm/clients/', data)
    return response.data
  },

  updateClient: async (id: number, data: Partial<Client>): Promise<Client> => {
    const response = await apiClient.put(`/crm/clients/${id}/`, data)
    return response.data
  },

  deleteClient: async (id: number): Promise<void> => {
    await apiClient.delete(`/crm/clients/${id}/`)
  },

  // Proposals
  getProposals: async (): Promise<Proposal[]> => {
    const response = await apiClient.get('/crm/proposals/')
    return response.data.results || response.data
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

  // Contracts
  getContracts: async (): Promise<Contract[]> => {
    const response = await apiClient.get('/crm/contracts/')
    return response.data.results || response.data
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
