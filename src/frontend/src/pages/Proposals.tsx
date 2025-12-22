import React, { useState, useEffect } from 'react'
import { crmApi, Proposal, Prospect } from '../api/crm'
import { clientsApi, Client } from '../api/clients'
import './Proposals.css'

const Proposals: React.FC = () => {
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [prospects, setProspects] = useState<Prospect[]>([])
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingProposal, setEditingProposal] = useState<Proposal | null>(null)
  const [formData, setFormData] = useState<Partial<Proposal>>({
    proposal_type: 'prospective_client',
    prospect: undefined,
    client: undefined,
    proposal_number: '',
    title: '',
    description: '',
    status: 'draft',
    total_value: '',
    currency: 'USD',
    valid_until: '',
    estimated_start_date: '',
    estimated_end_date: '',
    auto_create_project: true,
    enable_portal_on_acceptance: true,
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [proposalsData, prospectsData, clientsData] = await Promise.all([
        crmApi.getProposals(),
        crmApi.getProspects(),
        clientsApi.getClients(),
      ])
      setProposals(proposalsData)
      setProspects(prospectsData)
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
      proposal_type: 'prospective_client',
      prospect: undefined,
      client: undefined,
      proposal_number: '',
      title: '',
      description: '',
      status: 'draft',
      total_value: '',
      currency: 'USD',
      valid_until: '',
      estimated_start_date: '',
      estimated_end_date: '',
      auto_create_project: true,
      enable_portal_on_acceptance: true,
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

  const getProposalTypeLabel = (type: string) => {
    const labels: { [key: string]: string } = {
      prospective_client: 'New Business',
      update_client: 'Expansion/Upsell',
      renewal_client: 'Renewal',
    }
    return labels[type] || type
  }

  const getProposalTypeColor = (type: string) => {
    const colors: { [key: string]: string } = {
      prospective_client: 'blue',
      update_client: 'purple',
      renewal_client: 'green',
    }
    return colors[type] || 'gray'
  }

  return (
    <div className="proposals-page">
      <div className="page-header">
        <div>
          <h1>Proposals</h1>
          <p className="subtitle">Pre-sale proposals for prospects and client engagement proposals</p>
        </div>
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
                  <label>Proposal Type *</label>
                  <select
                    value={formData.proposal_type}
                    onChange={(e) => setFormData({
                      ...formData,
                      proposal_type: e.target.value as any,
                      prospect: undefined,
                      client: undefined,
                    })}
                    required
                  >
                    <option value="prospective_client">New Business (Prospect)</option>
                    <option value="update_client">Expansion/Upsell (Existing Client)</option>
                    <option value="renewal_client">Renewal (Existing Client)</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                {formData.proposal_type === 'prospective_client' ? (
                  <div className="form-group">
                    <label>Prospect *</label>
                    <select
                      value={formData.prospect || ''}
                      onChange={(e) => setFormData({ ...formData, prospect: parseInt(e.target.value) || undefined })}
                      required
                    >
                      <option value="">Select a prospect</option>
                      {prospects.map((prospect) => (
                        <option key={prospect.id} value={prospect.id}>
                          {prospect.company_name}
                        </option>
                      ))}
                    </select>
                  </div>
                ) : (
                  <div className="form-group">
                    <label>Client *</label>
                    <select
                      value={formData.client || ''}
                      onChange={(e) => setFormData({ ...formData, client: parseInt(e.target.value) || undefined })}
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
                )}
                <div className="form-group">
                  <label>Status *</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    required
                  >
                    <option value="draft">Draft</option>
                    <option value="sent">Sent</option>
                    <option value="under_review">Under Review</option>
                    <option value="accepted">Accepted</option>
                    <option value="rejected">Rejected</option>
                    <option value="expired">Expired</option>
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
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Estimated Start Date</label>
                  <input
                    type="date"
                    value={formData.estimated_start_date}
                    onChange={(e) => setFormData({ ...formData, estimated_start_date: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Estimated End Date</label>
                  <input
                    type="date"
                    value={formData.estimated_end_date}
                    onChange={(e) => setFormData({ ...formData, estimated_end_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group checkbox-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.auto_create_project}
                      onChange={(e) => setFormData({ ...formData, auto_create_project: e.target.checked })}
                    />
                    Auto-create project on acceptance
                  </label>
                </div>
                <div className="form-group checkbox-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.enable_portal_on_acceptance}
                      onChange={(e) => setFormData({ ...formData, enable_portal_on_acceptance: e.target.checked })}
                    />
                    Enable portal on acceptance
                  </label>
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
              <div className="header-badges">
                <span className={`type-badge type-${getProposalTypeColor(proposal.proposal_type)}`}>
                  {getProposalTypeLabel(proposal.proposal_type)}
                </span>
                <span className={`status-badge status-${proposal.status}`}>
                  {proposal.status.replace('_', ' ')}
                </span>
                {proposal.converted_to_engagement && (
                  <span className="converted-badge">✓ Converted</span>
                )}
              </div>
            </div>
            <div className="proposal-details">
              {proposal.proposal_type === 'prospective_client' ? (
                <p><strong>Prospect:</strong> {proposal.prospect_name || `Prospect #${proposal.prospect}`}</p>
              ) : (
                <p><strong>Client:</strong> {proposal.client_name || `Client #${proposal.client}`}</p>
              )}
              <p><strong>Value:</strong> {proposal.currency} ${parseFloat(proposal.total_value).toLocaleString()}</p>
              <p><strong>Valid Until:</strong> {new Date(proposal.valid_until).toLocaleDateString()}</p>
              {proposal.estimated_start_date && (
                <p><strong>Start Date:</strong> {new Date(proposal.estimated_start_date).toLocaleDateString()}</p>
              )}
              <p className="proposal-description">{proposal.description}</p>
            </div>
            <div className="proposal-actions">
              {proposal.status === 'draft' && (
                <button
                  onClick={async () => {
                    try {
                      await crmApi.sendProposal(proposal.id)
                      loadData()
                    } catch (error) {
                      console.error('Failed to send proposal:', error)
                    }
                  }}
                  className="btn-small btn-success"
                >
                  Send
                </button>
              )}
              {proposal.status === 'sent' && !proposal.converted_to_engagement && (
                <button
                  onClick={async () => {
                    if (window.confirm('Accept this proposal and trigger client conversion?')) {
                      try {
                        await crmApi.acceptProposal(proposal.id)
                        loadData()
                        alert('Proposal accepted! Client conversion in progress.')
                      } catch (error) {
                        console.error('Failed to accept proposal:', error)
                        alert('Failed to accept proposal')
                      }
                    }
                  }}
                  className="btn-small btn-success"
                >
                  Accept
                </button>
              )}
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
