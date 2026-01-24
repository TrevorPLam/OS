import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { useClients } from '../api/clients'
import { projectsApi, Project, ProjectCreate } from '../api/projects'
import './Projects.css'

const Projects: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([])
  const { data: clients = [], isLoading: clientsLoading } = useClients()
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingProject, setEditingProject] = useState<Project | null>(null)

  const [formData, setFormData] = useState<ProjectCreate>({
    client: 0,
    project_code: '',
    name: '',
    description: '',
    status: 'planning',
    billing_type: 'time_and_materials',
    budget: null,
    hourly_rate: null,
    start_date: '',
    end_date: '',
    notes: '',
  })

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      const [projectsData] = await Promise.all([
        projectsApi.getProjects(),
      ])
      setProjects(projectsData)
    } catch (error) {
      console.error('Error loading projects:', error)
    } finally {
      setLoading(false)
    }
  }

  const generateProjectCode = () => {
    const date = new Date()
    const year = date.getFullYear()
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const random = Math.floor(Math.random() * 1000)
      .toString()
      .padStart(3, '0')
    return `PROJ-${year}${month}-${random}`
  }

  const openModal = (project?: Project) => {
    if (project) {
      setEditingProject(project)
      setFormData({
        client: project.client,
        project_code: project.project_code,
        name: project.name,
        description: project.description,
        status: project.status,
        billing_type: project.billing_type,
        budget: project.budget,
        hourly_rate: project.hourly_rate,
        start_date: project.start_date,
        end_date: project.end_date,
        notes: project.notes,
      })
    } else {
      setEditingProject(null)
      setFormData({
        client: clients.length > 0 ? clients[0].id : 0,
        project_code: generateProjectCode(),
        name: '',
        description: '',
        status: 'planning',
        billing_type: 'time_and_materials',
        budget: null,
        hourly_rate: null,
        start_date: '',
        end_date: '',
        notes: '',
      })
    }
    setShowModal(true)
  }

  const resetForm = () => {
    setShowModal(false)
    setEditingProject(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingProject) {
        await projectsApi.updateProject(editingProject.id, formData)
      } else {
        await projectsApi.createProject(formData)
      }
      await loadData()
      resetForm()
    } catch (error) {
      console.error('Error saving project:', error)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return
    try {
      await projectsApi.deleteProject(id)
      await loadData()
    } catch (error) {
      console.error('Error deleting project:', error)
    }
  }

  const getClientName = (clientId: number) => {
    const client = clients.find((c) => c.id === clientId)
    return client ? client.company_name : 'Unknown'
  }

  if (loading || clientsLoading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="projects-page">
      <div className="page-header">
        <h1>Projects</h1>
        <button onClick={() => openModal()} className="btn btn-primary">
          + New Project
        </button>
      </div>

      <div className="projects-grid">
        {projects.map((project) => (
          <div key={project.id} className="project-card">
            <div className="project-card-header">
              <div>
                <h3>{project.name}</h3>
                <p className="project-code">{project.project_code}</p>
              </div>
              <span className={`badge status-${project.status}`}>
                {project.status.replace('_', ' ')}
              </span>
            </div>

            <div className="project-card-body">
              <div className="project-info">
                <span className="info-label">Client</span>
                <span className="info-value">{getClientName(project.client)}</span>
              </div>

              <div className="project-info">
                <span className="info-label">Billing</span>
                <span className="info-value">{project.billing_type.replace('_', ' ')}</span>
              </div>

              <div className="project-info">
                <span className="info-label">Timeline</span>
                <span className="info-value">
                  {new Date(project.start_date).toLocaleDateString()} -{' '}
                  {new Date(project.end_date).toLocaleDateString()}
                </span>
              </div>

              {project.budget && (
                <div className="project-info">
                  <span className="info-label">Budget</span>
                  <span className="info-value">${parseFloat(project.budget).toLocaleString()}</span>
                </div>
              )}
            </div>

            <div className="project-card-actions">
              <Link to={`/projects/${project.id}/kanban`} className="btn btn-primary btn-sm">
                📋 Kanban Board
              </Link>
              <button onClick={() => openModal(project)} className="btn btn-secondary btn-sm">
                Edit
              </button>
              <button onClick={() => handleDelete(project.id)} className="btn btn-danger btn-sm">
                Delete
              </button>
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal modal-lg" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingProject ? 'Edit Project' : 'Create Project'}</h2>
              <button className="modal-close" onClick={resetForm}>
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="project-form">
              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="project_code">Project Code *</label>
                  <input
                    id="project_code"
                    type="text"
                    value={formData.project_code}
                    onChange={(e) => setFormData({ ...formData, project_code: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="client">Client *</label>
                  <select
                    id="client"
                    value={formData.client}
                    onChange={(e) => setFormData({ ...formData, client: parseInt(e.target.value) })}
                    required
                  >
                    {clients.map((client) => (
                      <option key={client.id} value={client.id}>
                        {client.company_name}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="name">Project Name *</label>
                <input
                  id="name"
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label htmlFor="description">Description</label>
                <textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="status">Status</label>
                  <select
                    id="status"
                    value={formData.status}
                    onChange={(e) =>
                      setFormData({ ...formData, status: e.target.value as Project['status'] })
                    }
                  >
                    <option value="planning">Planning</option>
                    <option value="in_progress">In Progress</option>
                    <option value="on_hold">On Hold</option>
                    <option value="completed">Completed</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="billing_type">Billing Type</label>
                  <select
                    id="billing_type"
                    value={formData.billing_type}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        billing_type: e.target.value as Project['billing_type'],
                      })
                    }
                  >
                    <option value="fixed_price">Fixed Price</option>
                    <option value="time_and_materials">Time & Materials</option>
                    <option value="retainer">Retainer</option>
                    <option value="non_billable">Non-Billable</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="budget">Budget</label>
                  <input
                    id="budget"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.budget || ''}
                    onChange={(e) => setFormData({ ...formData, budget: e.target.value || null })}
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="hourly_rate">Hourly Rate</label>
                  <input
                    id="hourly_rate"
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.hourly_rate || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, hourly_rate: e.target.value || null })
                    }
                  />
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="start_date">Start Date *</label>
                  <input
                    id="start_date"
                    type="date"
                    value={formData.start_date}
                    onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                    required
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="end_date">End Date *</label>
                  <input
                    id="end_date"
                    type="date"
                    value={formData.end_date}
                    onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="notes">Notes</label>
                <textarea
                  id="notes"
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="modal-actions">
                <button type="button" onClick={resetForm} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingProject ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default Projects
