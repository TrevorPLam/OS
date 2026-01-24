import apiClient from './client'
import type { Client } from './clients'
import type { Proposal, Contract } from './crm'

// Define types for time entries and invoices (not in imported files)
interface TimeEntry {
  id: number;
  hours: string | number;
  is_billable: boolean;
  invoiced: boolean;
  [key: string]: unknown;
}

interface Invoice {
  id: number;
  status: string;
  total_amount: string | number;
  amount_paid: string | number;
  [key: string]: unknown;
}

export interface DashboardStats {
  total_clients: number
  active_clients: number
  total_proposals: number
  accepted_proposals: number
  active_contracts: number
  total_contract_value: string
  unbilled_hours: string
  unpaid_invoices: number
  total_receivable: string
}

export const dashboardApi = {
  getStats: async (): Promise<DashboardStats> => {
    // For now, aggregate from existing endpoints
    const [clients, proposals, contracts, timeEntries, invoices] = await Promise.all([
      apiClient.get('/crm/clients/'),
      apiClient.get('/crm/proposals/'),
      apiClient.get('/crm/contracts/'),
      apiClient.get('/projects/time-entries/'),
      apiClient.get('/finance/invoices/'),
    ])

    const clientsData = (clients.data.results || clients.data) as Client[]
    const proposalsData = (proposals.data.results || proposals.data) as Proposal[]
    const contractsData = (contracts.data.results || contracts.data) as Contract[]
    const timeEntriesData = (timeEntries.data.results || timeEntries.data) as TimeEntry[]
    const invoicesData = (invoices.data.results || invoices.data) as Invoice[]

    // Calculate stats
    const totalClients = clientsData.length
    const activeClients = clientsData.filter((c) => c.status === 'active').length
    const totalProposals = proposalsData.length
    const acceptedProposals = proposalsData.filter((p) => p.status === 'accepted').length
    const activeContracts = contractsData.filter((c) => c.status === 'active').length
    const totalContractValue = contractsData
      .filter((c) => c.status === 'active')
      .reduce((sum: number, c) => sum + parseFloat(String(c.total_value || 0)), 0)
      .toFixed(2)

    const unbilledHours = timeEntriesData
      .filter((t) => t.is_billable && !t.invoiced)
      .reduce((sum: number, t) => sum + parseFloat(String(t.hours || 0)), 0)
      .toFixed(2)

    const unpaidInvoices = invoicesData.filter((i) => i.status !== 'paid').length
    const totalReceivable = invoicesData
      .filter((i) => i.status !== 'paid')
      .reduce((sum: number, i) => {
        const total = parseFloat(String(i.total_amount || 0))
        const paid = parseFloat(String(i.amount_paid || 0))
        return sum + (total - paid)
      }, 0)
      .toFixed(2)

    return {
      total_clients: totalClients,
      active_clients: activeClients,
      total_proposals: totalProposals,
      accepted_proposals: acceptedProposals,
      active_contracts: activeContracts,
      total_contract_value: totalContractValue,
      unbilled_hours: unbilledHours,
      unpaid_invoices: unpaidInvoices,
      total_receivable: totalReceivable,
    }
  },
}
