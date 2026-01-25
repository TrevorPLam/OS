import React, { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { tasksApi, Task, TaskCreate } from '../api/tasks'
import { projectsApi } from '../api/projects'
import './ProjectKanban.css'

interface Project {
  id: number
  project_code: string
  name: string
}

const ProjectKanban: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>()
  const [project, setProject] = useState<Project | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [editingTask, setEditingTask] = useState<Task | null>(null)
  const [draggedTask, setDraggedTask] = useState<Task | null>(null)

  const [formData, setFormData] = useState<TaskCreate>({
    project: parseInt(projectId || '0'),
    title: '',
    description: '',
    status: 'todo',
    priority: 'medium',
    assigned_to: null,
    estimated_hours: null,
    due_date: null,
  })

  const columns: { id: Task['status']; title: string; color: string }[] = [
    { id: 'todo', title: 'To Do', color: '#718096' },
    { id: 'in_progress', title: 'In Progress', color: '#4299e1' },
    { id: 'blocked', title: 'Blocked', color: '#f56565' },
    { id: 'review', title: 'In Review', color: '#ed8936' },
    { id: 'done', title: 'Done', color: '#48bb78' },
  ]

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      const [projectData, tasksData] = await Promise.all([
        projectsApi.getProject(parseInt(projectId || '0')),
        tasksApi.getTasks(parseInt(projectId || '0')),
      ])
      setProject(projectData)
      setTasks(tasksData)
    } catch (error) {
      console.error('Error loading data:', error)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    loadData()
  }, [loadData])

  const getTasksByStatus = (status: Task['status']) => {
    return tasks.filter((task) => task.status === status).sort((a, b) => a.position - b.position)
  }

  const handleDragStart = (e: React.DragEvent, task: Task) => {
    setDraggedTask(task)
    e.dataTransfer.effectAllowed = 'move'
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    e.dataTransfer.dropEffect = 'move'
  }

  const handleDrop = async (e: React.DragEvent, targetStatus: Task['status']) => {
    e.preventDefault()
    if (!draggedTask) return

    if (draggedTask.status === targetStatus) {
      setDraggedTask(null)
      return
    }

    try {
      // Calculate new position (put at end of column)
      const tasksInTargetColumn = getTasksByStatus(targetStatus)
      const newPosition = tasksInTargetColumn.length > 0
        ? Math.max(...tasksInTargetColumn.map(t => t.position)) + 1
        : 0

      // Update task status and position
      await tasksApi.updateTaskStatus(draggedTask.id, targetStatus, newPosition)

      // Reload tasks
      await loadData()
    } catch (error) {
      console.error('Error updating task:', error)
    } finally {
      setDraggedTask(null)
    }
  }

  const openModal = (task?: Task) => {
    if (task) {
      setEditingTask(task)
      setFormData({
        project: task.project,
        title: task.title,
        description: task.description,
        status: task.status,
        priority: task.priority,
        assigned_to: task.assigned_to,
        estimated_hours: task.estimated_hours,
        due_date: task.due_date,
      })
    } else {
      setEditingTask(null)
      setFormData({
        project: parseInt(projectId || '0'),
        title: '',
        description: '',
        status: 'todo',
        priority: 'medium',
        assigned_to: null,
        estimated_hours: null,
        due_date: null,
      })
    }
    setShowModal(true)
  }

  const resetForm = () => {
    setShowModal(false)
    setEditingTask(null)
    setFormData({
      project: parseInt(projectId || '0'),
      title: '',
      description: '',
      status: 'todo',
      priority: 'medium',
      assigned_to: null,
      estimated_hours: null,
      due_date: null,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      if (editingTask) {
        await tasksApi.updateTask(editingTask.id, formData)
      } else {
        await tasksApi.createTask(formData)
      }
      await loadData()
      resetForm()
    } catch (error) {
      console.error('Error saving task:', error)
    }
  }

  const handleDelete = async (id: number) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return
    try {
      await tasksApi.deleteTask(id)
      await loadData()
    } catch (error) {
      console.error('Error deleting task:', error)
    }
  }

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'urgent':
        return '#f56565'
      case 'high':
        return '#ed8936'
      case 'medium':
        return '#4299e1'
      case 'low':
        return '#718096'
      default:
        return '#718096'
    }
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="kanban-page">
      <div className="kanban-header">
        <div>
          <h1>{project?.name}</h1>
          <p className="project-code">{project?.project_code}</p>
        </div>
        <button onClick={() => openModal()} className="btn btn-primary">
          + Add Task
        </button>
      </div>

      <div className="kanban-board">
        {columns.map((column) => (
          <div
            key={column.id}
            className="kanban-column"
            onDragOver={handleDragOver}
            onDrop={(e) => handleDrop(e, column.id)}
          >
            <div className="column-header" style={{ borderTopColor: column.color }}>
              <h3>{column.title}</h3>
              <span className="task-count">{getTasksByStatus(column.id).length}</span>
            </div>

            <div className="column-tasks">
              {getTasksByStatus(column.id).map((task) => (
                <div
                  key={task.id}
                  className="task-card"
                  draggable
                  onDragStart={(e) => handleDragStart(e, task)}
                >
                  <div className="task-card-header">
                    <span
                      className="priority-badge"
                      style={{ backgroundColor: getPriorityColor(task.priority) }}
                    >
                      {task.priority}
                    </span>
                    {task.due_date && (
                      <span className="due-date">
                        📅 {new Date(task.due_date).toLocaleDateString()}
                      </span>
                    )}
                  </div>

                  <h4>{task.title}</h4>
                  {task.description && <p className="task-description">{task.description}</p>}

                  {task.estimated_hours && (
                    <div className="task-meta">
                      ⏱️ {task.estimated_hours}h estimated
                    </div>
                  )}

                  <div className="task-actions">
                    <button onClick={() => openModal(task)} className="btn-text">
                      Edit
                    </button>
                    <button onClick={() => handleDelete(task.id)} className="btn-text text-danger">
                      Delete
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {showModal && (
        <div className="modal-overlay" onClick={resetForm}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{editingTask ? 'Edit Task' : 'Create Task'}</h2>
              <button className="modal-close" onClick={resetForm}>
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="task-form">
              <div className="form-group">
                <label htmlFor="title">Title *</label>
                <input
                  id="title"
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
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
                      setFormData({ ...formData, status: e.target.value as Task['status'] })
                    }
                  >
                    <option value="todo">To Do</option>
                    <option value="in_progress">In Progress</option>
                    <option value="blocked">Blocked</option>
                    <option value="review">In Review</option>
                    <option value="done">Done</option>
                  </select>
                </div>

                <div className="form-group">
                  <label htmlFor="priority">Priority</label>
                  <select
                    id="priority"
                    value={formData.priority}
                    onChange={(e) =>
                      setFormData({ ...formData, priority: e.target.value as Task['priority'] })
                    }
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label htmlFor="estimated_hours">Estimated Hours</label>
                  <input
                    id="estimated_hours"
                    type="number"
                    step="0.25"
                    min="0"
                    value={formData.estimated_hours || ''}
                    onChange={(e) =>
                      setFormData({ ...formData, estimated_hours: e.target.value || null })
                    }
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="due_date">Due Date</label>
                  <input
                    id="due_date"
                    type="date"
                    value={formData.due_date || ''}
                    onChange={(e) => setFormData({ ...formData, due_date: e.target.value || null })}
                  />
                </div>
              </div>

              <div className="modal-actions">
                <button type="button" onClick={resetForm} className="btn btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  {editingTask ? 'Update' : 'Create'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default ProjectKanban
