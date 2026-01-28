import React, { useState } from 'react'
import { Client, useClients, useCreateClient, useDeleteClient, useUpdateClient } from '../api/clients'
import { useConfirmDialog } from '../components/ConfirmDialog'
import ErrorDisplay from '../components/ErrorDisplay'
import './Clients.css'

const getErrorMessage = (error: unknown, fallback: string) => {
  if (!error) {
    return ''
  }

  if (error instanceof Error && error.message) {
    return error.message
  }

  if (typeof error === 'string') {
    return error
  }

  return fallback
}

const Clients: React.FC = () => {
  const { data: clients = [], isLoading, error: clientsError } = useClients()
  const createClientMutation = useCreateClient()
  const updateClientMutation = useUpdateClient()
  const deleteClientMutation = useDeleteClient()
  const [showForm, setShowForm] = useState(false)
  const [editingClient, setEditingClient] = useState<Client | null>(null)
  const [clientToDelete, setClientToDelete] = useState<number | null>(null)
  const [formData, setFormData] = useState<Partial<Client>>({
    company_name: '',
    industry: '',
    status: 'active',
    primary_contact_name: '',
    primary_contact_email: '',
    primary_contact_phone: '',
    country: 'USA',
    portal_enabled: false,
    assigned_team: [],
  })

  const deleteDialog = useConfirmDialog({
    title: 'Delete Client',
    message: 'Are you sure you want to delete this client? This action cannot be undone.',
    variant: 'danger',
    confirmText: 'Delete',
    onConfirm: async () => {
      if (clientToDelete === null) return
      deleteClientMutation.reset()
      await deleteClientMutation.mutateAsync(clientToDelete)
      setClientToDelete(null)
    },
  })

  const clearMutationErrors = () => {
    createClientMutation.reset()
    updateClientMutation.reset()
    deleteClientMutation.reset()
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    clearMutationErrors()

    if (editingClient) {
      updateClientMutation.mutate(
        { id: editingClient.id, data: formData },
        { onSuccess: resetForm }
      )
      return
    }

    createClientMutation.mutate(formData, { onSuccess: resetForm })
  }

  const handleEdit = (client: Client) => {
    clearMutationErrors()
    setEditingClient(client)
    setFormData(client)
    setShowForm(true)
  }

  const handleDelete = (id: number) => {
    setClientToDelete(id)
    deleteDialog.show()
  }

  const resetForm = () => {
    clearMutationErrors()
    setFormData({
      company_name: '',
      industry: '',
      status: 'active',
      primary_contact_name: '',
      primary_contact_email: '',
      primary_contact_phone: '',
      country: 'USA',
      portal_enabled: false,
      assigned_team: [],
    })
    setEditingClient(null)
    setShowForm(false)
  }

  const clientLoadError = getErrorMessage(clientsError, 'Unable to load clients. Please try again.')
  const clientMutationError = getErrorMessage(
    createClientMutation.error ?? updateClientMutation.error ?? deleteClientMutation.error,
    'Unable to save client changes. Please try again.'
  )
  const isSaving = createClientMutation.isPending || updateClientMutation.isPending

  if (isLoading) {
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

      {clientLoadError && (
        <ErrorDisplay
          error={clientLoadError}
          variant="banner"
        />
      )}

      {showForm && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingClient ? 'Edit Client' : 'New Client'}</h2>
            {clientMutationError && (
              <ErrorDisplay
                error={clientMutationError}
                variant="inline"
              />
            )}
            <form onSubmit={handleSubmit} className="client-form">
              <div className="form-group">
                <label htmlFor="client-company-name">Company Name *</label>
                <input
                  type="text"
                  id="client-company-name"
                  value={formData.company_name}
                  onChange={(e) => setFormData({ ...formData, company_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="client-industry">Industry</label>
                  <input
                    type="text"
                    id="client-industry"
                    value={formData.industry}
                    onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="client-status">Status *</label>
                  <select
                    id="client-status"
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    required
                  >
                    <option value="active">Active</option>
                    <option value="at_risk">At Risk</option>
                    <option value="inactive">Inactive</option>
                    <option value="churned">Churned</option>
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="client-primary-contact-name">Primary Contact Name *</label>
                <input
                  type="text"
                  id="client-primary-contact-name"
                  value={formData.primary_contact_name}
                  onChange={(e) => setFormData({ ...formData, primary_contact_name: e.target.value })}
                  required
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="client-primary-email">Email *</label>
                  <input
                    type="email"
                    id="client-primary-email"
                    value={formData.primary_contact_email}
                    onChange={(e) => setFormData({ ...formData, primary_contact_email: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label htmlFor="client-primary-phone">Phone</label>
                  <input
                    type="tel"
                    id="client-primary-phone"
                    value={formData.primary_contact_phone}
                    onChange={(e) => setFormData({ ...formData, primary_contact_phone: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-actions">
                <button type="button" onClick={resetForm} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={isSaving}>
                  {isSaving ? 'Saving...' : `${editingClient ? 'Update' : 'Create'} Client`}
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

      <deleteDialog.ConfirmDialog />
    </div>
  )
}

export default Clients
