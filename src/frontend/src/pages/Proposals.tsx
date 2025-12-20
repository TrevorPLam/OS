import React, { useState, useEffect } from 'react'
import { crmApi, Proposal, Client } from '../api/crm'
import './Proposals.css'

const Proposals: React.FC = () => {
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingProposal, setEditingProposal] = useState<Proposal | null>(null)
  const [formData, setFormData] = useState<Partial<Proposal>>({
    client: 0,
    proposal_number: '',
    title: '',
    description: '',
    status: 'draft',
    total_value: '',
    currency: 'USD',
    valid_until: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [proposalsData, clientsData] = await Promise.all([
        crmApi.getProposals(),
        crmApi.getClients(),
      ])
      setProposals(proposalsData)
      setClients(clientsData)
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateProposalNumber = () => {
    const date = new Date()
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0')
    return `PROP-${year}${month}-${random}`
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingProposal) {
        await crmApi.updateProposal(editingProposal.id, formData)
      } else {
        await crmApi.createProposal(formData)
      }
      loadData()
      resetForm()
    } catch (error) {
      console.error('Failed to save proposal:', error)
    }
  }

  const handleEdit = (proposal: Proposal) => {
    setEditingProposal(proposal)
    setFormData(proposal)
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this proposal?')) {
      try {
        await crmApi.deleteProposal(id)
        loadData()
      } catch (error) {
        console.error('Failed to delete proposal:', error)
      }
    }
  }

  const resetForm = () => {
    setFormData({
      client: 0,
      proposal_number: '',
      title: '',
      description: '',
      status: 'draft',
      total_value: '',
      currency: 'USD',
      valid_until: '',
    })
    setEditingProposal(null)
    setShowForm(false)
  }

  const handleNewProposal = () => {
    setFormData({
      ...formData,
      proposal_number: generateProposalNumber(),
    })
    setShowForm(true)
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="proposals-page">
      <div className="page-header">
        <h1>Proposals</h1>
        <button onClick={handleNewProposal} className="btn-primary">
          + Create Proposal
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <h2>{editingProposal ? 'Edit Proposal' : 'New Proposal'}</h2>
            <form onSubmit={handleSubmit} className="proposal-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Proposal Number *</label>
                  <input
                    type="text"
                    value={formData.proposal_number}
                    onChange={(e) => setFormData({ ...formData, proposal_number: e.target.value })}
                    required
                    placeholder="PROP-202501-001"
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
                <label>Title *</label>
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  placeholder="e.g., Digital Transformation Consulting"
                />
              </div>

              <div className="form-group">
                <label>Description *</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  rows={5}
                  placeholder="Scope of work, deliverables, timeline..."
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
                    placeholder="50000.00"
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
                  <label>Valid Until *</label>
                  <input
                    type="date"
                    value={formData.valid_until}
                    onChange={(e) => setFormData({ ...formData, valid_until: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Status *</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    required
                  >
                    <option value="draft">Draft</option>
                    <option value="sent">Sent to Client</option>
                    <option value="under_review">Under Review</option>
                    <option value="accepted">Accepted</option>
                    <option value="rejected">Rejected</option>
                    <option value="expired">Expired</option>
                  </select>
                </div>
              </div>

              <div className="form-actions">
                <button type="button" onClick={resetForm} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingProposal ? 'Update' : 'Create'} Proposal
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="proposals-grid">
        {proposals.map((proposal) => (
          <div key={proposal.id} className="proposal-card">
            <div className="proposal-header">
              <div>
                <h3>{proposal.title}</h3>
                <p className="proposal-number">{proposal.proposal_number}</p>
              </div>
              <span className={`status-badge status-${proposal.status}`}>
                {proposal.status.replace('_', ' ')}
              </span>
            </div>
            <div className="proposal-details">
              <p><strong>Client:</strong> {proposal.client_name || `Client #${proposal.client}`}</p>
              <p><strong>Value:</strong> {proposal.currency} ${parseFloat(proposal.total_value).toLocaleString()}</p>
              <p><strong>Valid Until:</strong> {new Date(proposal.valid_until).toLocaleDateString()}</p>
              <p className="proposal-description">{proposal.description}</p>
            </div>
            <div className="proposal-actions">
              <button onClick={() => handleEdit(proposal)} className="btn-small">
                Edit
              </button>
              <button onClick={() => handleDelete(proposal.id)} className="btn-small btn-danger">
                Delete
              </button>
            </div>
          </div>
        ))}

        {proposals.length === 0 && (
          <div className="empty-state">
            <p>No proposals yet. Create your first proposal!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Proposals
