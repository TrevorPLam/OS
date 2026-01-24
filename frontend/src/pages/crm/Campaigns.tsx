import React, { useState } from 'react'
import {
  Campaign,
  useCampaignPerformance,
  useCampaigns,
  useCreateCampaign,
  useDeleteCampaign,
  useUpdateCampaign,
} from '../../api/crm'
import './CRM.css'

const Campaigns: React.FC = () => {
  const [showForm, setShowForm] = useState(false)
  const [editingCampaign, setEditingCampaign] = useState<Campaign | null>(null)
  const [filterType, setFilterType] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [selectedCampaign, setSelectedCampaign] = useState<number | null>(null)
  const { data: campaigns = [], isLoading } = useCampaigns()
  const { data: performanceData } = useCampaignPerformance(selectedCampaign ?? undefined)
  const createCampaignMutation = useCreateCampaign()
  const updateCampaignMutation = useUpdateCampaign()
  const deleteCampaignMutation = useDeleteCampaign()
  const [formData, setFormData] = useState<Partial<Campaign>>({
    name: '',
    description: '',
    type: 'email',
    status: 'planning',
    start_date: '',
    end_date: '',
    budget: '0',
    actual_cost: '0',
    target_leads: 0,
  })

  const loadPerformance = (id: number) => {
    setSelectedCampaign(id)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingCampaign) {
        await updateCampaignMutation.mutateAsync({ id: editingCampaign.id, data: formData })
      } else {
        await createCampaignMutation.mutateAsync(formData)
      }
      resetForm()
    } catch (error) {
      console.error('Failed to save campaign:', error)
    }
  }

  const handleEdit = (campaign: Campaign) => {
    setEditingCampaign(campaign)
    setFormData(campaign)
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this campaign?')) {
      try {
        await deleteCampaignMutation.mutateAsync(id)
      } catch (error) {
        console.error('Failed to delete campaign:', error)
      }
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      description: '',
      type: 'email',
      status: 'planning',
      start_date: '',
      end_date: '',
      budget: '0',
      actual_cost: '0',
      target_leads: 0,
    })
    setEditingCampaign(null)
    setShowForm(false)
  }

  const filteredCampaigns = campaigns.filter((campaign) => {
    const typeMatch = filterType === 'all' || campaign.type === filterType
    const statusMatch = filterStatus === 'all' || campaign.status === filterStatus
    return typeMatch && statusMatch
  })

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      planning: 'blue',
      active: 'green',
      paused: 'yellow',
      completed: 'gray',
      cancelled: 'red',
    }
    return colors[status] || 'gray'
  }

  const getTypeIcon = (type: string) => {
    const icons: { [key: string]: string } = {
      email: '📧',
      webinar: '🎥',
      content: '📄',
      event: '🎫',
      social: '📱',
      partnership: '🤝',
      renewal: '🔄',
      annual_review: '📊',
      other: '📌',
    }
    return icons[type] || '📌'
  }

  if (isLoading) {
    return <div className="loading">Loading campaigns...</div>
  }

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1>Campaigns</h1>
          <p className="subtitle">Marketing & sales campaigns for lead generation and client engagement</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary">
          + Add Campaign
        </button>
      </div>

      <div className="filters">
        <div className="filter-group">
          <label>Type:</label>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
            <option value="all">All Types</option>
            <option value="email">Email Campaign</option>
            <option value="webinar">Webinar</option>
            <option value="content">Content Marketing</option>
            <option value="event">Event/Conference</option>
            <option value="social">Social Media</option>
            <option value="partnership">Partnership</option>
            <option value="renewal">Renewal Campaign</option>
            <option value="annual_review">Annual Review</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div className="filter-group">
          <label>Status:</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="all">All Statuses</option>
            <option value="planning">Planning</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="completed">Completed</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <div className="stats">
          <span className="stat-badge">Total: {filteredCampaigns.length}</span>
          <span className="stat-badge">
            Active: {filteredCampaigns.filter((c) => c.status === 'active').length}
          </span>
        </div>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <h2>{editingCampaign ? 'Edit Campaign' : 'New Campaign'}</h2>
            <form onSubmit={handleSubmit} className="crm-form">
              <div className="form-row">
                <div className="form-group">
                  <label>Campaign Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Description</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Campaign Type *</label>
                  <select
                    value={formData.type}
                    onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                    required
                  >
                    <option value="email">Email Campaign</option>
                    <option value="webinar">Webinar</option>
                    <option value="content">Content Marketing</option>
                    <option value="event">Event/Conference</option>
                    <option value="social">Social Media</option>
                    <option value="partnership">Partnership</option>
                    <option value="renewal">Renewal Campaign</option>
                    <option value="annual_review">Annual Review</option>
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
                    <option value="planning">Planning</option>
                    <option value="active">Active</option>
                    <option value="paused">Paused</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Start Date</label>
                  <input
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>End Date</label>
                  <input
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Budget</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.budget}
                    onChange={(e) => setFormData({ ...formData, budget: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Actual Cost</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.actual_cost}
                    onChange={(e) => setFormData({ ...formData, actual_cost: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Target Leads</label>
                <input
                  type="number"
                  value={formData.target_leads}
                  onChange={(e) => setFormData({ ...formData, target_leads: parseInt(e.target.value) || 0 })}
                />
              </div>

              <div className="form-actions">
                <button type="button" onClick={resetForm} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingCampaign ? 'Update' : 'Create'} Campaign
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {performanceData && selectedCampaign && (
        <div className="modal-overlay" onClick={() => setSelectedCampaign(null)}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <h2>Campaign Performance: {performanceData.campaign.name}</h2>

            <div className="performance-grid">
              <div className="metric-card">
                <h4>ROI</h4>
                <p className="metric-value">{performanceData.metrics.roi.toFixed(2)}%</p>
              </div>
              <div className="metric-card">
                <h4>Cost per Lead</h4>
                <p className="metric-value">${performanceData.metrics.cost_per_lead.toFixed(2)}</p>
              </div>
              <div className="metric-card">
                <h4>Conversion Rate</h4>
                <p className="metric-value">{performanceData.metrics.conversion_rate.toFixed(2)}%</p>
              </div>
            </div>

            <div className="performance-details">
              <h3>Lead Generation</h3>
              <div className="detail-row">
                <span>Target Leads:</span>
                <span>{performanceData.campaign.target_leads}</span>
              </div>
              <div className="detail-row">
                <span>Leads Generated:</span>
                <span>{performanceData.campaign.leads_generated}</span>
              </div>
              <div className="detail-row">
                <span>Opportunities Created:</span>
                <span>{performanceData.campaign.opportunities_created}</span>
              </div>

              <h3>Client Engagement</h3>
              <div className="detail-row">
                <span>Clients Contacted:</span>
                <span>{performanceData.campaign.clients_contacted}</span>
              </div>
              <div className="detail-row">
                <span>Renewal Proposals Sent:</span>
                <span>{performanceData.campaign.renewal_proposals_sent}</span>
              </div>
              <div className="detail-row">
                <span>Renewals Won:</span>
                <span>{performanceData.campaign.renewals_won}</span>
              </div>

              <h3>Financial</h3>
              <div className="detail-row">
                <span>Budget:</span>
                <span>${parseFloat(performanceData.campaign.budget).toLocaleString()}</span>
              </div>
              <div className="detail-row">
                <span>Actual Cost:</span>
                <span>${parseFloat(performanceData.campaign.actual_cost).toLocaleString()}</span>
              </div>
              <div className="detail-row">
                <span>Revenue Generated:</span>
                <span>${parseFloat(performanceData.campaign.revenue_generated).toLocaleString()}</span>
              </div>
            </div>

            <div className="form-actions">
              <button onClick={() => setSelectedCampaign(null)} className="btn-primary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="campaigns-grid">
        {filteredCampaigns.map((campaign) => (
          <div key={campaign.id} className="campaign-card">
            <div className="card-header">
              <div>
                <h3>
                  {getTypeIcon(campaign.type)} {campaign.name}
                </h3>
                <p className="campaign-type">{campaign.type}</p>
              </div>
              <span className={`status-badge status-${getStatusColor(campaign.status)}`}>
                {campaign.status}
              </span>
            </div>

            {campaign.description && (
              <div className="campaign-description">
                <p>{campaign.description}</p>
              </div>
            )}

            <div className="campaign-metrics">
              <div className="metric-row">
                <div className="metric-item">
                  <strong>Leads Generated</strong>
                  <span>{campaign.leads_generated}/{campaign.target_leads}</span>
                </div>
                <div className="metric-item">
                  <strong>Opportunities</strong>
                  <span>{campaign.opportunities_created}</span>
                </div>
              </div>
              <div className="metric-row">
                <div className="metric-item">
                  <strong>Clients Contacted</strong>
                  <span>{campaign.clients_contacted}</span>
                </div>
                <div className="metric-item">
                  <strong>Renewals Won</strong>
                  <span>{campaign.renewals_won}</span>
                </div>
              </div>
              <div className="metric-row">
                <div className="metric-item">
                  <strong>Budget</strong>
                  <span>${parseFloat(campaign.budget).toLocaleString()}</span>
                </div>
                <div className="metric-item">
                  <strong>Revenue</strong>
                  <span>${parseFloat(campaign.revenue_generated).toLocaleString()}</span>
                </div>
              </div>
            </div>

            {campaign.start_date && (
              <div className="card-footer">
                <small>
                  {new Date(campaign.start_date).toLocaleDateString()}
                  {campaign.end_date && ` - ${new Date(campaign.end_date).toLocaleDateString()}`}
                </small>
              </div>
            )}

            <div className="card-actions">
              <button onClick={() => loadPerformance(campaign.id)} className="btn-small btn-success">
                View Performance
              </button>
              <button onClick={() => handleEdit(campaign)} className="btn-small">
                Edit
              </button>
              <button onClick={() => handleDelete(campaign.id)} className="btn-small btn-danger">
                Delete
              </button>
            </div>
          </div>
        ))}

        {filteredCampaigns.length === 0 && (
          <div className="empty-state">
            <p>No campaigns found. Create your first campaign to get started!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Campaigns
