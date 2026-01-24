import React, { useState } from 'react'
import {
  Lead,
  useConvertLeadToProspect,
  useCreateLead,
  useDeleteLead,
  useLeads,
  useUpdateLead,
} from '../../api/crm'
import './CRM.css'

const Leads: React.FC = () => {
  const [showForm, setShowForm] = useState(false)
  const [editingLead, setEditingLead] = useState<Lead | null>(null)
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [filterSource, setFilterSource] = useState<string>('all')
  const { data: leads = [], isLoading, error: leadsError } = useLeads()
  const createLeadMutation = useCreateLead()
  const updateLeadMutation = useUpdateLead()
  const deleteLeadMutation = useDeleteLead()
  const convertLeadMutation = useConvertLeadToProspect()
  const [actionError, setActionError] = useState<string | null>(null)
  const [formData, setFormData] = useState<Partial<Lead>>({
    company_name: '',
    industry: '',
    website: '',
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    contact_title: '',
    source: 'website',
    status: 'new',
    lead_score: 0,
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingLead) {
        await updateLeadMutation.mutateAsync({ id: editingLead.id, data: formData })
      } else {
        await createLeadMutation.mutateAsync(formData)
      }
      resetForm()
      setActionError(null)
    } catch {
      setActionError('Unable to save the lead. Please try again.')
    }
  }

  const handleEdit = (lead: Lead) => {
    setEditingLead(lead)
    setFormData(lead)
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this lead?')) {
      try {
        await deleteLeadMutation.mutateAsync(id)
        setActionError(null)
      } catch {
        setActionError('Unable to delete the lead. Please try again.')
      }
    }
  }

  const handleConvertToProspect = async (lead: Lead) => {
    if (window.confirm(`Convert ${lead.company_name} to a prospect (sales opportunity)?`)) {
      try {
        const result = await convertLeadMutation.mutateAsync({ id: lead.id })
        alert(`Successfully converted to prospect! Prospect ID: ${result.prospect.id}`)
        setActionError(null)
      } catch {
        setActionError('Failed to convert lead to prospect. Please try again.')
      }
    }
  }

  const resetForm = () => {
    setFormData({
      company_name: '',
      industry: '',
      website: '',
      contact_name: '',
      contact_email: '',
      contact_phone: '',
      contact_title: '',
      source: 'website',
      status: 'new',
      lead_score: 0,
    })
    setEditingLead(null)
    setShowForm(false)
    setActionError(null)
  }

  const filteredLeads = leads.filter((lead) => {
    const statusMatch = filterStatus === 'all' || lead.status === filterStatus
    const sourceMatch = filterSource === 'all' || lead.source === filterSource
    return statusMatch && sourceMatch
  })

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      new: 'blue',
      contacted: 'purple',
      qualified: 'green',
      unqualified: 'red',
      converted: 'teal',
    }
    return colors[status] || 'gray'
  }

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'green'
    if (score >= 50) return 'yellow'
    if (score >= 20) return 'orange'
    return 'red'
  }

  if (isLoading) {
    return <div className="loading">Loading leads...</div>
  }

  if (leadsError) {
    return <div className="error">Unable to load leads. Please refresh and try again.</div>
  }

  return (
    <div className="crm-page">
      {actionError && <div className="error">{actionError}</div>}
      <div className="page-header">
        <div>
          <h1>Leads</h1>
          <p className="subtitle">Marketing-captured prospects before qualification</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary">
          + Add Lead
        </button>
      </div>

      <div className="filters">
        <div className="filter-group">
          <label>Status:</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="all">All Statuses</option>
            <option value="new">New</option>
            <option value="contacted">Contacted</option>
            <option value="qualified">Qualified</option>
            <option value="unqualified">Unqualified</option>
            <option value="converted">Converted</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Source:</label>
          <select value={filterSource} onChange={(e) => setFilterSource(e.target.value)}>
            <option value="all">All Sources</option>
            <option value="website">Website</option>
            <option value="referral">Referral</option>
            <option value="linkedin">LinkedIn</option>
            <option value="email_campaign">Email Campaign</option>
            <option value="event">Event</option>
            <option value="cold_outreach">Cold Outreach</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div className="stats">
          <span className="stat-badge">Total: {filteredLeads.length}</span>
          <span className="stat-badge">
            Qualified: {filteredLeads.filter((l) => l.status === 'qualified').length}
          </span>
        </div>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingLead ? 'Edit Lead' : 'New Lead'}</h2>
            <form onSubmit={handleSubmit} className="crm-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Company Name *</label>
                  <input
                    type="text"
                    value={formData.company_name}
                    onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Industry</label>
                  <input
                    type="text"
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Contact Name *</label>
                  <input
                    type="text"
                    value={formData.contact_name}
                    onChange={(e) => setFormData({ ...formData, contact_name: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Contact Title</label>
                  <input
                    type="text"
                    value={formData.contact_title}
                    onChange={(e) => setFormData({ ...formData, contact_title: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    value={formData.contact_email}
                    onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={formData.contact_phone}
                    onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Source *</label>
                  <select
                    value={formData.source}
                    onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                    required
                  >
                    <option value="website">Website</option>
                    <option value="referral">Referral</option>
                    <option value="linkedin">LinkedIn</option>
                    <option value="email_campaign">Email Campaign</option>
                    <option value="event">Event</option>
                    <option value="cold_outreach">Cold Outreach</option>
                    <option value="other">Other</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Status *</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    required
                  >
                    <option value="new">New</option>
                    <option value="contacted">Contacted</option>
                    <option value="qualified">Qualified</option>
                    <option value="unqualified">Unqualified</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Website</label>
                  <input
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Lead Score (0-100)</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.lead_score}
                    onChange={(e) => setFormData({ ...formData, lead_score: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="form-actions">
                <button type="button" onClick={resetForm} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingLead ? 'Update' : 'Create'} Lead
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="leads-grid">
        {filteredLeads.map((lead) => (
          <div key={lead.id} className="lead-card">
            <div className="card-header">
              <div>
                <h3>{lead.company_name}</h3>
                <p className="contact-name">{lead.contact_name}</p>
              </div>
              <div className="card-badges">
                <span className={`status-badge status-${getStatusColor(lead.status)}`}>
                  {lead.status}
                </span>
                <span className={`score-badge score-${getScoreColor(lead.lead_score)}`}>
                  Score: {lead.lead_score}
                </span>
              </div>
            </div>

            <div className="card-details">
              <p><strong>Email:</strong> {lead.contact_email}</p>
              {lead.contact_phone && <p><strong>Phone:</strong> {lead.contact_phone}</p>}
              {lead.contact_title && <p><strong>Title:</strong> {lead.contact_title}</p>}
              {lead.industry && <p><strong>Industry:</strong> {lead.industry}</p>}
              <p><strong>Source:</strong> {lead.source}</p>
              {lead.campaign_name && <p><strong>Campaign:</strong> {lead.campaign_name}</p>}
              {lead.assigned_to_name && <p><strong>Assigned to:</strong> {lead.assigned_to_name}</p>}
            </div>

            <div className="card-footer">
              <small>Captured: {new Date(lead.captured_date).toLocaleDateString()}</small>
            </div>

            <div className="card-actions">
              {lead.status !== 'converted' && (
                <button
                  onClick={() => handleConvertToProspect(lead)}
                  className="btn-small btn-success"
                  title="Convert to sales prospect"
                >
                  Convert to Prospect
                </button>
              )}
              <button onClick={() => handleEdit(lead)} className="btn-small">
                Edit
              </button>
              <button onClick={() => handleDelete(lead.id)} className="btn-small btn-danger">
                Delete
              </button>
            </div>
          </div>
        ))}

        {filteredLeads.length === 0 && (
          <div className="empty-state">
            <p>No leads found. Add your first lead to get started!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Leads
