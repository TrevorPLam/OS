import React, { useState } from 'react'
import {
  Prospect,
  useCreateProspect,
  useDeleteProspect,
  usePipelineReport,
  useProspects,
  useUpdateProspect,
} from '../../api/crm'
import './CRM.css'

const Prospects: React.FC = () => {
  const [showForm, setShowForm] = useState(false)
  const [editingProspect, setEditingProspect] = useState<Prospect | null>(null)
  const [filterStage, setFilterStage] = useState<string>('all')
  const { data: prospects = [], isLoading } = useProspects()
  const { data: pipelineReport } = usePipelineReport()
  const createProspectMutation = useCreateProspect()
  const updateProspectMutation = useUpdateProspect()
  const deleteProspectMutation = useDeleteProspect()
  const [formData, setFormData] = useState<Partial<Prospect>>({
    company_name: '',
    industry: '',
    website: '',
    employee_count: 0,
    annual_revenue: '',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    primary_contact_title: '',
    pipeline_stage: 'discovery',
    probability: 10,
    estimated_value: '0',
    close_date_estimate: '',
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingProspect) {
        await updateProspectMutation.mutateAsync({ id: editingProspect.id, data: formData })
      } else {
        await createProspectMutation.mutateAsync(formData)
      }
      resetForm()
    } catch (error) {
      console.error('Failed to save prospect:', error)
    }
  }

  const handleEdit = (prospect: Prospect) => {
    setEditingProspect(prospect)
    setFormData(prospect)
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this prospect?')) {
      try {
        await deleteProspectMutation.mutateAsync(id)
      } catch (error) {
        console.error('Failed to delete prospect:', error)
      }
    }
  }

  const resetForm = () => {
    setFormData({
      company_name: '',
      industry: '',
      website: '',
      employee_count: 0,
      annual_revenue: '',
      primary_contact_name: '',
      primary_contact_email: '',
      primary_contact_phone: '',
      primary_contact_title: '',
      pipeline_stage: 'discovery',
      probability: 10,
      estimated_value: '0',
      close_date_estimate: '',
    })
    setEditingProspect(null)
    setShowForm(false)
  }

  const filteredProspects = prospects.filter((prospect) => {
    return filterStage === 'all' || prospect.pipeline_stage === filterStage
  })

  const getStageColor = (stage: string) => {
    const colors: { [key: string]: string } = {
      discovery: 'blue',
      qualification: 'purple',
      proposal: 'orange',
      negotiation: 'yellow',
      won: 'green',
      lost: 'red',
    }
    return colors[stage] || 'gray'
  }

  const getProbabilityColor = (probability: number) => {
    if (probability >= 75) return 'green'
    if (probability >= 50) return 'yellow'
    if (probability >= 25) return 'orange'
    return 'red'
  }

  if (isLoading) {
    return <div className="loading">Loading prospects...</div>
  }

  return (
    <div className="crm-page">
      <div className="page-header">
        <div>
          <h1>Prospects (Sales Pipeline)</h1>
          <p className="subtitle">Qualified sales opportunities</p>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary">
          + Add Prospect
        </button>
      </div>

      {pipelineReport && (
        <div className="pipeline-summary">
          <div className="summary-card">
            <h4>Total Prospects</h4>
            <p className="metric-value">{pipelineReport.total_prospects}</p>
          </div>
          <div className="summary-card">
            <h4>Pipeline Value</h4>
            <p className="metric-value">${parseFloat(pipelineReport.total_pipeline_value).toLocaleString()}</p>
          </div>
          {pipelineReport.pipeline.map((stage) => (
            <div key={stage.pipeline_stage} className="summary-card">
              <h4>{stage.pipeline_stage}</h4>
              <p className="metric-value">{stage.count}</p>
              <small>${parseFloat(stage.total_value || '0').toLocaleString()}</small>
            </div>
          ))}
        </div>
      )}

      <div className="filters">
        <div className="filter-group">
          <label>Pipeline Stage:</label>
          <select value={filterStage} onChange={(e) => setFilterStage(e.target.value)}>
            <option value="all">All Stages</option>
            <option value="discovery">Discovery</option>
            <option value="qualification">Qualification</option>
            <option value="proposal">Proposal</option>
            <option value="negotiation">Negotiation</option>
            <option value="won">Won</option>
            <option value="lost">Lost</option>
          </select>
        </div>
        <div className="stats">
          <span className="stat-badge">Showing: {filteredProspects.length}</span>
        </div>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content modal-large" onClick={(e) => e.stopPropagation()}>
            <h2>{editingProspect ? 'Edit Prospect' : 'New Prospect'}</h2>
            <form onSubmit={handleSubmit} className="crm-form">
              <h3>Company Information</h3>
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
                  <label>Website</label>
                  <input
                    type="url"
                    value={formData.website}
                    onChange={(e) => setFormData({ ...formData, website: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Employee Count</label>
                  <input
                    type="number"
                    value={formData.employee_count}
                    onChange={(e) => setFormData({ ...formData, employee_count: parseInt(e.target.value) || 0 })}
                  />
                </div>
              </div>

              <h3>Primary Contact</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>Contact Name *</label>
                  <input
                    type="text"
                    value={formData.primary_contact_name}
                    onChange={(e) => setFormData({ ...formData, primary_contact_name: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Contact Title</label>
                  <input
                    type="text"
                    value={formData.primary_contact_title}
                    onChange={(e) => setFormData({ ...formData, primary_contact_title: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Email *</label>
                  <input
                    type="email"
                    value={formData.primary_contact_email}
                    onChange={(e) => setFormData({ ...formData, primary_contact_email: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Phone</label>
                  <input
                    type="tel"
                    value={formData.primary_contact_phone}
                    onChange={(e) => setFormData({ ...formData, primary_contact_phone: e.target.value })}
                  />
                </div>
              </div>

              <h3>Opportunity Details</h3>
              <div className="form-row">
                <div className="form-group">
                  <label>Pipeline Stage *</label>
                  <select
                    value={formData.pipeline_stage}
                    onChange={(e) => setFormData({ ...formData, pipeline_stage: e.target.value })}
                    required
                  >
                    <option value="discovery">Discovery</option>
                    <option value="qualification">Qualification</option>
                    <option value="proposal">Proposal</option>
                    <option value="negotiation">Negotiation</option>
                    <option value="won">Won</option>
                    <option value="lost">Lost</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>Probability (%) *</label>
                  <input
                    type="number"
                    min="0"
                    max="100"
                    value={formData.probability}
                    onChange={(e) => setFormData({ ...formData, probability: parseInt(e.target.value) || 0 })}
                    required
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Estimated Value *</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.estimated_value}
                    onChange={(e) => setFormData({ ...formData, estimated_value: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Expected Close Date</label>
                  <input
                    type="date"
                    value={formData.close_date_estimate}
                    onChange={(e) => setFormData({ ...formData, close_date_estimate: e.target.value })}
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
                  {editingProspect ? 'Update' : 'Create'} Prospect
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="prospects-grid">
        {filteredProspects.map((prospect) => (
          <div key={prospect.id} className="prospect-card">
            <div className="card-header">
              <div>
                <h3>{prospect.company_name}</h3>
                <p className="contact-name">{prospect.primary_contact_name}</p>
              </div>
              <div className="card-badges">
                <span className={`status-badge status-${getStageColor(prospect.pipeline_stage)}`}>
                  {prospect.pipeline_stage}
                </span>
                <span className={`probability-badge prob-${getProbabilityColor(prospect.probability)}`}>
                  {prospect.probability}% prob
                </span>
              </div>
            </div>

            <div className="card-details">
              <p><strong>Value:</strong> ${parseFloat(prospect.estimated_value).toLocaleString()}</p>
              <p><strong>Email:</strong> {prospect.primary_contact_email}</p>
              {prospect.primary_contact_phone && <p><strong>Phone:</strong> {prospect.primary_contact_phone}</p>}
              {prospect.industry && <p><strong>Industry:</strong> {prospect.industry}</p>}
              {prospect.close_date_estimate && (
                <p><strong>Expected Close:</strong> {new Date(prospect.close_date_estimate).toLocaleDateString()}</p>
              )}
              {prospect.assigned_to_name && <p><strong>Assigned to:</strong> {prospect.assigned_to_name}</p>}
            </div>

            <div className="card-footer">
              <small>Created: {new Date(prospect.created_at).toLocaleDateString()}</small>
            </div>

            <div className="card-actions">
              <button onClick={() => handleEdit(prospect)} className="btn-small">
                Edit
              </button>
              <button onClick={() => handleDelete(prospect.id)} className="btn-small btn-danger">
                Delete
              </button>
            </div>
          </div>
        ))}

        {filteredProspects.length === 0 && (
          <div className="empty-state">
            <p>No prospects found. Add your first prospect to get started!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Prospects
