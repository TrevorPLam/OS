import apiClient from './client'

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

    const clientsData = clients.data.results || clients.data
    const proposalsData = proposals.data.results || proposals.data
    const contractsData = contracts.data.results || contracts.data
    const timeEntriesData = timeEntries.data.results || timeEntries.data
    const invoicesData = invoices.data.results || invoices.data

    // Calculate stats
    const totalClients = clientsData.length
    const activeClients = clientsData.filter((c: any) => c.status === 'active').length
    const totalProposals = proposalsData.length
    const acceptedProposals = proposalsData.filter((p: any) => p.status === 'accepted').length
    const activeContracts = contractsData.filter((c: any) => c.status === 'active').length
    const totalContractValue = contractsData
      .filter((c: any) => c.status === 'active')
      .reduce((sum: number, c: any) => sum + parseFloat(c.total_value || 0), 0)
      .toFixed(2)

    const unbilledHours = timeEntriesData
      .filter((t: any) => t.is_billable && !t.invoiced)
      .reduce((sum: number, t: any) => sum + parseFloat(t.hours || 0), 0)
      .toFixed(2)

    const unpaidInvoices = invoicesData.filter((i: any) => i.status !== 'paid').length
    const totalReceivable = invoicesData
      .filter((i: any) => i.status !== 'paid')
      .reduce((sum: number, i: any) => {
        const total = parseFloat(i.total_amount || 0)
        const paid = parseFloat(i.amount_paid || 0)
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
