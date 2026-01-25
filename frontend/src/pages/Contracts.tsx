import React, { useMemo, useState } from 'react'
import { Contract, useContracts, useCreateContract, useDeleteContract, useProposals, useUpdateContract } from '../api/crm'
import { useClients } from '../api/clients'
import './Contracts.css'

const Contracts: React.FC = () => {
  const { data: contracts = [], isLoading: contractsLoading } = useContracts()
  const { data: clients = [], isLoading: clientsLoading } = useClients()
  const { data: proposals = [], isLoading: proposalsLoading } = useProposals()
  const createContractMutation = useCreateContract()
  const updateContractMutation = useUpdateContract()
  const deleteContractMutation = useDeleteContract()
  const [showForm, setShowForm] = useState(false)
  const [editingContract, setEditingContract] = useState<Contract | null>(null)
  const [formData, setFormData] = useState<Partial<Contract>>({
    client: 0,
    contract_number: '',
    title: '',
    description: '',
    status: 'draft',
    total_value: '',
    currency: 'USD',
    payment_terms: 'net_30',
    start_date: '',
    end_date: '',
  })

  const acceptedProposals = useMemo(
    () => proposals.filter((proposal) => proposal.status === 'accepted'),
    [proposals],
  )

  const generateContractNumber = () => {
    const date = new Date()
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0')
    return `CONT-${year}${month}-${random}`
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingContract) {
        await updateContractMutation.mutateAsync({ id: editingContract.id, data: formData })
      } else {
        await createContractMutation.mutateAsync(formData)
      }
      resetForm()
    } catch (error) {
      console.error('Failed to save contract:', error)
    }
  }

  const handleEdit = (contract: Contract) => {
    setEditingContract(contract)
    setFormData(contract)
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this contract?')) {
      try {
        await deleteContractMutation.mutateAsync(id)
      } catch (error) {
        console.error('Failed to delete contract:', error)
      }
    }
  }

  const resetForm = () => {
    setFormData({
      client: 0,
      contract_number: '',
      title: '',
      description: '',
      status: 'draft',
      total_value: '',
      currency: 'USD',
      payment_terms: 'net_30',
      start_date: '',
      end_date: '',
    })
    setEditingContract(null)
    setShowForm(false)
  }

  const handleNewContract = () => {
    setFormData({
      ...formData,
      contract_number: generateContractNumber(),
    })
    setShowForm(true)
  }

  if (contractsLoading || clientsLoading || proposalsLoading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="contracts-page">
      <div className="page-header">
        <h1>Contracts</h1>
        <button onClick={handleNewContract} className="btn-primary">
          + Create Contract
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <h2>{editingContract ? 'Edit Contract' : 'New Contract'}</h2>
            <form onSubmit={handleSubmit} className="contract-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Contract Number *</label>
                  <input
                    type="text"
                    value={formData.contract_number}
                    onChange={(e) => setFormData({ ...formData, contract_number: e.target.value })}
                    required
                    placeholder="CONT-202501-001"
                  />
                </div>
                <div className="form-group">
                  <label>Client *</label>
                  <select
                    value={formData.client}
                    onChange={(e) => setFormData({ ...formData, client: parseInt(e.target.value) })}
                    required
                  >
                    <option value="">Select a client</option>
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.company_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Related Proposal (Optional)</label>
                <select
                  value={formData.proposal || ''}
                  onChange={(e) => setFormData({ ...formData, proposal: e.target.value ? parseInt(e.target.value) : undefined })}
                >
                  <option value="">None</option>
                  {acceptedProposals.map((proposal) => (
                    <option key={proposal.id} value={proposal.id}>
                      {proposal.proposal_number} - {proposal.title}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-group">
                <label>Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  placeholder="e.g., Digital Transformation Project"
                />
              </div>

              <div className="form-group">
                <label>Description *</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  rows={5}
                  placeholder="Statement of work, deliverables, terms..."
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Total Value *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.total_value}
                    onChange={(e) => setFormData({ ...formData, total_value: e.target.value })}
                    required
                    placeholder="75000.00"
                  />
                </div>
                <div className="form-group">
                  <label>Currency *</label>
                  <select
                    value={formData.currency}
                    onChange={(e) => setFormData({ ...formData, currency: e.target.value })}
                    required
                  >
                    <option value="USD">USD</option>
                    <option value="EUR">EUR</option>
                    <option value="GBP">GBP</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Payment Terms *</label>
                  <select
                    value={formData.payment_terms}
                    onChange={(e) => setFormData({ ...formData, payment_terms: e.target.value })}
                    required
                  >
                    <option value="net_15">Net 15</option>
                    <option value="net_30">Net 30</option>
                    <option value="net_45">Net 45</option>
                    <option value="net_60">Net 60</option>
                    <option value="due_on_receipt">Due on Receipt</option>
                    <option value="milestone">Milestone-based</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Status *</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    required
                  >
                    <option value="draft">Draft</option>
                    <option value="active">Active</option>
                    <option value="completed">Completed</option>
                    <option value="terminated">Terminated</option>
                    <option value="on_hold">On Hold</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Start Date *</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>End Date *</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-actions">
                <button type="button" onClick={resetForm} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingContract ? 'Update' : 'Create'} Contract
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="contracts-list">
        {contracts.map((contract) => (
          <div key={contract.id} className="contract-card">
            <div className="contract-header">
              <div>
                <h3>{contract.title}</h3>
                <p className="contract-number">{contract.contract_number}</p>
              </div>
              <span className={`status-badge status-${contract.status}`}>
                {contract.status.replace('_', ' ')}
              </span>
            </div>
            <div className="contract-body">
              <div className="contract-details">
                <div className="detail-item">
                  <span className="detail-label">Client:</span>
                  <span className="detail-value">{contract.client_name || `Client #${contract.client}`}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Value:</span>
                  <span className="detail-value">{contract.currency} ${parseFloat(contract.total_value).toLocaleString()}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Payment Terms:</span>
                  <span className="detail-value">{contract.payment_terms.replace('_', ' ')}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Duration:</span>
                  <span className="detail-value">
                    {new Date(contract.start_date).toLocaleDateString()} - {new Date(contract.end_date).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <div className="contract-description">
                <p>{contract.description}</p>
              </div>
            </div>
            <div className="contract-actions">
              <button onClick={() => handleEdit(contract)} className="btn-small">
                Edit
              </button>
              <button onClick={() => handleDelete(contract.id)} className="btn-small btn-danger">
                Delete
              </button>
            </div>
          </div>
        ))}

        {contracts.length === 0 && (
          <div className="empty-state">
            <p>No contracts yet. Create your first contract!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Contracts
