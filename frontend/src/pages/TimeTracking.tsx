import React, { useCallback, useEffect, useState } from 'react'
import { timeTrackingApi, TimeEntry, Project } from '../api/timeTracking'
import './TimeTracking.css'

const TimeTracking: React.FC = () => {
  const [timeEntries, setTimeEntries] = useState<TimeEntry[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  const [formData, setFormData] = useState<Partial<TimeEntry>>({
    project: 0,
    date: new Date().toISOString().split('T')[0],
    hours: '',
    description: '',
    is_billable: true,
    hourly_rate: '150.00',
  })

  const loadData = useCallback(async () => {
    try {
      const [entries, projectsList] = await Promise.all([
        timeTrackingApi.getTimeEntries(),
        timeTrackingApi.getProjects(),
      ])
      setTimeEntries(entries)
      setProjects(projectsList)

      // Set default hourly rate from first project if available
      if (projectsList.length > 0) {
        setFormData((prev) => {
          if (prev.project) return prev
          return {
            ...prev,
            project: projectsList[0].id,
            hourly_rate: projectsList[0].hourly_rate || '150.00',
          }
        })
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await timeTrackingApi.createTimeEntry(formData)
      loadData()
      resetForm()
    } catch (error) {
      console.error('Failed to save time entry:', error)
    }
  }

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this time entry?')) {
      try {
        await timeTrackingApi.deleteTimeEntry(id)
        loadData()
      } catch (error) {
        console.error('Failed to delete time entry:', error)
      }
    }
  }

  const resetForm = () => {
    setFormData({
      project: projects.length > 0 ? projects[0].id : 0,
      date: new Date().toISOString().split('T')[0],
      hours: '',
      description: '',
      is_billable: true,
      hourly_rate: projects.length > 0 ? projects[0].hourly_rate || '150.00' : '150.00',
    })
    setShowForm(false)
  }

  const calculateTotal = () => {
    return timeEntries
      .filter((entry) => entry.is_billable)
      .reduce((sum, entry) => sum + parseFloat(entry.billed_amount || '0'), 0)
      .toFixed(2)
  }

  const calculateTotalHours = () => {
    return timeEntries
      .reduce((sum, entry) => sum + parseFloat(entry.hours || '0'), 0)
      .toFixed(2)
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="time-tracking-page">
      <div className="page-header">
        <div>
          <h1>Time Tracking</h1>
          <div className="stats">
            <div className="stat">
              <span className="stat-label">Total Hours:</span>
              <span className="stat-value">{calculateTotalHours()}h</span>
            </div>
            <div className="stat">
              <span className="stat-label">Billable Amount:</span>
              <span className="stat-value">${calculateTotal()}</span>
            </div>
          </div>
        </div>
        <button onClick={() => setShowForm(true)} className="btn-primary">
          + Log Time
        </button>
      </div>

      {showForm && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Log Time Entry</h2>
            <form onSubmit={handleSubmit} className="time-form">
              <div className="form-group">
                <label>Project *</label>
                <select
                  value={formData.project}
                  onChange={(e) => {
                    const projectId = parseInt(e.target.value)
                    const project = projects.find((p) => p.id === projectId)
                    setFormData({
                      ...formData,
                      project: projectId,
                      hourly_rate: project?.hourly_rate || '150.00',
                    })
                  }}
                  required
                >
                  <option value="">Select a project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      [{project.project_code}] {project.name}
                    </option>
                  ))}
                </select>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Date *</label>
                  <input
                    type="date"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>Hours *</label>
                  <input
                    type="number"
                    step="0.25"
                    min="0.25"
                    value={formData.hours}
                    onChange={(e) => setFormData({ ...formData, hours: e.target.value })}
                    required
                    placeholder="1.5"
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Description *</label>
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  required
                  rows={3}
                  placeholder="What did you work on?"
                />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Hourly Rate *</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    value={formData.hourly_rate}
                    onChange={(e) => setFormData({ ...formData, hourly_rate: e.target.value })}
                    required
                  />
                </div>
                <div className="form-group">
                  <label>
                    <input
                      type="checkbox"
                      checked={formData.is_billable}
                      onChange={(e) => setFormData({ ...formData, is_billable: e.target.checked })}
                    />{' '}
                    Billable
                  </label>
                </div>
              </div>

              <div className="form-actions">
                <button type="button" onClick={resetForm} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Log Time
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="time-entries">
        {timeEntries.length === 0 ? (
          <div className="empty-state">
            <p>No time entries yet. Log your first time entry!</p>
          </div>
        ) : (
          <table className="time-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Project</th>
                <th>Description</th>
                <th>Hours</th>
                <th>Rate</th>
                <th>Amount</th>
                <th>Billable</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {timeEntries.map((entry) => (
                <tr key={entry.id}>
                  <td>{new Date(entry.date).toLocaleDateString()}</td>
                  <td>{entry.project_name || `Project #${entry.project}`}</td>
                  <td>{entry.description}</td>
                  <td>{entry.hours}h</td>
                  <td>${entry.hourly_rate}</td>
                  <td>${entry.billed_amount}</td>
                  <td>
                    <span className={`badge ${entry.is_billable ? 'badge-yes' : 'badge-no'}`}>
                      {entry.is_billable ? 'Yes' : 'No'}
                    </span>
                  </td>
                  <td>
                    <button onClick={() => handleDelete(entry.id)} className="btn-small btn-danger">
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

export default TimeTracking
