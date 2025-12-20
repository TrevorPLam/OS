import React, { useState, useEffect } from 'react'
import { crmApi, Client } from '../api/crm'
import './Clients.css'

const Clients: React.FC = () => {
  const [clients, setClients] = useState<Client[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [editingClient, setEditingClient] = useState<Client | null>(null)
  const [formData, setFormData] = useState<Partial<Client>>({
    company_name: '',
    industry: '',
    status: 'lead',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    country: 'USA',
  })

  useEffect(() => {
    loadClients()
  }, [])

  const loadClients = async () => {
    try {
      const data = await crmApi.getClients()
      setClients(data)
    } catch (error) {
      console.error('Failed to load clients:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingClient) {
        await crmApi.updateClient(editingClient.id, formData)
      } else {
        await crmApi.createClient(formData)
      }
      loadClients()
      resetForm()
    } catch (error) {
      console.error('Failed to save client:', error)
    }
  }

  const handleEdit = (client: Client) => {
    setEditingClient(client)
    setFormData(client)
    setShowForm(true)
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this client?')) {
      try {
        await crmApi.deleteClient(id)
        loadClients()
      } catch (error) {
        console.error('Failed to delete client:', error)
      }
    }
  }

  const resetForm = () => {
    setFormData({
      company_name: '',
      industry: '',
      status: 'lead',
      primary_contact_name: '',
      primary_contact_email: '',
      primary_contact_phone: '',
      country: 'USA',
    })
    setEditingClient(null)
    setShowForm(false)
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="clients-page">
      <div className="page-header">
        <h1>Clients</h1>
        <button onClick={() => setShowForm(true)} className="btn-primary">
          + Add Client
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingClient ? 'Edit Client' : 'New Client'}</h2>
            <form onSubmit={handleSubmit} className="client-form">
              <div className="form-group">
                <label>Company Name *</label>
                <input
                  type="text"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Industry</label>
                  <input
                    type="text"
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label>Status *</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    required
                  >
                    <option value="lead">Lead</option>
                    <option value="prospect">Prospect</option>
                    <option value="active">Active Client</option>
                    <option value="inactive">Inactive</option>
                    <option value="lost">Lost</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label>Primary Contact Name *</label>
                <input
                  type="text"
                  value={formData.primary_contact_name}
                  onChange={(e) => setFormData({ ...formData, primary_contact_name: e.target.value })}
                  required
                />
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

              <div className="form-actions">
                <button type="button" onClick={resetForm} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  {editingClient ? 'Update' : 'Create'} Client
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="clients-grid">
        {clients.map((client) => (
          <div key={client.id} className="client-card">
            <div className="client-header">
              <h3>{client.company_name}</h3>
              <span className={`status-badge status-${client.status}`}>
                {client.status}
              </span>
            </div>
            <div className="client-details">
              <p><strong>Contact:</strong> {client.primary_contact_name}</p>
              <p><strong>Email:</strong> {client.primary_contact_email}</p>
              {client.industry && <p><strong>Industry:</strong> {client.industry}</p>}
            </div>
            <div className="client-actions">
              <button onClick={() => handleEdit(client)} className="btn-small">
                Edit
              </button>
              <button onClick={() => handleDelete(client.id)} className="btn-small btn-danger">
                Delete
              </button>
            </div>
          </div>
        ))}

        {clients.length === 0 && (
          <div className="empty-state">
            <p>No clients yet. Add your first client to get started!</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default Clients
